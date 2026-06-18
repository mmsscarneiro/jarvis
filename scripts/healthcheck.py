#!/usr/bin/env python3
"""Verify that this machine can reach the laptop's Ollama service over the LAN.

Usage (from the repo root):
    python scripts/healthcheck.py
"""

import sys
from pathlib import Path

import requests
import yaml

CONFIG_PATH = Path(__file__).parent.parent / "config" / "config.yaml"
TIMEOUT = 5  # seconds


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        sys.exit(
            f"Config not found: {CONFIG_PATH}\n"
            "Copy config/config.example.yaml → config/config.yaml and fill in LAPTOP_IP."
        )
    with CONFIG_PATH.open() as f:
        return yaml.safe_load(f)


def main() -> None:
    cfg = load_config()
    brain = cfg["brain"]
    base_url = f"http://{brain['laptop_ip']}:{brain['ollama_port']}"
    tags_url = f"{base_url}/api/tags"

    print(f"Pinging Ollama at {base_url} ...")

    try:
        resp = requests.get(tags_url, timeout=TIMEOUT)
        resp.raise_for_status()
    except requests.exceptions.ConnectionError:
        sys.exit(
            f"[FAIL] Cannot reach {base_url}.\n"
            "       Is the laptop awake? Is 'ollama serve' running?"
        )
    except requests.exceptions.Timeout:
        sys.exit(
            f"[FAIL] Timed out after {TIMEOUT}s.\n"
            "       Check LAN connectivity and firewall rules (port 11434)."
        )
    except requests.exceptions.HTTPError as exc:
        sys.exit(f"[FAIL] Ollama returned an HTTP error: {exc}")

    models = [m["name"] for m in resp.json().get("models", [])]
    print("[OK]   Ollama is reachable.")

    if models:
        print(f"       Available models: {', '.join(models)}")
    else:
        print("       No models pulled yet. Run on the laptop: ollama pull <model>")

    target = brain.get("model")
    if target:
        if any(m == target or m.startswith(target + ":") for m in models):
            print(f"       Target model '{target}' is ready.")
        else:
            print(
                f"[WARN] Target model '{target}' not found locally.\n"
                f"       Run on the laptop: ollama pull {target}"
            )


if __name__ == "__main__":
    main()
