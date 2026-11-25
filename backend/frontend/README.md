# AI-Pulse personal frontend

React + Vite frontend for the existing AI-Pulse FastAPI backend.

## Quick start

1. Run FastAPI from `D:\AI-Pulse\backend`: `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`
2. In a second PowerShell terminal, `cd D:\AI-Pulse\backend\frontend`
3. `npm install`
4. `npm run dev`
5. Browse `http://127.0.0.1:5173` and sign in with the existing administrator credentials.

The Vite proxy forwards `/api` calls to `http://127.0.0.1:8000`. No CORS changes are required for local development.

## Features

- Login and session verification using `/api/v1/auth/login` and `/api/v1/auth/me`.
- News feed, search, categories, pagination, and full article reader.
- Saved briefing reader (requires the separately bundled `scripts/install_saved_briefing_api.py` to be run once).
- On-demand briefing via `/api/v1/briefing/generate` (consumes Gemini quota).
- Gemini chat via `/api/v1/chat/ask` (single-turn prompts in this first version).
- Read-only projects, tasks, skills and goals workspace.
- Responsive dark UI.

## Security and limitations

- The JWT is kept in the current browser session's `sessionStorage`. It remains accessible to JavaScript and should not be treated as protection against XSS; only run trusted frontend code.
- This is intended for `127.0.0.1` local access, not public deployment.
- Personal project data can only be modified via existing APIs, not through this read-only workspace yet.
- Saved briefings are read from local JSON by an **admin-only** FastAPI route installed separately. The `POST /briefing/generate` button does not save its result to that JSON file.
- No remote fonts or images are fetched by the frontend itself.
- Do not commit `.env`, `data/`, JWTs, or application secrets to Git.
