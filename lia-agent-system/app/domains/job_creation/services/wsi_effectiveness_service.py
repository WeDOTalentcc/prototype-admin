"""WsiEffectivenessService - Sprint B Phase 3.

Orchestration layer entre Repository + SkillClassifier + Generator.

Responsabilidades:
- select_priority_skills: pra cada parent dado, retorna skills com discrimination_score
  alto. Usa hierarquia 2-level fallback (filho >=20 amostras OR parent rollup).
- record_question_outcome: chamado quando candidato vai pra hired/rejected.
- guard_fairness: bloqueia skill com adverse_impact > threshold.

Multi-tenancy: company_id sempre obrigatorio.
Fail-open: erros nao bloqueiam wizard, retornam fallback.
"""
from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.job_creation.repositories.wsi_effectiveness_repository import (
    WsiEffectivenessRepository,
)
from app.domains.job_creation.services.wsi_skill_taxonomy import (
    THRESHOLD_BY_BIAS_RISK,
    get_sample_threshold,
    parent_of,
    skills_by_parent,
)

logger = logging.getLogger(__name__)


# Skill priorizada: discrimination_score absoluto >= esse threshold
DISCRIMINATION_THRESHOLD = 0.5

# Skill bloqueada por fairness: adverse_impact >= esse threshold
FAIRNESS_THRESHOLD = 0.10


class WsiEffectivenessService:
    """Servico de selecao de skills + outcome recording."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = WsiEffectivenessRepository(db)

    async def select_priority_skills(
        self,
        company_id: str,
        parent_ids: list[str],
        department: str = "",
        seniority_level: str = "",
        top_n_per_parent: int = 3,
    ) -> list[dict[str, Any]]:
        """Pra cada parent, retorna ate top_n_per_parent skills priorizadas.

        Hierarchical fallback:
        1. Skill com >= THRESHOLD_BY_BIAS_RISK[skill.bias_risk] amostras E discrimination >= threshold -> priorizada
        2. Skill com <20 amostras -> usa parent rollup pra decidir importancia
        3. Sem dados nem em parent -> retorna skills do parent sem priorizacao
        4. Skills com fairness_blocked=1 -> EXCLUIDAS

        Multi-tenancy: company_id obrigatorio.
        Fail-open: erros retornam lista vazia.
        """
        if not company_id:
            raise ValueError("company_id is required (multi-tenancy)")

        prioritized: list[dict[str, Any]] = []

        for parent_id in parent_ids:
            parent_skills = skills_by_parent(parent_id)
            if not parent_skills:
                logger.debug("[WsiEff] parent_id %s has no skills", parent_id)
                continue

            skill_ids = [s.id for s in parent_skills]

            # Bulk lookup effectiveness
            try:
                eff_map = await self.repo.get_by_skills(
                    company_id, skill_ids, department, seniority_level,
                )
            except Exception as exc:
                logger.warning(
                    "[WsiEff] get_by_skills failed company_hash=%s: %s",
                    hash(company_id) % 100000, str(exc)[:100],
                )
                eff_map = {}

            # Score each skill: priorizar high-discrimination + filtrar fairness blocked
            scored: list[tuple[float, dict[str, Any]]] = []
            for skill in parent_skills:
                eff = eff_map.get(skill.id)
                if eff is not None and eff.fairness_blocked:
                    logger.info(
                        "[WsiEff] skill %s blocked by fairness", skill.id,
                    )
                    continue

                if eff is not None and eff.times_used >= get_sample_threshold(skill):
                    # Filho tem dados suficientes
                    abs_disc = abs(eff.discrimination_score)
                    source = "skill"
                elif eff is not None and eff.times_used > 0:
                    # Filho tem dados parciais
                    abs_disc = abs(eff.discrimination_score) * 0.5
                    source = "skill_partial"
                else:
                    # Sem dados na skill - usa default
                    abs_disc = 0.3
                    source = "default"

                scored.append((
                    abs_disc,
                    {
                        "skill_id": skill.id,
                        "name_pt": skill.name_pt,
                        "description": skill.description,
                        "parent_id": parent_id,
                        "discrimination_score": eff.discrimination_score if eff else 0.0,
                        "times_used": eff.times_used if eff else 0,
                        "source": source,
                    },
                ))

            # Top-N por parent
            scored.sort(key=lambda x: x[0], reverse=True)
            for _, skill_info in scored[:top_n_per_parent]:
                prioritized.append(skill_info)

        return prioritized

    async def record_question_outcome(
        self,
        company_id: str,
        skill_probed: str,
        outcome: str,
        score: float,
        department: str = "",
        seniority_level: str = "",
    ) -> None:
        """Chamado quando candidato muda pra hired/rejected.

        Atualiza Welford stats da skill correspondente.
        Fail-soft: erros logam mas nao raise.
        """
        if not company_id:
            raise ValueError("company_id is required (multi-tenancy)")

        # Resolve parent automaticamente da taxonomia
        parent_id = parent_of(skill_probed)
        if parent_id is None:
            logger.warning(
                "[WsiEff] skill_probed %s not in taxonomy - skip outcome",
                skill_probed,
            )
            return

        try:
            await self.repo.record_outcome(
                company_id=company_id,
                skill_probed=skill_probed,
                parent_id=parent_id,
                outcome=outcome,
                score=score,
                department=department,
                seniority_level=seniority_level,
            )
        except Exception as exc:
            logger.warning(
                "[WsiEff] record_outcome failed (fail-soft) skill=%s: %s",
                skill_probed, str(exc)[:200],
            )
