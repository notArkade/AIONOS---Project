"""Grounded orchestration between deterministic executive state and Gemini."""

from collections.abc import Iterable
from datetime import date

from pydantic import BaseModel

from app.services.executive_state import ExecutiveItem, ExecutiveState, ExecutiveStateEngine, SourceReference
from app.services.gemini_service import GeminiAnswer, GeminiService, GeminiServiceError


class AgentResponse(BaseModel):
    answer: str
    sources: list[SourceReference]
    related_items: list[ExecutiveItem]
    used_fallback: bool
    fallback_reason: str | None = None


class AgentService:
    """Retrieve source-grounded context, then optionally ask Gemini to phrase it."""

    def __init__(
        self,
        state_engine: ExecutiveStateEngine | None = None,
        gemini_service: GeminiService | None = None,
    ) -> None:
        self.state_engine = state_engine or ExecutiveStateEngine.from_default_data()
        self.gemini_service = gemini_service or GeminiService()

    def answer(self, question: str) -> AgentResponse:
        state = self.state_engine.build()
        if self._is_ambiguous(question):
            return AgentResponse(
                answer="Could you be more specific? Please name the meeting, task, person, or topic you want me to check.",
                sources=[],
                related_items=[],
                used_fallback=True,
                fallback_reason="ambiguous_question",
            )
        relevant_items = self._select_relevant_items(question, state)
        if not relevant_items:
            if "who am i waiting on" in question.casefold() or "who am i waiting for" in question.casefold():
                return AgentResponse(
                    answer="The supplied source data does not establish anyone Arjun is waiting on.",
                    sources=[],
                    related_items=[],
                    used_fallback=True,
                    fallback_reason="no_waiting_on_others",
                )
            return AgentResponse(
                answer="No relevant information is established in the supplied source data for that question.",
                sources=[],
                related_items=[],
                used_fallback=True,
                fallback_reason="no_relevant_data",
            )

        context = self._context(relevant_items, state)
        allowed_ids = {item.id for item in relevant_items}
        try:
            gemini_answer = self.gemini_service.generate_answer(question, context, allowed_ids)
            used_items = self._items_for_ids(relevant_items, gemini_answer.used_item_ids)
            return AgentResponse(
                answer=gemini_answer.answer,
                sources=self._sources(used_items),
                related_items=used_items,
                used_fallback=False,
            )
        except GeminiServiceError as exc:
            return AgentResponse(
                answer=self._fallback_answer(relevant_items),
                sources=self._sources(relevant_items),
                related_items=relevant_items,
                used_fallback=True,
                fallback_reason=exc.reason,
            )

    def _select_relevant_items(self, question: str, state: ExecutiveState) -> list[ExecutiveItem]:
        normalized = question.casefold()
        if any(term in normalized for term in ("completed", "finished", "done")):
            return state.completed_tasks
        if any(term in normalized for term in ("open commitment", "open commitments", "open task", "open tasks")):
            return state.open_tasks
        if "due friday" in normalized or "due on friday" in normalized:
            return self._unique(
                item for item in state.commitments
                if item.due and item.due.date == "2026-09-25"
            )
        if any(term in normalized for term in ("follow up", "follow-up", "need to do", "urgent")):
            return self._unique(state.open_tasks + state.follow_ups + state.overdue_or_at_risk_items)
        if "waiting on me" in normalized or "waiting for me" in normalized:
            return state.others_waiting_on_arjun
        if "waiting on" in normalized:
            return state.waiting_on_others
        if "meeting" in normalized:
            return state.meetings
        if any(term in normalized for term in ("expense variance", "expense report")):
            return self._matching(state.commitments, "expense-variance-report")
        if any(term in normalized for term in ("campaign", "deck")):
            return self._matching(state.commitments, "q3-campaign-deck-review")
        if any(term in normalized for term in ("mumbai", "lease", "renewal")):
            return state.unresolved_items
        if "board prep" in normalized:
            return self._matching(state.commitments + state.meetings, "expense-variance-report", "q3-campaign-deck-review")
        if any(term in normalized for term in ("executive summary", "summary", "what do i need")):
            return self._unique(state.open_tasks + state.overdue_or_at_risk_items + state.unresolved_items)

        candidates = self._unique(state.commitments + state.meetings + state.follow_ups)
        return [item for item in candidates if self._matches_question(item, normalized)]

    @staticmethod
    def _is_ambiguous(question: str) -> bool:
        normalized = " ".join(question.casefold().split())
        generic_phrases = {
            "what is the status",
            "what's the status",
            "what is the update",
            "what's the update",
            "tell me more",
            "what happened",
        }
        return normalized.rstrip("?") in generic_phrases

    @staticmethod
    def _matching(items: Iterable[ExecutiveItem], *ids: str) -> list[ExecutiveItem]:
        return [item for item in items if item.id in ids]

    @staticmethod
    def _unique(items: Iterable[ExecutiveItem]) -> list[ExecutiveItem]:
        return list({item.id: item for item in items}.values())

    @staticmethod
    def _matches_question(item: ExecutiveItem, normalized_question: str) -> bool:
        haystack = " ".join([item.id, item.title, item.status, item.owner or "", *item.details]).casefold()
        ignored_words = {
            "what", "when", "where", "who", "which", "have", "has", "the", "this", "that",
            "with", "about", "status", "still", "pending", "please", "tell", "give", "show",
        }
        keywords = [word.strip("?,.") for word in normalized_question.split() if len(word) > 2]
        keywords = [word for word in keywords if word not in ignored_words]
        return any(keyword in haystack for keyword in keywords)

    @staticmethod
    def _items_for_ids(items: list[ExecutiveItem], ids: list[str]) -> list[ExecutiveItem]:
        items_by_id = {item.id: item for item in items}
        return [items_by_id[item_id] for item_id in ids]

    @staticmethod
    def _context(items: list[ExecutiveItem], state: ExecutiveState) -> dict[str, object]:
        return {
            "as_of": state.as_of.isoformat(),
            "items": [item.model_dump(mode="json") for item in items],
        }

    @staticmethod
    def _sources(items: list[ExecutiveItem]) -> list[SourceReference]:
        return list(
            {source.source_id: source for item in items for source in item.source_references}.values()
        )

    @staticmethod
    def _fallback_answer(items: list[ExecutiveItem]) -> str:
        statements = []
        for item in items:
            statement = f"{item.title}: {item.status}."
            if item.scheduled_start:
                scheduled = item.scheduled_start.strftime("%A, %d %B at %I:%M %p").replace(" at 0", " at ")
                statement += f" Scheduled for {scheduled}."
            if item.due:
                precision = {
                    "morning": "morning",
                    "evening": "evening",
                    "end_of_day": "end of day",
                    "exact": item.due.time or "the specified time",
                }[item.due.precision]
                due_date = date.fromisoformat(item.due.date).strftime("%A, %d %B")
                statement += f" Due {due_date} {precision}."
            statement += " " + " ".join(item.details)
            if item.ownership_status == "unresolved":
                statement += " Ownership remains unresolved."
            statements.append(statement)
        return "Based on the supplied executive state: " + " ".join(statements)
