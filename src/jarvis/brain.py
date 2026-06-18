"""Ollama client — streams responses from the laptop LLM over the LAN."""

import json
import sys
from pathlib import Path
from typing import Iterator

import requests
import yaml

CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "config.yaml"
REQUEST_TIMEOUT = 60  # seconds; LLM first-token latency can be a few seconds

SYSTEM_PROMPT = (
    "És o Jarvis, um assistente pessoal inteligente. "
    "Responde sempre em português europeu (pt-PT), de forma concisa e direta. "
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

    def chat(self, user_message: str) -> Iterator[str]:
        """Send *user_message* and yield response tokens as they stream in.

        On connection failure, yields a Portuguese error message instead of raising.
        """
        self._history.append({"role": "user", "content": user_message})

        try:
            resp = requests.post(
                f"{self.base_url}/api/chat",
                json={"model": self.model, "messages": self._history, "stream": True},
                stream=True,
                timeout=REQUEST_TIMEOUT,
            )
            resp.raise_for_status()
        except requests.exceptions.ConnectionError:
            self._history.pop()
            yield "[Erro: não consigo ligar ao cérebro. O portátil está ligado e o Ollama a correr?]"
            return
        except requests.exceptions.Timeout:
            self._history.pop()
            yield "[Erro: o cérebro demorou demasiado a responder.]"
            return
        except requests.exceptions.HTTPError as exc:
            self._history.pop()
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

        self._history.append({"role": "assistant", "content": full_response})

    def reset(self) -> None:
        """Clear conversation history (keeps system prompt)."""
        self._history = [self._history[0]]
