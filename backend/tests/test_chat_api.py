import pytest
from fastapi.testclient import TestClient

from app.api.chat import get_agent_service
from app.main import app
from app.services.agent_service import AgentService
from app.services.gemini_service import GeminiAnswer, GeminiService, GeminiServiceError

client = TestClient(app)


class SuccessfulGemini:
    def __init__(self) -> None:
        self.context: dict[str, object] | None = None

    def generate_answer(
        self, question: str, context: dict[str, object], allowed_item_ids: set[str]
    ) -> GeminiAnswer:
        self.context = context
        assert "vendor-list" in allowed_item_ids
        return GeminiAnswer(
            answer="Raghav is waiting for the updated vendor list.",
            used_item_ids=["vendor-list"],
        )


class FailingGemini:
    def __init__(self, reason: str = "gemini_failure") -> None:
        self.reason = reason

    def generate_answer(
        self, question: str, context: dict[str, object], allowed_item_ids: set[str]
    ) -> GeminiAnswer:
        raise GeminiServiceError("provider unavailable", reason=self.reason)


def override_agent(agent: AgentService) -> None:
    app.dependency_overrides[get_agent_service] = lambda: agent


def clear_override() -> None:
    app.dependency_overrides.pop(get_agent_service, None)


def test_missing_api_key_uses_deterministic_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    override_agent(AgentService(gemini_service=GeminiService(api_key=None)))
    try:
        response = client.post("/api/chat", json={"message": "What is urgent?"})
    finally:
        clear_override()

    body = response.json()
    assert response.status_code == 200
    assert body["used_fallback"] is True
    assert body["fallback_reason"] == "missing_api_key"
    assert body["related_items"]


@pytest.mark.parametrize("body", [{}, {"message": ""}, {"message": "   "}, {"message": 123}])
def test_chat_rejects_malformed_requests(body: dict[str, object]) -> None:
    response = client.post("/api/chat", json=body)

    assert response.status_code == 422


def test_successful_chat_flow_uses_mocked_gemini_and_only_relevant_context() -> None:
    gemini = SuccessfulGemini()
    override_agent(AgentService(gemini_service=gemini))
    try:
        response = client.post("/api/chat", json={"message": "What do I need to follow up on?"})
    finally:
        clear_override()

    body = response.json()
    assert response.status_code == 200
    assert body["answer"] == "Raghav is waiting for the updated vendor list."
    assert body["used_fallback"] is False
    assert [item["id"] for item in body["related_items"]] == ["vendor-list"]
    assert gemini.context is not None
    context_item_ids = {item["id"] for item in gemini.context["items"]}  # type: ignore[index]
    assert "vendor-list" in context_item_ids
    assert "expense-variance-report" not in context_item_ids


def test_provider_failure_uses_source_cited_fallback() -> None:
    override_agent(AgentService(gemini_service=FailingGemini()))  # type: ignore[arg-type]
    try:
        response = client.post("/api/chat", json={"message": "What is the status of the Mumbai lease?"})
    finally:
        clear_override()

    body = response.json()
    assert response.status_code == 200
    assert body["used_fallback"] is True
    assert body["fallback_reason"] == "gemini_failure"
    assert body["related_items"][0]["id"] == "mumbai-office-lease-renewal"
    assert {source["source_id"] for source in body["sources"]} >= {
        "email-mumbai-lease-renewal-01",
        "email-mumbai-lease-renewal-05",
    }


def test_timeout_uses_deterministic_fallback() -> None:
    override_agent(AgentService(gemini_service=FailingGemini(reason="timeout")))  # type: ignore[arg-type]
    try:
        response = client.post("/api/chat", json={"message": "What meetings do I have?"})
    finally:
        clear_override()

    assert response.status_code == 200
    assert response.json()["used_fallback"] is True
    assert response.json()["fallback_reason"] == "timeout"


def test_malformed_gemini_response_uses_deterministic_fallback() -> None:
    override_agent(AgentService(gemini_service=FailingGemini(reason="invalid_response")))  # type: ignore[arg-type]
    try:
        response = client.post("/api/chat", json={"message": "When is the Meridian call?"})
    finally:
        clear_override()

    body = response.json()
    assert response.status_code == 200
    assert body["used_fallback"] is True
    assert body["fallback_reason"] == "invalid_response"
    assert body["related_items"][0]["id"] == "meridian-logistics-call"
    assert body["sources"]


def test_no_relevant_data_does_not_call_gemini() -> None:
    response = AgentService(gemini_service=SuccessfulGemini()).answer("Tell me about quarterly product engineering")

    assert response.used_fallback is True
    assert response.fallback_reason == "no_relevant_data"
    assert response.sources == []
    assert response.related_items == []
