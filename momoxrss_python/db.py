import sqlite3
from pathlib import Path
from contextlib import contextmanager
from typing import Generator

DB_PATH = Path(__file__).parent / "data" / "sent_items.db"

@contextmanager
def get_db_connection() -> Generator[sqlite3.Connection, None, None]:
    """Context manager pour la connexion à la base de données."""
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
    finally:
        conn.close()

def init_db() -> None:
    """Initialise la base de données."""
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS sent_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                flux_id TEXT NOT NULL,
                item_url TEXT NOT NULL UNIQUE,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

def mark_as_sent(flux_id: str, item_url: str) -> None:
    """Marque un élément comme envoyé dans la base de données."""
    with get_db_connection() as conn:
        c = conn.cursor()
        try:
            c.execute("INSERT INTO sent_items (flux_id, item_url) VALUES (?, ?)", (flux_id, item_url))
            conn.commit()
        except sqlite3.IntegrityError:
            pass

def already_sent(item_url: str) -> bool:
    """Vérifie si un élément a déjà été envoyé."""
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT 1 FROM sent_items WHERE item_url = ?", (item_url,))
        return c.fetchone() is not None

def cleanup_old_entries(days: int = 7) -> int:
    """Nettoie les anciennes entrées de la base de données."""
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM sent_items WHERE sent_at < datetime('now', ?)", (f'-{days} days',))
        deleted = c.rowcount
        conn.commit()
        return deleted
