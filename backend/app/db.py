import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from .config import DATA_DIR, ensure_data_dirs, settings


def _db_path() -> Path:
    if settings.database_url.startswith("sqlite:///"):
        return Path(settings.database_url.replace("sqlite:///", "", 1))
    return DATA_DIR / "sentinelai.db"


@contextmanager
def get_db() -> Iterator[sqlite3.Connection]:
    ensure_data_dirs()
    conn = sqlite3.connect(_db_path())
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    ensure_data_dirs()
    with get_db() as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS assets (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                sport TEXT,
                owner TEXT,
                filename TEXT NOT NULL,
                file_path TEXT NOT NULL,
                synthid_token TEXT NOT NULL,
                ai_summary TEXT NOT NULL,
                structured_analysis TEXT NOT NULL,
                content_passport TEXT NOT NULL DEFAULT '[]',
                passport_embedding TEXT NOT NULL DEFAULT '[]',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS asset_keyframes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_id TEXT NOT NULL,
                frame_index INTEGER NOT NULL,
                timestamp_ms INTEGER NOT NULL,
                dhash TEXT NOT NULL,
                evidence_path TEXT,
                FOREIGN KEY(asset_id) REFERENCES assets(id)
            );

            CREATE TABLE IF NOT EXISTS violations (
                id TEXT PRIMARY KEY,
                asset_id TEXT NOT NULL,
                suspect_id TEXT NOT NULL,
                platform TEXT NOT NULL,
                url TEXT NOT NULL,
                title TEXT NOT NULL,
                mutation_type TEXT NOT NULL,
                status TEXT NOT NULL,
                stage TEXT NOT NULL,
                confidence_visual REAL NOT NULL,
                confidence_semantic REAL NOT NULL,
                confidence_audio REAL NOT NULL,
                confidence_gemini REAL NOT NULL,
                confidence_overall REAL NOT NULL,
                synthid_match INTEGER NOT NULL DEFAULT 0,
                dhash_distance INTEGER NOT NULL DEFAULT 64,
                embedding_similarity REAL NOT NULL DEFAULT 0,
                semantic_description_similarity REAL NOT NULL DEFAULT 0,
                audio_transcript_match REAL NOT NULL DEFAULT 0,
                explanation TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(asset_id) REFERENCES assets(id)
            );

            CREATE TABLE IF NOT EXISTS audit_log (
                id TEXT PRIMARY KEY,
                stage_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                video_hash TEXT NOT NULL,
                similarity_score REAL NOT NULL,
                decision TEXT NOT NULL,
                estimated_cost_usd REAL NOT NULL,
                matched_asset_id TEXT NOT NULL,
                suspect_id TEXT NOT NULL,
                details TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS graph_nodes (
                id TEXT PRIMARY KEY,
                asset_id TEXT NOT NULL,
                label TEXT NOT NULL,
                type TEXT NOT NULL,
                metadata TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS graph_edges (
                id TEXT PRIMARY KEY,
                asset_id TEXT NOT NULL,
                source TEXT NOT NULL,
                target TEXT NOT NULL,
                relation TEXT NOT NULL,
                weight REAL NOT NULL
            );
            """
        )
        _ensure_columns(
            db,
            "assets",
            {
                "content_passport": "TEXT NOT NULL DEFAULT '[]'",
                "passport_embedding": "TEXT NOT NULL DEFAULT '[]'",
            },
        )
        _ensure_columns(
            db,
            "violations",
            {
                "synthid_match": "INTEGER NOT NULL DEFAULT 0",
                "dhash_distance": "INTEGER NOT NULL DEFAULT 64",
                "embedding_similarity": "REAL NOT NULL DEFAULT 0",
                "semantic_description_similarity": "REAL NOT NULL DEFAULT 0",
                "audio_transcript_match": "REAL NOT NULL DEFAULT 0",
            },
        )


def _ensure_columns(db: sqlite3.Connection, table: str, columns: dict[str, str]) -> None:
    existing = {row["name"] for row in db.execute(f"PRAGMA table_info({table})")}
    for name, definition in columns.items():
        if name not in existing:
            db.execute(f"ALTER TABLE {table} ADD COLUMN {name} {definition}")
