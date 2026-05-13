import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'digest.db')


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS seen_articles (
                url TEXT PRIMARY KEY,
                title TEXT,
                seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS digests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                articles_json TEXT NOT NULL
            )
        ''')


def has_seen(url: str) -> bool:
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute('SELECT 1 FROM seen_articles WHERE url = ?', (url,))
        return cur.fetchone() is not None


def mark_seen(url: str, title: str):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            'INSERT OR IGNORE INTO seen_articles (url, title) VALUES (?, ?)',
            (url, title)
        )


def save_digest(articles_json: str):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('INSERT INTO digests (articles_json) VALUES (?)', (articles_json,))


def get_latest_digest():
    """Returns (articles_json, created_at) or None."""
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            'SELECT articles_json, created_at FROM digests ORDER BY created_at DESC LIMIT 1'
        )
        return cur.fetchone()
