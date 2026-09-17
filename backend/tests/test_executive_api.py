import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@pytest.mark.parametrize(
    ("path", "response_key"),
    [
        ("/api/health", "status"),
        ("/api/dashboard", "commitments"),
        ("/api/tasks", "tasks"),
        ("/api/tasks/open", "tasks"),
        ("/api/tasks/completed", "tasks"),
        ("/api/meetings", "meetings"),
        ("/api/deadlines", "upcoming_deadlines"),
        ("/api/follow-ups", "follow_ups"),
        ("/api/unresolved", "unresolved_items"),
        ("/api/summary", "highlights"),
        ("/api/search?q=vendor", "results"),
    ],
)
def test_endpoint_returns_json(path: str, response_key: str) -> None:
    response = client.get(path)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert response_key in response.json()


def test_open_tasks_exclude_completed_expense_report() -> None:
    response = client.get("/api/tasks/open")

    task_ids = {task["id"] for task in response.json()["tasks"]}
    assert "expense-variance-report" not in task_ids
    assert "vendor-list" in task_ids


def test_unresolved_includes_mumbai_lease_with_source_metadata() -> None:
    response = client.get("/api/unresolved")

    lease = next(
        item
        for item in response.json()["unresolved_items"]
        if item["id"] == "mumbai-office-lease-renewal"
    )
    assert lease["status"] == "pending"
    assert lease["ownership"] == "unresolved"
    assert lease["deadline"] == "2026-09-25"
    assert lease["sources"]
    assert {source["source_id"] for source in lease["sources"]} >= {
        "email-mumbai-lease-renewal-01",
        "email-mumbai-lease-renewal-05",
    }


def test_meetings_include_confirmed_meridian_logistics_call() -> None:
    response = client.get("/api/meetings")

    meridian = next(item for item in response.json()["meetings"] if item["id"] == "meridian-logistics-call")
    assert meridian["status"] == "confirmed"
    assert meridian["scheduled_start"] == "2026-09-23T15:00:00"
    assert any(source["source_id"] == "calendar-arjun-06" for source in meridian["sources"])


def test_search_is_case_insensitive_and_source_cited() -> None:
    response = client.get("/api/search?q=LEASE")

    assert response.json()["query"] == "lease"
    result = next(item for item in response.json()["results"] if item["id"] == "mumbai-office-lease-renewal")
    assert result["sources"]


def test_search_requires_query() -> None:
    response = client.get("/api/search")

    assert response.status_code == 422


def test_cors_allows_react_development_server() -> None:
    response = client.options(
        "/api/dashboard",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
