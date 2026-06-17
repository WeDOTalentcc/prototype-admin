"""
Self-Scheduling Public API — Sprint 1C.

Endpoints públicos (sem autenticação) para o fluxo de auto-agendamento
de entrevistas pelo candidato:

  GET  /scheduling/link/{token}          — exibe slots disponíveis
  POST /scheduling/link/{token}/confirm  — candidato confirma horário

E endpoints autenticados para o recrutador/agente criar links:

  POST /scheduling/link                  — cria link e envia ao candidato
"""
import logging
from app.shared.errors import LIAInternalError
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user_or_demo
from app.auth.models import User
from app.core.database import get_db
from app.shared.services.zero_touch_scheduling_service import zero_touch_scheduling_service
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel

logger = logging.getLogger(__name__)


async def _is_self_scheduling_enabled(company_id: str, db: AsyncSession) -> bool:
    """Return True iff the company policy allows recruiters to create
    self-scheduling links.

    Closes P1-7 (audit 2026-05-21): the toggle
    ``CompanyHiringPolicy.scheduling_rules.self_scheduling_enabled`` was
    propagated to the frontend (``scheduling_service.py:94``) but no
    write-path endpoint actually refused to create links when off.
    Recruiter could disable the feature in Configurações and still create
    self-scheduling links via the API or LLM tool.

    Fail-soft posture: DB error returns the canonical default (False).
    Cold-start tenants (no policy row yet) return False — explicit opt-in
    matches the schema default in ``SchedulingRulesIn``.
    """
    from app.domains.hiring_policy.repositories.hiring_policy_repository import (
        HiringPolicyRepository,
    )
    try:
        repo = HiringPolicyRepository(db)
        policy = await repo.get_by_company(company_id)
        if not policy or not policy.scheduling_rules:
            return False
        return bool(policy.scheduling_rules.get("self_scheduling_enabled", False))
    except Exception as exc:
        logger.warning(
            "[self_scheduling] policy load failed for company=%s; defaulting to OFF. Reason: %s",
            company_id, str(exc)[:120],
        )
        return False

router = APIRouter(prefix="/scheduling", tags=["self-scheduling"])


# ─── Schemas ──────────────────────────────────────────────────────────────────

class SlotSchema(BaseModel):
    start: str = Field(..., description="ISO 8601 datetime, ex: '2026-03-10T10:00:00'")
    end: str = Field(..., description="ISO 8601 datetime, ex: '2026-03-10T11:00:00'")


class CreateSchedulingLinkRequest(WeDoBaseModel):
    candidate_id: str
    candidate_name: str
    candidate_email: EmailStr
    candidate_phone: str | None = None
    job_vacancy_id: str
    job_title: str
    available_slots: list[SlotSchema]
    interviewer_emails: list[str]
    interview_type: str = "hr"
    interview_mode: str = "video"
    duration_minutes: int = 60
    preferred_channel: str = "whatsapp"
    expires_hours: int = 72


class ConfirmSlotRequest(WeDoBaseModel):
    start: str = Field(..., description="ISO 8601 datetime do slot selecionado")
    end: str = Field(..., description="ISO 8601 datetime fim do slot selecionado")


# ─── Endpoints Públicos (sem auth) ────────────────────────────────────────────

