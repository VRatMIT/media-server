import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from rapidfuzz import process, utils

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"


def data_dir() -> Path:
    return REPO_ROOT / "data"

def videos_dir() -> Path:
    return data_dir() / "videos"

def incoming_dir() -> Path:
    return data_dir() / "incoming"


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(data_dir() / "matrix.db", timeout=5)
    conn.row_factory = sqlite3.Row
    return conn

# I'm honestly still not super sure how this works. From my understanding, opens
# a connection, that can be used with the Python with keyword. If failed, then
# rolls back and closes.
@contextmanager
def transaction():
    conn = connect()
    try:
        with conn:
            yield conn
    finally:
        conn.close()


# Called at startup
def init():
    for directory in (data_dir(), videos_dir(), incoming_dir()):
        directory.mkdir(parents=True, exist_ok=True)

    with transaction() as conn:
        conn.execute("PRAGMA journal_mode = WAL")
        conn.executescript(SCHEMA_PATH.read_text())


# Videos
def add_video(title: str, filename: str, user_id: int) -> int:
    with transaction() as conn:
        cur = conn.execute(
            "INSERT INTO videos (title, filename, uploaded_by) VALUES (?, ?, ?)",
            (title, filename, user_id),
        )
        return cur.lastrowid

def get_video(title: str) -> sqlite3.Row | None:
    with transaction() as conn:
        return conn.execute("SELECT * FROM videos WHERE title = ?", (title,)).fetchone()

def search_videos(search: str, limit: int = 25) -> list[sqlite3.Row]:
    with transaction() as conn:
        return conn.execute(
            "SELECT * FROM videos WHERE title LIKE ? ORDER BY title LIMIT ?",
            (f"%{search}%", limit),
        ).fetchall()

def search_videos_fuzzy(search: str, limit: int = 25) -> list[tuple[str, float, int]]:
    # This fetch could start taking long as we increase the library size. Consider altering eimplemneation in the future.
    with transaction() as conn:
        candidates = conn.execute("SELECT title FROM videos").fetchall()

    candidates_titles = [row["title"] for row in candidates]

    hits = process.extract(search, candidates_titles, limit=limit, processor=utils.default_process, score_cutoff=60)

    return hits
