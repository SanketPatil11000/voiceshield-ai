
import sqlite3
from pathlib import Path
from datetime import datetime, timezone

DB_PATH = Path(__file__).resolve().parent / "voiceshield.db"


def get_connection():
    return sqlite3.connect(DB_PATH, timeout=10)


def initialize_database():
    """Create the history table if it does not exist."""
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS analysis_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                filename TEXT NOT NULL,
                prediction TEXT NOT NULL,
                score REAL NOT NULL,
                duration REAL NOT NULL
            )
        """)


def save_analysis(filename, prediction, score, duration):
    """Save analysis metadata, not the audio recording."""
    created_at = datetime.now(timezone.utc).isoformat()

    with get_connection() as connection:
        connection.execute("""
            INSERT INTO analysis_history (
                created_at,
                filename,
                prediction,
                score,
                duration
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            created_at,
            filename,
            prediction,
            float(score),
            float(duration),
        ))


def get_history(limit=50):
    """Return the most recent analysis records."""
    with get_connection() as connection:
        rows = connection.execute("""
            SELECT id, created_at, filename,
                   prediction, score, duration
            FROM analysis_history
            ORDER BY id DESC
            LIMIT ?
        """, (limit,)).fetchall()

    columns = [
        "ID",
        "Date (UTC)",
        "Filename",
        "Model label",
        "Model score",
        "Duration (seconds)",
    ]

    return [dict(zip(columns, row)) for row in rows]
