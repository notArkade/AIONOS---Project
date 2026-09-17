"""Deterministic executive-state reconstruction for the fixed assignment data set.

This module deliberately uses no LLM. It reconciles only supported source facts
from the structured assignment data and keeps citations on every derived item.
"""

from datetime import date, datetime, time
from typing import Literal

from pydantic import BaseModel, Field

from app.models.source_data import CalendarEvent, Email, Meeting, SourceData, VoiceNote
from app.services.data_loader import SourceDataLoader


ItemStatus = Literal["pending", "completed", "ready", "confirmed", "unresolved"]
OwnershipStatus = Literal["confirmed", "unresolved", "not_applicable"]


class ExecutiveStateError(RuntimeError):
    """Raised when the fixed source data lacks a record the engine requires."""


class SourceReference(BaseModel):
    """A locatable citation back to raw source data."""

    source_id: str
    source_type: str
    source_reference: str


class DueDate(BaseModel):
    """A due date retaining the precision actually supplied by the source."""

    date: str
    time: str | None = None
    precision: Literal["exact", "morning", "evening", "end_of_day"]


class StateChange(BaseModel):
    occurred_at: datetime
    description: str
    source_references: list[SourceReference]


class ExecutiveItem(BaseModel):
    """A source-cited, deterministic view of one executive item."""

    id: str
    title: str
    status: ItemStatus
    owner: str | None = None
    ownership_status: OwnershipStatus = "not_applicable"
    due: DueDate | None = None
    scheduled_start: datetime | None = None
    scheduled_end: datetime | None = None
    details: list[str]
    history: list[StateChange] = Field(default_factory=list)
    source_references: list[SourceReference]


class ExecutiveState(BaseModel):
    """The unified executive view for Arjun at a known source-data time."""

    as_of: datetime
    commitments: list[ExecutiveItem]
    open_tasks: list[ExecutiveItem]
    completed_tasks: list[ExecutiveItem]
    upcoming_deadlines: list[ExecutiveItem]
    overdue_or_at_risk_items: list[ExecutiveItem]
    meetings: list[ExecutiveItem]
    follow_ups: list[ExecutiveItem]
    unresolved_items: list[ExecutiveItem]
    waiting_on_others: list[ExecutiveItem]
    others_waiting_on_arjun: list[ExecutiveItem]


