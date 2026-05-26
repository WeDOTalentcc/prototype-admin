"""
PipelineTemplateService — orchestration canonical para templates de pipeline.

Sprint Pipeline Templates Afya (2026-05-26) — Fase 1.4.

Responsabilidades:
- Wrappers de CRUD (create/update/archive/clone) que emitem audit log canonical.
- apply_to_vacancy: copy-on-write canonical (template.stages -> vacancy.interview_stages
  com translação de shape) + increment_usage + audit.

Princípios:
- ADR-001 Repository Pattern: SQL via repo, NUNCA inline aqui.
- REGRA #1 ACH-026: todo mutation emite audit_service.log_decision.
- Multi-tenancy: company_id fail-closed (delegado ao repo + AuditService).
- Translação canonical template.stages -> InterviewStage idêntica à versão
  frontend em plataforma-lia/src/components/modals/edit-job/useEditJob.ts:applyPipelineTemplate
  (mantém isomorfismo backend<->frontend até unificarmos via server-side apply).

Refs:
- Plan ~/.claude/plans/precisamos-fazer-uma-analise-polished-quill.md
- Memory project_chat_tool_dispatch_canonical_fix_2026-05-24 (audit canonical)
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.pipeline.repositories.pipeline_template_repository import (
    PipelineTemplateRepository,
)
from app.domains.job_management.repositories.job_vacancy_crud_repository import (
    JobVacancyCrudRepository,
)
from app.shared.compliance.audit_service import audit_service
from app.shared.observability.tracing import trace_span
from lia_models.audit_log import DecisionType
from app.models.pipeline_template import PipelineTemplate

logger = logging.getLogger(__name__)


# Prometheus telemetry counters (Fase 5 - Sprint Pipeline Templates).
# Cardinalidade controlada: company_id + enums fechados (action, source).
# template_id NAO e label (cardinality unbounded).
# Reuso via REGISTRY._names_to_collectors (pattern fallback_metrics.py).
_pipeline_template_apply_total = None  # type: ignore[assignment]
_pipeline_template_mutation_total = None  # type: ignore[assignment]

try:
    from prometheus_client import REGISTRY as _PROM_REGISTRY  # type: ignore
    from prometheus_client import Counter as _PromCounter  # type: ignore

    _names_map = getattr(_PROM_REGISTRY, "_names_to_collectors", {})

    _APPLY_NAME = "pipeline_template_apply_total"
    if _APPLY_NAME in _names_map:
        _pipeline_template_apply_total = _names_map[_APPLY_NAME]
    else:
        _pipeline_template_apply_total = _PromCounter(
            _APPLY_NAME,
            "Number of pipeline template applies (canonical apply_to_vacancy)",
            ["company_id", "source"],
        )

    _MUT_NAME = "pipeline_template_mutation_total"
    if _MUT_NAME in _names_map:
        _pipeline_template_mutation_total = _names_map[_MUT_NAME]
    else:
        _pipeline_template_mutation_total = _PromCounter(
            _MUT_NAME,
            "Number of pipeline template CRUD mutations",
            ["company_id", "action"],
        )
except Exception as _exc:  # pragma: no cover - fail-open
    logger.debug("Prometheus counters unavailable for pipeline_template_service: %s", _exc)


def _inc_mutation(company_id: str, action: str) -> None:
    """Increment mutation counter - fail-open (telemetria NUNCA bloqueia mutation)."""
    try:
        if _pipeline_template_mutation_total is not None:
            _pipeline_template_mutation_total.labels(
                company_id=str(company_id), action=action
            ).inc()
    except Exception as exc:  # pragma: no cover
        logger.debug("pipeline_template_mutation_total inc failed: %s", exc)


def _inc_apply(company_id: str, source: str) -> None:
    """Increment apply counter - fail-open."""
    try:
        if _pipeline_template_apply_total is not None:
            _pipeline_template_apply_total.labels(
                company_id=str(company_id), source=source
            ).inc()
    except Exception as exc:  # pragma: no cover
        logger.debug("pipeline_template_apply_total inc failed: %s", exc)


# canonical source enum — auditável e tipado.
APPLY_SOURCE_MANUAL_MODAL = "manual_modal"
APPLY_SOURCE_WIZARD_AUTO_SUGGEST = "wizard_auto_suggest"
APPLY_SOURCE_WIZARD_EXPLICIT = "wizard_explicit"
APPLY_VALID_SOURCES = {
    APPLY_SOURCE_MANUAL_MODAL,
    APPLY_SOURCE_WIZARD_AUTO_SUGGEST,
    APPLY_SOURCE_WIZARD_EXPLICIT,
}


def translate_template_stages_to_interview_stages(
    template_stages: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Translate PipelineTemplate.stages shape into JobVacancy.interview_stages shape.

    Espelha 1-pra-1 a função frontend applyPipelineTemplate em useEditJob.ts:185.
    Mantém invariant até unificarmos via server-side apply.
    """
    out: list[dict[str, Any]] = []
    for idx, s in enumerate(template_stages or []):
        t = s.get("type", "manual")
        # frontend mapeia automatic -> automated por convenção legada
        if t == "automatic":
            t = "automated"
        out.append({
            "stageName": s.get("name"),
            "order": s.get("order", idx + 1),
            "sla": s.get("sla_days"),
            "type": t,
        })
    return out


