from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List

from app import config


class SQLiteStore:
    def __init__(self) -> None:
        self.db_path = Path(config.DB_PATH)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS analysis_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    labs_json TEXT NOT NULL,
                    retinal_json TEXT,
                    risks_json TEXT NOT NULL,
                    recommendations_json TEXT NOT NULL,
                    warnings_json TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def insert_analysis(
        self,
        labs: Dict[str, Any],
        retinal: Dict[str, Any] | None,
        risks: Dict[str, Any],
        recommendations: List[Dict[str, Any]],
        warnings: List[str],
    ) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO analysis_history
                (created_at, labs_json, retinal_json, risks_json, recommendations_json, warnings_json)
                VALUES (datetime('now'), ?, ?, ?, ?, ?)
                """,
                (
                    json.dumps(labs),
                    json.dumps(retinal) if retinal else None,
                    json.dumps(risks),
                    json.dumps(recommendations),
                    json.dumps(warnings),
                ),
            )
            conn.commit()
            return int(cursor.lastrowid)

    def fetch_recent(self, limit: int = 10) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT id, created_at, labs_json, retinal_json, risks_json, recommendations_json, warnings_json
                FROM analysis_history
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            )
            rows = cursor.fetchall()

        results = []
        for row in rows:
            results.append(
                {
                    "id": row[0],
                    "created_at": row[1],
                    "labs": json.loads(row[2]),
                    "retinal": json.loads(row[3]) if row[3] else None,
                    "risk_scores": json.loads(row[4]),
                    "recommendations": json.loads(row[5]),
                    "warnings": json.loads(row[6]),
                }
            )
        return results
