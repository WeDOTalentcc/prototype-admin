"""Resolve the structural ``RecruitmentStage.id`` for a textual stage name.

Task #1303 added ``VacancyCandidate.recruitment_stage_id`` (a stable link to
``RecruitmentStage.id``) and populated it at the canonical transition point
(``pipeline_stage_service.transition_candidate``). Task #1306 extends the same
guarantee to every other path that writes ``VacancyCandidate.stage`` directly,
so the SLA detector can join by id instead of fragile name matching.

This helper resolves a stage name to its ``RecruitmentStage.id`` within a
company. It is fail-soft: any lookup error returns ``None`` so callers never
break a candidate-movement write because of the best-effort id population.
"""
from __future__ import annotations

import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def resolve_recruitment_stage_id(
    db: AsyncSession,
    company_id: str | None,
    stage_name: str | None,
) -> uuid.UUID | None:
    """Return the ``RecruitmentStage.id`` matching ``stage_name`` for a company.

    Matching mirrors the canonical service (exact ``name``) but adds
    case-insensitive ``name`` and ``display_name`` fallbacks so common label
    variations still resolve. Returns ``None`` when nothing matches (the row
    keeps its legacy name-only behaviour) or on any error.
    """
    if not company_id or not stage_name:
        return None

    try:
        from lia_models.recruitment_stages import RecruitmentStage

        result = await db.execute(
            select(RecruitmentStage.id, RecruitmentStage.name, RecruitmentStage.display_name)
            .where(
                RecruitmentStage.company_id == str(company_id),
                RecruitmentStage.is_active,
            )
        )
        rows = result.all()
    except Exception as exc:  # noqa: BLE001 — fail-soft, never block the write
        logger.debug("resolve_recruitment_stage_id query failed: %s", exc)
        return None

    if not rows:
        return None

    target = stage_name.strip()
    target_lower = target.lower()

    # 1) Exact name match (aligns with pipeline_stage_service).
    for stage_id, name, _display in rows:
        if name == target:
            return stage_id
    # 2) Case-insensitive name match.
    for stage_id, name, _display in rows:
        if name and name.strip().lower() == target_lower:
            return stage_id
    # 3) Case-insensitive display_name match.
    for stage_id, _name, display in rows:
        if display and display.strip().lower() == target_lower:
            return stage_id

    return None