@router.get("/link/{token}", include_in_schema=True, response_model=None)
async def get_scheduling_link(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    # T-1157: endpoint LEGITIMAMENTE público (candidato sem JWT).
    # Tenant scope deriva do token opaco (single-use, expira via SelfSchedulingLink.is_valid).
    # NÃO adicionar Depends(require_company_id) aqui — quebra o fluxo de candidato.
    # Arquivo está em tests/.allowlist_public_endpoints.txt (T-1129 sealing).
    """
    Retorna dados públicos de um link de auto-agendamento.

    Usado pela página pública `/agendar/{token}` no frontend para
    exibir os horários disponíveis ao candidato.
    """
    link_data = await zero_touch_scheduling_service.get_link_by_token(token=token, db=db)
    if not link_data:
        raise HTTPException(status_code=404, detail="Link de agendamento não encontrado")

    if link_data.get("status") not in ("pending", "active"):
        raise HTTPException(
            status_code=410,
            detail="Este link já foi utilizado ou expirou",
        )

    expires_at_str = link_data.get("expires_at")
    if expires_at_str:
        try:
            expires_dt = datetime.fromisoformat(expires_at_str.replace("Z", "+00:00"))
            if expires_dt.replace(tzinfo=None) < datetime.utcnow():
                raise HTTPException(status_code=410, detail="Este link expirou")
        except ValueError:
            pass

    # Retorna apenas campos públicos (sem dados internos)
    return {
        "candidate_name": link_data.get("candidate_name"),
        "job_title": link_data.get("job_title"),
        "interview_type": link_data.get("interview_type"),
        "interview_mode": link_data.get("interview_mode"),
        "duration_minutes": link_data.get("duration_minutes"),
        "available_slots": link_data.get("available_slots", []),
        "expires_at": link_data.get("expires_at"),
        "is_valid": link_data.get("is_valid", False),
    }


@router.post("/link/{token}/confirm", include_in_schema=True, response_model=None)
async def confirm_scheduling_slot(
    token: str,
    body: ConfirmSlotRequest,
    db: AsyncSession = Depends(get_db),
):
    # T-1157: endpoint LEGITIMAMENTE público (candidato sem JWT).
    # Tenant scope deriva do token opaco; replay protegido por SelfSchedulingLink.is_valid
    # (status pending/active, expires_at, use_count < max_uses).
    """
    Candidato confirma o horário escolhido.

    Cria o Interview automaticamente e marca o link como utilizado.
    """
    selected_slot: dict[str, str] = {"start": body.start, "end": body.end}

    result = await zero_touch_scheduling_service.confirm_slot(
        token=token,
        selected_slot=selected_slot,
        db=db,
    )

    if not result.get("success"):
        error = result.get("error", "Erro ao confirmar agendamento")
        if "não encontrado" in error.lower():
            raise HTTPException(status_code=404, detail=error)
        if "expirado" in error.lower() or "utilizado" in error.lower():
            raise HTTPException(status_code=410, detail=error)
        raise HTTPException(status_code=400, detail=error)

    return {
        "success": True,
        "message": "Entrevista agendada com sucesso! Você receberá um e-mail de confirmação.",
        "candidate_name": result.get("candidate_name"),
        "job_title": result.get("job_title"),
        "selected_slot": result.get("selected_slot"),
    }


# ─── Endpoints Autenticados (recrutador/agente) ───────────────────────────────

@router.post("/link", include_in_schema=True, response_model=None)
async def create_scheduling_link(
    body: CreateSchedulingLinkRequest,
    current_user: User = Depends(get_current_user_or_demo),
    db: AsyncSession = Depends(get_db),
    company_id: str = Depends(require_company_id),
):
    """
    Cria um link de auto-agendamento e envia ao candidato via WhatsApp ou e-mail.

    Retorna o token do link e a URL para o candidato acessar.

    T-1157: endpoint do recrutador — mantém gate require_company_id.
    Hardening: ignora ``company_id`` se diferir do JWT (defesa em
    profundidade contra tenant-spoofing via body).
    """
    # P1-7 gate (audit 2026-05-21): refuse to create the link if the
    # company has disabled self-scheduling in Configurações. Default is
    # False (opt-in) — recruiters must explicitly enable. Without this
    # gate, the toggle was a ghost setting.
    if not await _is_self_scheduling_enabled(company_id, db):
        logger.info(
            "[self_scheduling] create_scheduling_link refused — policy OFF. company_id=%s",
            company_id,
        )
        raise HTTPException(
            status_code=403,
            detail={
                "error": "self_scheduling_disabled",
                "message": (
                    "Auto-agendamento esta desativado para esta empresa. "
                    "Ative em Configuracoes > Politicas de Recrutamento > "
                    "Auto-agendamento, ou agende manualmente."
                ),
                "ui_action": "enable_self_scheduling",
            },
        )

    # R2 canonical: company_id from JWT (require_company_id) — company_id removed from schema
    slots_as_dicts = [{"start": s.start, "end": s.end} for s in body.available_slots]
    created_by = getattr(current_user, "id", "system") or "system"

    result = await zero_touch_scheduling_service.send_scheduling_link(
        company_id=company_id,
        candidate_id=body.candidate_id,
        candidate_name=body.candidate_name,
        candidate_email=body.candidate_email,
        candidate_phone=body.candidate_phone,
        job_vacancy_id=body.job_vacancy_id,
        job_title=body.job_title,
        available_slots=slots_as_dicts,
        interviewer_emails=body.interviewer_emails,
        interview_type=body.interview_type,
        interview_mode=body.interview_mode,
        duration_minutes=body.duration_minutes,
        preferred_channel=body.preferred_channel,
        expires_hours=body.expires_hours,
        created_by=str(created_by),
        db=db,
    )

    if not result.get("success"):
        raise LIAInternalError(result.get("error", "Erro ao criar link de agendamento"))

    return result