class PipelineTemplateService:
    """Service canonical para Pipeline Templates.

    Convenção: cada mutation chama _emit_audit() para trail LGPD/SOX
    (REGRA #1 ACH-026). Sensor scripts/check_pipeline_template_audit_emitted.py
    enforça baseline 0 violations.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = PipelineTemplateRepository(db)
        self._vacancy_repo = JobVacancyCrudRepository(db)

    # ─────────────────────────────────────────────────────────────────
    # Mutations canonical
    # ─────────────────────────────────────────────────────────────────

    async def create(self, company_id: str, data: dict, created_by: str) -> PipelineTemplate:
        if data.get("is_default"):
            await self.repo.clear_default(company_id)
        template = await self.repo.create(company_id, data, created_by=created_by)
        await self._emit_audit(
            action="pipeline_template_created",
            company_id=company_id,
            actor=created_by,
            template=template,
        )
        _inc_mutation(company_id, "created")
        return template

    async def update(
        self,
        template_id: uuid.UUID,
        company_id: str,
        data: dict,
        updated_by: str,
    ) -> PipelineTemplate | None:
        template = await self.repo.get_by_id(template_id, company_id)
        if not template:
            return None
        if data.get("is_default") and not template.is_default:
            await self.repo.clear_default(company_id, exclude_id=template_id)
        template = await self.repo.update(template, data, updated_by=updated_by)
        await self._emit_audit(
            action="pipeline_template_updated",
            company_id=company_id,
            actor=updated_by,
            template=template,
            extra_reasoning=[f"fields_updated: {sorted(data.keys())}"],
        )
        _inc_mutation(company_id, "updated")
        return template

    async def archive(
        self,
        template_id: uuid.UUID,
        company_id: str,
        updated_by: str,
    ) -> PipelineTemplate | None:
        template = await self.repo.get_by_id(template_id, company_id)
        if not template:
            return None
        await self.repo.archive(template, updated_by=updated_by)
        await self._emit_audit(
            action="pipeline_template_archived",
            company_id=company_id,
            actor=updated_by,
            template=template,
        )
        _inc_mutation(company_id, "archived")
        return template

    async def clone(
        self,
        template_id: uuid.UUID,
        company_id: str,
        new_name: str,
        created_by: str,
    ) -> PipelineTemplate | None:
        original = await self.repo.get_by_id(template_id, company_id)
        if not original:
            return None
        cloned = await self.repo.clone(original, new_name=new_name, created_by=created_by)
        await self._emit_audit(
            action="pipeline_template_cloned",
            company_id=company_id,
            actor=created_by,
            template=cloned,
            extra_reasoning=[f"cloned_from_id: {original.id}", f"cloned_from_name: {original.name}"],
        )
        _inc_mutation(company_id, "cloned")
        return cloned

    # ─────────────────────────────────────────────────────────────────
    # Apply canonical (copy-on-write)
    # ─────────────────────────────────────────────────────────────────

    @trace_span("pipeline.template.apply", attributes={"pipeline.template.applied": True})
    async def apply_to_vacancy(
        self,
        template_id: uuid.UUID,
        vacancy_id: uuid.UUID,
        company_id: str,
        applied_by: str,
        source: str,
    ) -> dict[str, Any] | None:
        """Apply template to vacancy as a snapshot (copy-on-write).

        Returns dict {vacancy_id, template_id, template_name, stages_applied, usage_count}
        ou None se template ou vacancy não existir/cross-tenant.

        Source ∈ APPLY_VALID_SOURCES. Audit log canonical com source no reasoning.
        Edit posterior na vaga deve setar is_pipeline_customized=True externamente
        (frontend ou outro endpoint).
        """
        if source not in APPLY_VALID_SOURCES:
            raise ValueError(
                f"invalid apply source {source!r}; expected one of {sorted(APPLY_VALID_SOURCES)}"
            )

        template = await self.repo.get_by_id(template_id, company_id)
        if not template:
            return None

        # Multi-tenancy fail-closed via canonical CRUD repo helper.
        vacancy = await self._vacancy_repo.get_vacancy_by_id_and_company(vacancy_id, company_id)
        if not vacancy:
            return None

        new_stages = translate_template_stages_to_interview_stages(template.stages or [])
        vacancy.interview_stages = new_stages
        # Reset customization flag — apply traz template limpo.
        if hasattr(vacancy, "is_pipeline_customized"):
            vacancy.is_pipeline_customized = False
        vacancy.updated_at = datetime.utcnow()
        self.db.add(vacancy)

        await self.repo.increment_usage(template)
        await self.db.flush()

        await self._emit_audit(
            action="pipeline_template_applied",
            company_id=company_id,
            actor=applied_by,
            template=template,
            job_vacancy_id=str(vacancy_id),
            extra_reasoning=[
                f"source: {source}",
                f"stages_applied: {len(new_stages)}",
            ],
        )

        _inc_apply(company_id, source)
        return {
            "vacancy_id": str(vacancy_id),
            "template_id": str(template.id),
            "template_name": template.name,
            "stages_applied": len(new_stages),
            "usage_count": template.usage_count,
            "source": source,
        }

    # ─────────────────────────────────────────────────────────────────
    # Audit emitter canonical (REGRA #1 ACH-026)
    # ─────────────────────────────────────────────────────────────────

    async def _emit_audit(
        self,
        *,
        action: str,
        company_id: str,
        actor: str,
        template: PipelineTemplate,
        job_vacancy_id: str | None = None,
        extra_reasoning: list[str] | None = None,
    ) -> None:
        reasoning = [
            f"action: {action}",
            f"template_id: {template.id}",
            f"template_name: {template.name}",
        ]
        if extra_reasoning:
            reasoning.extend(extra_reasoning)
        try:
            await audit_service.log_decision(
                company_id=company_id,
                agent_name="pipeline_template_service",
                decision_type=DecisionType.COMPANY_SETTINGS_CHANGE.value,
                action=action,
                decision=f"{action}: {template.name}",
                reasoning=reasoning,
                criteria_used=["template_id", "company_id"],
                job_vacancy_id=job_vacancy_id,
                actor_user_id=actor,
                human_review_required=False,
            )
        except Exception as exc:
            # Audit failure should not block the mutation — log loudly.
            logger.error(
                "PipelineTemplate audit emission FAILED action=%s template_id=%s err=%s",
                action,
                template.id,
                exc,
                exc_info=True,
            )
