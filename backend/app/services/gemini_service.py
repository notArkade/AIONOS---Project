"""Constrained Google Gemini generation for source-grounded executive answers."""

import json
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from os import getenv
from typing import Any

from pydantic import BaseModel, Field, ValidationError

SYSTEM_PROMPT = """You are the Executive Productivity Agent for Arjun Malhotra, VP Sales.

Answer only from the structured context supplied in this request. It is the
authoritative assignment data. Never invent people, emails, meetings, dates,
deadlines, task statuses, responsibilities, or outcomes. Do not assign an
unresolved responsibility. Prefer the latest known state while respecting the
history supplied. Distinguish completed from pending work, and confirmed from
unconfirmed meetings. Clearly say when the context does not establish an
answer. Use only the provided item IDs in `used_item_ids`.

Return JSON only, with exactly this shape:
{"answer": "grounded answer", "used_item_ids": ["item-id"]}
"""


class GeminiServiceError(RuntimeError):
    """Raised when Gemini cannot provide a validated response."""

    def __init__(self, message: str, *, reason: str) -> None:
        super().__init__(message)
        self.reason = reason


class GeminiAnswer(BaseModel):
    """The limited Gemini output accepted by the agent service."""

    answer: str = Field(min_length=1)
    used_item_ids: list[str] = Field(min_length=1)


class GeminiService:
    """Small adapter around the official Google GenAI SDK.

    The service has no access to local files, state mutation, tools, or memory.
    It receives only context already selected by the deterministic agent service.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        timeout_seconds: float = 15.0,
    ) -> None:
        self.api_key = api_key if api_key is not None else getenv("GEMINI_API_KEY")
        self.model = model or getenv("GEMINI_MODEL", "gemini-2.5-flash")
        self.timeout_seconds = timeout_seconds

    def generate_answer(
        self,
        question: str,
        context: dict[str, Any],
        allowed_item_ids: set[str],
    ) -> GeminiAnswer:
        """Generate a response and reject malformed or uncited model output."""
        if not self.api_key:
            raise GeminiServiceError("Gemini API key is not configured.", reason="missing_api_key")

        prompt = self._build_prompt(question, context)
        try:
            raw_text = self._generate_with_timeout(prompt)
        except FutureTimeoutError as exc:
            raise GeminiServiceError("Gemini request timed out.", reason="timeout") from exc
        except GeminiServiceError:
            raise
        except Exception as exc:  # SDK/network failures are intentionally converted to a safe fallback.
            raise GeminiServiceError("Gemini request failed.", reason="gemini_failure") from exc

        try:
            answer = GeminiAnswer.model_validate(json.loads(raw_text))
        except (json.JSONDecodeError, ValidationError) as exc:
            raise GeminiServiceError("Gemini returned an invalid response format.", reason="invalid_response") from exc

        unsupported_ids = set(answer.used_item_ids) - allowed_item_ids
        if unsupported_ids:
            raise GeminiServiceError(
                "Gemini referenced items outside the supplied context.", reason="invalid_response"
            )
        return answer

    def _generate_with_timeout(self, prompt: str) -> str:
        """Use a bounded synchronous SDK call so a slow provider cannot crash the API."""
        executor = ThreadPoolExecutor(max_workers=1)
        future = executor.submit(self._generate, prompt)
        try:
            return future.result(timeout=self.timeout_seconds)
        finally:
            executor.shutdown(wait=False, cancel_futures=True)

    def _generate(self, prompt: str) -> str:
        try:
            from google import genai
            from google.genai import types
        except ImportError as exc:
            raise GeminiServiceError("Google GenAI SDK is not installed.", reason="sdk_unavailable") from exc

        client = genai.Client(api_key=self.api_key)
        response = client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                response_mime_type="application/json",
                temperature=0,
                max_output_tokens=600,
            ),
        )
        text = getattr(response, "text", None)
        if not text:
            raise GeminiServiceError("Gemini returned no answer text.", reason="gemini_failure")
        return text

    @staticmethod
    def _build_prompt(question: str, context: dict[str, Any]) -> str:
        return (
            "Question from Arjun:\n"
            f"{question}\n\n"
            "Authoritative relevant context (JSON):\n"
            f"{json.dumps(context, ensure_ascii=False, default=str)}"
        )
