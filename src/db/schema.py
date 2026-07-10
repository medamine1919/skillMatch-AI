from __future__ import annotations

from src.db.connection import get_connection


def initialize_database() -> None:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        '''
        CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            file_name TEXT,
            input_mode TEXT,
            raw_requirement TEXT,
            cv_json TEXT,
            requirement_json TEXT,
            result_json TEXT
        )
        '''
    )

    conn.commit()
    conn.close()
