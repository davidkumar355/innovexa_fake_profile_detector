"""
HistoryStore: Persists prediction interactions (browse/simulate) to SQLite.
"""

import os
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Any

from app.config import settings

class HistoryStore:
    _instance: Optional["HistoryStore"] = None

    def __init__(self):
        self.db_path = settings.DATABASE_PATH
        self._init_db()

    @classmethod
    def get_instance(cls) -> "HistoryStore":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS detection_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                node_id INTEGER,
                mode TEXT NOT NULL,
                prediction INTEGER NOT NULL,
                prediction_label TEXT NOT NULL,
                risk_score REAL NOT NULL,
                confidence REAL NOT NULL,
                archetype TEXT,
                model_version TEXT NOT NULL,
                details TEXT,
                timestamp TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()

    def record_prediction(
        self,
        mode: str,
        prediction: int,
        prediction_label: str,
        risk_score: float,
        confidence: float,
        model_version: str,
        node_id: Optional[int] = None,
        archetype: Optional[str] = None,
        details: Optional[str] = None
    ) -> int:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO detection_history
            (node_id, mode, prediction, prediction_label, risk_score, confidence, archetype, model_version, details, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (node_id, mode, prediction, prediction_label, risk_score, confidence, archetype, model_version, details, now_str))
        inserted_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return inserted_id

    def list_history(
        self,
        mode: Optional[str] = None,
        prediction: Optional[int] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = "SELECT * FROM detection_history WHERE 1=1"
        params = []
        if mode:
            query += " AND mode = ?"
            params.append(mode)
        if prediction is not None:
            query += " AND prediction = ?"
            params.append(prediction)

        count_query = query.replace("SELECT *", "SELECT COUNT(*)")
        cursor.execute(count_query, params)
        total = cursor.fetchone()[0]

        query += " ORDER BY id DESC LIMIT ? OFFSET ?"
        offset = (page - 1) * page_size
        params.extend([page_size, offset])

        cursor.execute(query, params)
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()

        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "items": rows
        }
