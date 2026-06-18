"""SQLite-backed project store."""

import datetime
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

DB_PATH = Path(__file__).parent.parent.parent.parent / "data" / "jarvis.db"

# Maps Portuguese field names → SQLite column names
FIELD_MAP: dict[str, str] = {
    "objetivo": "goal",
    "goal": "goal",
    "estado": "status",
    "status": "status",
    "onde ficou": "where_i_left_off",
    "where_i_left_off": "where_i_left_off",
    "próximo passo": "next_step",
    "proximo passo": "next_step",
    "next_step": "next_step",
    "notas": "notes",
    "notes": "notes",
}

VALID_STATUSES = {"idea", "exploring", "active", "paused", "dead"}


@dataclass
class Project:
    name: str
    goal: str = ""
    status: str = "idea"
    where_i_left_off: str = ""
    next_step: str = ""
    notes: str = ""
    created_at: str = ""
    updated_at: str = ""
    id: Optional[int] = None

    def to_context_text(self) -> str:
        lines = [f"Projeto: {self.name}"]
        if self.goal:
            lines.append(f"Objetivo: {self.goal}")
        lines.append(f"Estado: {self.status}")
        if self.where_i_left_off:
            lines.append(f"Onde ficou: {self.where_i_left_off}")
        if self.next_step:
            lines.append(f"Próximo passo: {self.next_step}")
        if self.notes:
            lines.append(f"Notas: {self.notes}")
        if self.updated_at:
            lines.append(f"Atualizado: {self.updated_at[:10]}")
        return "\n".join(lines)

    def to_summary_line(self) -> str:
        goal_part = f" — {self.goal}" if self.goal else ""
        return f"  [{self.status}] {self.name}{goal_part}"


class Store:
    def __init__(self, db_path: Path = DB_PATH) -> None:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._migrate()

    def _migrate(self) -> None:
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id                INTEGER PRIMARY KEY AUTOINCREMENT,
                name              TEXT NOT NULL UNIQUE,
                goal              TEXT DEFAULT '',
                status            TEXT DEFAULT 'idea',
                where_i_left_off  TEXT DEFAULT '',
                next_step         TEXT DEFAULT '',
                notes             TEXT DEFAULT '',
                created_at        TEXT DEFAULT (datetime('now')),
                updated_at        TEXT DEFAULT (datetime('now'))
            )
        """)
        self._conn.commit()

    def _row_to_project(self, row: sqlite3.Row) -> Project:
        return Project(**dict(row))

    def create(self, name: str, goal: str = "", status: str = "idea", **kwargs) -> Project:
        now = datetime.datetime.utcnow().isoformat(timespec="seconds")
        self._conn.execute(
            """INSERT INTO projects
               (name, goal, status, where_i_left_off, next_step, notes, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (name, goal, status,
             kwargs.get("where_i_left_off", ""),
             kwargs.get("next_step", ""),
             kwargs.get("notes", ""),
             now, now),
        )
        self._conn.commit()
        return self.get_by_name(name)

    def get_by_name(self, name: str) -> Optional[Project]:
        row = self._conn.execute(
            "SELECT * FROM projects WHERE name LIKE ?", (name,)
        ).fetchone()
        return self._row_to_project(row) if row else None

    def list_all(self) -> list[Project]:
        rows = self._conn.execute(
            "SELECT * FROM projects ORDER BY updated_at DESC"
        ).fetchall()
        return [self._row_to_project(r) for r in rows]

    def update(self, name: str, **fields) -> Optional[Project]:
        if not fields:
            return self.get_by_name(name)
        now = datetime.datetime.utcnow().isoformat(timespec="seconds")
        set_clause = ", ".join(f"{k} = ?" for k in fields)
        values = list(fields.values()) + [now, name]
        self._conn.execute(
            f"UPDATE projects SET {set_clause}, updated_at = ? WHERE name LIKE ?",
            values,
        )
        self._conn.commit()
        return self.get_by_name(name)

    def delete(self, name: str) -> bool:
        cur = self._conn.execute(
            "DELETE FROM projects WHERE name LIKE ?", (name,)
        )
        self._conn.commit()
        return cur.rowcount > 0

    def names(self) -> list[str]:
        rows = self._conn.execute("SELECT name FROM projects").fetchall()
        return [r["name"] for r in rows]
