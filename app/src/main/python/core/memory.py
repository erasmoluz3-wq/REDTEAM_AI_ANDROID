import sqlite3
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
DB_DIR = ROOT / "memory"
DB_PATH = DB_DIR / "redteam.db"

DB_DIR.mkdir(parents=True, exist_ok=True)


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    return conn


def remember(content):
    content = str(content).strip()
    if not content:
        raise ValueError("Memória vazia.")

    with connect() as conn:
        conn.execute(
            "INSERT INTO memories (content, created_at) VALUES (?, ?)",
            (content, datetime.now(timezone.utc).isoformat())
        )


def search_memory(term):
    with connect() as conn:
        return conn.execute(
            """SELECT id, content, created_at
               FROM memories
               WHERE content LIKE ?
               ORDER BY id DESC LIMIT 20""",
            (f"%{term}%",)
        ).fetchall()


def list_memories():
    with connect() as conn:
        return conn.execute(
            """SELECT id, content, created_at
               FROM memories ORDER BY id DESC LIMIT 50"""
        ).fetchall()


def save_message(role, content):
    if role not in ("user", "assistant"):
        raise ValueError("Papel inválido.")

    content = str(content).strip()
    if not content:
        return

    with connect() as conn:
        conn.execute(
            """INSERT INTO chat_history
               (role, content, created_at) VALUES (?, ?, ?)""",
            (role, content, datetime.now(timezone.utc).isoformat())
        )


def load_recent_messages(limit=18):
    limit = max(1, min(int(limit), 100))

    with connect() as conn:
        rows = conn.execute(
            """SELECT role, content FROM chat_history
               ORDER BY id DESC LIMIT ?""",
            (limit,)
        ).fetchall()

    rows.reverse()
    return [
        {"role": role, "content": content}
        for role, content in rows
    ]


def clear_chat_history():
    with connect() as conn:
        conn.execute("DELETE FROM chat_history")
