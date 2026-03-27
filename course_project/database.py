"""
SQLite game state and chat memory utilities.
"""

import sqlite3
from pathlib import Path
from typing import List, Tuple


class GameStateDB:
    """Simple SQLite-backed memory for sessions, turns, and quest progress."""

    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _initialize(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS turns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    message TEXT NOT NULL,
                    scenario TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS quests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    quest_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    notes TEXT DEFAULT ''
                )
                """
            )

    def log_turn(self, session_id: str, role: str, message: str, scenario: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO turns (session_id, role, message, scenario) VALUES (?, ?, ?, ?)",
                (session_id, role, message, scenario),
            )

    def set_quest_status(self, session_id: str, quest_name: str, status: str, notes: str = "") -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "DELETE FROM quests WHERE session_id = ? AND quest_name = ?",
                (session_id, quest_name),
            )
            conn.execute(
                "INSERT INTO quests (session_id, quest_name, status, notes) VALUES (?, ?, ?, ?)",
                (session_id, quest_name, status, notes),
            )

    def get_recent_turns(self, session_id: str, limit: int = 8) -> List[Tuple[str, str]]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT role, message
                FROM turns
                WHERE session_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (session_id, limit),
            ).fetchall()

        rows.reverse()
        return rows

    def get_quests(self, session_id: str) -> List[Tuple[str, str, str]]:
        with sqlite3.connect(self.db_path) as conn:
            return conn.execute(
                "SELECT quest_name, status, notes FROM quests WHERE session_id = ? ORDER BY id DESC",
                (session_id,),
            ).fetchall()
