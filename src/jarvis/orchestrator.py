"""Phase 1+2: text brain loop with project memory.

Run from the repo root:
    python -m jarvis.orchestrator

Memory commands (case-insensitive):
    nova ideia: <nome> - <descrição>     → save a new idea
    novo projeto: <nome> - <descrição>   → save a new active project
    lista projetos                       → show all projects
    contexto <nome>                      → summarise a project (LLM gets the stored data)
    contexto <nome>: <pergunta>          → ask something about a project with its context injected
    atualiza <nome>: <campo> = <valor>   → update a project field
    apaga projeto: <nome>                → delete a project
    reset                                → clear conversation history
    sair / exit / quit                   → exit
"""

import re
import sys
from typing import Optional

from jarvis.brain import Brain
from jarvis.memory.providers import get_provider
from jarvis.memory.store import FIELD_MAP, VALID_STATUSES, Store

# ── command patterns ──────────────────────────────────────────────────────────
_RE_NOVA_IDEIA   = re.compile(r'^nova ideia:\s*(.+?)(?:\s*[-–]\s*(.+))?$', re.I)
_RE_NOVO_PROJETO = re.compile(r'^novo projeto:\s*(.+?)(?:\s*[-–]\s*(.+))?$', re.I)
_RE_LISTA        = re.compile(r'^lista projetos?$', re.I)
_RE_CONTEXTO     = re.compile(r'^contexto\s+(.+?)(?::\s*(.+))?$', re.I)
_RE_ATUALIZA     = re.compile(r'^atualiza\s+(.+?):\s*(.+?)\s*[=:]\s*(.+)$', re.I)
_RE_APAGA        = re.compile(r'^apaga projeto:\s*(.+)$', re.I)


def _print_jarvis(text: str) -> None:
    print(f"Jarvis: {text}\n")


def _stream_jarvis(brain: Brain, message: str, context: Optional[str] = None) -> None:
    print("Jarvis: ", end="", flush=True)
    for token in brain.chat(message, context=context):
        print(token, end="", flush=True)
    print("\n")


def handle_input(raw: str, brain: Brain, store: Store) -> bool:
    """Process one line of user input. Returns False to exit."""
    text = raw.strip()

    if not text:
        return True

    low = text.lower()
    if low in {"sair", "exit", "quit"}:
        _print_jarvis("Até logo!")
        return False

    if low == "reset":
        brain.reset()
        _print_jarvis("Conversa reiniciada.")
        return True

    # lista projetos
    if _RE_LISTA.match(text):
        projects = store.list_all()
        if not projects:
            _print_jarvis("Ainda não tens nenhum projeto guardado.")
        else:
            lines = "\n".join(p.to_summary_line() for p in projects)
            _print_jarvis(f"Os teus projetos:\n{lines}")
        return True

    # nova ideia: nome - descrição
    m = _RE_NOVA_IDEIA.match(text)
    if m:
        name, goal = m.group(1).strip(), (m.group(2) or "").strip()
        try:
            store.create(name, goal=goal, status="idea")
            _print_jarvis(f"Ideia '{name}' guardada!")
        except Exception:
            _print_jarvis(f"Já existe um projeto chamado '{name}'.")
        return True

    # novo projeto: nome - descrição
    m = _RE_NOVO_PROJETO.match(text)
    if m:
        name, goal = m.group(1).strip(), (m.group(2) or "").strip()
        try:
            store.create(name, goal=goal, status="active")
            _print_jarvis(f"Projeto '{name}' criado!")
        except Exception:
            _print_jarvis(f"Já existe um projeto chamado '{name}'.")
        return True

    # contexto <nome> / contexto <nome>: <pergunta>
    m = _RE_CONTEXTO.match(text)
    if m:
        name, question = m.group(1).strip(), (m.group(2) or "").strip()
        provider = get_provider(name, store)
        if provider is None:
            _print_jarvis(f"Não encontrei nenhum projeto chamado '{name}'.")
            return True
        context = provider()
        if question:
            _stream_jarvis(brain, question, context=context)
        else:
            # No question — show context and let the LLM summarise it
            _stream_jarvis(
                brain,
                f"Resume o estado atual do projeto '{name}' de forma casual.",
                context=context,
            )
        return True

    # atualiza <nome>: <campo> = <valor>
    m = _RE_ATUALIZA.match(text)
    if m:
        name = m.group(1).strip()
        field_raw = m.group(2).strip().lower()
        value = m.group(3).strip()
        column = FIELD_MAP.get(field_raw)
        if column is None:
            valid = ", ".join(sorted(set(FIELD_MAP.keys())))
            _print_jarvis(f"Campo desconhecido '{field_raw}'. Campos válidos: {valid}")
            return True
        if column == "status" and value not in VALID_STATUSES:
            _print_jarvis(
                f"Estado inválido '{value}'. Usa: {', '.join(sorted(VALID_STATUSES))}"
            )
            return True
        updated = store.update(name, **{column: value})
        if updated is None:
            _print_jarvis(f"Projeto '{name}' não encontrado.")
        else:
            _print_jarvis(f"'{name}' atualizado!")
        return True

    # apaga projeto: <nome>
    m = _RE_APAGA.match(text)
    if m:
        name = m.group(1).strip()
        if store.delete(name):
            _print_jarvis(f"Projeto '{name}' apagado.")
        else:
            _print_jarvis(f"Projeto '{name}' não encontrado.")
        return True

    # Default: send to LLM
    _stream_jarvis(brain, text)
    return True


def main() -> None:
    print("Jarvis. Escreve 'ajuda' para ver os comandos de memória, 'sair' para terminar.\n")
    brain = Brain()
    store = Store()

    while True:
        try:
            user_input = input("Tu: ")
        except (EOFError, KeyboardInterrupt):
            print("\nJarvis: Até logo!")
            sys.exit(0)

        if user_input.strip().lower() == "ajuda":
            print(
                "\nComandos de memória:"
                "\n  nova ideia: <nome> - <descrição>"
                "\n  novo projeto: <nome> - <descrição>"
                "\n  lista projetos"
                "\n  contexto <nome>"
                "\n  contexto <nome>: <pergunta>"
                "\n  atualiza <nome>: <campo> = <valor>"
                "\n    campos: objetivo, estado, onde ficou, próximo passo, notas"
                "\n    estados: idea, exploring, active, paused, dead"
                "\n  apaga projeto: <nome>"
                "\n  reset  — limpa o histórico de conversa"
                "\n  sair\n"
            )
            continue

        if not handle_input(user_input, brain, store):
            break


if __name__ == "__main__":
    main()
