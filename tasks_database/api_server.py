#!/usr/bin/env python3
"""
Flask API server providing CRUD operations for tasks stored in a SQLite database.

Environment variables:
- SQLITE_DB: Path to the SQLite database file (default: ./myapp.db relative to this script)
- PORT: Port for the HTTP server (default: 5001)

Routes:
- GET    /api/tasks                       -> List all tasks
- POST   /api/tasks                       -> Create a new task (JSON: {title: str, completed?: bool})
- PUT    /api/tasks/<int:task_id>         -> Update task (JSON: {title?: str, completed?: bool})
- PATCH  /api/tasks/<int:task_id>/toggle  -> Toggle completed state
- DELETE /api/tasks/<int:task_id>         -> Delete task

Notes:
- The 'completed' field is stored as INTEGER 0/1 in SQLite and mapped to boolean in API.
- Uses per-request SQLite connections with row_factory for dict-like access.
"""

import os
import sqlite3
from datetime import datetime
from typing import Dict, Any, Optional

from flask import Flask, jsonify, request
from flask_cors import CORS

# App initialization with OpenAPI-like metadata style in comments
app = Flask(
    __name__,
)
# Enable CORS for development
CORS(app)

# Configuration via environment variables
DEFAULT_DB = os.environ.get("SQLITE_DB") or os.path.join(os.path.dirname(__file__), "myapp.db")
DEFAULT_PORT = int(os.environ.get("PORT") or "5001")


def get_db_path() -> str:
    """Resolve the SQLite DB path from env or default."""
    return os.environ.get("SQLITE_DB", DEFAULT_DB)


def get_connection() -> sqlite3.Connection:
    """Create a new SQLite connection with sensible pragmas."""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    # Enable foreign keys and better concurrency
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    return conn


def row_to_task(row: sqlite3.Row) -> Dict[str, Any]:
    """Convert a SQLite row to a task dictionary with boolean completed."""
    return {
        "id": row["id"],
        "title": row["title"],
        "completed": bool(row["completed"] or 0),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def get_task_by_id(conn: sqlite3.Connection, task_id: int) -> Optional[Dict[str, Any]]:
    """Fetch a task by id, return None if not found."""
    cur = conn.execute("SELECT id, title, completed, created_at, updated_at FROM tasks WHERE id = ?", (task_id,))
    row = cur.fetchone()
    return row_to_task(row) if row else None


# PUBLIC_INTERFACE
@app.get("/api/tasks")
def list_tasks():
    """List all tasks.
    Returns:
      200: JSON list of task objects
    """
    conn = get_connection()
    try:
        cur = conn.execute("SELECT id, title, completed, created_at, updated_at FROM tasks ORDER BY created_at DESC, id DESC")
        tasks = [row_to_task(r) for r in cur.fetchall()]
        return jsonify(tasks), 200
    finally:
        conn.close()


# PUBLIC_INTERFACE
@app.post("/api/tasks")
def create_task():
    """Create a new task.
    Request JSON:
      - title: string, required
      - completed: boolean, optional
    Returns:
      201: Created task object
      400: Bad request if missing/invalid data
    """
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    if not title:
        return jsonify({"error": "title is required"}), 400
    completed = 1 if bool(data.get("completed", False)) else 0

    now_iso = datetime.utcnow().isoformat(timespec="seconds")
    conn = get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO tasks (title, completed, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (title, completed, now_iso, now_iso),
        )
        task_id = cur.lastrowid
        conn.commit()
        task = get_task_by_id(conn, task_id)
        return jsonify(task), 201
    finally:
        conn.close()


# PUBLIC_INTERFACE
@app.put("/api/tasks/<int:task_id>")
def update_task(task_id: int):
    """Update a task's title and/or completed state.
    Request JSON:
      - title: string, optional
      - completed: boolean, optional
    Returns:
      200: Updated task object
      400: Bad request (no fields provided)
      404: Not found
    """
    data = request.get_json(silent=True) or {}
    fields = []
    params = []

    if "title" in data:
        title = (data.get("title") or "").strip()
        if not title:
            return jsonify({"error": "title cannot be empty"}), 400
        fields.append("title = ?")
        params.append(title)

    if "completed" in data:
        completed = 1 if bool(data.get("completed")) else 0
        fields.append("completed = ?")
        params.append(completed)

    if not fields:
        return jsonify({"error": "no fields to update"}), 400

    fields.append("updated_at = ?")
    params.append(datetime.utcnow().isoformat(timespec="seconds"))
    params.append(task_id)

    conn = get_connection()
    try:
        cur = conn.execute(f"UPDATE tasks SET {', '.join(fields)} WHERE id = ?", tuple(params))
        if cur.rowcount == 0:
            conn.rollback()
            return jsonify({"error": "task not found"}), 404
        conn.commit()
        task = get_task_by_id(conn, task_id)
        return jsonify(task), 200
    finally:
        conn.close()


# PUBLIC_INTERFACE
@app.patch("/api/tasks/<int:task_id>/toggle")
def toggle_task(task_id: int):
    """Toggle the 'completed' state of a task by id.
    Returns:
      200: Updated task object
      404: Not found
    """
    conn = get_connection()
    try:
        # Get current value
        cur = conn.execute("SELECT completed FROM tasks WHERE id = ?", (task_id,))
        row = cur.fetchone()
        if not row:
            return jsonify({"error": "task not found"}), 404

        new_val = 0 if (row["completed"] or 0) else 1
        conn.execute(
            "UPDATE tasks SET completed = ?, updated_at = ? WHERE id = ?",
            (new_val, datetime.utcnow().isoformat(timespec="seconds"), task_id),
        )
        conn.commit()
        task = get_task_by_id(conn, task_id)
        return jsonify(task), 200
    finally:
        conn.close()


# PUBLIC_INTERFACE
@app.delete("/api/tasks/<int:task_id>")
def delete_task(task_id: int):
    """Delete a task by id.
    Returns:
      204: No Content on success
      404: Not found
    """
    conn = get_connection()
    try:
        cur = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        if cur.rowcount == 0:
            conn.rollback()
            return jsonify({"error": "task not found"}), 404
        conn.commit()
        return "", 204
    finally:
        conn.close()


def ensure_tasks_table():
    """Ensure the tasks table exists to avoid boot failures."""
    conn = get_connection()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                completed INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    # Ensure DB file and tasks table exist
    # If DB path does not exist, SQLite will create it on first connection.
    ensure_tasks_table()
    app.run(host="0.0.0.0", port=DEFAULT_PORT, debug=False)
