"""Context provider interface.

A ContextProvider is any callable that returns the current state of a
project as a plain-text string. The default reads from SQLite.
Future providers (e.g. IRONLOG) can return richer, live data.
"""

from typing import Callable, Optional

from jarvis.memory.store import Project, Store

ContextProvider = Callable[[], str]


def store_provider(project: Project) -> ContextProvider:
    """Wraps a Project snapshot as a provider."""
    def _provide() -> str:
        return project.to_context_text()
    return _provide


def get_provider(name: str, store: Store) -> Optional[ContextProvider]:
    """Return the best available provider for *name*, or None if unknown."""
    project = store.get_by_name(name)
    if project is None:
        return None
    # Phase 4 will register custom providers here (e.g. IRONLOG live data)
    return store_provider(project)
