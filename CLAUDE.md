# CLAUDE.md

Operating instructions for Claude Code working in this repository.
For the full vision and reasoning, read `docs/JARVIS_CONTEXT.md` first — this file
is the **operational** layer (how to work here); that file is the **why**.

---

## What this project is

A personal, **voice-activated, fully local** AI assistant ("Jarvis"). Always-on,
private, free to run. It also grows into a system where each of my side-projects is
an "agent" that can report its state, with Jarvis as the orchestrator.

**One-line model:** `wake word → STT → local LLM → TTS`, split across two machines.

---

## Non-negotiable constraints

- **Free & local only.** Never add code that depends on a paid API or a cloud LLM
  (no OpenAI/Anthropic/Gemini billing). Inference is local via Ollama. If a task
  seems to need a paid/cloud service, stop and flag it instead of adding it.
- **Privacy.** Nothing leaves the LAN. No telemetry, no external logging.
- **European Portuguese (pt-PT)** for everything user-facing (TTS voice, prompts,
  assistant replies). **English** for code, comments, commits, and docs.
- **Modular & incremental.** Build in thin vertical slices, one phase at a time.
  Do not scaffold the whole "agent world" before the basic loop runs.
- **Honest trade-offs.** When there's an open decision (see below), surface options;
  don't silently pick one.

---

## Hardware & topology (architectural invariant)

| Role | Machine | Runs |
|------|---------|------|
| Front-end (always-on) | Raspberry Pi 5, 8GB | wake word, mic, STT, TTS, orchestrator |
| Brain (on-demand) | Laptop, RTX 3060 **6GB VRAM** | Ollama (the LLM) |

- The two talk over the **LAN via HTTP** (Ollama API, default port `11434`).
- **Never assume the laptop is awake.** The brain may be unreachable; handle it
  gracefully (clear spoken error, optional tiny fallback model on the Pi later).
- Pi OS: Raspberry Pi OS Lite (64-bit), headless, with the active cooler.

---

## Repository layout (target — scaffold as you go)

```
jarvis/
├── CLAUDE.md                 # this file
├── README.md
├── docs/
│   └── JARVIS_CONTEXT.md     # full vision / reasoning
├── config/
│   └── config.example.yaml   # LAPTOP_IP, OLLAMA_PORT, model, language, wakeword
├── src/jarvis/
│   ├── orchestrator.py       # main loop (Pi)
│   ├── wakeword.py           # openWakeWord ("hey jarvis")
│   ├── stt.py                # faster-whisper
│   ├── tts.py                # Piper (pt-PT voice)
│   ├── brain.py              # Ollama client (calls laptop over LAN)
│   └── memory/
│       ├── store.py          # SQLite project store
│       └── providers/        # one context provider per project-agent
├── scripts/
│   ├── setup_pi.sh
│   └── healthcheck.py        # verify Pi → laptop Ollama reachability
├── requirements.txt
└── pyproject.toml
```

Keep each pipeline stage behind a **small, swappable interface** (so the wake word,
STT, LLM, or TTS engine can each be replaced without touching the others).

---

## Tech stack (all free / open source)

- **Wake word:** openWakeWord (prebuilt "hey jarvis" model) — on Pi.
- **STT:** faster-whisper (tiny/base), configured for Portuguese — on Pi.
- **LLM runtime:** Ollama (CUDA) — on laptop.
- **TTS:** Piper, pt-PT voice — on Pi.
- **Orchestration:** custom Python service (preferred). Home Assistant "Assist" is a
  fallback shortcut but keep the custom path unless told otherwise.
- **Store:** SQLite to start. Postgres (already on the Pi for IRONLOG) is an option later.

### Model (6GB VRAM)
Target a **4B-class** model. Candidates to benchmark for pt-PT quality/speed:
Gemma 4 (E2B/E4B), Qwen3 4B, Phi-3.5 Mini, Llama 3.x 3B. Keep context ~4k.

---

## Conventions

- **Python 3.11+.** Type hints everywhere. Format with `ruff` / `black`. Small modules.
- **Config over hardcoding.** All host/IP/port/model/language values come from
  `config/config.yaml` (copied from `config.example.yaml`). Never hardcode the
  laptop's IP or the model name in source.
- **Latency:** stream TTS sentence-by-sentence while the LLM is still generating.
- **Fail loud, locally.** On any stage failure, speak a short pt-PT error; never crash silently.
- **No secrets in the repo.** `config.yaml` is git-ignored; only the `.example` is committed.

---

## Commands

> Most don't exist yet — Phase 0/1 create them. Use these names when scaffolding.

```bash
# On the laptop (brain):
ollama serve                          # start the LLM server
ollama run <model>                    # pull/run a model

# From the Pi, verify the brain is reachable over the LAN:
python scripts/healthcheck.py         # checks Ollama at LAPTOP_IP:11434
curl http://<LAPTOP_IP>:11434/api/tags

# Run the assistant (Pi):
python -m jarvis.orchestrator

# Dev:
ruff check . && black .
pytest                                # once tests exist
```

---

## Build plan — work one phase at a time

- **Phase 0 (current):** Pi OS Lite ready; Ollama answering on the laptop; Pi reaches
  it over the LAN (`healthcheck.py` green). Active cooler on.
- **Phase 1:** text-only brain — type on the Pi, get a pt-PT answer from the laptop LLM.
- **Phase 2:** memory — SQLite project store + context-provider pattern
  ("where did I leave off on X?").
- **Phase 3:** voice loop — openWakeWord → faster-whisper → brain → Piper, + streaming TTS.
- **Phase 4:** first project-agent = IRONLOG (existing PWA on the Pi) as a context provider.
- **Phase 5:** polish — autostart service, robustness, optional Pi fallback model.

**Always tell me which phase a change belongs to, and don't jump ahead.**

---

## Open decisions (flag, don't silently choose)

1. Orchestrator: custom Python vs Home Assistant Assist.
2. Store: SQLite vs reuse IRONLOG's PostgreSQL on the Pi.
3. Model: which 4B model wins on pt-PT quality/speed at 6GB VRAM.
4. IRONLOG placement: keep on the Pi (recommended, easy integration) vs move.

---

## About the developer (me)

Cybersecurity / OT engineer. Comfortable with Python, Node/Express, React+Vite+
Tailwind, PostgreSQL, Raspberry Pi / Linux servers, Tailscale, REST/WebSockets.
Built IRONLOG from scratch. Prefer simple, guided, well-explained steps — especially
for ML. Explain trade-offs; keep it free, local, and incremental.
