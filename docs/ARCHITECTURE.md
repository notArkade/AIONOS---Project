# Architecture

## Proposed architecture

```text
React + Vite + Tailwind (frontend)
  └─ API client / view models
       └─ FastAPI (backend)
            ├─ source repository (immutable JSON)
            ├─ deterministic extraction/state service
            ├─ calendar and temporal-reasoning service
            ├─ citation service
            └─ optional Gemini grounded-query adapter
```

Keep frontend and backend as sibling directories, `frontend/` and `backend/`, at the repository root. The frontend consumes the API only; it contains no task-status, deadline, ownership, or temporal reconciliation rules.

## Backend design

- `app/main.py`: FastAPI composition and routing only.
- `app/models/`: Pydantic request/response and domain models.
- `app/repositories/`: JSON loading, validation, and source lookup.
- `app/services/state.py`: deterministic state reconstruction and field-history reconciliation.
- `app/services/temporal.py`: date resolution, due/overdue calculation, and precision handling.
- `app/services/calendar.py`: calendar filtering and overlap detection.
- `app/services/citations.py`: evidence selection and response citation shaping.
- `app/services/gemini.py`: constrained model gateway.
- `app/api/`: thin endpoint handlers.

No LangChain, vector database, authentication, microservices, Docker, or additional infrastructure is needed for this scoped prototype.

## Frontend design

- `src/api/`: typed API client and request functions.
- `src/features/dashboard/`: summary cards for urgent, pending, completed, and unresolved items.
- `src/features/tasks/`: item list/detail with a state-history timeline and citations.
- `src/features/calendar/`: schedule display and conflict panel.
- `src/features/ask/`: grounded question input and answer with citations/unknowns.
- `src/components/`: presentation-only reusable UI components.
- `src/lib/`: formatting and API error utilities; no domain decisions.

Essential screens are Dashboard, Task/Commitment Detail, Calendar, and Ask Arjun’s Agent. The detail screen must make superseded commitments legible rather than hiding them.

## Gemini integration design

Gemini is an optional natural-language layer, not a source of record or rules engine.

1. The backend retrieves structured current state, relevant source excerpts, and history deterministically.
2. It sends Gemini only this bounded evidence plus instructions: answer solely from evidence, cite source IDs, preserve uncertainty, and never create people/tasks/events/dates/statuses.
3. Gemini returns structured JSON: `answer`, `used_source_ids`, and `unknowns`.
4. The backend validates every returned source ID, attaches canonical excerpts, and rejects/falls back if a claim lacks support or schema validation fails.
5. Deterministic endpoint data remains available if Gemini is unconfigured, unavailable, or fails validation.

Store the API key only in backend environment configuration (for example `GEMINI_API_KEY`), never in source JSON or frontend code. Log only request metadata and source IDs, not secrets.

## Testing strategy

- Use `pytest` for pure temporal/state unit tests and FastAPI endpoint tests.
- Fixture tests must cover every supplied state transition, including changed deadlines, completion evidence, meeting confirmation versus occurrence, and unresolved lease ownership.
- Test historical `as_of` queries so prior promises appear before later revisions.
- Test calendar overlap: Neha deck review Thu 9:30–10:00 conflicts with Arjun board prep Thu 9:00–10:00.
- Test that citation references are valid and that unsupported/unknown questions return uncertainty.
- Mock Gemini; test malformed outputs, invented source IDs, and failure fallback.
- Frontend: build check plus focused component tests for citation and unknown-state presentation when introduced.

## Deployment strategy

For the prototype, use a single service deployment: FastAPI serves its API and the built Vite static files, with JSON source files packaged read-only. Configuration is environment-based and includes only the Gemini key and timezone assumption. A documented local run path should require installing backend/frontend dependencies and launching the service; no external database is required. Production deployment must use HTTPS and platform-managed secret storage, while preserving the ability to run without Gemini.

## Verification and evolution

Before each milestone: run backend tests, frontend build when a frontend exists, inspect `git diff`, and report changed files with a proposed commit command. Add source ingestion or writable task actions only when a later milestone explicitly authorizes them; preserve raw sources and append state history rather than rewriting it.
