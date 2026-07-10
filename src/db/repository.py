from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from src.db.connection import get_connection


def save_analysis(
    file_name: str,
    input_mode: str,
    raw_requirement: str,
    cv_json: dict[str, Any],
    requirement_json: dict[str, Any],
    result_json: dict[str, Any],
) -> int:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        '''
        INSERT INTO analyses (
            created_at, file_name, input_mode, raw_requirement, cv_json, requirement_json, result_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''',
        (
            datetime.utcnow().isoformat(),
            file_name,
            input_mode,
            raw_requirement,
            json.dumps(cv_json, ensure_ascii=False),
            json.dumps(requirement_json, ensure_ascii=False),
            json.dumps(result_json, ensure_ascii=False),
        ),
    )

    analysis_id = cur.lastrowid
    conn.commit()
    conn.close()
    return int(analysis_id)


def list_analyses(limit: int = 20) -> list[dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        '''
        SELECT id, created_at, file_name, input_mode, result_json
        FROM analyses
        ORDER BY id DESC
        LIMIT ?
        ''',
        (limit,),
    )
    rows = cur.fetchall()
    conn.close()

    results: list[dict[str, Any]] = []
    for row in rows:
        parsed_result = json.loads(row["result_json"]) if row["result_json"] else {}
        results.append(
            {
                "id": row["id"],
                "created_at": row["created_at"],
                "file_name": row["file_name"],
                "input_mode": row["input_mode"],
                "result": parsed_result,
            }
        )
    return results


def get_analysis(analysis_id: int) -> dict[str, Any] | None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM analyses WHERE id = ?", (analysis_id,))
    row = cur.fetchone()
    conn.close()

    if row is None:
        return None

    return {
        "id": row["id"],
        "created_at": row["created_at"],
        "file_name": row["file_name"],
        "input_mode": row["input_mode"],
        "raw_requirement": row["raw_requirement"],
        "cv_json": json.loads(row["cv_json"]) if row["cv_json"] else {},
        "requirement_json": json.loads(row["requirement_json"]) if row["requirement_json"] else {},
        "result_json": json.loads(row["result_json"]) if row["result_json"] else {},
    }
