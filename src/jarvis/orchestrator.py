"""Phase 1: text-only brain loop.

Run from the repo root:
    python -m jarvis.orchestrator
"""

import sys

from jarvis.brain import Brain


def main() -> None:
    print("Jarvis (Fase 1 — texto). Escreve 'sair' para terminar.\n")
    brain = Brain()

    while True:
        try:
            user_input = input("Tu: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nJarvis: Até logo!")
            sys.exit(0)

        if not user_input:
            continue

        if user_input.lower() in {"sair", "exit", "quit"}:
            print("Jarvis: Até logo!")
            break

        if user_input.lower() == "reset":
            brain.reset()
            print("Jarvis: Conversa reiniciada.\n")
            continue

        print("Jarvis: ", end="", flush=True)
        for token in brain.chat(user_input):
            print(token, end="", flush=True)
        print("\n")


if __name__ == "__main__":
    main()
