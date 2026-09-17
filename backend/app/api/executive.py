"""Read-only API endpoints backed by the deterministic executive-state engine."""

from fastapi import APIRouter, Query

from app.models.api import (
    ApiItem,
    ApiSourceReference,
    ApiStateChange,
    DashboardResponse,
    DeadlinesResponse,
    FollowUpsResponse,
    ItemsResponse,
    MeetingsResponse,
    SearchResponse,
    SummaryResponse,
    UnresolvedResponse,
)
from app.services.executive_state import ExecutiveItem, ExecutiveState, ExecutiveStateEngine

router = APIRouter(tags=["executive-state"])


def get_state() -> ExecutiveState:
    """Build a fresh deterministic view from the immutable local source data."""
    return ExecutiveStateEngine.from_default_data().build()


def to_api_item(item: ExecutiveItem) -> ApiItem:
    """Map engine models to the stable public API representation."""
    due = item.due
    return ApiItem(
        id=item.id,
        title=item.title,
        status=item.status,
        owner=item.owner,
        ownership=item.ownership_status,
        deadline=due.date if due else None,
        deadline_time=due.time if due else None,
        deadline_precision=due.precision if due else None,
        scheduled_start=item.scheduled_start,
        scheduled_end=item.scheduled_end,
        details=item.details,
        history=[
            ApiStateChange(
                occurred_at=change.occurred_at,
                description=change.description,
                sources=[ApiSourceReference(**reference.model_dump()) for reference in change.source_references],
            )
            for change in item.history
        ],
        sources=[ApiSourceReference(**reference.model_dump()) for reference in item.source_references],
    )


def to_api_items(items: list[ExecutiveItem]) -> list[ApiItem]:
    return [to_api_item(item) for item in items]


@router.get("/dashboard", response_model=DashboardResponse)
def dashboard() -> DashboardResponse:
    state = get_state()
    return DashboardResponse(
        as_of=state.as_of,
        commitments=to_api_items(state.commitments),
        open_tasks=to_api_items(state.open_tasks),
        completed_tasks=to_api_items(state.completed_tasks),
        upcoming_deadlines=to_api_items(state.upcoming_deadlines),
        overdue_or_at_risk_items=to_api_items(state.overdue_or_at_risk_items),
        meetings=to_api_items(state.meetings),
        follow_ups=to_api_items(state.follow_ups),
        unresolved_items=to_api_items(state.unresolved_items),
        waiting_on_others=to_api_items(state.waiting_on_others),
        others_waiting_on_arjun=to_api_items(state.others_waiting_on_arjun),
    )


@router.get("/tasks", response_model=ItemsResponse)
def tasks() -> ItemsResponse:
    state = get_state()
    return ItemsResponse(as_of=state.as_of, tasks=to_api_items(state.open_tasks + state.completed_tasks))


@router.get("/tasks/open", response_model=ItemsResponse)
def open_tasks() -> ItemsResponse:
    state = get_state()
    return ItemsResponse(as_of=state.as_of, tasks=to_api_items(state.open_tasks))


@router.get("/tasks/completed", response_model=ItemsResponse)
def completed_tasks() -> ItemsResponse:
    state = get_state()
    return ItemsResponse(as_of=state.as_of, tasks=to_api_items(state.completed_tasks))


@router.get("/meetings", response_model=MeetingsResponse)
def meetings() -> MeetingsResponse:
    state = get_state()
    return MeetingsResponse(as_of=state.as_of, meetings=to_api_items(state.meetings))


@router.get("/deadlines", response_model=DeadlinesResponse)
def deadlines() -> DeadlinesResponse:
    state = get_state()
    return DeadlinesResponse(
        as_of=state.as_of,
        upcoming_deadlines=to_api_items(state.upcoming_deadlines),
        overdue_or_at_risk_items=to_api_items(state.overdue_or_at_risk_items),
    )


@router.get("/follow-ups", response_model=FollowUpsResponse)
def follow_ups() -> FollowUpsResponse:
    state = get_state()
    return FollowUpsResponse(as_of=state.as_of, follow_ups=to_api_items(state.follow_ups))


@router.get("/unresolved", response_model=UnresolvedResponse)
def unresolved() -> UnresolvedResponse:
    state = get_state()
    return UnresolvedResponse(as_of=state.as_of, unresolved_items=to_api_items(state.unresolved_items))


@router.get("/summary", response_model=SummaryResponse)
def summary() -> SummaryResponse:
    state = get_state()
    highlights = state.overdue_or_at_risk_items + state.unresolved_items
    unique_highlights = {item.id: item for item in highlights}
    return SummaryResponse(
        as_of=state.as_of,
        open_task_count=len(state.open_tasks),
        completed_task_count=len(state.completed_tasks),
        upcoming_deadline_count=len(state.upcoming_deadlines),
        at_risk_item_count=len(state.overdue_or_at_risk_items),
        unresolved_item_count=len(state.unresolved_items),
        highlights=to_api_items(list(unique_highlights.values())),
    )


@router.get("/search", response_model=SearchResponse)
def search(q: str = Query(min_length=1, description="Case-insensitive search query")) -> SearchResponse:
    state = get_state()
    candidate_items = state.commitments + state.meetings + state.follow_ups
    unique_items = {item.id: item for item in candidate_items}
    query = q.casefold()
    matched_items = [
        item
        for item in unique_items.values()
        if query in " ".join([item.title, item.status, item.owner or "", *item.details]).casefold()
    ]
    return SearchResponse(query=query, as_of=state.as_of, results=to_api_items(matched_items))
