"""
Navigation Intent API — Classifies user messages into navigation pages.

POST /api/v1/navigation-intent
  Body: { "message": "quais vagas estão abertas?" }
  Response: { "page": "Vagas", "confidence": 0.7, "hint": "Quer que eu abra a página de Vagas?" }

Used by the LIA Float panel to suggest contextual navigation.
"""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.orchestrator.context.navigation_intent import detect_navigation_intent
from fastapi import Depends
from app.shared.types import WeDoBaseModel

router = APIRouter(prefix="/navigation-intent", tags=["navigation"])


class NavigationIntentRequest(WeDoBaseModel):
    message: str = Field(..., min_length=1, max_length=2000)


class NavigationIntentResponse(BaseModel):
    page: str | None = None
    confidence: float
    hint: str | None = None
    matched_pattern: str | None = None


@router.post("", response_model=NavigationIntentResponse)
async def classify_navigation_intent(request: NavigationIntentRequest, ) -> NavigationIntentResponse:
    # multi-tenancy: public endpoint (navigation_intent) — no tenant data
    """
    Classify a user message to detect which platform page it refers to.
    Returns page name matching dashboard-app navigation keys.
    """
    result = detect_navigation_intent(request.message)
    return NavigationIntentResponse(
        page=result.page,
        confidence=result.confidence,
        hint=result.hint,
        matched_pattern=result.matched_pattern,
    )
