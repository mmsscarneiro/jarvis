"""Speech-to-text via faster-whisper.

Records audio from the default microphone, detects end-of-speech via
energy-based silence detection, then transcribes with Whisper.
"""

import threading
from pathlib import Path
from typing import Optional

import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel

SAMPLE_RATE = 16_000       # Hz — Whisper expects 16 kHz mono
CHUNK = 512                # frames per callback
SILENCE_RMS = 0.01         # RMS below this = silence
SILENCE_SECONDS = 1.2      # stop after this many consecutive silent seconds
MAX_SECONDS = 30           # hard cap on recording duration

_model: Optional[WhisperModel] = None
_model_lock = threading.Lock()


def _get_model(size: str = "base") -> WhisperModel:
    global _model
    with _model_lock:
        if _model is None:
            _model = WhisperModel(size, device="cpu", compute_type="int8")
    return _model


def record(max_seconds: float = MAX_SECONDS) -> np.ndarray:
    """Record from the default mic until silence or *max_seconds*. Returns float32 mono array."""
    chunks: list[np.ndarray] = []
    silent_frames = 0
    silent_limit = int(SILENCE_SECONDS * SAMPLE_RATE / CHUNK)
    max_frames = int(max_seconds * SAMPLE_RATE / CHUNK)
    done = threading.Event()

    def callback(indata: np.ndarray, frames: int, time, status) -> None:
        nonlocal silent_frames
        audio = indata[:, 0].copy()
        chunks.append(audio)
        rms = float(np.sqrt(np.mean(audio ** 2)))
        if rms < SILENCE_RMS:
            silent_frames += 1
        else:
            silent_frames = 0
        if silent_frames >= silent_limit or len(chunks) >= max_frames:
            done.set()

    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="float32",
        blocksize=CHUNK,
        callback=callback,
    ):
        done.wait()

    return np.concatenate(chunks) if chunks else np.zeros(SAMPLE_RATE, dtype="float32")


def transcribe(audio: np.ndarray, language: str = "pt") -> str:
    """Transcribe *audio* (float32 16 kHz mono) and return the text."""
    model = _get_model()
    segments, _ = model.transcribe(
        audio,
        language=language,
        beam_size=5,
        vad_filter=True,          # skip silent parts
        vad_parameters={"min_silence_duration_ms": 300},
    )
    return " ".join(s.text for s in segments).strip()


def listen(language: str = "pt") -> str:
    """Record until silence and return the transcribed text. Convenience wrapper."""
    audio = record()
    return transcribe(audio, language=language)
