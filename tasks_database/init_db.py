#!/usr/bin/env python3
"""Initialize SQLite database for tasks_database, including the 'tasks' table.
This script is safe to run multiple times (idempotent). It will:
- Create required tables if they do not exist
- Leave existing data intact
- Print a clear confirmation that the 'tasks' table exists
"""

import sqlite3
import os
from typing import Tuple

# Allow overriding DB path via env var for consistency with the API server
DB_NAME = os.environ.get("SQLITE_DB") or "myapp.db"
DB_USER = "kaviasqlite"  # Not used for SQLite, but kept for consistency
DB_PASSWORD = "kaviadefaultpassword"  # Not used for SQLite, but kept for consistency
DB_PORT = "5000"  # Not used for SQLite, but kept for consistency

print("Starting SQLite setup...")

# Check if database already exists
db_exists = os.path.exists(DB_NAME)
if db_exists:
    print(f"SQLite database already exists at {DB_NAME}")
    # Verify it's accessible
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.execute("SELECT 1")
        conn.close()
        print("Database is accessible and working.")
    except Exception as e:
        print(f"Warning: Database exists but may be corrupted: {e}")
else:
    print("Creating new SQLite database...")

# Create database with sample tables
conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

# Enable foreign keys for completeness
cursor.execute("PRAGMA foreign_keys = ON")

# Create initial schema
cursor.execute("""
    CREATE TABLE IF NOT EXISTS app_info (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key TEXT UNIQUE NOT NULL,
        value TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

# Create a sample users table as an example
cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

# Create the tasks table idempotently
cursor.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        completed INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

# Insert initial data
cursor.execute("INSERT OR REPLACE INTO app_info (key, value) VALUES (?, ?)", 
               ("project_name", "tasks_database"))
cursor.execute("INSERT OR REPLACE INTO app_info (key, value) VALUES (?, ?)", 
               ("version", "0.1.0"))
cursor.execute("INSERT OR REPLACE INTO app_info (key, value) VALUES (?, ?)", 
               ("author", "John Doe"))
cursor.execute("INSERT OR REPLACE INTO app_info (key, value) VALUES (?, ?)", 
               ("description", ""))

conn.commit()

def table_exists(cur, name: str) -> bool:
    """Return True if a table with given name exists."""
    cur.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1",
        (name,),
    )
    return cur.fetchone() is not None

def count_tables_and_appinfo(cur) -> Tuple[int, int]:
    """Return counts for user tables and app_info rows."""
    cur.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    table_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM app_info")
    record_count = cur.fetchone()[0]
    return table_count, record_count

# Verify tasks table existence (idempotency confirmation)
tasks_exists = table_exists(cursor, "tasks")
if tasks_exists:
    print("✓ Verified: 'tasks' table exists.")
else:
    # This should not happen as we just created with IF NOT EXISTS, but handle defensively
    print("✗ Warning: 'tasks' table was not found; attempting to create again.")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            completed INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    tasks_exists = table_exists(cursor, "tasks")
    print("✓ Created and verified: 'tasks' table exists." if tasks_exists else "✗ Error: Unable to verify 'tasks' table.")

# Get database statistics
table_count, record_count = count_tables_and_appinfo(cursor)

conn.close()

# Save connection information to a file (use absolute path to avoid ambiguity)
current_dir = os.getcwd()
abs_db_path = os.path.abspath(DB_NAME)
connection_string = f"sqlite:///{abs_db_path}"

try:
    with open("db_connection.txt", "w") as f:
        f.write(f"# SQLite connection methods:\n")
        f.write(f"# Python: sqlite3.connect('{abs_db_path}')\n")
        f.write(f"# Connection string: {connection_string}\n")
        f.write(f"# File path: {abs_db_path}\n")
    print("Connection information saved to db_connection.txt")
except Exception as e:
    print(f"Warning: Could not save connection info: {e}")

# Create environment variables file for Node.js viewer
db_path = abs_db_path

# Ensure db_visualizer directory exists
if not os.path.exists("db_visualizer"):
    os.makedirs("db_visualizer", exist_ok=True)
    print("Created db_visualizer directory")

try:
    with open("db_visualizer/sqlite.env", "w") as f:
        f.write(f"export SQLITE_DB=\"{db_path}\"\n")
    print(f"Environment variables saved to db_visualizer/sqlite.env")
except Exception as e:
    print(f"Warning: Could not save environment variables: {e}")

print("\nSQLite setup complete!")
print(f"Database file: {abs_db_path}")
print("")
print("Idempotency check:")
print(f"  tasks table present: {'YES' if tasks_exists else 'NO'}")
print("")
print("Database statistics:")
print(f"  Tables: {table_count}")
print(f"  app_info records: {record_count}")
print("")
print("To use with Node.js viewer, run: source db_visualizer/sqlite.env")
print("\nTo connect to the database, use one of the following methods:")
print(f"1. Python: sqlite3.connect('{abs_db_path}')")
print(f"2. Connection string: {connection_string}")
print(f"3. Direct file access: {abs_db_path}")
print("")

# If sqlite3 CLI is available, show how to use it
try:
    import subprocess
    result = subprocess.run(['which', 'sqlite3'], capture_output=True, text=True)
    if result.returncode == 0:
        print("SQLite CLI is available. You can also use:")
        print(f"  sqlite3 {abs_db_path}")
except Exception:
    pass

# Exit successfully
print("\nScript completed successfully.")