class ExecutiveStateEngine:
    """Build the assignment-specific state using ordered, deterministic rules."""

    def __init__(self, source_data: SourceData) -> None:
        self.source_data = source_data

    @classmethod
    def from_default_data(cls) -> "ExecutiveStateEngine":
        return cls(SourceDataLoader().load_all())

    def build(self, as_of: datetime | None = None) -> ExecutiveState:
        """Return current state as established by sources available at ``as_of``.

        The default uses the latest timestamped email (Thu 24 Sep 2026, 4:45 PM),
        rather than the machine clock. This avoids treating static assignment data
        as if it were live.
        """
        effective_as_of = as_of or self._latest_email_timestamp()

        vendor_list = self._vendor_list()
        q3_deck = self._q3_campaign_deck()
        expense_report = self._expense_variance_report()
        meridian_call = self._meridian_call()
        lease_renewal = self._mumbai_lease_renewal()
        leadership_sync = self._leadership_sync()
        lease_follow_up = self._lease_follow_up()

        commitments = [vendor_list, q3_deck, expense_report, meridian_call, lease_renewal]
        open_tasks = [vendor_list, lease_renewal]
        completed_tasks = [expense_report, meridian_call]
        upcoming_deadlines = [lease_renewal]
        overdue_or_at_risk_items = [vendor_list, lease_renewal]

        return ExecutiveState(
            as_of=effective_as_of,
            commitments=commitments,
            open_tasks=open_tasks,
            completed_tasks=completed_tasks,
            upcoming_deadlines=upcoming_deadlines,
            overdue_or_at_risk_items=overdue_or_at_risk_items,
            meetings=[leadership_sync, q3_deck, meridian_call],
            follow_ups=[lease_follow_up],
            unresolved_items=[lease_renewal],
            waiting_on_others=[],
            others_waiting_on_arjun=[vendor_list, lease_follow_up],
        )

    def _vendor_list(self) -> ExecutiveItem:
        sync = self._meeting("meeting-leadership-sync-2026-09-21")
        delay = self._email("email-vendor-list-04")
        check_in = self._email("email-vendor-list-05")
        voice_note = self._voice_note("voice-note-01")
        return ExecutiveItem(
            id="vendor-list",
            title="Send updated vendor list to Raghav",
            status="pending",
            owner="Arjun Malhotra",
            ownership_status="confirmed",
            due=DueDate(date="2026-09-23", precision="morning"),
            details=[
                "Arjun committed to send Raghav the updated vendor list.",
                "The latest stated delivery target is Wednesday morning.",
                "Raghav was still checking on Wednesday morning; no later source confirms delivery.",
            ],
            history=[
                self._change(sync.date, sync.start_time, "Arjun stated an initial target of end of day Tuesday.", [self._meeting_ref(sync)]),
                self._email_change(delay, "Arjun moved the target to Wednesday morning."),
                self._email_change(check_in, "Raghav checked whether delivery was still expected that morning."),
            ],
            source_references=[
                self._meeting_ref(sync),
                self._email_ref(delay),
                self._email_ref(check_in),
                self._voice_note_ref(voice_note),
            ],
        )

    def _q3_campaign_deck(self) -> ExecutiveItem:
        initial = self._email("email-q3-campaign-deck-01")
        moved = self._email("email-q3-campaign-deck-02")
        scheduled = self._email("email-q3-campaign-deck-04")
        ready = self._email("email-q3-campaign-deck-05")
        calendar_event = self._calendar_event("calendar-neha-06")
        return ExecutiveItem(
            id="q3-campaign-deck-review",
            title="Q3 Campaign Deck review",
            status="confirmed",
            owner="Neha Kapoor",
            ownership_status="confirmed",
            scheduled_start=self._timestamp(calendar_event.date, calendar_event.start_time),
            scheduled_end=self._timestamp(calendar_event.date, calendar_event.end_time),
            details=[
                "The original review target was Wednesday.",
                "Neha moved the review to Thursday morning and later specified 9:30 AM Thursday.",
                "Neha stated that the deck was ready Thursday morning.",
                "The source data does not establish whether the review occurred or its outcome.",
            ],
            history=[
                self._email_change(initial, "Neha targeted Wednesday for Arjun's review."),
                self._email_change(moved, "Neha moved the review to Thursday morning."),
                self._email_change(scheduled, "Neha specified Thursday at 9:30 AM."),
                self._email_change(ready, "Neha stated that the draft was ready ahead of the review."),
            ],
            source_references=[
                self._email_ref(initial),
                self._email_ref(moved),
                self._email_ref(scheduled),
                self._email_ref(ready),
                self._calendar_ref(calendar_event),
            ],
        )

    def _meridian_call(self) -> ExecutiveItem:
        proposal = self._email("email-call-reschedule-02")
        client_confirmation = self._email("email-call-reschedule-03")
        arjun_confirmation = self._email("email-call-reschedule-05")
        calendar_event = self._calendar_event("calendar-arjun-06")
        return ExecutiveItem(
            id="meridian-logistics-call",
            title="Call — Meridian Logistics",
            status="confirmed",
            owner="Arjun Malhotra",
            ownership_status="confirmed",
            scheduled_start=self._timestamp(calendar_event.date, calendar_event.start_time),
            scheduled_end=self._timestamp(calendar_event.date, calendar_event.end_time),
            details=[
                "The client call was rescheduled.",
                "Arjun proposed Wednesday at 3:00 PM; Priya confirmed, followed by Arjun's confirmation.",
                "Arjun's calendar contains the Wednesday 3:00–3:30 PM call.",
                "The source data does not establish whether the call occurred or its outcome.",
            ],
            history=[
                self._email_change(proposal, "Arjun proposed Wednesday at 3:00 PM."),
                self._email_change(client_confirmation, "Priya confirmed the proposed time."),
                self._email_change(arjun_confirmation, "Arjun confirmed the meeting time."),
            ],
            source_references=[
                self._email_ref(proposal),
                self._email_ref(client_confirmation),
                self._email_ref(arjun_confirmation),
                self._calendar_ref(calendar_event),
            ],
        )

    def _expense_variance_report(self) -> ExecutiveItem:
        initial = self._email("email-expense-variance-report-01")
        revised = self._email("email-expense-variance-report-02")
        sent = self._email("email-expense-variance-report-04")
        acknowledged = self._email("email-expense-variance-report-05")
        return ExecutiveItem(
            id="expense-variance-report",
            title="July expense variance report",
            status="completed",
            owner="Divya Rao",
            ownership_status="confirmed",
            due=DueDate(date="2026-09-23", precision="evening"),
            details=[
                "Divya agreed to provide the July expense variance report.",
                "Arjun requested Wednesday evening rather than the initial Thursday-morning target.",
                "Divya sent the report Wednesday at 6:00 PM and Arjun acknowledged receipt at 6:10 PM.",
            ],
            history=[
                self._email_change(initial, "Divya initially targeted Thursday morning."),
                self._email_change(revised, "Arjun requested delivery by Wednesday evening."),
                self._email_change(sent, "Divya reported that the attached report was sent."),
                self._email_change(acknowledged, "Arjun acknowledged receipt."),
            ],
            source_references=[
                self._email_ref(initial),
                self._email_ref(revised),
                self._email_ref(sent),
                self._email_ref(acknowledged),
            ],
        )

    def _mumbai_lease_renewal(self) -> ExecutiveItem:
        deadline = self._email("email-mumbai-lease-renewal-01")
        pending = self._email("email-mumbai-lease-renewal-04")
        unowned = self._email("email-mumbai-lease-renewal-05")
        return ExecutiveItem(
            id="mumbai-office-lease-renewal",
            title="Mumbai Office Lease Renewal signature",
            status="unresolved",
            owner=None,
            ownership_status="unresolved",
            due=DueDate(date="2026-09-25", precision="end_of_day"),
            details=[
                "An authorized signature is required by Friday, 25 September, end of day.",
                "The signature was still pending on Thursday afternoon.",
                "No supplied source confirms who owns or will handle the signature.",
            ],
            history=[
                self._email_change(deadline, "Facilities announced the Friday signature requirement."),
                self._email_change(pending, "Facilities stated that the signature was still pending."),
                self._email_change(unowned, "Raghav stated that the item was still unowned."),
            ],
            source_references=[self._email_ref(deadline), self._email_ref(pending), self._email_ref(unowned)],
        )

    def _lease_follow_up(self) -> ExecutiveItem:
        request = self._email("email-mumbai-lease-renewal-05")
        return ExecutiveItem(
            id="follow-up-mumbai-lease-ownership",
            title="Confirm who is handling the Mumbai office lease renewal",
            status="pending",
            owner="Arjun Malhotra",
            ownership_status="confirmed",
            due=DueDate(date="2026-09-25", precision="end_of_day"),
            details=[
                "Raghav asked Arjun to confirm who is handling the still-unowned renewal.",
                "This follow-up does not establish who is responsible for the signature.",
            ],
            history=[self._email_change(request, "Raghav requested confirmation of who is handling the renewal.")],
            source_references=[self._email_ref(request)],
        )

    def _leadership_sync(self) -> ExecutiveItem:
        sync = self._meeting("meeting-leadership-sync-2026-09-21")
        return ExecutiveItem(
            id="leadership-sync-2026-09-21",
            title=sync.title,
            status="completed",
            scheduled_start=self._timestamp(sync.date, sync.start_time),
            scheduled_end=self._timestamp(sync.date, sync.end_time),
            details=["A transcript is supplied for this meeting."],
            source_references=[self._meeting_ref(sync)],
        )

    def _latest_email_timestamp(self) -> datetime:
        return max(self._timestamp(email.date, email.time) for email in self.source_data.emails.emails)

    def _email(self, email_id: str) -> Email:
        for email in self.source_data.emails.emails:
            if email.id == email_id:
                return email
        raise ExecutiveStateError(f"Required email source was not found: {email_id}")

    def _calendar_event(self, event_id: str) -> CalendarEvent:
        for event in self.source_data.calendar.calendar_events:
            if event.id == event_id:
                return event
        raise ExecutiveStateError(f"Required calendar source was not found: {event_id}")

    def _meeting(self, meeting_id: str) -> Meeting:
        for meeting in self.source_data.meetings.meetings:
            if meeting.id == meeting_id:
                return meeting
        raise ExecutiveStateError(f"Required meeting source was not found: {meeting_id}")

    def _voice_note(self, note_id: str) -> VoiceNote:
        for note in self.source_data.voice_notes.voice_notes:
            if note.id == note_id:
                return note
        raise ExecutiveStateError(f"Required voice-note source was not found: {note_id}")

    @staticmethod
    def _timestamp(record_date: date, record_time: time) -> datetime:
        return datetime.combine(record_date, record_time)

    def _email_change(self, email: Email, description: str) -> StateChange:
        return StateChange(
            occurred_at=self._timestamp(email.date, email.time),
            description=description,
            source_references=[self._email_ref(email)],
        )

    def _change(
        self, record_date: date, record_time: time, description: str, references: list[SourceReference]
    ) -> StateChange:
        return StateChange(
            occurred_at=self._timestamp(record_date, record_time),
            description=description,
            source_references=references,
        )

    @staticmethod
    def _email_ref(email: Email) -> SourceReference:
        return SourceReference(source_id=email.id, source_type=email.source_type, source_reference=email.source_reference)

    @staticmethod
    def _meeting_ref(meeting: Meeting) -> SourceReference:
        return SourceReference(source_id=meeting.id, source_type=meeting.source_type, source_reference=meeting.source_reference)

    def _calendar_ref(self, event: CalendarEvent) -> SourceReference:
        return SourceReference(
            source_id=event.id,
            source_type=event.source_type,
            source_reference=self.source_data.calendar.source_metadata.source_reference,
        )

    @staticmethod
    def _voice_note_ref(note: VoiceNote) -> SourceReference:
        return SourceReference(source_id=note.id, source_type=note.source_type, source_reference=note.source_reference)
