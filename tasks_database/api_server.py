import os
import sqlite3
from flask import Flask, request, jsonify
from flask_cors import CORS

DB_PATH = os.environ.get("SQLITE_DB", "./myapp.db")

def get_db_connection():
    """Create a new SQLite connection with row factory for dict-like access."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the SQLite database with tasks table if not exists."""
    conn = get_db_connection()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                completed INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        conn.commit()
    finally:
        conn.close()

app = Flask(__name__)

# Configure CORS
origins = os.environ.get("CORS_ORIGINS")
if origins:
    origins_list = [o.strip() for o in origins.split(",") if o.strip()]
    CORS(app, resources={r"/*": {"origins": origins_list}})
else:
    # Allow all origins in development if not specified
    CORS(app)

@app.get("/health")
def health():
    """
    Health check endpoint.
    Returns 200 OK if the service is up.
    """
    return jsonify({"status": "ok"}), 200

# PUBLIC_INTERFACE
@app.get("/tasks")
def list_tasks():
    """List all tasks."""
    conn = get_db_connection()
    try:
        rows = conn.execute("SELECT id, title, completed FROM tasks ORDER BY id DESC").fetchall()
        tasks = [{"id": r["id"], "title": r["title"], "completed": bool(r["completed"])} for r in rows]
        return jsonify(tasks), 200
    finally:
        conn.close()

# PUBLIC_INTERFACE
@app.post("/tasks")
def create_task():
    """Create a new task from JSON body: { "title": "..." }"""
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    if not title:
        return jsonify({"error": "Title is required"}), 400

    conn = get_db_connection()
    try:
        cur = conn.execute("INSERT INTO tasks (title, completed) VALUES (?, ?)", (title, 0))
        conn.commit()
        task_id = cur.lastrowid
        row = conn.execute("SELECT id, title, completed FROM tasks WHERE id = ?", (task_id,)).fetchone()
        task = {"id": row["id"], "title": row["title"], "completed": bool(row["completed"])}
        return jsonify(task), 201
    finally:
        conn.close()

# PUBLIC_INTERFACE
@app.put("/tasks/<int:task_id>")
def update_task(task_id: int):
    """Update a task by id. Body may include 'title' and/or 'completed'."""
    data = request.get_json(silent=True) or {}
    fields = []
    values = []

    if "title" in data:
        title = (data.get("title") or "").strip()
        if not title:
            return jsonify({"error": "Title cannot be empty"}), 400
        fields.append("title = ?")
        values.append(title)
    if "completed" in data:
        completed = 1 if bool(data.get("completed")) else 0
        fields.append("completed = ?")
        values.append(completed)

    if not fields:
        return jsonify({"error": "No fields to update"}), 400

    conn = get_db_connection()
    try:
        values.append(task_id)
        conn.execute(f"UPDATE tasks SET {', '.join(fields)} WHERE id = ?", values)
        conn.commit()
        row = conn.execute("SELECT id, title, completed FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if not row:
            return jsonify({"error": "Task not found"}), 404
        task = {"id": row["id"], "title": row["title"], "completed": bool(row["completed"])}
        return jsonify(task), 200
    finally:
        conn.close()

# PUBLIC_INTERFACE
@app.patch("/tasks/<int:task_id>/toggle")
def toggle_task(task_id: int):
    """Toggle the 'completed' state of a task by id."""
    conn = get_db_connection()
    try:
        row = conn.execute("SELECT completed FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if not row:
            return jsonify({"error": "Task not found"}), 404
        new_state = 0 if bool(row["completed"]) else 1
        conn.execute("UPDATE tasks SET completed = ? WHERE id = ?", (new_state, task_id))
        conn.commit()
        row = conn.execute("SELECT id, title, completed FROM tasks WHERE id = ?", (task_id,)).fetchone()
        task = {"id": row["id"], "title": row["title"], "completed": bool(row["completed"])}
        return jsonify(task), 200
    finally:
        conn.close()

# PUBLIC_INTERFACE
@app.delete("/tasks/<int:task_id>")
def delete_task(task_id: int):
    """Delete a task by id."""
    conn = get_db_connection()
    try:
        cur = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
        if cur.rowcount == 0:
            return jsonify({"error": "Task not found"}), 404
        return jsonify({"status": "deleted"}), 200
    finally:
        conn.close()

def main():
    """Entrypoint to start the Flask app, binding to PORT from environment."""
    init_db()
    port = int(os.environ.get("PORT", "5001"))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()
