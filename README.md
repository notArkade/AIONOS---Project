# Executive Productivity Agent

An AI-assisted executive productivity dashboard for **Arjun Malhotra, VP Sales**.
The application turns the supplied Assignment 1 data pack into a source-grounded
executive view of tasks, meetings, deadlines, follow-ups, unresolved items, and
natural-language questions.

## Project Overview

The application has a React/Vite frontend and a Python/FastAPI backend. The
backend loads the fixed assignment JSON files, reconstructs executive state with
deterministic rules, and optionally uses Google Gemini to phrase answers. The
frontend displays the resulting state and provides a chat interface.

The supplied assignment data is the source of truth. The application does not
invent people, messages, meetings, deadlines, responsibilities, statuses, or
events. It does not connect to real Gmail, Google Calendar, or other external
business systems.

## Assignment Objective

Build an AI-powered executive productivity assistant for Arjun that can answer
questions about his commitments and schedule while preserving source metadata
and clearly identifying unknown or unresolved information.

## Features

- Executive dashboard for Arjun Malhotra
- Summary cards for open tasks, meetings, follow-ups, and unresolved items
- Open and completed task views
- Upcoming and at-risk deadline view
- Meeting schedule view
- Follow-up and ownership view
- Source-grounded chat through `POST /api/chat`
- Quick-action questions
- Source references on assistant responses
- Deterministic fallback when Gemini is missing or unavailable
- Loading, empty, error, and retry states
- Responsive desktop and mobile layout

## Architecture

```text
React + Vite + Tailwind-style CSS
        |
        | HTTP JSON requests
        v
FastAPI /api routes
        |
        +--> SourceDataLoader --> data/*.json
        |
        +--> ExecutiveStateEngine --> deterministic state
        |
        +--> AgentService --> relevant context selection
                                  |
                                  +--> GeminiService (optional)
                                  +--> deterministic fallback
```

The frontend contains presentation and API-request code only. Task status,
deadline precision, ownership, source reconciliation, and uncertainty rules are
implemented in the backend.

## Tech Stack

- React 19
- Vite
- Tailwind CSS/PostCSS dependencies
- Python 3.11+
- FastAPI and Uvicorn
- Pydantic
- Google GenAI SDK for Gemini
- JSON files for initial storage
- pytest and FastAPI TestClient

## Project Structure

```text
.
├── backend/
│   ├── app/
│   │   ├── api/                 # FastAPI route handlers
│   │   ├── models/              # API and source-data models
│   │   ├── services/            # state engine, agent, Gemini, data loader
│   │   ├── config.py
│   │   └── main.py
│   ├── tests/                   # state, API, accuracy, and failure tests
│   ├── requirements.txt
│   └── requirements-dev.txt
├── data/                        # fixed assignment JSON source data
├── docs/
│   ├── Assignment 1_DataPack_ExecutiveProductivityAgent.pdf
│   ├── API_SPEC.md
│   ├── ARCHITECTURE.md
│   ├── DATA_MODEL.md
│   ├── PRODUCT_REQUIREMENTS.md
│   └── QA_REPORT.md
├── frontend/
│   ├── src/components/          # dashboard and chat presentation
│   ├── src/pages/               # Dashboard page
│   ├── src/services/api.js      # centralized API client
│   ├── .env.example
│   ├── vercel.json
│   └── package.json
├── .env.example                 # backend and shared environment template
├── render.yaml                  # Render backend service blueprint
└── .gitignore
```

## How the Data Works

The immutable source dataset is stored in `data/`:

- `meetings.json`: Leadership Sync transcript and meeting metadata
- `calendar.json`: calendar events
- `emails.json`: five email threads with five messages each
- `voice_notes.json`: two personal voice-note transcripts
- `people.json`: source participants and their roles

The loader validates every file with Pydantic before the state engine uses it.
Every important derived item keeps source IDs and source references.

## How the Executive State Engine Works

`ExecutiveStateEngine` builds a fresh state from the source files. It applies
deterministic rules to reconcile the latest known status and history, including:

- pending versus completed work
- confirmed meetings versus unknown meeting outcomes
- exact dates, times, morning/evening, and end-of-day precision
- confirmed versus unresolved ownership
- commitments, follow-ups, deadlines, and waiting states

The default `as_of` value is the latest timestamp in the supplied emails, not
the current machine time. The engine never mutates the source JSON files.

## How Gemini Is Used

Gemini is an optional language-generation layer, not the source of record.

1. The agent selects relevant structured state deterministically.
2. Only that bounded context is sent to Gemini.
3. Gemini is instructed to use only the supplied context and return structured JSON.
4. Returned item IDs are validated against the supplied context.
5. Invalid, unavailable, timed-out, or unconfigured Gemini responses use a
   deterministic source-grounded fallback.

The Gemini API key is read only by the backend. It is never sent to the
frontend, stored in source JSON, or committed to Git.

