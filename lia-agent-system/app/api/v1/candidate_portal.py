"""Candidate Portal API — /api/v1/candidate/*.

ADR-014: All routes under /api/v1.
ADR-005: All endpoints declare response_model.
ADR-006: No PII in logs — candidate_id/vacancy_id/company_id only.
ADR-008: APIResponse envelope.
"""
import logging
import os
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.schemas.api_envelope import APIResponse
from fastapi import Depends
from app.shared.security.require_company_id import require_company_id
from app.shared.errors import LIAError
from app.shared.types import WeDoBaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/candidate", tags=["candidate-portal"])

_JWT_SECRET = os.getenv("CANDIDATE_PORTAL_JWT_SECRET", "")


class CandidateChatRequest(WeDoBaseModel):
    message: str
    candidate_token: str
    vacancy_id: str | None = None


class CandidateChatResponse(BaseModel):
    reply: str
    domain: str = "candidate_self_service"


class CandidateApplicationsResponse(BaseModel):
    applications: list[dict[str, Any]]


@router.post("/chat", response_model=APIResponse)
async def candidate_chat(request_data: CandidateChatRequest, request: Request, company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Candidate-facing chat endpoint — LLM-powered status queries.

    Auth: JWT token in body (candidate_token).
    Rate limiting: per candidate_id via Redis (10/hour, 30/day).
    Routing: CandidateSelfServiceAgent.
    """
    from app.domains.candidate_self_service.services.candidate_status_service import (
        CandidateStatusService,
    )
    from app.domains.candidate_self_service.repositories.candidate_status_repository import (
        CandidateSelfServiceRepository,
    )

    service = CandidateStatusService()
    token_data = await service.validate_token(request_data.candidate_token, _JWT_SECRET)
    if not token_data:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado.")

    candidate_id = token_data["candidate_id"]
    vacancy_id = request_data.vacancy_id or token_data["vacancy_id"]
    company_id = token_data["company_id"]  # always from token — anti-IDOR

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

    tools_called: list[str] = []
    fairness_triggered = False

    try:
        from lia_agents_core.agent_interface import AgentInput
        from app.domains.candidate_self_service.agents.candidate_react_agent import (
            CandidateSelfServiceAgent,
        )

        agent = CandidateSelfServiceAgent()

        # ── Gap F (ADR LGPD, 2026-06-08): mascarar PII antes do LLM ──────────
        # Surface candidate-facing: o candidato digita CPF/RG/email/telefone
        # (próprios ou de terceiros). mask_names=True (default) é correto aqui
        # — diferente do chat do recrutador (agent_chat_sse.py, mask_names=False
        # para preservar nomes em busca de entidade). C3b comment fechado.
        try:
            from app.shared.pii_masking import strip_pii_for_llm_prompt
            safe_message = strip_pii_for_llm_prompt(request_data.message)
        except Exception as _pii_exc:
            logger.warning(
                "[CandidatePortal] PII strip falhou (fail-open): %s", _pii_exc
            )
            safe_message = request_data.message

        agent_input = AgentInput(
            message=safe_message,
            company_id=company_id,
            # AgentInput.user_id é obrigatório (Field(...)). O portal do
            # candidato não tem usuário recrutador — usar o candidate_id como
            # identidade. Sem isto o endpoint falhava com validation error/500.
            user_id=f"candidate_{candidate_id}",
            session_id=f"css_{candidate_id}_{vacancy_id}",
            context={
                "candidate_id": candidate_id,
                "vacancy_id": vacancy_id,
                "domain": "candidate_self_service",
                "channel": "web",
            },
        )
        output = await agent.process(agent_input)

        tools_called = getattr(output, "tools_called", []) or []
        fairness_triggered = getattr(output, "fairness_triggered", False) or False

        return APIResponse.ok(
            data={
                "reply": output.message,
                "domain": "candidate_self_service",
            }
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("[CandidatePortal] chat error candidate_id=%s: %s", candidate_id, exc)
        raise LIAError(message="Erro interno. Tente novamente.")
    finally:
        # Audit log — ADR-006: IDs only, no PII
        try:
            repo = CandidateSelfServiceRepository()
            await repo.log_portal_access(
                candidate_id=candidate_id,
                vacancy_id=vacancy_id,
                company_id=company_id,
                channel="web",
                tools_called=tools_called,
                fairness_triggered=bool(fairness_triggered),
            )
        except Exception as audit_exc:
            logger.debug("[CandidatePortal] audit log failed: %s", audit_exc)


@router.get("/applications", response_model=APIResponse)
async def list_candidate_applications(candidate_token: str, company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """List active applications for a candidate — used by frontend job selector.

    Returns list of applies so UI can show selector if candidate has 2+ vacancies.
    """
    from app.domains.candidate_self_service.services.candidate_status_service import (
        CandidateStatusService,
    )
    from app.domains.candidate_self_service.repositories.candidate_status_repository import (
        CandidateSelfServiceRepository,
    )

    service = CandidateStatusService()
    token_data = await service.validate_token(candidate_token, _JWT_SECRET)
    if not token_data:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado.")

    candidate_id = token_data["candidate_id"]
    company_id = token_data["company_id"]  # always from token — anti-IDOR

    logger.info("[CandidatePortal] list_applications candidate_id=%s", candidate_id)

    # Rails eliminated (RAILS_API_URL absent) — candidate portal applications
    # managed via FastAPI CandidateSelfService domain (migration T5 pending).
    raise HTTPException(status_code=503, detail="Portal do candidato: migração Rails→FastAPI pendente.")
