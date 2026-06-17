"""WsiEffectivenessRepository - Sprint B Phase 3.

ADR-001: unico lugar de queries SQL contra wsi_question_effectiveness.
Welford incremental: O(1) updates sem releitura de historico.

Multi-tenancy: company_id obrigatorio (fail-closed).
LGPD: zero PII - so agregados anonimizados.
"""
from __future__ import annotations

import logging
import math
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.wsi_question_effectiveness import WsiQuestionEffectiveness

logger = logging.getLogger(__name__)


# Outcome enum (validado em record_outcome)
ALLOWED_OUTCOMES = frozenset({"hired", "rejected"})

# Threshold pra ativar learning a nivel de skill
MIN_SAMPLES_FOR_DISCRIMINATION = 20


class WsiEffectivenessRepository:
    """Repository com Welford incremental + multi-tenancy fail-closed."""

    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def _require_company_id(company_id: str) -> None:
        if not company_id:
            raise ValueError("company_id is required (multi-tenancy enforcement)")

    @staticmethod
    def _validate_outcome(outcome: str) -> None:
        if outcome not in ALLOWED_OUTCOMES:
            raise ValueError(
                f"outcome must be one of {sorted(ALLOWED_OUTCOMES)}, got {outcome!r}",
            )

    @staticmethod
    def _welford_update(
        old_n: int, old_mean: float, old_m2: float, x: float,
    ) -> tuple[int, float, float]:
        """Welford online algorithm: 1 sample update.

        Returns (new_n, new_mean, new_m2).
        std = sqrt(M2 / (n - 1)) when n > 1.
        """
        new_n = old_n + 1
        delta = x - old_mean
        new_mean = old_mean + delta / new_n
        delta2 = x - new_mean
        new_m2 = old_m2 + delta * delta2
        return new_n, new_mean, new_m2

    @staticmethod
    def _compute_discrimination(
        mean_h: float, m2_h: float, n_h: int,
        mean_r: float, m2_r: float, n_r: int,
    ) -> float:
        """discrimination = (mean_hired - mean_rejected) / std_total.

        Pooled std calculation (Welford). Returns 0.0 se ambos n < 2.
        """
        total_n = n_h + n_r
        if total_n < 2:
            return 0.0
        # Pooled variance (combining 2 Welford running stats)
        # var_pooled = (m2_h + m2_r) / (total_n - 1)
        var_pooled = (m2_h + m2_r) / (total_n - 1)
        if var_pooled <= 0:
            return 0.0
        std_pooled = math.sqrt(var_pooled)
        if std_pooled < 1e-9:
            return 0.0
        return (mean_h - mean_r) / std_pooled

    # -- Read --------------------------------------------------------------

    async def get_or_none(
        self,
        company_id: str,
        skill_probed: str,
        department: str = "",
        seniority_level: str = "",
    ) -> WsiQuestionEffectiveness | None:
        self._require_company_id(company_id)
        stmt = select(WsiQuestionEffectiveness).where(
            and_(
                WsiQuestionEffectiveness.company_id == company_id,
                WsiQuestionEffectiveness.skill_probed == skill_probed,
                WsiQuestionEffectiveness.department == department,
                WsiQuestionEffectiveness.seniority_level == seniority_level,
            ),
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_skills(
        self,
        company_id: str,
        skill_ids: list[str],
        department: str = "",
        seniority_level: str = "",
    ) -> dict[str, WsiQuestionEffectiveness]:
        """Bulk lookup por lista de skills. Returns {skill_id: row}."""
        self._require_company_id(company_id)
        if not skill_ids:
            return {}
        stmt = select(WsiQuestionEffectiveness).where(
            and_(
                WsiQuestionEffectiveness.company_id == company_id,
                WsiQuestionEffectiveness.skill_probed.in_(skill_ids),
                WsiQuestionEffectiveness.department == department,
                WsiQuestionEffectiveness.seniority_level == seniority_level,
            ),
        )
        result = await self.db.execute(stmt)
        rows = result.scalars().all()
        return {r.skill_probed: r for r in rows}

    async def get_parent_aggregate(
        self,
        company_id: str,
        parent_id: str,
        department: str = "",
        seniority_level: str = "",
    ) -> dict[str, Any]:
        """Aggrega stats no nivel de parent (rollup de todas skills filhas).

        Returns dict com totals; pondera media e M2 conforme combine algorithm.
        Used quando filho < MIN_SAMPLES_FOR_DISCRIMINATION (fallback parent).
        """
        self._require_company_id(company_id)
        stmt = select(WsiQuestionEffectiveness).where(
            and_(
                WsiQuestionEffectiveness.company_id == company_id,
                WsiQuestionEffectiveness.parent_id == parent_id,
                WsiQuestionEffectiveness.department == department,
                WsiQuestionEffectiveness.seniority_level == seniority_level,
            ),
        )
        result = await self.db.execute(stmt)
        rows = list(result.scalars().all())
        if not rows:
            return {
                "times_used": 0, "times_hired": 0, "times_rejected": 0,
                "discrimination_score": 0.0,
            }

        total_used = sum(r.times_used for r in rows)
        total_hired = sum(r.times_hired for r in rows)
        total_rejected = sum(r.times_rejected for r in rows)

        # Combine Welford stats (Chan parallel formula)
        # For pooled mean: weighted by n
        if total_hired == 0 and total_rejected == 0:
            return {
                "times_used": total_used,
                "times_hired": 0, "times_rejected": 0,
                "discrimination_score": 0.0,
            }

        # Simplified combination: usa average das medias ponderado por n
        if total_hired > 0:
            mean_h = sum(r.mean_score_hired * r.times_hired for r in rows) / total_hired
            m2_h = sum(r.m2_score_hired for r in rows)  # approx (assume mesma media)
        else:
            mean_h = 0.0
            m2_h = 0.0
        if total_rejected > 0:
            mean_r = sum(r.mean_score_rejected * r.times_rejected for r in rows) / total_rejected
            m2_r = sum(r.m2_score_rejected for r in rows)
        else:
            mean_r = 0.0
            m2_r = 0.0

        disc = self._compute_discrimination(
            mean_h, m2_h, total_hired,
            mean_r, m2_r, total_rejected,
        )

        return {
            "times_used": total_used,
            "times_hired": total_hired,
            "times_rejected": total_rejected,
            "discrimination_score": disc,
        }

    # -- Write --------------------------------------------------------------

    async def record_outcome(
        self,
        company_id: str,
        skill_probed: str,
        parent_id: str,
        outcome: str,
        score: float,
        department: str = "",
        seniority_level: str = "",
    ) -> WsiQuestionEffectiveness:
        """Update Welford stats apos outcome de um candidato.

        Multi-tenancy: company_id obrigatorio.
        Atomicidade: upsert + commit (single transaction).
        """
        self._require_company_id(company_id)
        self._validate_outcome(outcome)
        if not skill_probed or not parent_id:
            raise ValueError("skill_probed and parent_id required")
        if not (0.0 <= score <= 100.0):
            raise ValueError(f"score must be in [0, 100], got {score}")

        row = await self.get_or_none(
            company_id, skill_probed, department, seniority_level,
        )
        if row is None:
            row = WsiQuestionEffectiveness(
                company_id=company_id,
                skill_probed=skill_probed,
                parent_id=parent_id,
                department=department,
                seniority_level=seniority_level,
                times_used=0,
                times_hired=0,
                times_rejected=0,
                mean_score_hired=0.0,
                m2_score_hired=0.0,
                mean_score_rejected=0.0,
                m2_score_rejected=0.0,
                discrimination_score=0.0,
            )
            self.db.add(row)

        # Welford update na branch correta
        if outcome == "hired":
            new_n, new_mean, new_m2 = self._welford_update(
                row.times_hired, row.mean_score_hired, row.m2_score_hired, score,
            )
            row.times_hired = new_n
            row.mean_score_hired = new_mean
            row.m2_score_hired = new_m2
        else:  # rejected
            new_n, new_mean, new_m2 = self._welford_update(
                row.times_rejected, row.mean_score_rejected, row.m2_score_rejected, score,
            )
            row.times_rejected = new_n
            row.mean_score_rejected = new_mean
            row.m2_score_rejected = new_m2

        row.times_used = row.times_hired + row.times_rejected
        row.last_outcome_at = datetime.utcnow()

        # Recompute discrimination_score
        row.discrimination_score = self._compute_discrimination(
            row.mean_score_hired, row.m2_score_hired, row.times_hired,
            row.mean_score_rejected, row.m2_score_rejected, row.times_rejected,
        )

        try:
            await self.db.commit()
        except SQLAlchemyError:
            await self.db.rollback()
            raise

        logger.info(
            "[WsiEffectiveness] outcome=%s skill=%s n=%d disc=%.3f",
            outcome, skill_probed, row.times_used, row.discrimination_score,
        )
        return row
