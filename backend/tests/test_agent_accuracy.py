import pytest

from app.services.agent_service import AgentService, is_greeting
from app.services.gemini_service import GeminiAnswer, GeminiServiceError


class DeterministicFallbackGemini:
    def generate_answer(
        self, question: str, context: dict[str, object], allowed_item_ids: set[str]
    ) -> GeminiAnswer:
        raise GeminiServiceError("Gemini unavailable for deterministic QA", reason="gemini_failure")


@pytest.fixture
def agent() -> AgentService:
    return AgentService(gemini_service=DeterministicFallbackGemini())  # type: ignore[arg-type]


def ids(response) -> set[str]:
    return {item.id for item in response.related_items}


@pytest.mark.parametrize(
    ("question", "expected_ids"),
    [
        ("What meetings do I have this week?", {"leadership-sync-2026-09-21", "q3-campaign-deck-review", "meridian-logistics-call"}),
        ("When is the campaign deck review?", {"q3-campaign-deck-review"}),
        ("Is the expense variance report still pending?", {"expense-variance-report"}),
        ("When is the Meridian call?", {"meridian-logistics-call"}),
        ("What's the status of the Mumbai lease?", {"mumbai-office-lease-renewal"}),
        ("Who is responsible for the Mumbai lease?", {"mumbai-office-lease-renewal"}),
        ("What do I need to follow up on?", {"vendor-list", "mumbai-office-lease-renewal", "follow-up-mumbai-lease-ownership"}),
        ("Who is waiting on me?", {"vendor-list", "follow-up-mumbai-lease-ownership"}),
        ("Who am I waiting on?", set()),
        ("What have I completed?", {"expense-variance-report", "meridian-logistics-call"}),
        ("What are my open commitments?", {"vendor-list", "mumbai-office-lease-renewal"}),
        ("What is due Friday?", {"mumbai-office-lease-renewal"}),
        ("Prepare me for board prep.", {"expense-variance-report", "q3-campaign-deck-review"}),
        ("What changed about the campaign deck?", {"q3-campaign-deck-review"}),
        ("What happened with the Meridian call?", {"meridian-logistics-call"}),
        ("What happened with the vendor list?", {"vendor-list"}),
    ],
)
def test_assignment_question_retrieval(agent: AgentService, question: str, expected_ids: set[str]) -> None:
    response = agent.answer(question)

    assert response.used_fallback is True
    assert ids(response) == expected_ids
    assert response.sources or not expected_ids


def test_campaign_review_fallback_preserves_exact_schedule(agent: AgentService) -> None:
    response = agent.answer("When is the campaign deck review?")

    assert "Thursday, 24 September at 9:30 AM" in response.answer
    assert "calendar-neha-06" in {source.source_id for source in response.sources}


def test_meridian_fallback_preserves_exact_schedule(agent: AgentService) -> None:
    response = agent.answer("When is the Meridian call?")

    assert "Wednesday, 23 September at 3:00 PM" in response.answer


def test_expense_report_is_not_pending(agent: AgentService) -> None:
    response = agent.answer("Is the expense variance report still pending?")

    assert "completed" in response.answer
    assert "sent" in response.answer
    assert "acknowledged" in response.answer


def test_lease_fallback_preserves_unresolved_ownership_and_deadline(agent: AgentService) -> None:
    response = agent.answer("Who is responsible for the Mumbai lease?")

    assert "Friday, 25 September end of day" in response.answer
    assert "Ownership remains unresolved" in response.answer
    assert "owner" not in response.answer.lower() or "unresolved" in response.answer.lower()


def test_unknown_question_does_not_invent_information(agent: AgentService) -> None:
    response = agent.answer("What is the status of the Singapore acquisition?")

    assert response.related_items == []
    assert response.sources == []
    assert response.fallback_reason == "no_relevant_data"
    assert "No relevant information" in response.answer


def test_ambiguous_question_requests_clarification(agent: AgentService) -> None:
    response = agent.answer("What is the status?")

    assert response.fallback_reason == "ambiguous_question"
    assert "specific" in response.answer.lower()
    assert response.related_items == []


def test_reworded_questions_return_consistent_facts(agent: AgentService) -> None:
    first = agent.answer("When is the campaign deck review?")
    second = agent.answer("What day and time is the Q3 deck review scheduled?")

    assert ids(first) == ids(second) == {"q3-campaign-deck-review"}
    assert "Thursday, 24 September at 9:30 AM" in first.answer
    assert "Thursday, 24 September at 9:30 AM" in second.answer


def test_waiting_on_others_is_explicitly_empty(agent: AgentService) -> None:
    response = agent.answer("Who am I waiting on?")

    assert response.related_items == []
    assert response.fallback_reason == "no_waiting_on_others"
    assert "does not establish anyone" in response.answer


@pytest.mark.parametrize(
    "message",
    [
        "hi", "Hello!", "  HEY  ", "hii", "hiii", "good morning", "Good afternoon!",
        "good evening", "good night", "hi there", "hello assistant", "good morning assistant",
        "how are you", "hope you're doing well", "greetings",
    ],
)
def test_pure_greetings_are_detected(message: str) -> None:
    assert is_greeting(message) is True


@pytest.mark.parametrize(
    "message",
    [
        "Good morning, what meetings do I have today?",
        "Hi, what tasks are pending?",
        "Hello, when is the campaign deck review?",
        "Good morning, what do I need to prepare for tomorrow?",
        "What is the status of the vendor list?",
        "What meetings do I have on Thursday?",
        "Who owns the Mumbai lease renewal?",
        "Did Divya send the expense report?",
        "",
        "hi there please",
    ],
)
def test_information_requests_are_not_greetings(message: str) -> None:
    assert is_greeting(message) is False


def test_pure_greeting_skips_state_and_gemini() -> None:
    class FailingStateEngine:
        def build(self):
            raise AssertionError("pure greetings must not build executive state")

    class FailingGemini:
        def generate_answer(self, *args, **kwargs):
            raise AssertionError("pure greetings must not call Gemini")

    response = AgentService(
        state_engine=FailingStateEngine(),  # type: ignore[arg-type]
        gemini_service=FailingGemini(),  # type: ignore[arg-type]
    ).answer("Good morning!")

    assert response.answer == "Good morning, Arjun! How can I help you today?"
    assert response.sources == []
    assert response.related_items == []
    assert response.fallback_reason == "greeting"


def test_greeting_with_query_uses_normal_pipeline(agent: AgentService) -> None:
    response = agent.answer("Hello, when is the campaign deck review?")

    assert response.related_items[0].id == "q3-campaign-deck-review"
    assert response.fallback_reason == "gemini_failure"
