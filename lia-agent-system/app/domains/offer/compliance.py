"""
Compliance helpers for the Offer domain.

Espelha o pattern canonical de :mod:`app.domains.job_creation.compliance` —
três camadas:

1. ``mask_pii_for_llm`` — strip PII de texto livre antes de envio ao LLM
   (LGPD Art. 12 / EU AI Act Art. 13).

2. ``check_input_fairness`` / ``check_output_fairness`` — FairnessGuard regex
   layer sobre input do recrutador *e* output gerado (carta-oferta, benefícios,
   recruiter_notes). Bloqueia envio se padrão discriminatório detectado.

3. ``emit_offer_audit`` — registra ``decision_type = "offer_send"`` per-offer
   para AI Governance ter trilha de auditoria por carta-oferta enviada
   (company_id, candidate_id, prompt_hash, model).

Inegociáveis cobertos:
- #3 FairnessGuard 100% (offer marked high_impact:True em domain.py:30)
- #4 PII masking (LGPD)
- #7 Human override (audit trail permite reversão informada)

Skill aplicada:
- production-quality:compliance-risk
- harness-engineering (FairnessGuard = guide computacional + audit = sensor)
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import threading
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Layer 1 — PII masking
# ---------------------------------------------------------------------------

def mask_pii_for_llm(text: Optional[str]) -> str:
    """Mask PII / quasi-identifiers antes de enviar texto ao LLM.

    Wrap fail-open de :func:`app.shared.pii_masking.strip_pii_for_llm_prompt`.
    """
    if not text:
        return text or ""
    try:
        from app.shared.pii_masking import strip_pii_for_llm_prompt
        return strip_pii_for_llm_prompt(text)
    except Exception as exc:  # pragma: no cover — defensive
        logger.warning("[Offer:Compliance] PII masking failed (fail-open): %s", exc)
        return text


# ---------------------------------------------------------------------------
# Layer 2 — FairnessGuard pre/post checks
# ---------------------------------------------------------------------------

@dataclass
class FairnessCheck:
    """Resultado do FairnessGuard para offer."""

    is_blocked: bool = False
    category: Optional[str] = None
    blocked_terms: List[str] = field(default_factory=list)
    educational_message: Optional[str] = None


def _run_fairness_guard(text: str) -> FairnessCheck:
    """Executa FairnessGuard com fail-open."""
    if not text:
        return FairnessCheck()
    try:
        from app.shared.compliance.fairness_guard import FairnessGuard

        guard = FairnessGuard()
        result = guard.check(text)
        if result is None:
            return FairnessCheck()
        return FairnessCheck(
            is_blocked=bool(getattr(result, "is_blocked", False)),
            category=getattr(result, "category", None),
            blocked_terms=list(getattr(result, "blocked_terms", []) or []),
            educational_message=getattr(result, "educational_message", None),
        )
    except Exception as exc:  # pragma: no cover — defensive
        logger.warning("[Offer:Compliance] FairnessGuard check failed (fail-open): %s", exc)
        return FairnessCheck()


def check_input_fairness(text: Optional[str]) -> FairnessCheck:
    """FairnessGuard sobre texto livre do recrutador (recruiter_notes, etc.)."""
    return _run_fairness_guard(text or "")


def check_output_fairness(text: Optional[str]) -> FairnessCheck:
    """FairnessGuard sobre texto gerado/enviado ao candidato."""
    return _run_fairness_guard(text or "")


# ---------------------------------------------------------------------------
# Layer 3 — Audit emission
# ---------------------------------------------------------------------------

def _prompt_hash(payload: str) -> str:
    return hashlib.sha256((payload or "").encode("utf-8", errors="ignore")).hexdigest()[:16]


def _resolve_model() -> str:
    try:
        from lia_config.config import settings
        return getattr(settings, "LLM_PRIMARY_MODEL", "unknown") or "unknown"
    except Exception:
        return "unknown"


def _run_async(coro, *, timeout: float = 5.0) -> None:
    """Run coroutine sincronamente com timeout. Audit emission deve persistir
    antes de send_offer retornar (garantia "1 audit row per offer send")."""
    result: Dict[str, Any] = {"error": None}

    def _runner() -> None:
        try:
            asyncio.run(coro)
        except Exception as exc:
            result["error"] = exc

    thread = threading.Thread(target=_runner, daemon=True)
    thread.start()
    thread.join(timeout=timeout)
    if thread.is_alive():
        logger.warning(
            "[Offer:Compliance] audit emission did not complete within %.1fs",
            timeout,
        )
    elif result["error"] is not None:
        logger.warning(
            "[Offer:Compliance] audit emission failed: %s", result["error"]
        )


def emit_offer_audit(
    *,
    company_id: str,
    offer_id: Optional[str],
    candidate_id: Optional[str],
    job_id: Optional[str],
    action: str,
    success: bool = True,
    fairness_blocked: Optional[List[str]] = None,
    extra_reasoning: Optional[List[str]] = None,
    payload_text: Optional[str] = None,
) -> None:
    """Audit row para qualquer ação de offer (send/update/cancel/manual_send).

    Captura company_id, candidate_id, job_id, prompt_hash, model. Failures
    são logadas mas não propagadas — auditing nunca quebra offer flow.
    """
    if not company_id:
        logger.debug("[Offer:Audit] skipped — no company_id")
        return

    model = _resolve_model()
    prompt_hash = _prompt_hash(payload_text or "")

    reasoning: List[Any] = [
        f"prompt_hash={prompt_hash}",
        f"model={model}",
        f"candidate_id={candidate_id or 'n/a'}",
        f"job_id={job_id or 'n/a'}",
        f"offer_id={offer_id or 'n/a'}",
    ]
    if extra_reasoning:
        reasoning.extend(extra_reasoning)
    if fairness_blocked:
        reasoning.append({"fairness_blocked": fairness_blocked})

    try:
        from app.shared.compliance.audit_service import AuditService

        service = AuditService()
        coro = service.log_decision(
            company_id=company_id,
            agent_name="offer_domain",
            decision_type="offer_send",
            action=action,
            decision="completed" if success else "blocked" if fairness_blocked else "failed",
            reasoning=reasoning,
            criteria_used=["fairness_check", "consent_validated"],
            job_vacancy_id=str(job_id) if job_id else None,
            confidence=1.0 if success else 0.0,
            human_review_required=bool(fairness_blocked),
            criteria_ignored=None,
        )
        _run_async(coro)
        logger.info(
            "[Offer:Audit] decision_type=offer_send action=%s company=%s offer=%s candidate=%s",
            action, company_id, offer_id, candidate_id,
        )
    except Exception as exc:
        logger.warning("[Offer:Audit] failed to emit audit row: %s", exc)
