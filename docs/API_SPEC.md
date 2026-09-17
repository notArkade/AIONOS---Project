# API Specification

## Conventions

FastAPI serves JSON at `/api/v1`. All read responses provide `as_of` and citations. The backend derives state deterministically from JSON sources; no endpoint accepts unaudited facts as source truth.

`as_of` is an optional ISO-8601 local datetime. If omitted, use the latest supplied source timestamp for the initial static data set, not server time. API errors use `{ "detail": "..." }` and return 422 for invalid parameters.

## Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/v1/health` | Health and data-load status. |
| GET | `/api/v1/dashboard` | Arjun’s current executive summary: urgent/pending/completed items, meetings, conflicts, and unresolved risks. |
| GET | `/api/v1/items` | Filterable executive items. Query: `status`, `kind`, `owner_id`, `due_before`, `as_of`. |
| GET | `/api/v1/items/{item_id}` | Current state, full state history, and evidence. |
| GET | `/api/v1/calendar` | Calendar events. Query: `person_id` (defaults to Arjun), `from`, `to`. |
| GET | `/api/v1/calendar/conflicts` | Derived overlaps; query `person_id`, `from`, `to`. |
| GET | `/api/v1/sources` | Source metadata, type, time, participants; query `type`, `thread_id`. |
| GET | `/api/v1/sources/{source_id}` | Raw/transcribed source plus metadata. |
| POST | `/api/v1/query` | Grounded natural-language Q&A; body `{ "question": "...", "as_of": "..." }`. |

## Representative contracts

`GET /api/v1/items/item.mumbai-lease-renewal?as_of=2026-09-24T16:45:00`

```json
{
  "item": {
    "id": "item.mumbai-lease-renewal",
    "status": "pending",
    "owner": {"person_id": null, "state": "unresolved"},
    "due": {"value": "2026-09-25T17:00:00", "precision": "end_of_day"},
    "state_reason": "No source confirms an owner or signature.",
    "citations": [
      {"source_id": "email.lease.2026-09-24T16:45:00", "excerpt": "still unowned"}
    ]
  },
  "history": [],
  "as_of": "2026-09-24T16:45:00"
}
```

`POST /api/v1/query` response:

```json
{
  "answer": "The Mumbai lease signature is still pending and its owner is unresolved. It is due Friday, 25 September, end of day.",
  "citations": [
    {"source_id": "email.lease.2026-09-24T16:00:00", "excerpt": "signature is still pending"},
    {"source_id": "email.lease.2026-09-24T16:45:00", "excerpt": "still unowned"}
  ],
  "unknowns": ["No source confirms who will sign."],
  "as_of": "2026-09-24T16:45:00"
}
```

## API safeguards

- Validate IDs, enums, date ranges, and `as_of` values with Pydantic models.
- Reject source-mutating endpoints in the initial milestone; later ingestion must require raw source metadata.
- Return evidence with all material claims and explicit `unknowns` where the record does not establish an answer.
- State calculation must be deterministic and reusable by dashboard, item, and query endpoints.
