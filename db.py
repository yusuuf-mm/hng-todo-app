"""All SQLite access lives here.

app.py must never import sqlite3 directly. To swap to a hosted DB
(Neon / Supabase / Turso) later, keep these function names and
signatures and replace the internals only.
"""

import os
import sqlite3

# Allowed list filter values. Anything else falls back to "all".
FILTERS = ("all", "active", "completed")


def get_db_path() -> str:
    """Resolve the SQLite file path.

    Priority: TODO_DB_PATH env var (local override / tests) >
    /tmp/todo.db when VERCEL is set (read-only FS elsewhere) >
    todo.db in the repo root for normal local dev.
    """
    override = os.environ.get("TODO_DB_PATH")
    if override:
        return override
    if os.environ.get("VERCEL"):
        return "/tmp/todo.db"
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(here, "todo.db")


def get_conn() -> sqlite3.Connection:
    """Open a connection with Row access (row["title"] style)."""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create the tasks table if it does not exist.

    Called once at app startup and on Vercel cold starts.
    """
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                done INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def get_tasks(filter: str = "all") -> list[sqlite3.Row]:
    """Return tasks for a filter: all / active / completed (newest last)."""
    if filter not in FILTERS:
        filter = "all"
    with get_conn() as conn:
        if filter == "active":
            rows = conn.execute("SELECT * FROM tasks WHERE done = 0 ORDER BY id ASC").fetchall()
        elif filter == "completed":
            rows = conn.execute("SELECT * FROM tasks WHERE done = 1 ORDER BY id ASC").fetchall()
        else:
            rows = conn.execute("SELECT * FROM tasks ORDER BY id ASC").fetchall()
    return rows


def get_task(task_id: int) -> sqlite3.Row | None:
    """Return one task by id, or None."""
    with get_conn() as conn:
        return conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()


def add_task(title: str) -> int:
    """Insert a stripped title. Caller validates non-empty / length."""
    with get_conn() as conn:
        cur = conn.execute("INSERT INTO tasks (title, done) VALUES (?, 0)", (title,))
        return cur.lastrowid


def toggle_task(task_id: int) -> None:
    """Flip done between 0 and 1 for one task."""
    with get_conn() as conn:
        conn.execute("UPDATE tasks SET done = 1 - done WHERE id = ?", (task_id,))


def update_title(task_id: int, title: str) -> None:
    """Replace a task's title. Caller validates non-empty / length."""
    with get_conn() as conn:
        conn.execute("UPDATE tasks SET title = ? WHERE id = ?", (title, task_id))


def delete_task(task_id: int) -> None:
    """Delete one task by id."""
    with get_conn() as conn:
        conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))


def clear_completed() -> None:
    """Delete all completed tasks."""
    with get_conn() as conn:
        conn.execute("DELETE FROM tasks WHERE done = 1")


def get_counts() -> dict:
    """Return {"total": n, "active": n, "completed": n} for the tab badges."""
    with get_conn() as conn:
        total = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        completed = conn.execute("SELECT COUNT(*) FROM tasks WHERE done = 1").fetchone()[0]
    return {"total": total, "active": total - completed, "completed": completed}
