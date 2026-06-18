"""Ollama client — streams responses from the laptop LLM over the LAN."""

import json
import sys
import time
from pathlib import Path
from typing import Iterator, Optional

import requests
import yaml

CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "config.yaml"
REQUEST_TIMEOUT = 60  # seconds

SYSTEM_PROMPT = (
    "És o Jarvis, o assistente pessoal do teu utilizador. "
    "Fala sempre em português europeu (pt-PT), de forma casual e descontraída — "
    "como um amigo inteligente. Usa 'tu', frases curtas e vai direto ao assunto. "
    "Nunca respondas em inglês, mesmo que a pergunta seja em inglês."
)


def _load_config() -> dict:
    if not CONFIG_PATH.exists():
        sys.exit(
            f"Config não encontrado: {CONFIG_PATH}\n"
            "Copia config/config.example.yaml → config/config.yaml e preenche os valores."
        )
    with CONFIG_PATH.open() as f:
        return yaml.safe_load(f)


class Brain:
    """Stateful Ollama chat client. Keeps conversation history in memory."""

    def __init__(self) -> None:
        cfg = _load_config()
        b = cfg["brain"]
        self.base_url = f"http://{b['laptop_ip']}:{b['ollama_port']}"
        self.model: str = b["model"]
        self._history: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]
        self.last_latency_ms: int = 0

    def chat(self, user_message: str, context: Optional[str] = None) -> Iterator[str]:
        """Send *user_message* and yield response tokens as they stream in.

        *context* is injected as a temporary system note for this turn only —
        it does not get stored in the conversation history.
        """
        # Build per-request messages without mutating history yet
        messages = list(self._history)
        if context:
            messages.append({
                "role": "system",
                "content": f"Contexto relevante para esta resposta:\n{context}",
            })
        messages.append({"role": "user", "content": user_message})

        _start = time.monotonic()
        try:
            resp = requests.post(
                f"{self.base_url}/api/chat",
                json={"model": self.model, "messages": messages, "stream": True},
                stream=True,
                timeout=REQUEST_TIMEOUT,
            )
            resp.raise_for_status()
        except requests.exceptions.ConnectionError:
            self.last_latency_ms = round((time.monotonic() - _start) * 1000)
            yield "[Erro: não consigo ligar ao cérebro. O portátil está ligado e o Ollama a correr?]"
            return
        except requests.exceptions.Timeout:
            self.last_latency_ms = round((time.monotonic() - _start) * 1000)
            yield "[Erro: o cérebro demorou demasiado a responder.]"
            return
        except requests.exceptions.HTTPError as exc:
            self.last_latency_ms = round((time.monotonic() - _start) * 1000)
            yield f"[Erro do Ollama: {exc}]"
            return

        full_response = ""
        for line in resp.iter_lines():
            if not line:
                continue
            data = json.loads(line)
            token: str = data.get("message", {}).get("content", "")
            if token:
                full_response += token
                yield token
            if data.get("done"):
                break

        self.last_latency_ms = round((time.monotonic() - _start) * 1000)
        # Persist only the actual user/assistant exchange — not the ephemeral context
        self._history.append({"role": "user", "content": user_message})
        self._history.append({"role": "assistant", "content": full_response})

    def reset(self) -> None:
        """Clear conversation history, keeping the system prompt."""
        self._history = [self._history[0]]
