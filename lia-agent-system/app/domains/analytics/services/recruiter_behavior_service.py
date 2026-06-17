"""
Recruiter Behavior Service — Z7-01.

Rastreia e agrega padrões comportamentais de recrutadores para personalizar
a experiência LIA e melhorar sugestões do agente.

Sinais coletados:
  - active_hours_distribution: horas do dia em que o recrutador é mais ativo
  - preferred_sourcing_channels: canais favoritos (linkedin, whatsapp, email)
  - avg_response_time_hours: tempo médio para responder candidatos
  - stage_conversion_rates: taxa de aprovação em cada estágio do pipeline
  - typical_batch_size: tamanho médio de revisões em lote
  - rejection_reasons_top: principais razões de rejeição identificadas
  - communication_style: style derivado de frequência de canais usados

Armazenamento: Redis (TTL 24h) + snapshot opcional em RecruiterProfile.behavior_data
Falha graciosamente em todas as operações.
"""
from __future__ import annotations
# ADR-001-EXEMPT: recruiter behavior analytics. Multi-aggregation queries with
# tenant scope passed explicitly as company_id parameter (caller responsibility).
# Repo-layer ContextVar gate not applicable to admin/internal-tools call paths.

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)

_BEHAVIOR_TTL_SECONDS = 86_400  # 24 horas
_BEHAVIOR_KEY_PREFIX = "recruiter_behavior"


def _behavior_key(recruiter_id: str, company_id: str) -> str:
    return f"{_BEHAVIOR_KEY_PREFIX}:{company_id}:{recruiter_id}"


# ── Dataclass de perfil comportamental ────────────────────────────────────────

@dataclass
class RecruiterBehaviorProfile:
    """Perfil de comportamento de um recrutador, derivado de sinais de uso."""

    recruiter_id: str
    company_id: str
    computed_at: str = ""

    # Padrão de horas ativas (hora→contagem de ações)
    active_hours_distribution: dict[str, int] = field(default_factory=dict)

    # Canais de sourcing preferidos (canal→frequência)
    preferred_sourcing_channels: dict[str, int] = field(default_factory=dict)

    # Métricas de velocidade
    avg_response_time_hours: float | None = None   # tempo médio candidato→resposta
    avg_hiring_velocity_days: float | None = None  # criação da vaga→primeira contratação

    # Taxas de conversão por estágio
    stage_conversion_rates: dict[str, float] = field(default_factory=dict)

    # Preferências de comunicação
    communication_style: str = "balanced"  # "high_volume" | "selective" | "balanced"
    typical_batch_size: int | None = None

    # Top razões de rejeição observadas
    rejection_reasons_top: list[str] = field(default_factory=list)

    # Score de risco de viés (derivado de bias_audit, se disponível)
    bias_risk_score: float | None = None

    # Nível de experiência inferido (de RecruiterProfile se disponível)
    experience_level: str = "intermediate"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RecruiterBehaviorProfile:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


# ── Service ───────────────────────────────────────────────────────────────────

