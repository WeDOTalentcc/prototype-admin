"""Candidate Portal API — /api/v1/candidate-chat and /api/v1/candidate-portal/*.

ADR-014: All routes under /api/v1.
ADR-005: All endpoints declare response_model.
ADR-006: No PII in logs — candidate_id only.
ADR-008: APIResponse envelope.
"""
import logging
import os
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.schemas.api_envelope import APIResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/candidate", tags=["candidate-portal"])

_JWT_SECRET = os.getenv("CANDIDATE_PORTAL_JWT_SECRET", "")


class CandidateChatRequest(BaseModel):
    message: str
    candidate_token: str


class CandidateChatResponse(BaseModel):
    reply: str
    domain: str = "candidate_self_service"


class CandidateApplicationsResponse(BaseModel):
    applications: list[dict[str, Any]]
    candidate_name: str


@router.post("/chat", response_model=APIResponse)
async def candidate_chat(request_data: CandidateChatRequest, request: Request):
    """Candidate-facing chat endpoint — LLM-powered status queries.

    Auth: JWT token in body (candidate_token).
    Rate limiting: per candidate_id via Redis (10/hour, 30/day).
    Routing: cascaded_router → candidate_self_service domain.
    """
    from app.domains.candidate_self_service.services.candidate_status_service import (
        CandidateStatusService,
    )

    service = CandidateStatusService()
    token_data = await service.validate_token(request_data.candidate_token, _JWT_SECRET)
    if not token_data:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado.")

    candidate_id = token_data["candidate_id"]
    vacancy_id = token_data["vacancy_id"]
    company_id = token_data["company_id"]

    # Rate limiting per candidate_id (ADR-006: log id only)
    rate = await service.check_rate_limit(candidate_id)
    if not rate["allowed"]:
        raise HTTPException(
            status_code=429,
            detail="Limite de mensagens atingido. Tente novamente mais tarde.",
        )

    logger.info(
        "[CandidatePortal] chat candidate_id=%s vacancy_id=%s",
        candidate_id, vacancy_id,
    )

    try:
        from lia_agents_core.agent_interface import AgentInput
        from app.domains.candidate_self_service.agents.candidate_react_agent import (
            CandidateSelfServiceAgent,
        )

        agent = CandidateSelfServiceAgent()
        agent_input = AgentInput(
            message=request_data.message,
            company_id=company_id,
            session_id=f"css_{candidate_id}_{vacancy_id}",
            context={
                "candidate_id": candidate_id,
                "vacancy_id": vacancy_id,
                "domain": "candidate_self_service",
            },
        )
        output = await agent.process(agent_input)

        return APIResponse.ok(
            data={
                "reply": output.message,
                "domain": "candidate_self_service",
            }
        )
    except Exception as exc:
        logger.error("[CandidatePortal] chat error candidate_id=%s: %s", candidate_id, exc)
        raise HTTPException(status_code=500, detail="Erro interno. Tente novamente.")


@router.get("/applications", response_model=APIResponse)
async def list_candidate_applications(candidate_token: str):
    """List active applications for a candidate — used by frontend job selector.

    Returns list of applies so UI can show selector if candidate has 2+ vacancies.
    """
    from app.domains.candidate_self_service.services.candidate_status_service import (
        CandidateStatusService,
    )

    service = CandidateStatusService()
    token_data = await service.validate_token(candidate_token, _JWT_SECRET)
    if not token_data:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado.")

    candidate_id = token_data["candidate_id"]
    company_id = token_data["company_id"]

    logger.info("[CandidatePortal] list_applications candidate_id=%s", candidate_id)

    try:
        from app.shared.rails_client import rails_get
        data = await rails_get(
            "/v1/candidate-portal/applications",
            params={"candidate_id": candidate_id},
            company_id=company_id,
        )
        return APIResponse.ok(data=data)
    except Exception as exc:
        logger.error("[CandidatePortal] list_applications error candidate_id=%s: %s", candidate_id, exc)
        raise HTTPException(status_code=500, detail="Erro ao buscar candidaturas.")
