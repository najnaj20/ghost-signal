"""SQLite access. Schema follows PRD.md section 7 exactly."""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "ghost-signal.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY,
    source TEXT NOT NULL,
    source_type TEXT NOT NULL,
    title TEXT,
    url TEXT NOT NULL UNIQUE,
    published_at TEXT,
    collected_at TEXT NOT NULL,
    raw_text TEXT,
    cleaned_text TEXT,
    language TEXT NOT NULL DEFAULT 'en'
);
CREATE TABLE IF NOT EXISTS entities (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('company','technology','disease','product','person')),
    first_seen_at TEXT,
    mention_count INTEGER NOT NULL DEFAULT 0,
    UNIQUE (name, type)
);
CREATE TABLE IF NOT EXISTS relations (
    id INTEGER PRIMARY KEY,
    doc_id INTEGER NOT NULL REFERENCES documents(id),
    entity_a_id INTEGER NOT NULL REFERENCES entities(id),
    entity_b_id INTEGER NOT NULL REFERENCES entities(id),
    relation_label TEXT NOT NULL,
    claim_text TEXT NOT NULL,
    evidence_quote TEXT NOT NULL CHECK (length(evidence_quote) > 0),
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS scores (
    entity_id INTEGER NOT NULL REFERENCES entities(id),
    date TEXT NOT NULL,
    novelty REAL NOT NULL,
    velocity REAL NOT NULL,
    corroboration REAL NOT NULL,
    weirdness REAL NOT NULL,
    ghost_score REAL NOT NULL,
    PRIMARY KEY (entity_id, date)
);
CREATE TABLE IF NOT EXISTS watchlist (
    entity_id INTEGER PRIMARY KEY REFERENCES entities(id),
    added_at TEXT NOT NULL
);
"""


def connect(path=DB_PATH):
    if str(path) != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    con.execute("PRAGMA foreign_keys = ON")
    con.executescript(SCHEMA)
    return con
