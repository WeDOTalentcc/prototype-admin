"""Helper canonical para emit_intake_audit (F-4.3 / PR-11 Onda 4).

Extrai ~70 LOC de boilerplate fire-and-forget inline em intake_node (graph.py)
para um helper dedicado, replicando o pattern canonical do
emit_audit_fire_and_forget (PR-4) mas com payload pre-formatado para
log_automated_decision (WT-2022 P0.C — LGPD Art. 20 audit trail).

Diferenca para emit_audit_fire_and_forget:
- emit_audit_fire_and_forget e o helper generico (qualquer audit coro)
- emit_intake_audit e o helper especifico do intake_node, que monta
  o payload canonical de log_automated_decision (PROTECTED_CRITERIA_PT,
  silent_on_persist_error=True, etc) e schedula via async_session_factory.

Fail-safe: gap de log NUNCA bloqueia wizard. Erros internos viram warning.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def emit_intake_audit(
    *,
    company_id: str,
    job_id: Optional[str],
    intake_source: str,
    intake_confidence: float,
    parsed_title: Optional[str],
    parsed_seniority: Optional[str],
    parsed_location: Optional[str],
    parsed_model: Optional[str],
) -> None:
    """Emit audit log canonical de intake completion sem bloquear node.

    Cobre WT-2022 P0.C (LGPD Art. 20 decisao automatizada).

    Args:
        company_id: tenant identifier (vazio = skip silencioso).
        job_id: vaga em construcao, opcional (None no intake inicial).
        intake_source: "llm" | "regex" | "form" | "file" | "none".
        intake_confidence: confidence overall do IntakeExtractor (0.0-1.0).
        parsed_title: titulo extraido.
        parsed_seniority: senioridade extraida.
        parsed_location: localizacao extraida.
        parsed_model: modelo de trabalho extraido.

    Behavior:
    - Sem company_id: skip silencioso (sem warning, normal em fluxos parciais).
    - Sem running loop: skip silencioso + log debug (testes sync isolados).
    - Excecao interna: warning, nao propaga (fail-safe).
    """
    if not company_id:
        return

    try:
        # Lazy imports para evitar circular import no module load time.
        from app.core.database import async_session_factory
        from app.shared.services.automated_decision_logger import (
            PROTECTED_CRITERIA_PT,
            log_automated_decision,
        )

        audit_model = f"intake_extractor_{intake_source}"
        explanation = (
            f"Intake extraction (source={intake_source}, "
            f"conf={intake_confidence:.2f}): "
            f"title={parsed_title!r}, seniority={parsed_seniority!r}, "
            f"location={parsed_location!r}, model={parsed_model!r}."
        )
        confidence = float(intake_confidence) if intake_confidence else None

        async def _do_audit_log() -> None:
            # Fire-and-forget audit context (scheduled via loop.create_task
            # below); persist errors are logged but MUST NOT bubble up — the
            # wizard intake path cannot block on the LGPD audit log.
            # P0.C.HELPER pattern: caller opts in to silent persist degrade.
            try:
                async with async_session_factory() as _adl_db:
                    await log_automated_decision(
                        db=_adl_db,
                        company_id=company_id,
                        job_id=job_id,
                        decision_type="intake_extraction",
                        ai_model_used=audit_model,
                        explanation_text=explanation,
                        criteria_used=[
                            "title",
                            "seniority",
                            "department",
                            "location",
                            "work_model",
                        ],
                        criteria_ignored=PROTECTED_CRITERIA_PT,
                        confidence_score=confidence,
                        review_eligible=True,
                        silent_on_persist_error=True,
                    )
                    await _adl_db.commit()
            except Exception as _inner_exc:  # noqa: BLE001 fail-safe
                logger.warning(
                    "[intake_audit] inner audit log failed (fail-safe): %s",
                    _inner_exc,
                )

        try:
            _loop = asyncio.get_running_loop()
            _loop.create_task(_do_audit_log())
        except RuntimeError:
            # Sem loop ativo (testes sync isolados). Pular log canonical
            # fail-safe pattern.
            logger.debug(
                "[intake_audit] audit log skipped (no running loop)",
            )
    except Exception as _exc:  # noqa: BLE001 fail-safe
        logger.warning(
            "[intake_audit] audit log scheduling failed (fail-safe): %s",
            _exc,
        )
