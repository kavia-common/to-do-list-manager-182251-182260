#!/usr/bin/env python3
"""
Verify that the 'tasks' table exists in the configured SQLite database.

Usage:
  - Optionally set SQLITE_DB to point to the database file
  - Run: python verify_tasks_table.py

Exit codes:
  0 -> tasks table exists
  1 -> tasks table missing or DB inaccessible
"""
import os
import sqlite3
import sys

# PUBLIC_INTERFACE
def verify() -> bool:
    """Check whether the 'tasks' table exists in the SQLite database."""
    db_path = os.environ.get("SQLITE_DB") or os.path.join(os.path.dirname(__file__), "myapp.db")
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='tasks' LIMIT 1")
        exists = cur.fetchone() is not None
        conn.close()
        print(f"DB: {db_path}")
        print("tasks table: PRESENT" if exists else "tasks table: MISSING")
        return exists
    except Exception as e:
        print(f"Error accessing database: {e}")
        return False

if __name__ == "__main__":
    ok = verify()
    sys.exit(0 if ok else 1)
