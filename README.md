# Executive Productivity Agent

An AI-assisted executive productivity application for Arjun Malhotra, VP Sales. This initial scaffold provides a FastAPI health endpoint and a minimal React interface. The supplied data pack and project specifications are in [`docs/`](docs/).

## Structure

```text
.
├── docs/                 # Source pack and technical specifications
├── backend/              # FastAPI application and pytest tests
├── frontend/             # React, Vite, and Tailwind application
└── data/                 # Future JSON data storage (intentionally empty)
```

## Backend setup

Requires Python 3.11+.

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
uvicorn app.main:app --reload --port 8000
```

The health endpoint is available at `http://127.0.0.1:8000/api/health` and returns `{"status":"ok"}`.

Run backend tests:

```powershell
cd backend
pytest
```

## Frontend setup

Requires Node.js 20+.

```powershell
cd frontend
npm install
npm run dev
```

Open the Vite URL shown in the terminal (normally `http://localhost:5173`).

Create a production build:

```powershell
cd frontend
npm run build
```

## Configuration

Copy `.env.example` to `.env` when configuration is needed. Gemini is not integrated in this scaffold; `GEMINI_API_KEY` is reserved for a later milestone and must not be exposed to the frontend.
