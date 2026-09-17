from datetime import datetime

import pytest

from app.services.executive_state import ExecutiveItem, ExecutiveState, ExecutiveStateEngine


@pytest.fixture
def state() -> ExecutiveState:
    return ExecutiveStateEngine.from_default_data().build()


def find_item(items: list[ExecutiveItem], item_id: str) -> ExecutiveItem:
    return next(item for item in items if item.id == item_id)


def test_vendor_list_is_delayed_pending_and_waited_on_by_raghav(state: ExecutiveState) -> None:
    vendor_list = find_item(state.open_tasks, "vendor-list")

    assert vendor_list.owner == "Arjun Malhotra"
    assert vendor_list.status == "pending"
    assert vendor_list.due is not None
    assert vendor_list.due.date == "2026-09-23"
    assert vendor_list.due.precision == "morning"
    assert "Wednesday morning" in vendor_list.details[1]
    assert "Raghav was still checking" in vendor_list.details[2]
    assert find_item(state.others_waiting_on_arjun, "vendor-list") == vendor_list


def test_q3_campaign_deck_tracks_moved_and_confirmed_review(state: ExecutiveState) -> None:
    q3_deck = find_item(state.meetings, "q3-campaign-deck-review")

    assert q3_deck.status == "confirmed"
    assert q3_deck.scheduled_start == datetime(2026, 9, 24, 9, 30)
    assert q3_deck.scheduled_end == datetime(2026, 9, 24, 10, 0)
    assert [change.occurred_at for change in q3_deck.history] == sorted(
        change.occurred_at for change in q3_deck.history
    )
    assert "Thursday morning" in q3_deck.details[1]
    assert "ready Thursday morning" in q3_deck.details[2]


def test_meridian_call_is_confirmed_and_matches_calendar(state: ExecutiveState) -> None:
    meridian = find_item(state.meetings, "meridian-logistics-call")

    assert meridian.status == "confirmed"
    assert meridian.scheduled_start == datetime(2026, 9, 23, 15, 0)
    assert meridian.scheduled_end == datetime(2026, 9, 23, 15, 30)
    source_ids = {reference.source_id for reference in meridian.source_references}
    assert "email-call-reschedule-03" in source_ids
    assert "email-call-reschedule-05" in source_ids
    assert "calendar-arjun-06" in source_ids


def test_expense_report_is_completed_and_not_open(state: ExecutiveState) -> None:
    expense_report = find_item(state.completed_tasks, "expense-variance-report")

    assert expense_report.status == "completed"
    assert expense_report.owner == "Divya Rao"
    assert expense_report.due is not None
    assert expense_report.due.date == "2026-09-23"
    assert expense_report.due.precision == "evening"
    assert "6:00 PM" in expense_report.details[2]
    assert "6:10 PM" in expense_report.details[2]
    assert "expense-variance-report" not in {item.id for item in state.open_tasks}


def test_lease_renewal_remains_unresolved_with_friday_eod_deadline(state: ExecutiveState) -> None:
    lease = find_item(state.unresolved_items, "mumbai-office-lease-renewal")

    assert lease.status == "unresolved"
    assert lease.owner is None
    assert lease.ownership_status == "unresolved"
    assert lease.due is not None
    assert lease.due.date == "2026-09-25"
    assert lease.due.precision == "end_of_day"
    assert find_item(state.upcoming_deadlines, "mumbai-office-lease-renewal") == lease


def test_history_is_in_source_date_order(state: ExecutiveState) -> None:
    vendor_list = find_item(state.commitments, "vendor-list")
    history_times = [change.occurred_at for change in vendor_list.history]

    assert history_times == sorted(history_times)
    assert history_times[-1] == datetime(2026, 9, 23, 8, 45)


def test_status_transitions_preserve_superseded_history(state: ExecutiveState) -> None:
    expense_report = find_item(state.commitments, "expense-variance-report")

    descriptions = [change.description for change in expense_report.history]
    assert descriptions == [
        "Divya initially targeted Thursday morning.",
        "Arjun requested delivery by Wednesday evening.",
        "Divya reported that the attached report was sent.",
        "Arjun acknowledged receipt.",
    ]
    assert expense_report.status == "completed"


def test_source_tracking_includes_raw_source_metadata(state: ExecutiveState) -> None:
    vendor_list = find_item(state.commitments, "vendor-list")

    source_ids = {reference.source_id for reference in vendor_list.source_references}
    assert {
        "meeting-leadership-sync-2026-09-21",
        "email-vendor-list-04",
        "email-vendor-list-05",
        "voice-note-01",
    }.issubset(source_ids)
    assert all(reference.source_reference.startswith("PDF") for reference in vendor_list.source_references)


def test_engine_uses_latest_source_timestamp_as_default_as_of(state: ExecutiveState) -> None:
    assert state.as_of == datetime(2026, 9, 24, 16, 45)


def test_follow_up_requests_confirmation_without_assigning_lease_ownership(state: ExecutiveState) -> None:
    follow_up = find_item(state.follow_ups, "follow-up-mumbai-lease-ownership")

    assert follow_up.owner == "Arjun Malhotra"
    assert "does not establish who is responsible" in follow_up.details[1]
    assert find_item(state.others_waiting_on_arjun, follow_up.id) == follow_up
