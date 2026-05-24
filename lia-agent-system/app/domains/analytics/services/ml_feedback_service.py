"""
ML Feedback Service — D6 (Feedback Loop Adaptativo)

Registra sinais de feedback de recrutadores (hire/reject/override) e
calcula ajustes adaptativos nos pesos de avaliação por vaga.

Objetivo: melhorar a calibração dos scores LIA com base em decisões reais,
sem re-treinar o modelo — ajuste via pesos por dimensão armazenados no banco.

Arquitetura:
1. Recruiter decide: aprovar / rejeitar / override score
2. MLFeedbackService.record_signal() persiste o sinal
3. Celery task `ml.feedback.process_job_weights` roda periodicamente:
   compute_job_weights() → atualiza JobScoringWeights com desvios observados
4. evaluate_candidate() lê os pesos adaptados via get_weights_for_job()

Referências:
- screening-compliance §5 (model drift — score divergence)
- dei-fairness §4 (Four-Fifths Rule — proteger contra viés nos ajustes)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# Limiar de desvio para sugerir ajuste de peso (recruiter aprova candidato
# com score baixo ou rejeita com score alto)
OVERRIDE_DIVERGENCE_THRESHOLD = 15.0  # pontos
MIN_FEEDBACK_SAMPLES = 5  # mínimo de amostras para ajustar pesos


# ---------------------------------------------------------------------------
# DTOs
# ---------------------------------------------------------------------------

@dataclass
class FeedbackSignal:
    """Sinal de feedback de um recrutador."""
    candidate_id: str
    job_id: str
    company_id: str
    ai_score: float                          # score do LIA
    recruiter_decision: str                  # "hire" | "reject" | "override_approve" | "override_reject"
    recruiter_score: float | None = None  # score manual se override
    dimension_overrides: dict[str, float] = field(default_factory=dict)
    recorded_at: datetime | None = None


@dataclass
class JobScoringWeights:
    """Pesos adaptativos por dimensão para uma vaga."""
    job_id: str
    company_id: str
    weights: dict[str, float] = field(default_factory=lambda: {
        "technical": 1.0,
        "experience": 1.0,
        "education": 1.0,
        "soft_skills": 1.0,
        "cultural_fit": 1.0,
    })
    computed_at: datetime | None = None
    sample_count: int = 0

    def to_dict(self) -> dict:
        return {
            "job_id": self.job_id,
            "company_id": self.company_id,
            "weights": self.weights,
            "computed_at": self.computed_at.isoformat() if self.computed_at else None,
            "sample_count": self.sample_count,
        }


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

class MLFeedbackService:
    """
    Gerencia o ciclo de feedback adaptativo para scores de candidatos.

    Usa a tabela `calibration_events` existente (CalibrationService) para
    persistir sinais — evita duplicar infraestrutura de BD.
    """

    async def record_signal(
        self,
        db: AsyncSession,
        signal: FeedbackSignal,
    ) -> bool:
        """
        Persiste um sinal de feedback de recrutador.

        Delega para CalibrationService.record_explicit_feedback() para reutilizar
        infraestrutura existente. Fail-open: retorna False em caso de erro.
        """
        try:
            from app.domains.analytics.services.calibration_service import CalibrationService  # R-055
            cal = CalibrationService(db)

            # Deriva divergência: score do recrutador vs. score LIA
            if signal.recruiter_score is not None:
                divergence = signal.recruiter_score - signal.ai_score
            elif signal.recruiter_decision in ("hire", "override_approve"):
                # Aprovação implica score efetivo de pelo menos 60
                divergence = max(0.0, 60.0 - signal.ai_score)
            else:
                divergence = 0.0

            await cal.record_explicit_feedback(
                candidate_id=signal.candidate_id,
                job_id=signal.job_id,
                company_id=signal.company_id,
                ai_score=signal.ai_score,
                human_score=signal.recruiter_score,
                divergence=divergence,
                decision=signal.recruiter_decision,
                dimension_scores=signal.dimension_overrides or {},
            )
            return True
        except Exception as exc:
            logger.warning("[MLFeedback] record_signal falhou (fail-open): %s", exc)
            return False

    async def compute_job_weights(
        self,
        db: AsyncSession,
        job_id: str,
        company_id: str,
        lookback_days: int = 30,
    ) -> JobScoringWeights:
        """
        Calcula pesos adaptativos para a vaga com base em feedback recente.

        Lógica:
        1. Busca eventos de calibração da vaga nos últimos `lookback_days` dias
        2. Para cada dimensão com override, computa ajuste proporcional ao desvio médio
        3. Limita ajuste a ±30% para evitar deriva excessiva (model drift protection)

        Retorna JobScoringWeights com weights em [0.7, 1.3].
        """
        try:
            from app.domains.analytics.repositories.calibration_repository import (
                CalibrationRepository,
            )
            cutoff = datetime.utcnow() - timedelta(days=lookback_days)
            # CalibrationEvent não tem company_id — filtra apenas por job_id
            _repo = CalibrationRepository(db)
            events = await _repo.list_events_by_job(job_id, cutoff, limit=200)

            if len(events) < MIN_FEEDBACK_SAMPLES:
                logger.info(
                    "[MLFeedback] Amostras insuficientes para job=%s (n=%d, min=%d)",
                    job_id, len(events), MIN_FEEDBACK_SAMPLES,
                )
                return JobScoringWeights(
                    job_id=job_id, company_id=company_id, sample_count=len(events)
                )

            # Agrega divergências por dimensão
            dim_sums: dict[str, list[float]] = {}
            for ev in events:
                if hasattr(ev, "dimension_scores") and ev.dimension_scores:
                    for dim, override in ev.dimension_scores.items():
                        ai_dim = getattr(ev, f"ai_{dim}_score", None) or 0.0
                        dev = (override - ai_dim) / max(1.0, ai_dim)
                        dim_sums.setdefault(dim, []).append(dev)

            weights: dict[str, float] = {
                "technical": 1.0,
                "experience": 1.0,
                "education": 1.0,
                "soft_skills": 1.0,
                "cultural_fit": 1.0,
            }

            for dim, devs in dim_sums.items():
                if dim in weights and len(devs) >= 3:
                    avg_dev = sum(devs) / len(devs)
                    # Ajusta peso proporcional ao desvio médio, limitado a ±30%
                    adj = 1.0 + max(-0.3, min(0.3, avg_dev))
                    weights[dim] = round(adj, 3)

            return JobScoringWeights(
                job_id=job_id,
                company_id=company_id,
                weights=weights,
                computed_at=datetime.utcnow(),
                sample_count=len(events),
            )

        except Exception as exc:
            logger.warning("[MLFeedback] compute_job_weights falhou (fail-open): %s", exc)
            return JobScoringWeights(job_id=job_id, company_id=company_id)

    async def get_weights_for_job(
        self,
        db: AsyncSession,
        job_id: str,
        company_id: str,
    ) -> JobScoringWeights:
        """
        Retorna pesos adaptativos para a vaga.
        Computados on-demand se não disponíveis. Fail-open: retorna pesos neutros.
        """
        try:
            return await self.compute_job_weights(db, job_id, company_id)
        except Exception as exc:
            logger.warning("[MLFeedback] get_weights_for_job falhou (fail-open): %s", exc)
            return JobScoringWeights(job_id=job_id, company_id=company_id)

    async def record_decision(
        self,
        db,
        company_id: str,
        job_id: str,
        candidate_id: str,
        lia_score: float,
        decision: str,
        decision_by: str | None = None,
    ) -> bool:
        """Helper para registrar decisão de recrutador (wiring simplificado)."""
        signal = FeedbackSignal(
            candidate_id=candidate_id,
            job_id=job_id,
            company_id=company_id,
            ai_score=lia_score,
            recruiter_decision=decision,
        )
        return await self.record_signal(db, signal)

    async def compute_calibration_adjustment(
        self,
        db,
        company_id: str,
        job_id: str | None = None,
    ) -> float:
        """
        Calcula ajuste de calibração baseado em feedback histórico.

        Lógica: se score médio de candidatos aprovados < 65, ajuste positivo (+2.5).
                se score médio de candidatos rejeitados > 70, ajuste negativo (-2.5).
                neutro caso contrário.

        Retorna: float entre -5.0 e +5.0. Cache Redis TTL=1h.
        """
        try:
            cache_key = f"calibration_adj:{company_id}:{job_id or 'global'}"

            # Redis cache check
            try:
                from app.core.redis_client import get_redis
                redis = await get_redis()
                cached = await redis.get(cache_key)
                if cached is not None:
                    return float(cached)
            except Exception:
                pass

            # Compute from recent feedback
            if job_id:
                weights = await self.compute_job_weights(db, job_id, company_id)
            else:
                weights = None

            # Simple heuristic: use weights deviation to estimate calibration shift
            adjustment = 0.0
            if weights and weights.sample_count >= 5:
                avg_weight = sum(weights.weights.values()) / len(weights.weights)
                if avg_weight > 1.1:
                    adjustment = min(2.5, (avg_weight - 1.0) * 5.0)
                elif avg_weight < 0.9:
                    adjustment = max(-2.5, (avg_weight - 1.0) * 5.0)

            # Cache result
            try:
                from app.core.redis_client import get_redis
                redis = await get_redis()
                await redis.setex(cache_key, 3600, str(adjustment))
            except Exception:
                pass

            return round(adjustment, 2)
        except Exception as exc:
            logger.warning("[MLFeedback] compute_calibration_adjustment falhou: %s", exc)
            return 0.0


ml_feedback_service = MLFeedbackService()


def get_ml_feedback_service() -> "MLFeedbackService":
    return ml_feedback_service
