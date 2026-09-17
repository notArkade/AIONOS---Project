# Data Model

## Principles

JSON files are the initial storage layer. Keep raw source records immutable; place normalised entities and derived executive state in separate JSON files. Each derived fact must reference supporting source evidence. IDs are stable strings, not inferred from array order.

Suggested layout:

```text
backend/data/
  sources.json          # source metadata and immutable raw/transcribed content
  calendar_events.json  # normalized supplied calendar records
  entities.json         # people, email addresses, organisations
  executive_state.json  # derived current state and audit history
```

## Core JSON schema (conceptual)

```json
{
  "source": {
    "id": "email.vendor-list.2026-09-22T18:30:00",
    "type": "email|meeting_transcript|calendar|voice_note",
    "title": "Vendor List",
    "occurred_at": "2026-09-22T18:30:00",
    "participants": ["person.arjun", "person.raghav"],
    "sender_id": "person.arjun",
    "raw_text": "Sorry, got pulled into board prep...",
    "source_locator": {"thread_id": "thread.vendor-list", "message_number": 4}
  },
  "calendar_event": {
    "id": "calendar.arjun.2026-09-23.meridian-call",
    "person_id": "person.arjun",
    "start_at": "2026-09-23T15:00:00",
    "end_at": "2026-09-23T15:30:00",
    "title": "Call — Meridian Logistics",
    "availability": "busy|blocked",
    "source_refs": ["calendar.arjun.week-2026-09-21"]
  },
  "evidence": {
    "source_id": "email.vendor-list.2026-09-22T18:30:00",
    "excerpt": "will send by tomorrow (Wednesday) morning for sure",
    "supports": "due_at|status|owner|meeting_time|ownership",
    "observed_at": "2026-09-22T18:30:00"
  }
}
```

Dates have no stated timezone. Use ISO 8601 local datetimes with an application-configured timezone (initially `Asia/Kolkata`) and record that assumption; do not imply a source supplied it.

## Executive state schema

An executive item is the current, queryable representation of one task, commitment, meeting, or risk. It keeps a complete field-level state history.

```json
{
  "id": "item.vendor-list",
  "kind": "task|meeting|risk",
  "title": "Send updated vendor list to Raghav",
  "owner": {"person_id": "person.arjun", "state": "confirmed"},
  "counterparty_ids": ["person.raghav"],
  "status": "pending|completed|confirmed|unresolved|unknown",
  "status_reason": "No completion evidence after Raghav's Wed check-in.",
  "due": {"value": "2026-09-23T12:00:00", "precision": "morning", "state": "overdue_as_of"},
  "latest_evidence": ["email.vendor-list.2026-09-23T08:45:00"],
  "history": [
    {
      "field": "due",
      "value": "2026-09-22T17:00:00",
      "precision": "end_of_day",
      "valid_from": "2026-09-21T09:00:00",
      "superseded_at": "2026-09-21T17:40:00",
      "evidence_refs": ["meeting.leadership-sync"]
    }
  ],
  "source_refs": ["meeting.leadership-sync", "email.vendor-list.2026-09-23T08:45:00"]
}
```

Use `null` for an absent established value and a paired state/reason, not guessed values. A task’s status is distinct from its owner state. For the lease renewal use `owner: {"person_id": null, "state": "unresolved"}`; Facilities may appear only in evidence/history as a suggestion.

## Required current items

| ID | Kind | Current status | Owner state |
| --- | --- | --- | --- |
| `item.vendor-list` | task | pending / overdue as of Thu 24 Sep 4:45 PM | Arjun confirmed |
| `item.q3-deck-review` | meeting/review | scheduled/ready; review occurrence unknown | Neha delivery completed; Arjun review occurrence unknown |
| `item.expense-variance-report` | task | completed | Divya confirmed |
| `item.meridian-call` | meeting | confirmed; occurrence/outcome unknown | Arjun scheduling commitment completed |
| `item.mumbai-lease-renewal` | risk/task | pending | unresolved |

## State transitions to preserve

- Vendor list: Tue EOD promise from Sync → Tue morning → Wed morning; no later completion evidence.
- Q3 deck: Wednesday review target → Thu morning → Thu 9:30 AM → deck sent Thu 8:00 AM.
- Expense report: Thursday-morning target → Wed evening requested/accepted → sent Wed 6:00 PM → Arjun acknowledged 6:10 PM.
- Meridian: needs reconfirmation/reschedule → proposed Wed 3 PM → client confirmed → Arjun confirmed; meeting outcome absent.
- Lease: signer required by Fri → still no confirmed owner → signature still pending Thu 4 PM → Raghav asks Arjun to confirm handling at 4:45 PM.
