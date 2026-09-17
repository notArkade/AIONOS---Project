"""Pydantic response models for the deterministic executive-data API."""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class ApiSourceReference(BaseModel):
    source_id: str
    source_type: str
    source_reference: str


class ApiStateChange(BaseModel):
    occurred_at: datetime
    description: str
    sources: list[ApiSourceReference]


class ApiItem(BaseModel):
    id: str
    title: str
    status: str
    owner: str | None
    ownership: str
    deadline: str | None
    deadline_time: str | None
    deadline_precision: str | None
    scheduled_start: datetime | None
    scheduled_end: datetime | None
    details: list[str]
    history: list[ApiStateChange]
    sources: list[ApiSourceReference]


class HealthResponse(BaseModel):
    status: str


class DashboardResponse(BaseModel):
    as_of: datetime
    commitments: list[ApiItem]
    open_tasks: list[ApiItem]
    completed_tasks: list[ApiItem]
    upcoming_deadlines: list[ApiItem]
    overdue_or_at_risk_items: list[ApiItem]
    meetings: list[ApiItem]
    follow_ups: list[ApiItem]
    unresolved_items: list[ApiItem]
    waiting_on_others: list[ApiItem]
    others_waiting_on_arjun: list[ApiItem]


class ItemsResponse(BaseModel):
    as_of: datetime
    tasks: list[ApiItem]


class MeetingsResponse(BaseModel):
    as_of: datetime
    meetings: list[ApiItem]


class DeadlinesResponse(BaseModel):
    as_of: datetime
    upcoming_deadlines: list[ApiItem]
    overdue_or_at_risk_items: list[ApiItem]


class FollowUpsResponse(BaseModel):
    as_of: datetime
    follow_ups: list[ApiItem]


class UnresolvedResponse(BaseModel):
    as_of: datetime
    unresolved_items: list[ApiItem]


class SummaryResponse(BaseModel):
    as_of: datetime
    open_task_count: int
    completed_task_count: int
    upcoming_deadline_count: int
    at_risk_item_count: int
    unresolved_item_count: int
    highlights: list[ApiItem]


class SearchResponse(BaseModel):
    query: str
    as_of: datetime
    results: list[ApiItem]


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2_000)

    @field_validator("message")
    @classmethod
    def message_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("message must not be blank")
        return value.strip()


class ChatResponse(BaseModel):
    answer: str
    sources: list[ApiSourceReference]
    related_items: list[ApiItem]
    used_fallback: bool
    fallback_reason: str | None = None