class RecruiterBehaviorService:
    """
    Serviço que computa e armazena perfis comportamentais de recrutadores.

    Uso:
        profile = await recruiter_behavior_service.get_or_compute(
            recruiter_id="user-123",
            company_id="company-456",
            db=db,
        )
    """

    async def get_or_compute(
        self,
        recruiter_id: str,
        company_id: str,
        db=None,
        force_refresh: bool = False,
    ) -> RecruiterBehaviorProfile:
        """Retorna o perfil do cache Redis ou computa a partir do DB."""
        if not force_refresh:
            cached = await self._get_cached(recruiter_id, company_id)
            if cached is not None:
                return cached

        return await self._compute_and_cache(recruiter_id, company_id, db)

    async def record_action(
        self,
        recruiter_id: str,
        company_id: str,
        action_type: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Registra um sinal de comportamento (fail-safe).

        action_type: "sourcing_channel_used", "candidate_responded",
                     "stage_approved", "stage_rejected", "batch_review"
        """
        try:
            redis = await self._get_redis()
            if redis is None:
                return
            signal = {
                "action_type": action_type,
                "ts": datetime.now(UTC).isoformat(),
                "metadata": metadata or {},
            }
            signals_key = f"{_BEHAVIOR_KEY_PREFIX}:signals:{company_id}:{recruiter_id}"
            async with redis:
                await redis.lpush(signals_key, json.dumps(signal))
                await redis.ltrim(signals_key, 0, 499)  # mantém últimos 500 sinais
                await redis.expire(signals_key, _BEHAVIOR_TTL_SECONDS * 7)  # 7 dias
        except Exception as exc:
            logger.debug("[RecruiterBehavior] record_action falhou (fail-safe): %s", exc)

    async def invalidate(self, recruiter_id: str, company_id: str) -> None:
        """Remove o cache do perfil para forçar re-computação."""
        try:
            redis = await self._get_redis()
            if redis is None:
                return
            async with redis:
                await redis.delete(_behavior_key(recruiter_id, company_id))
        except Exception as exc:
            logger.debug("[RecruiterBehavior] invalidate falhou: %s", exc)

    # ── internals ──────────────────────────────────────────────────────────────

    async def _get_cached(
        self, recruiter_id: str, company_id: str
    ) -> RecruiterBehaviorProfile | None:
        try:
            redis = await self._get_redis()
            if redis is None:
                return None
            async with redis:
                raw = await redis.get(_behavior_key(recruiter_id, company_id))
            if raw is None:
                return None
            data = json.loads(raw)
            return RecruiterBehaviorProfile.from_dict(data)
        except Exception as exc:
            logger.debug("[RecruiterBehavior] cache miss: %s", exc)
            return None

    async def _compute_and_cache(
        self,
        recruiter_id: str,
        company_id: str,
        db,
    ) -> RecruiterBehaviorProfile:
        """Computa o perfil a partir de múltiplas fontes (fail-safe por fonte)."""
        profile = RecruiterBehaviorProfile(
            recruiter_id=recruiter_id,
            company_id=company_id,
            computed_at=datetime.now(UTC).isoformat(),
        )

        # 1. Hora de atividade a partir dos sinais Redis
        await self._enrich_active_hours(profile)

        # 2. Canais de sourcing e estilo de comunicação
        await self._enrich_sourcing_channels(profile)

        # 3. Velocidade e conversão (a partir do DB, se disponível)
        if db is not None:
            await self._enrich_from_db(profile, db)

        # 4. Experience level do RecruiterProfile (a partir do DB)
        if db is not None:
            await self._enrich_experience_level(profile, db)

        # Cache
        await self._store_cache(profile)

        logger.debug(
            "[RecruiterBehavior] perfil computado recruiter=%s company=%s style=%s",
            recruiter_id, company_id, profile.communication_style,
        )
        return profile

    async def _enrich_active_hours(self, profile: RecruiterBehaviorProfile) -> None:
        """Agrega horas de atividade dos sinais Redis."""
        try:
            redis = await self._get_redis()
            if redis is None:
                return
            signals_key = (
                f"{_BEHAVIOR_KEY_PREFIX}:signals:{profile.company_id}:{profile.recruiter_id}"
            )
            async with redis:
                raw_signals = await redis.lrange(signals_key, 0, 499)
            hour_counts: dict[str, int] = {}
            for raw in raw_signals:
                try:
                    sig = json.loads(raw)
                    ts_str = sig.get("ts", "")
                    if ts_str:
                        hour = str(datetime.fromisoformat(ts_str).hour)
                        hour_counts[hour] = hour_counts.get(hour, 0) + 1
                except Exception:
                    continue
            profile.active_hours_distribution = hour_counts
        except Exception as exc:
            logger.debug("[RecruiterBehavior] _enrich_active_hours falhou: %s", exc)

    async def _enrich_sourcing_channels(self, profile: RecruiterBehaviorProfile) -> None:
        """Agrega canais de sourcing dos sinais Redis."""
        try:
            redis = await self._get_redis()
            if redis is None:
                return
            signals_key = (
                f"{_BEHAVIOR_KEY_PREFIX}:signals:{profile.company_id}:{profile.recruiter_id}"
            )
            async with redis:
                raw_signals = await redis.lrange(signals_key, 0, 499)
            channel_counts: dict[str, int] = {}
            for raw in raw_signals:
                try:
                    sig = json.loads(raw)
                    if sig.get("action_type") == "sourcing_channel_used":
                        channel = sig.get("metadata", {}).get("channel", "unknown")
                        channel_counts[channel] = channel_counts.get(channel, 0) + 1
                except Exception:
                    continue
            profile.preferred_sourcing_channels = channel_counts
            # Derivar communication_style
            total = sum(channel_counts.values())
            if total >= 20:
                profile.communication_style = "high_volume"
            elif total >= 5:
                profile.communication_style = "balanced"
            else:
                profile.communication_style = "selective"
        except Exception as exc:
            logger.debug("[RecruiterBehavior] _enrich_sourcing_channels falhou: %s", exc)

    async def _enrich_from_db(self, profile: RecruiterBehaviorProfile, db) -> None:
        """Enriquece com dados de conversão e velocidade do DB."""
        try:
            from sqlalchemy import text as sa_text

            # Stage conversion rates via CandidateStageHistory
            sql = sa_text("""
                SELECT stage_to, COUNT(*) AS cnt,
                       AVG(CASE WHEN stage_to IN ('hired','approved') THEN 1.0 ELSE 0.0 END) AS conv
                FROM candidate_stage_history
                WHERE changed_by = :recruiter_id
                  AND company_id = :company_id
                  AND created_at >= NOW() - INTERVAL '90 days'
                GROUP BY stage_to
                LIMIT 20
            """)
            result = await db.execute(
                sql,
                {"recruiter_id": profile.recruiter_id, "company_id": profile.company_id},
            )
            rows = result.fetchall()
            if rows:
                profile.stage_conversion_rates = {
                    r[0]: round(float(r[2]), 3) for r in rows if r[0]
                }
        except Exception as exc:
            logger.debug("[RecruiterBehavior] _enrich_from_db falhou (gracioso): %s", exc)

    async def _enrich_experience_level(
        self, profile: RecruiterBehaviorProfile, db
    ) -> None:
        """Pega o experience_level do RecruiterProfile se disponível."""
        try:
            from sqlalchemy import text as sa_text

            sql = sa_text("""
                SELECT experience_level, total_jobs_created
                FROM recruiter_profiles
                WHERE recruiter_id = :recruiter_id
                  AND company_id = :company_id
                LIMIT 1
            """)
            result = await db.execute(
                sql,
                {"recruiter_id": profile.recruiter_id, "company_id": profile.company_id},
            )
            row = result.fetchone()
            if row:
                exp, total_jobs = row
                if exp:
                    profile.experience_level = exp
                if total_jobs:
                    profile.typical_batch_size = max(1, total_jobs // 10)
        except Exception as exc:
            logger.debug("[RecruiterBehavior] _enrich_experience_level falhou: %s", exc)

    async def _store_cache(self, profile: RecruiterBehaviorProfile) -> None:
        try:
            redis = await self._get_redis()
            if redis is None:
                return
            async with redis:
                await redis.set(
                    _behavior_key(profile.recruiter_id, profile.company_id),
                    json.dumps(profile.to_dict()),
                    ex=_BEHAVIOR_TTL_SECONDS,
                )
        except Exception as exc:
            logger.debug("[RecruiterBehavior] _store_cache falhou: %s", exc)

    async def _get_redis(self):
        from app.core.redis_client import get_redis_connection
        return await get_redis_connection()


# Singleton
recruiter_behavior_service = RecruiterBehaviorService()
