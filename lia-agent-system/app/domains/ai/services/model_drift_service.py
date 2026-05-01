"""
Model Drift Detection Service — screening-compliance §7

Monitora 4 gatilhos de drift comparando janela recente (7 dias) vs baseline (7 dias anteriores):
  1. score_drift:    variação no score médio WSI > 0.5 pontos
  2. approval_drift: variação na taxa de aprovação > 10 p.p.
  3. cost_drift:     variação no custo total > 20%
  4. latency_drift:  variação no P95 de latência > 50%

Referência:
- screening-compliance §7 (Model Drift Detection — 4 triggers)
- wedo-governance Produção Readiness #10 (alertas automáticos)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.ai_consumption import AiConsumption
from lia_models.observability import AIInferenceLog
from lia_models.rubric import RubricEvaluation

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Limites de drift (screening-compliance §7)
# ---------------------------------------------------------------------------
SCORE_DRIFT_THRESHOLD = 0.5       # variação absoluta no score médio
APPROVAL_DRIFT_THRESHOLD = 0.10   # variação percentual na taxa de aprovação (10 p.p.)
COST_DRIFT_THRESHOLD = 0.20       # variação relativa no custo (20%)
LATENCY_DRIFT_THRESHOLD = 0.50    # variação relativa no P95 de latência (50%)

WINDOW_DAYS = 7                   # dias por janela de análise

# Score mínimo para considerar "aprovado" (alinhado ao golden dataset APPROVAL_THRESHOLD)
SCORE_APPROVAL_CUTOFF = 60.0


# ---------------------------------------------------------------------------
# DTOs
# ---------------------------------------------------------------------------

@dataclass
class DriftTrigger:
    """Um gatilho de drift detectado."""
    name: str                         # ex: "score_drift"
    baseline_value: float
    recent_value: float
    delta: float                      # variação absoluta ou relativa
    threshold: float
    triggered: bool
    description: str = ""


@dataclass
class DriftStatus:
    """Resultado completo da análise de drift para uma empresa."""
    company_id: str
    evaluated_at: datetime
    recent_window_start: datetime
    baseline_window_start: datetime
    triggers: list[DriftTrigger] = field(default_factory=list)
    drift_detected: bool = False
    alert_level: str = "ok"          # "ok" | "warning" | "critical"
    sample_size_recent: int = 0
    sample_size_baseline: int = 0


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

class ModelDriftService:
    """
    Detecta drift em 4 dimensões comparando janela recente vs baseline.

    Uso:
        drift_status = await ModelDriftService().evaluate(db, company_id)
    """

    async def evaluate(
        self,
        db: AsyncSession,
        company_id: UUID,
        window_days: int = WINDOW_DAYS,
    ) -> DriftStatus:
        """Avalia drift para uma empresa. Retorna DriftStatus com lista de triggers."""
        now = datetime.utcnow()
        recent_start = now - timedelta(days=window_days)
        baseline_start = now - timedelta(days=2 * window_days)

        status = DriftStatus(
            company_id=str(company_id),
            evaluated_at=now,
            recent_window_start=recent_start,
            baseline_window_start=baseline_start,
        )

        triggers: list[DriftTrigger] = []

        # --- Trigger 1: Score Drift ---
        try:
            t = await self._score_drift(db, company_id, recent_start, baseline_start)
            triggers.append(t)
        except Exception as exc:
            logger.warning("model_drift: score_drift falhou: %s", exc)

        # --- Trigger 2: Approval Rate Drift ---
        try:
            t = await self._approval_drift(db, company_id, recent_start, baseline_start)
            triggers.append(t)
        except Exception as exc:
            logger.warning("model_drift: approval_drift falhou: %s", exc)

        # --- Trigger 3: Cost Drift ---
        try:
            t = await self._cost_drift(db, company_id, recent_start, baseline_start)
            triggers.append(t)
        except Exception as exc:
            logger.warning("model_drift: cost_drift falhou: %s", exc)

        # --- Trigger 4: Latency P95 Drift ---
        try:
            t = await self._latency_drift(db, company_id, recent_start, baseline_start)
            triggers.append(t)
        except Exception as exc:
            logger.warning("model_drift: latency_drift falhou: %s", exc)

        status.triggers = triggers
        triggered = [t for t in triggers if t.triggered]
        status.drift_detected = bool(triggered)

        if len(triggered) >= 2:
            status.alert_level = "critical"
        elif len(triggered) == 1:
            status.alert_level = "warning"
        else:
            status.alert_level = "ok"

        if status.drift_detected:
            logger.warning(
                "model_drift: drift detectado company=%s alert_level=%s triggers=%s",
                company_id,
                status.alert_level,
                [t.name for t in triggered],
            )

        return status

    # -----------------------------------------------------------------------
    # Trigger 1 — Score Drift
    # -----------------------------------------------------------------------

    async def _score_drift(
        self,
        db: AsyncSession,
        company_id: UUID,
        recent_start: datetime,
        baseline_start: datetime,
    ) -> DriftTrigger:
        """
        Compara score médio WSI entre janelas.
        Drift detectado se |recent_avg - baseline_avg| > SCORE_DRIFT_THRESHOLD.
        """
        now = datetime.utcnow()

        # Query scores recentes
        q_recent = await db.execute(
            select(func.avg(RubricEvaluation.score)).where(
                and_(
                    RubricEvaluation.evaluated_at >= recent_start,
                    RubricEvaluation.evaluated_at < now,
                )
            )
        )
        recent_avg = float(q_recent.scalar() or 0.0)

        # Query scores baseline
        q_base = await db.execute(
            select(func.avg(RubricEvaluation.score)).where(
                and_(
                    RubricEvaluation.evaluated_at >= baseline_start,
                    RubricEvaluation.evaluated_at < recent_start,
                )
            )
        )
        base_avg = float(q_base.scalar() or 0.0)

        delta = abs(recent_avg - base_avg)
        triggered = delta > SCORE_DRIFT_THRESHOLD and (recent_avg > 0 or base_avg > 0)

        return DriftTrigger(
            name="score_drift",
            baseline_value=round(base_avg, 3),
            recent_value=round(recent_avg, 3),
            delta=round(delta, 3),
            threshold=SCORE_DRIFT_THRESHOLD,
            triggered=triggered,
            description=f"Score médio WSI: baseline={base_avg:.2f} → recente={recent_avg:.2f} (Δ={delta:.2f})",
        )

    # -----------------------------------------------------------------------
    # Trigger 2 — Approval Rate Drift
    # -----------------------------------------------------------------------

    async def _approval_drift(
        self,
        db: AsyncSession,
        company_id: UUID,
        recent_start: datetime,
        baseline_start: datetime,
    ) -> DriftTrigger:
        """
        Compara taxa de aprovação (score >= cutoff) entre janelas.
        Drift detectado se |recent_rate - baseline_rate| > APPROVAL_DRIFT_THRESHOLD.
        """
        now = datetime.utcnow()

        async def _approval_rate(start: datetime, end: datetime) -> float:
            q_total = await db.execute(
                select(func.count()).where(
                    and_(
                        RubricEvaluation.evaluated_at >= start,
                        RubricEvaluation.evaluated_at < end,
                    )
                )
            )
            total = q_total.scalar() or 0

            if total == 0:
                return 0.0

            q_approved = await db.execute(
                select(func.count()).where(
                    and_(
                        RubricEvaluation.evaluated_at >= start,
                        RubricEvaluation.evaluated_at < end,
                        RubricEvaluation.score >= SCORE_APPROVAL_CUTOFF,
                    )
                )
            )
            approved = q_approved.scalar() or 0
            return approved / total

        recent_rate = await _approval_rate(recent_start, now)
        base_rate = await _approval_rate(baseline_start, recent_start)

        delta = abs(recent_rate - base_rate)
        triggered = delta > APPROVAL_DRIFT_THRESHOLD and (recent_rate > 0 or base_rate > 0)

        return DriftTrigger(
            name="approval_drift",
            baseline_value=round(base_rate, 4),
            recent_value=round(recent_rate, 4),
            delta=round(delta, 4),
            threshold=APPROVAL_DRIFT_THRESHOLD,
            triggered=triggered,
            description=(
                f"Taxa de aprovação: baseline={base_rate:.1%} → recente={recent_rate:.1%} "
                f"(Δ={delta:.1%})"
            ),
        )

    # -----------------------------------------------------------------------
    # Trigger 3 — Cost Drift
    # -----------------------------------------------------------------------

    async def _cost_drift(
        self,
        db: AsyncSession,
        company_id: UUID,
        recent_start: datetime,
        baseline_start: datetime,
    ) -> DriftTrigger:
        """
        Compara custo total (cost_cents) entre janelas.
        Drift detectado se variação relativa > COST_DRIFT_THRESHOLD.
        """
        now = datetime.utcnow()

        q_recent = await db.execute(
            select(func.sum(AiConsumption.cost_cents)).where(
                and_(
                    AiConsumption.company_id == company_id,
                    AiConsumption.created_at >= recent_start,
                    AiConsumption.created_at < now,
                )
            )
        )
        recent_cost = float(q_recent.scalar() or 0)

        q_base = await db.execute(
            select(func.sum(AiConsumption.cost_cents)).where(
                and_(
                    AiConsumption.company_id == company_id,
                    AiConsumption.created_at >= baseline_start,
                    AiConsumption.created_at < recent_start,
                )
            )
        )
        base_cost = float(q_base.scalar() or 0)

        if base_cost > 0:
            delta_relative = abs(recent_cost - base_cost) / base_cost
        else:
            delta_relative = 0.0

        triggered = delta_relative > COST_DRIFT_THRESHOLD and base_cost > 0

        return DriftTrigger(
            name="cost_drift",
            baseline_value=round(base_cost, 2),
            recent_value=round(recent_cost, 2),
            delta=round(delta_relative, 4),
            threshold=COST_DRIFT_THRESHOLD,
            triggered=triggered,
            description=(
                f"Custo (cents): baseline={base_cost:.0f} → recente={recent_cost:.0f} "
                f"(Δ_rel={delta_relative:.1%})"
            ),
        )

    # -----------------------------------------------------------------------
    # Trigger 4 — Latency P95 Drift
    # -----------------------------------------------------------------------

    async def _latency_drift(
        self,
        db: AsyncSession,
        company_id: UUID,
        recent_start: datetime,
        baseline_start: datetime,
    ) -> DriftTrigger:
        """
        Compara P95 de latência (AIInferenceLog.latency_ms) entre janelas.
        Drift detectado se variação relativa do P95 > LATENCY_DRIFT_THRESHOLD.
        """
        now = datetime.utcnow()

        async def _p95(start: datetime, end: datetime) -> float:
            q = await db.execute(
                select(AIInferenceLog.latency_ms).where(
                    and_(
                        AIInferenceLog.company_id == company_id,
                        AIInferenceLog.latency_ms.isnot(None),
                        AIInferenceLog.created_at >= start,
                        AIInferenceLog.created_at < end,
                    )
                )
            )
            values = [row[0] for row in q.fetchall() if row[0] is not None]
            if not values:
                return 0.0
            values.sort()
            idx = int(len(values) * 0.95)
            return float(values[min(idx, len(values) - 1)])

        recent_p95 = await _p95(recent_start, now)
        base_p95 = await _p95(baseline_start, recent_start)

        if base_p95 > 0:
            delta_relative = abs(recent_p95 - base_p95) / base_p95
        else:
            delta_relative = 0.0

        triggered = delta_relative > LATENCY_DRIFT_THRESHOLD and base_p95 > 0

        return DriftTrigger(
            name="latency_drift",
            baseline_value=round(base_p95, 1),
            recent_value=round(recent_p95, 1),
            delta=round(delta_relative, 4),
            threshold=LATENCY_DRIFT_THRESHOLD,
            triggered=triggered,
            description=(
                f"Latência P95 (ms): baseline={base_p95:.0f} → recente={recent_p95:.0f} "
                f"(Δ_rel={delta_relative:.1%})"
            ),
        )


    async def check_drift_trigger(
        self,
        company_id: str,
        trigger_type: str = "learning_feedback",
    ) -> None:
        """
        Trigger assíncrono de verificação de drift a partir do LearningLoop.

        Fail-safe: cria sessão própria e não propaga exceções.
        Usado quando feedbacks negativos acumulados sugerem possível drift.

        Args:
            company_id: Tenant ID para escopo da avaliação.
            trigger_type: Tipo do gatilho (ex: "learning_feedback").
        """
        try:
            import uuid as _uuid

            from app.core.database import AsyncSessionLocal

            async with AsyncSessionLocal() as db:
                try:
                    _company_uuid = _uuid.UUID(company_id)
                except (ValueError, AttributeError):
                    logger.warning(
                        "[ModelDriftService] check_drift_trigger: invalid company_id=%s", company_id
                    )
                    return

                status = await self.evaluate(db, _company_uuid)
                logger.info(
                    "[ModelDriftService] check_drift_trigger: company=%s trigger=%s "
                    "drift_detected=%s alert_level=%s",
                    company_id, trigger_type, status.drift_detected, status.alert_level,
                )
        except Exception as exc:
            logger.debug("[ModelDriftService] check_drift_trigger failed (fail-safe): %s", exc)


# Instância de módulo — singleton leve (stateless)
model_drift_service = ModelDriftService()
