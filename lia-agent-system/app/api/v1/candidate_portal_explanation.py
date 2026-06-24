"""Candidate Portal Explanation API — /api/v1/candidate/decisions/*.

Endpoint-ponte que dá ao candidato acesso estruturado à explicação das decisões
automatizadas tomadas sobre sua candidatura.

Complementa `decision_explanation.py` (que exige autenticação de recrutador via
`get_current_user`) com autenticação via candidate_token JWT — mesma arquitetura
de `candidate_portal.py` (chat/applications).

Compliant with:
  - EU AI Act Art. 86 (right to explanation of individual decision-making
    in high-risk AI systems — recrutamento enquadra via Anexo III item 4)
  - LGPD Art. 20 (direito de revisão de decisão automatizada)

ADR-005: All endpoints declare response_model.
ADR-006: No PII in logs — candidate_id/vacancy_id/company_id only.
ADR-008: APIResponse envelope.
ADR-014: All routes under /api/v1.
"""
import logging
import os
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.schemas.api_envelope import APIResponse
from fastapi import Depends
from app.shared.security.require_company_id import require_company_id
from app.shared.errors import LIAError, LIAInternalError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/candidate/decisions", tags=["candidate-portal"])

_JWT_SECRET = os.getenv("CANDIDATE_PORTAL_JWT_SECRET", "")


class CandidateDecisionExplanationResponse(BaseModel):
    decisions: list[dict[str, Any]]
    transparency_note: str | None = None
    art_86_notice: str
    total_decisions: int


_ART_86_NOTICE_PT = (
    "De acordo com o EU AI Act (Art. 86) e a LGPD (Art. 20), você tem direito "
    "de solicitar revisão humana desta decisão dentro de 30 dias. Para isso, "
    "responda a este canal ou contate o canal oficial de compliance da empresa."
)


@router.get("/explain", response_model=APIResponse)
async def explain_candidate_decisions_endpoint(
    candidate_token: str = Query(..., description="JWT do candidato"),
    vacancy_id: str | None = Query(
        None,
        description="Vaga específica; se omitido, usa a vaga do token",
    ),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Retorna explicação das decisões tomadas sobre a candidatura.

    Auth: JWT token via query param `candidate_token`.
    Rate limit: herda do CandidateStatusService (10/hora, 30/dia por candidate_id).
    Fonte dos dados: AuditLog + filtro PROTECTED_CRITERIA_LABELS.
    Sanitização: remove scoring bruto, confidence, weights; entrega criteria_evaluated
                 + criteria_ignored + fairness_check agregado + aviso Art. 86.
    """
    from app.domains.candidate_self_service.services.candidate_status_service import (
        CandidateStatusService,
    )

    service = CandidateStatusService()
    token_data = await service.validate_token(candidate_token, _JWT_SECRET)
    if not token_data:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado.")

    candidate_id = token_data["candidate_id"]
    resolved_vacancy_id = vacancy_id or token_data["vacancy_id"]
    company_id = token_data["company_id"]  # anti-IDOR: sempre do token

    rate = await service.check_rate_limit(candidate_id)
    if not rate["allowed"]:
        raise HTTPException(
            status_code=429,
            detail="Limite de consultas atingido. Tente novamente mais tarde.",
        )

    logger.info(
        "[CandidateDecisionExplain] candidate_id=%s vacancy_id=%s",
        candidate_id, resolved_vacancy_id,
    )

    tools_called: list[str] = ["explain_candidate_decision"]
    fairness_triggered = False

    try:
        from app.domains.candidate_self_service.tools.explain_candidate_decision import (
            _explain_candidate_decision,
        )

        result = await _explain_candidate_decision(
            candidate_id=candidate_id,
            vacancy_id=resolved_vacancy_id,
            company_id=company_id,
        )

        if not result.get("success"):
            raise LIAInternalError(result.get("message", "Erro ao recuperar explicação."))

        data = result.get("data", {})
        # Detect fairness triggering in any decision (transparency to audit log)
        for d in data.get("decisions", []):
            if d.get("fairness_check") == "under_review":
                fairness_triggered = True
                break

        # Ensure art_86_notice is always present
        data.setdefault("art_86_notice", _ART_86_NOTICE_PT)
        data.setdefault("total_decisions", len(data.get("decisions", [])))

        return APIResponse.ok(data=data)

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(
            "[CandidateDecisionExplain] error candidate_id=%s: %s",
            candidate_id, exc,
        )
        raise LIAError(message="Erro interno. Tente novamente.")
    finally:
        # Audit log — ADR-006: IDs only, no PII
        try:
            from app.domains.candidate_self_service.repositories.candidate_status_repository import (
                CandidateSelfServiceRepository,
            )
            from app.core.database import get_db

            async for db in get_db():
                repo = CandidateSelfServiceRepository(db)
                await repo.log_portal_access(
                    candidate_id=candidate_id,
                    vacancy_id=resolved_vacancy_id,
                    company_id=company_id,
                    channel="web",
                    tools_called=tools_called,
                    fairness_triggered=fairness_triggered,
                )
                break
        except Exception as audit_exc:
            logger.debug(
                "[CandidateDecisionExplain] audit log failed: %s", audit_exc,
            )
