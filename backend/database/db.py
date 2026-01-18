import sqlite3
import json
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager
from typing import Optional

# Database file path
DB_PATH = Path(__file__).parent / "gallery.db"


def get_connection():
    """Get a database connection."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def get_db():
    """Context manager for database connections."""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Initialize the database and create tables if they don't exist."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS saved_animations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                animation_data TEXT NOT NULL,
                cppn_data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)


def save_animation(animation_data: dict, cppn_data: dict) -> int:
    """
    Save an animation to the database.

    Args:
        animation_data: Animation JSON data (frames, positions, colors)
        cppn_data: CPPN network structure JSON data

    Returns:
        The ID of the saved animation
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO saved_animations (animation_data, cppn_data)
            VALUES (?, ?)
            """,
            (json.dumps(animation_data), json.dumps(cppn_data))
        )
        return cursor.lastrowid


def get_animations_list(offset: int = 0, limit: int = 50) -> list:
    """
    Get a list of saved animations (id and created_at only).

    Args:
        offset: Number of items to skip
        limit: Maximum number of items to return

    Returns:
        List of animations with id and created_at
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, created_at
            FROM saved_animations
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """,
            (limit, offset)
        )
        rows = cursor.fetchall()
        return [{"id": row["id"], "created_at": row["created_at"]} for row in rows]


def get_animation(animation_id: int) -> Optional[dict]:
    """
    Get a single animation by ID.

    Args:
        animation_id: The ID of the animation to retrieve

    Returns:
        Animation data including animation_data and cppn_data, or None if not found
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, animation_data, cppn_data, created_at
            FROM saved_animations
            WHERE id = ?
            """,
            (animation_id,)
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return {
            "id": row["id"],
            "animation_data": json.loads(row["animation_data"]),
            "cppn_data": json.loads(row["cppn_data"]),
            "created_at": row["created_at"]
        }


def delete_animation(animation_id: int) -> bool:
    """
    Delete an animation by ID.

    Args:
        animation_id: The ID of the animation to delete

    Returns:
        True if deleted, False if not found
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM saved_animations WHERE id = ?",
            (animation_id,)
        )
        return cursor.rowcount > 0


# Initialize database on module import
init_db()
