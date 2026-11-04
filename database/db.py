"""
SQLite Database module for Klein AI — ResearchMate AI.
Handles persistence of research sessions, telemetry, and artifact records.
"""
import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
import config


def get_connection():
    conn = sqlite3.connect(str(config.DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initializes the research_sessions database table with auto-migration for new columns."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS research_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                topic TEXT NOT NULL,
                title TEXT NOT NULL,
                sources_count INTEGER DEFAULT 0,
                is_demo_mode INTEGER DEFAULT 0,
                data_json TEXT NOT NULL,
                pdf_path TEXT,
                pptx_path TEXT
            )
        """)
        conn.commit()

        # Check existing table columns and add any missing ones
        cursor.execute("PRAGMA table_info(research_sessions)")
        existing_cols = {col["name"] for col in cursor.fetchall()}

        if "depth" not in existing_cols:
            cursor.execute("ALTER TABLE research_sessions ADD COLUMN depth TEXT DEFAULT 'Standard'")
        if "gaps_count" not in existing_cols:
            cursor.execute("ALTER TABLE research_sessions ADD COLUMN gaps_count INTEGER DEFAULT 0")

        conn.commit()


def save_session(report_data: Dict[str, Any], depth: str = "Standard", pdf_path: str = "", pptx_path: str = "") -> int:
    """Saves a completed research session."""
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        topic = report_data.get("topic", "Untitled Topic")
        title = report_data.get("title", topic)
        sources_count = report_data.get("sources_count", len(report_data.get("references", [])))
        gaps_count = len(report_data.get("research_gaps", []))
        is_demo = 1 if report_data.get("is_demo_mode") else 0
        json_str = json.dumps(report_data)

        cursor.execute("""
            INSERT INTO research_sessions (timestamp, topic, title, depth, sources_count, gaps_count, is_demo_mode, data_json, pdf_path, pptx_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (now_str, topic, title, depth, sources_count, gaps_count, is_demo, json_str, pdf_path, pptx_path))
        conn.commit()
        return cursor.lastrowid


def get_all_sessions() -> List[Dict[str, Any]]:
    """Retrieves all past research sessions sorted newest first."""
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, timestamp, topic, title, depth, sources_count, gaps_count, is_demo_mode, pdf_path, pptx_path
            FROM research_sessions
            ORDER BY id DESC
        """)
        rows = cursor.fetchall()
        return [dict(r) for r in rows]


def get_session_by_id(session_id: int) -> Optional[Dict[str, Any]]:
    """Retrieves complete session data by ID."""
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM research_sessions WHERE id = ?", (session_id,))
        row = cursor.fetchone()
        if not row:
            return None
        res = dict(row)
        res["report_data"] = json.loads(res["data_json"])
        return res


def delete_session(session_id: int):
    """Deletes a research session by ID."""
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM research_sessions WHERE id = ?", (session_id,))
        conn.commit()


def clear_all_sessions():
    """Clears all research sessions from the database."""
    init_db()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM research_sessions")
        conn.commit()

