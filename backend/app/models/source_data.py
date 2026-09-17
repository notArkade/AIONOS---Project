"""Validated models for the assignment's raw source data."""

from datetime import date, time
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class SourceMetadata(BaseModel):
    source_type: str
    source_reference: str


class Person(BaseModel):
    id: str
    name: str
    role: str
    email: str
    is_application_user: bool


class PeopleData(BaseModel):
    source_metadata: SourceMetadata
    people: list[Person]


class Email(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    thread_id: str
    subject: str
    date: date
    time: time
    sender: str = Field(alias="from")
    recipients: list[str] = Field(alias="to")
    message: str
    source_type: Literal["email"]
    source_reference: str
    message_order: int = Field(ge=1)


class EmailsData(BaseModel):
    source_metadata: SourceMetadata
    emails: list[Email]

    @model_validator(mode="after")
    def validate_thread_message_orders(self) -> "EmailsData":
        orders_by_thread: dict[str, set[int]] = {}
        for email in self.emails:
            thread_orders = orders_by_thread.setdefault(email.thread_id, set())
            if email.message_order in thread_orders:
                raise ValueError(
                    f"duplicate message_order {email.message_order} in thread {email.thread_id}"
                )
            thread_orders.add(email.message_order)
        return self


class CalendarEvent(BaseModel):
    id: str
    person: str
    date: date
    start_time: time
    end_time: time
    event: str
    source_type: Literal["calendar"]

    @model_validator(mode="after")
    def validate_time_range(self) -> "CalendarEvent":
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        return self


class CalendarData(BaseModel):
    source_metadata: SourceMetadata
    calendar_events: list[CalendarEvent]


class TranscriptEntry(BaseModel):
    speaker: str
    message: str


class Meeting(BaseModel):
    id: str
    title: str
    date: date
    start_time: time
    end_time: time
    attendees: list[str]
    transcript: list[TranscriptEntry]
    source_type: Literal["meeting_transcript"]
    source_reference: str

    @model_validator(mode="after")
    def validate_time_range(self) -> "Meeting":
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        return self


class MeetingsData(BaseModel):
    source_metadata: SourceMetadata
    meetings: list[Meeting]


class VoiceNote(BaseModel):
    id: str
    date: date
    time: time
    speaker: str
    transcript: str
    context: str | None = None
    source_type: Literal["voice_note"]
    source_reference: str


class VoiceNotesData(BaseModel):
    source_metadata: SourceMetadata
    voice_notes: list[VoiceNote]


class SourceData(BaseModel):
    """The complete validated assignment data set."""

    people: PeopleData
    emails: EmailsData
    calendar: CalendarData
    meetings: MeetingsData
    voice_notes: VoiceNotesData
