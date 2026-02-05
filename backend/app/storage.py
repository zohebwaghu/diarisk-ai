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
                    lab_insights_json TEXT,
                    retinal_json TEXT,
                    cognitive_json TEXT,
                    agent_trace_json TEXT,
                    risks_json TEXT NOT NULL,
                    recommendations_json TEXT NOT NULL,
                    warnings_json TEXT NOT NULL
                )
                """
            )
            self._ensure_column(conn, "analysis_history", "cognitive_json", "TEXT")
            self._ensure_column(conn, "analysis_history", "lab_insights_json", "TEXT")
            self._ensure_column(conn, "analysis_history", "agent_trace_json", "TEXT")
            conn.commit()

    def _ensure_column(self, conn: sqlite3.Connection, table: str, column: str, col_type: str) -> None:
        cursor = conn.execute(f"PRAGMA table_info({table})")
        columns = {row[1] for row in cursor.fetchall()}
        if column not in columns:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")

    def insert_analysis(
        self,
        labs: Dict[str, Any],
        lab_insights: Dict[str, Any] | None,
        retinal: Dict[str, Any] | None,
        cognitive: Dict[str, Any] | None,
        risks: Dict[str, Any],
        recommendations: List[Dict[str, Any]],
        agent_trace: List[Dict[str, Any]],
        warnings: List[str],
    ) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO analysis_history
                (created_at, labs_json, lab_insights_json, retinal_json, cognitive_json,
                 agent_trace_json, risks_json, recommendations_json, warnings_json)
                VALUES (datetime('now'), ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    json.dumps(labs),
                    json.dumps(lab_insights) if lab_insights else None,
                    json.dumps(retinal) if retinal else None,
                    json.dumps(cognitive) if cognitive else None,
                    json.dumps(agent_trace),
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
                SELECT id, created_at, labs_json, lab_insights_json, retinal_json, cognitive_json,
                       agent_trace_json, risks_json, recommendations_json, warnings_json
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
                    "lab_insights": json.loads(row[3]) if row[3] else None,
                    "retinal": json.loads(row[4]) if row[4] else None,
                    "cognitive": json.loads(row[5]) if row[5] else None,
                    "agent_trace": json.loads(row[6]) if row[6] else [],
                    "risk_scores": json.loads(row[7]),
                    "recommendations": json.loads(row[8]),
                    "warnings": json.loads(row[9]),
                }
            )
        return results
