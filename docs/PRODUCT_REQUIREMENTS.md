# Executive Productivity Agent — Product Requirements

## 1. Objective

Build an AI-assisted productivity application for **Arjun Malhotra, VP Sales**. It must turn the supplied leadership transcript, calendars, email threads, and Arjun's personal voice memos into an accurate, time-aware executive view of commitments, deadlines, meetings, follow-ups, and unresolved ownership.

The authoritative data set covers Monday 21 September through Friday 25 September 2026. The product must not add facts beyond it. When a fact cannot be established, it must say **unknown** or **unresolved**.

## 2. People and roles

| Person / address | Role in product |
| --- | --- |
| Arjun Malhotra | Sole application user; VP Sales; author/recipient of relevant commitments. |
| Neha Kapoor | Marketing Lead; information source only. |
| Raghav Sethi | Ops Manager; information source only. |
| Divya Rao | Finance; information source only. |
| Priya Nair | Meridian Logistics external client; information source only. |
| Facilities | Internal distribution list; information source only. |

The application does not give Neha, Raghav, Divya, Priya, or Facilities a user account, task list, or interactive workflow.

## 3. Authoritative source types

1. Leadership Sync transcript, Monday 21 Sep, 9:00–9:35 AM.
2. Calendars for Arjun, Neha, Raghav, and Divya, week of 21–25 Sep.
3. Five chronological email threads, five emails each: Vendor List, Q3 Campaign Deck, Call Reschedule, Expense Variance Report, and Mumbai Office Lease Renewal.
4. Two personal voice-note transcripts recorded by Arjun.

Every extracted item must retain its type, source identifier, timestamp (where supplied), speaker/sender, and exact supporting excerpt or locatable reference.

## 4. Required capabilities

- Show an executive dashboard of current commitments, imminent deadlines, meeting schedule, completed work, and risks.
- Answer grounded natural-language questions, such as “What do I owe today?”, “Is the Meridian call confirmed?”, and “Who owns the Mumbai renewal?”
- Extract commitments, tasks, deadlines, status signals, owners, meetings, and follow-up needs from each source.
- Reconcile contradictory or superseded facts into a latest known state while displaying source history.
- Present calendar availability and detect conflicts; distinguish busy/blocked periods from named events.
- Surface unresolved ownership explicitly rather than assigning an owner.
- Support source-linked detail views for each conclusion.

## 5. Current executive state derived from the data pack

This is the latest known state at the latest supplied timestamp, Thu 24 Sep 2026, 4:45 PM.

| Item | Latest known state | Evidence / temporal history |
| --- | --- | --- |
| Updated vendor list for Raghav | Pending; Arjun owes it. It was promised for Wed morning and Raghav checked at 8:45 AM Wed. No supplied completion exists. | Leadership Sync; Vendor List emails 1–5; Voice Note 1. |
| Q3 campaign deck review | Deck delivery completed: it was ready/sent Thu 8:00 AM; review was scheduled Thu 9:30 AM. Whether the review itself occurred is unknown. | Leadership Sync; Q3 Campaign Deck emails 1–5; Neha calendar. |
| July expense variance report | Completed: Divya sent it Wed 6:00 PM; Arjun acknowledged receipt Wed 6:10 PM. | Leadership Sync; Expense Variance Report emails 1–5; Voice Note 2. |
| Meridian Logistics call | Confirmed for Wed 23 Sep, 3:00 PM. Whether it occurred or what resulted is unknown. | Leadership Sync; Call Reschedule emails 1–5; Arjun calendar; Voice Note 2. |
| Mumbai office lease renewal signature | Pending, due Fri 25 Sep end of day; ownership unresolved. Facilities is suggested as the typical area but is not a confirmed owner. | Leadership Sync; Lease Renewal emails 1–5; Voice Note 1. |

### Important commitments and deadlines

- Arjun: send updated vendor list to Raghav; latest promised time is Wed 23 Sep morning. It remains pending in the supplied data.
- Neha: provide Q3 campaign deck for Arjun's review; the deadline moved from Wednesday to Thu 24 Sep morning, and the deck was sent Thu 8:00 AM.
- Divya: deliver July expense variance report by Wed 23 Sep evening; fulfilled at 6:00 PM.
- Arjun: reconfirm/reschedule Meridian Logistics call; fulfilled as a scheduling commitment when he confirmed Wed 3:00 PM with Priya. The call outcome is unknown.
- Authorized signer (unresolved): sign Mumbai office lease renewal by Fri 25 Sep EOD; still pending at Thu 4:00 PM.

### Follow-up requirements

- Alert Arjun that the vendor-list promise appears overdue, and suggest a follow-up to Raghav or completion of delivery. Do not claim delivery occurred.
- Flag the unowned Mumbai lease signature as urgent on Thu 24 Sep and due Fri EOD. Ask Arjun to identify/confirm an owner; do not assign Facilities.
- Do not create a follow-up for a completed expense report unless Arjun asks for review-related work; the source only establishes delivery and receipt.
- Do not claim a follow-up is required for the deck review or Meridian call after their scheduled times: their completion/outcome is unknown, not established.

## 6. Calendar requirements

- Store the calendar entries exactly as supplied, including person, date, start/end time, title, and whether a period is `blocked`.
- Arjun’s calendar is the primary schedule. Other calendars support availability reasoning only.
- Display all Arjun events: Leadership Sync, 1:1 with Neha, Internal Budget Review, Meridian call, Board Prep Session, Hiring Panel, Facilities Check-in, and blocked periods.
- Recognize the confirmed Meridian call at Wed 3:00–3:30 PM as consistent with Arjun’s calendar.
- Recognize the Q3 deck review at Thu 9:30–10:00 AM on Neha’s calendar overlaps Arjun’s Board Prep Session (9:00–10:00 AM); show this as a schedule conflict/risk, not a resolved change.
- Preserve original calendar data and derived meeting status separately. A calendar entry does not prove a meeting occurred.

## 7. Temporal reasoning rules

1. Use explicit timestamps and the data-pack week (21–25 September 2026) to resolve relative terms such as “tomorrow,” “Wednesday,” “Thursday morning,” and “one day out.”
2. Later, directly applicable dated evidence supersedes earlier plans for the same field; retain earlier evidence in history.
3. A promise or calendar entry is not completion. Completion requires explicit evidence, e.g., “attached,” “sent as promised,” or acknowledgement.
4. Confirmation establishes a planned meeting time, not attendance or outcome.
5. “Facilities typically sits with it” is a hypothesis, not ownership confirmation. State remains `unresolved`.
6. Preserve precision. “Wednesday evening” must not be turned into a fabricated exact time; when evidence has 6:00 PM, use it.
7. Compute overdue/due-soon only relative to an explicit `as_of` timestamp. Historical source facts must never be silently evaluated against current wall-clock time.

## 8. Acceptance criteria

- All displayed facts can be traced to one or more supplied sources.
- Latest states match the table above when evaluated as of Thu 24 Sep 2026, 4:45 PM.
- Previous deadlines/promises remain visible in history and are not presented as current.
- Unknown outcomes and unresolved ownership remain explicitly labelled.
- UI/API never fabricate tasks, people, or status changes.
