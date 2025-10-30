# Tasks Database API

Minimal Flask API server offering CRUD for tasks stored in a SQLite database.

## Environment variables
- SQLITE_DB: Absolute or relative path to the SQLite database file (default: ./myapp.db)
- PORT: Port to run the API server on (default: 5001)

## Setup
1. Create a virtual environment and install dependencies:
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt

2. Initialize the database and create the tasks table:
   # optionally set custom location
   # export SQLITE_DB=/absolute/path/to/myapp.db
   python init_db.py

3. Start the API server:
   # optionally override port
   # export PORT=5001
   # optionally set DB path for the server (must match where you initialized)
   # export SQLITE_DB=/absolute/path/to/myapp.db
   python api_server.py

The server will be available at:
http://localhost:${PORT:-5001}

## API Endpoints
- GET    /api/tasks
- POST   /api/tasks        (JSON: { "title": "Task title", "completed": false })
- PUT    /api/tasks/:id    (JSON: { "title": "New title", "completed": true })
- PATCH  /api/tasks/:id/toggle
- DELETE /api/tasks/:id

Notes:
- The completed field is stored as INTEGER (0/1) in SQLite but exposed as boolean in the API.
- Timestamps are ISO strings.

## Table schema
Table: tasks
- id INTEGER PK AUTOINCREMENT
- title TEXT NOT NULL
- completed INTEGER DEFAULT 0
- created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
- updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

## Development tips
- Ensure SQLITE_DB is the same between init_db.py and the running api_server.py if you set a custom path.
- CORS is enabled for all origins for development convenience.
