"""
Pipeline Template wizard tools — canonical helpers para o job_creation graph.

Sprint Pipeline Templates Afya 2026-05-26 — Fase 1.6.

Responsabilidades:
- `suggest_pipeline_template_db(db, company_id, ...)` — async helper consultando
  PipelineTemplateRepository.list_for_suggestion (scoring canonical 0.50/0.25/0.25).
- `apply_pipeline_template_with_hitl(db, ..., human_confirmed)` — HITL gate AUD-4
  (P1-4 fix) que delega a PipelineTemplateService.apply_to_vacancy quando aprovado
  pelo recrutador, ou retorna `pending_human_approval` quando não.
- `suggest_pipeline_template_sync_for_graph(...)` — wrapper sync usado dentro do
  graph.py (sync nodes), fail-open: qualquer erro retorna None (graph node cai
  no fallback heurístico legacy `_suggest_pipeline_template`).

Princípios canonical (CLAUDE.md):
- ADR-001: SQL via repo, NUNCA inline aqui.
- REGRA #1 ACH-026: apply emite audit via service.
- Multi-tenancy fail-closed: company_id obrigatório, validado pelo repo.
- HITL canonical (memory project_chat_tool_dispatch_canonical_fix_2026-05-24):
  apply NUNCA executa side-effect sem `human_confirmed=True`.
- Fail-open na ponta de graph (sync wrapper) — qualquer erro NÃO bloqueia
  fluxo do wizard chat; cai no fallback heurístico.

Refs:
- Plan ~/.claude/plans/precisamos-fazer-uma-analise-polished-quill.md
- app/domains/pipeline/services/pipeline_template_service.py (Fase 1.4)
- app/domains/pipeline/repositories/pipeline_template_repository.py (Fase 1.3)
"""
from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.pipeline.repositories.pipeline_template_repository import (
    PipelineTemplateRepository,
)
from app.domains.pipeline.services.pipeline_template_service import (
    APPLY_VALID_SOURCES,
    PipelineTemplateService,
)

logger = logging.getLogger(__name__)


# Prometheus telemetry counter (Fase 5 - Sprint Pipeline Templates).
# Buckets de score com cardinality fechada para evitar explosao de labels.
_pipeline_template_suggest_shown_total = None  # type: ignore[assignment]

try:
    from prometheus_client import REGISTRY as _PROM_REGISTRY  # type: ignore
    from prometheus_client import Counter as _PromCounter  # type: ignore

    _names_map = getattr(_PROM_REGISTRY, "_names_to_collectors", {})
    _SUGGEST_NAME = "pipeline_template_suggest_shown_total"
    if _SUGGEST_NAME in _names_map:
        _pipeline_template_suggest_shown_total = _names_map[_SUGGEST_NAME]
    else:
        _pipeline_template_suggest_shown_total = _PromCounter(
            _SUGGEST_NAME,
            "Pipeline template suggest_db calls com should_suggest=True",
            ["score_bucket"],
        )
except Exception as _exc:  # pragma: no cover - fail-open
    logger.debug("Prometheus counter unavailable for pipeline_template wizard tools: %s", _exc)


def _score_bucket(score: float) -> str:
    """Bucket canonical low-cardinality para score 0..1."""
    if score >= 0.85:
        return "0.85-1.0"
    if score >= 0.70:
        return "0.70-0.85"
    return "below_threshold"


def _inc_suggest_shown(top_score: float) -> None:
    """Increment suggestion counter - fail-open."""
    try:
        if _pipeline_template_suggest_shown_total is not None:
            _pipeline_template_suggest_shown_total.labels(
                score_bucket=_score_bucket(top_score)
            ).inc()
    except Exception as exc:  # pragma: no cover
        logger.debug("pipeline_template_suggest_shown_total inc failed: %s", exc)


# Threshold canonical para auto-suggest no wizard chat.
# < 0.7 = LIA não chama a sugestão (fluxo segue normal). >= 0.7 = card renderizado.
WIZARD_SUGGEST_THRESHOLD = 0.7

# Top-N templates retornados pelo helper sync (graph emit).
WIZARD_SUGGEST_TOP_N = 3


async def suggest_pipeline_template_db(
    db: AsyncSession,
    company_id: str,
    *,
    department: str | None = None,
    seniority: str | None = None,
    job_family: str | None = None,
    threshold: float = WIZARD_SUGGEST_THRESHOLD,
    top_n: int = WIZARD_SUGGEST_TOP_N,
) -> dict[str, Any]:
    """Suggest pipeline templates via DB query (canonical).

    Returns shape:
      {
        "templates": [
          {"template_id", "name", "description", "stages_count", "score"}
          ...top_n
        ],
        "top_score": float,
        "should_suggest": bool,  # True quando top_score >= threshold
      }

    Quando shouldnt_suggest, templates pode estar vazio — caller decide se
    emite ui_action ou se cai em fallback.
    """
    if not company_id:
        return {"templates": [], "top_score": 0.0, "should_suggest": False}

    repo = PipelineTemplateRepository(db)
    scored = await repo.list_for_suggestion(
        company_id,
        department=department,
        seniority=seniority,
        job_family=job_family,
    )
    if not scored:
        return {"templates": [], "top_score": 0.0, "should_suggest": False}

    top_score = scored[0][1]
    # Filtra por threshold mais conservador no caller; aqui já cortamos por top_n.
    filtered = [(t, s) for t, s in scored if s > 0.0][:top_n]

    templates = [
        {
            "template_id": str(t.id),
            "name": t.name,
            "description": t.description,
            "stages_count": len(t.stages or []),
            "score": round(s, 3),
        }
        for t, s in filtered
    ]

    _should_suggest = top_score >= threshold
    if _should_suggest:
        _inc_suggest_shown(top_score)
    return {
        "templates": templates,
        "top_score": round(top_score, 3),
        "should_suggest": _should_suggest,
    }