## Environment Variables

Copy `.env.example` to `backend/.env` for local backend configuration:

```env
APP_NAME=Executive Productivity Agent
GEMINI_API_KEY=your_google_gemini_api_key
GEMINI_MODEL=gemini-2.5-flash
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

For the frontend, copy `frontend/.env.example` to `frontend/.env` when the API
is not running at its default URL:

```env
VITE_API_URL=http://localhost:8000
```

For production, set `VITE_API_URL` to the deployed backend URL, for example
`https://executive-productivity-agent-api.onrender.com`. Set the backend
`CORS_ORIGINS` to the deployed frontend origin.

## Local Installation

Requirements: Python 3.11+, Node.js 18+, npm, and Git.

```powershell
git clone <your-github-repository-url>
cd AIONOS

python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements-dev.txt

cd frontend
npm install
cd ..
```

Do not commit `.env`, `.venv`, `node_modules`, `dist`, or test caches.

## Backend Startup

From the repository root:

```powershell
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

The API is available at `http://localhost:8000`. Health check:

```text
GET http://localhost:8000/api/health
```

## Frontend Startup

In a second terminal:

```powershell
cd frontend
npm run dev
```

Open `http://localhost:5173`.

The frontend API client is centralized in `frontend/src/services/api.js` and
uses `VITE_API_URL`; components do not make direct fetch calls.

## Testing

Run the complete backend suite:

```powershell
cd backend
pytest
```

Build the frontend:

```powershell
cd frontend
npm run build
```

The suite covers state reconstruction, API contracts, assignment accuracy,
malformed requests, missing Gemini configuration, Gemini failures/timeouts,
malformed Gemini responses, fallbacks, and source preservation.

## Deployment

No deployment is performed automatically by this repository.

### Backend on Render

The root `render.yaml` provides a suitable web service blueprint:

1. Create a new Render Blueprint from the GitHub repository.
2. Review the service generated from `render.yaml`.
3. Set `GEMINI_API_KEY` as a secret environment variable.
4. Set `CORS_ORIGINS` to the final Vercel frontend URL.
5. Deploy and verify `https://<render-host>/api/health`.

The backend uses:

```text
Build: pip install -r requirements.txt
Start: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Railway can use the same `backend` root directory, build command, start
command, and environment variables.

### Frontend on Vercel

1. Import the GitHub repository into Vercel.
2. Set the project root directory to `frontend`.
3. Use the Vite defaults or the included `frontend/vercel.json`.
4. Set `VITE_API_URL` to the deployed backend URL.
5. Deploy and verify the dashboard and chat request.
6. Add the final Vercel origin to backend `CORS_ORIGINS` and redeploy the backend.

The frontend is a static Vite build. No API key belongs in Vercel frontend
environment variables.

## Example Questions

- What meetings do I have this week?
- When is the campaign deck review?
- Is the expense variance report still pending?
- When is the Meridian call?
- What's the status of the Mumbai lease?
- Who is responsible for the Mumbai lease?
- What do I need to follow up on?
- Who is waiting on me?
- What have I completed?
- What is due Friday?
- Prepare me for board prep.

When the source data does not establish an answer, the agent says so. It does
not assign unresolved responsibility.

## Known Limitations

- The dataset is static JSON from the assignment and is not live mailbox or
  calendar data.
- Gemini is optional; without a key, deterministic fallback answers are used.
- No authentication or user-management system is implemented.
- No writable tasks, memory, database, vector store, or background ingestion is
  implemented.
- Waiting-state collections are currently returned through the aggregate
  dashboard endpoint.
- The frontend loads Poppins from Google Fonts and falls back to Helvetica/system
  fonts if that request is unavailable.
- The initial deployment configuration targets Render/Railway for the backend
  and Vercel for the frontend; cloud deployment must be configured by the
  repository owner.

## Screenshots / Demo

Run the backend and frontend locally, then open `http://localhost:5173` to demo:

1. Dashboard summary cards and executive overview
2. Upcoming schedule and source-grounded commitments
3. Completed tasks, deadlines, follow-ups, and unresolved ownership
4. Chat quick actions and source references

The responsive dashboard has been checked at desktop and 390px mobile widths.
Screenshots can be added to this section after the final hosted URL is chosen.

## GitHub Repository Instructions

Create a private or public GitHub repository, then push the project without
including secrets:

```powershell
git init
git add .
git commit -m "docs: prepare project for deployment and submission"
git branch -M main
git remote add origin <your-github-repository-url>
git push -u origin main
```

Before pushing, verify:

```powershell
git status --short
git ls-files | Select-String -Pattern '(^|/)\.env$|node_modules|(^|/)(\.venv|venv)/|(^|/)dist/|\.pytest_cache|__pycache__'
```

The second command should not report local secrets or generated directories.
Use `.env.example` files as templates only.
