# Tasks Database API (Flask + SQLite)

This service exposes a simple REST API for managing to-do tasks backed by SQLite.

## Environment Variables

Create a `.env` file in this directory (already provided) with:

- `PORT=5001` — The port the server listens on.
- `SQLITE_DB=./myapp.db` — SQLite database file path.
- `CORS_ORIGINS=http://localhost:3000` — Optional. Comma-separated list of allowed origins for CORS.

## REST Endpoints

These endpoints are aligned with the frontend (to_do_list_frontend/src/api.js):

- GET    `/tasks` — List all tasks.
- POST   `/tasks` — Create a new task. Body: `{ "title": "..." }`.
- PUT    `/tasks/{id}` — Update a task by id. Body: `{ "title": "...", "completed": true|false }` (fields optional).
- PATCH  `/tasks/{id}/toggle` — Toggle completion.
- DELETE `/tasks/{id}` — Delete a task.

Return payloads are JSON.

## Running

- Make sure Python dependencies are installed for Flask, CORS, and SQLite usage (e.g., flask, flask-cors).
- Ensure the server binds to the port from `PORT` and reads the database at `SQLITE_DB`.
- CORS should be enabled for the frontend origin.

Once running at `http://localhost:5001`, the React app (http://localhost:3000) will connect using `REACT_APP_API_URL`.