async def apply_pipeline_template_with_hitl(
    db: AsyncSession,
    *,
    template_id: str | uuid.UUID,
    vacancy_id: str | uuid.UUID,
    company_id: str,
    applied_by: str,
    source: str,
    human_confirmed: bool = False,
) -> dict[str, Any]:
    """Apply pipeline template to vacancy com HITL gate (AUD-4).

    HITL canonical: NUNCA executa apply (side-effect: muda interview_stages
    da vaga + increment usage_count + emite audit) sem human_confirmed=True.
    Caller (LLM agent OR frontend wizard card) deve OBRIGATORIAMENTE passar
    `human_confirmed=True` apenas quando recrutador clicou no botão de
    aprovação explícita.

    Returns:
      - `{status: "pending_human_approval", required: "human_confirmed=True", ...}`
        quando human_confirmed=False
      - `{status: "applied", ...result do service.apply_to_vacancy}` quando confirmed
      - `{status: "error", reason}` em validation/lookup failures
    """
    if not human_confirmed:
        return {
            "status": "pending_human_approval",
            "required": "human_confirmed=True",
            "message": (
                "Apply de pipeline template exige confirmação humana explícita. "
                "Recrutador deve clicar 'Aplicar este template' no card da LIA."
            ),
            "template_id": str(template_id),
            "vacancy_id": str(vacancy_id),
            "source": source,
        }

    if source not in APPLY_VALID_SOURCES:
        return {
            "status": "error",
            "reason": f"invalid source {source!r}; expected one of {sorted(APPLY_VALID_SOURCES)}",
        }

    try:
        tpl_uuid = uuid.UUID(str(template_id))
        vac_uuid = uuid.UUID(str(vacancy_id))
    except ValueError as exc:
        return {"status": "error", "reason": f"invalid id format: {exc}"}

    service = PipelineTemplateService(db)
    result = await service.apply_to_vacancy(
        template_id=tpl_uuid,
        vacancy_id=vac_uuid,
        company_id=company_id,
        applied_by=applied_by,
        source=source,
    )
    if result is None:
        return {
            "status": "error",
            "reason": "template or vacancy not found (or cross-tenant)",
        }
    return {"status": "applied", **result}


def suggest_pipeline_template_sync_for_graph(
    company_id: str,
    *,
    department: str | None = None,
    seniority: str | None = None,
    job_family: str | None = None,
    threshold: float = WIZARD_SUGGEST_THRESHOLD,
    top_n: int = WIZARD_SUGGEST_TOP_N,
) -> dict[str, Any] | None:
    """Sync wrapper para uso DENTRO de graph nodes sync (job_creation/graph.py).

    Fail-open canonical: qualquer erro (DB indisponível, ContextVar limpa,
    asyncio dispatch falhou, etc.) retorna None. Graph node ANTES e DEPOIS
    desta chamada continua funcional (cai no `_suggest_pipeline_template`
    legacy heurístico).

    Uso esperado:

        result = suggest_pipeline_template_sync_for_graph(
            state.get("company_id") or state.get("workspace_id"),
            department=state.get("parsed_department"),
            seniority=state.get("parsed_seniority"),
            job_family=state.get("parsed_job_family"),
        )
        # result é None OU {"templates": [...], "top_score": ..., "should_suggest": ...}
    """
    if not company_id:
        return None

    try:
        import asyncio as _asyncio

        from app.core.database import AsyncSessionLocal

        async def _run() -> dict[str, Any]:
            async with AsyncSessionLocal() as session:
                return await suggest_pipeline_template_db(
                    session,
                    company_id,
                    department=department,
                    seniority=seniority,
                    job_family=job_family,
                    threshold=threshold,
                    top_n=top_n,
                )

        # Mesmo padrão de _asyncio.run(...) usado no jd_enrichment_node para
        # audit log. Para queries read-only o risco de loop poisoning é
        # mínimo (sem mutations, sem long-lived connections).
        return _asyncio.run(_run())
    except Exception as exc:  # noqa: BLE001 — fail-open por design
        logger.warning(
            "suggest_pipeline_template_sync_for_graph fail-open (graph cairá no fallback heurístico): %s",
            exc,
        )
        return None
