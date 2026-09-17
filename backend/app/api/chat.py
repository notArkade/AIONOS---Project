"""Source-grounded chat endpoint for the executive productivity agent."""

from fastapi import APIRouter, Depends

from app.api.executive import to_api_item
from app.models.api import ApiSourceReference, ChatRequest, ChatResponse
from app.services.agent_service import AgentService

router = APIRouter(tags=["chat"])


def get_agent_service() -> AgentService:
    return AgentService()


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, agent: AgentService = Depends(get_agent_service)) -> ChatResponse:
    response = agent.answer(request.message)
    return ChatResponse(
        answer=response.answer,
        sources=[ApiSourceReference(**source.model_dump()) for source in response.sources],
        related_items=[to_api_item(item) for item in response.related_items],
        used_fallback=response.used_fallback,
        fallback_reason=response.fallback_reason,
    )
