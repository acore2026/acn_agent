from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from threading import Lock


@dataclass(frozen=True)
class StoredAgent:
    """One locally persisted agent row."""

    owner: str
    agent_id: str
    agent_name: str
    description: str


class AgentRepository:
    """SQLite-backed local persistence for registered agents."""

    def __init__(self, db_path: str) -> None:
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()
        self._init_db()

    def upsert_agent(self, owner: str, agent_id: str, agent_name: str, description: str) -> None:
        """Insert or update one agent, matching by agent_id."""
        with self._lock, sqlite3.connect(self._db_path) as conn:
            cursor = conn.execute("SELECT agent_id FROM agents WHERE agent_id = ?", (agent_id,))
            existing_agent = cursor.fetchone()
            if existing_agent:
                conn.execute(
                    """
                    UPDATE agents
                    SET owner = ?, agent_name = ?, description = ?
                    WHERE agent_id = ?
                    """,
                    (owner, agent_name, description, agent_id),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO agents (owner, agent_id, agent_name, description)
                    VALUES (?, ?, ?, ?)
                    """,
                    (owner, agent_id, agent_name, description),
                )
            conn.commit()

    def delete_agent(self, agent_id: str) -> None:
        """Delete one agent row by agent_id."""
        with self._lock, sqlite3.connect(self._db_path) as conn:
            conn.execute("DELETE FROM agents WHERE agent_id = ?", (agent_id,))
            conn.commit()

    def list_agents_by_owner(self, owner: str) -> list[StoredAgent]:
        """Return locally persisted agents for one owner."""
        with self._lock, sqlite3.connect(self._db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT owner, agent_id, agent_name, description
                FROM agents
                WHERE owner = ?
                ORDER BY agent_id
                """,
                (owner,),
            ).fetchall()
        return [
            StoredAgent(
                owner=row["owner"],
                agent_id=row["agent_id"],
                agent_name=row["agent_name"] or "",
                description=row["description"] or "",
            )
            for row in rows
        ]

    def clear(self) -> int:
        """Delete all locally persisted agent rows."""
        with self._lock, sqlite3.connect(self._db_path) as conn:
            cursor = conn.execute("DELETE FROM agents")
            conn.commit()
        return cursor.rowcount if cursor.rowcount >= 0 else 0

    def _init_db(self) -> None:
        with self._lock, sqlite3.connect(self._db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS agents (
                    agent_id TEXT PRIMARY KEY,
                    owner TEXT NOT NULL,
                    agent_name TEXT NOT NULL,
                    description TEXT NOT NULL
                )
                """
            )
            conn.commit()
