"""
Token Budget Service — Rate limiting de LLM por tenant (André R6/P2).

Budget diário por plano, verificado via Redis antes de cada chamada LLM.
Isola consumo entre tenants — um tenant não bloqueia outro.

Planos:
  starter    → 10.000 tokens/dia
  pro        → 100.000 tokens/dia
  business   → 500.000 tokens/dia
  enterprise → ilimitado (-1)

Limites por request individual (Fase 3):
  starter    → 2.000 tokens/request
  pro        → 10.000 tokens/request
  business   → 25.000 tokens/request
  enterprise → 50.000 tokens/request

Fluxo:
  1. check_budget(company_id, plan_code) → antes de chamar LLM
  2. check_request_budget(...) → verifica ceiling por request individual
  3. track_llm_usage_start(...) → marca inicio da chamada (R-002, observabilidade)
  4. increment_usage(company_id, tokens_used) → após chamada LLM
  5. get_budget_status(company_id, plan_code) → para dashboard admin

Task #1355 — in-memory cache (TTL 60s) para plan_code e contador diário.
PING movido para a primeira conexão ou após ConnectionError, não a cada
invocação de _get_redis(). Isso elimina a maioria dos GETs repetidos dentro
do mesmo turno de chat.
"""

import logging
import os
import time
from datetime import UTC, datetime

logger = logging.getLogger(__name__)


def track_llm_usage_start(
    company_id: str | None,
    *,
    model: str | None = None,
    domain: str | None = None,
    operation: str | None = None,
) -> dict[str, str]:
    """R-002: Marca o inicio de uma chamada LLM antes do .complete() / .invoke().

    Helper canonical para todos os callers de get_provider_for_tenant().
    Emite log estruturado (Grafana/Kibana picks up) e retorna metadata de
    correlacao para uso opcional pelo caller (ex: increment_usage depois).

    Sprint 1 Quick Wins (REMEDIATION_BRIEF Wave 0) — card R-002 / achado F-205.
    Pattern de chamada (canonical):

        from app.domains.credits.services.token_budget_service import track_llm_usage_start
        track_llm_usage_start(company_id, model="claude-3-5-sonnet", domain="wsi.report")
        container = get_provider_for_tenant()
        result = await container.generate_with_fallback(...)

    Args:
        company_id: tenant id (obrigatorio em prod; aceita None apenas em
            paths sintéticos como skills_ontology singleton).
        model: nome do modelo invocado (informativo).
        domain: dominio funcional (ex: "wsi.report", "candidate_search.archetype").
        operation: descritor curto da operacao (ex: "embed_skills", "cbi_questions").

    Returns:
        Dict com {tenant_id, model, domain, operation, started_at} para
        correlacao opcional pelo caller.

    Notes:
        - NAO bloqueia (sem raise). Budget enforcement vive em
          check_request_budget_before_llm().
        - Log payload otimizado para parsing por LLM-as-judge / observability.
        - Hashimoto: nunca mais chamada LLM sem log de inicio (sensor de spend).
    """
    started_at = datetime.now(UTC).isoformat()
    payload = {
        "tenant_id": company_id or "unknown",
        "model": model or "unknown",
        "domain": domain or "unknown",
        "operation": operation or "unknown",
        "started_at": started_at,
    }
    logger.info(
        "[TokenBudget][R-002] llm.call.start tenant_id=%s model=%s domain=%s operation=%s started_at=%s",
        payload["tenant_id"],
        payload["model"],
        payload["domain"],
        payload["operation"],
        payload["started_at"],
    )
    return payload


class RequestBudgetExceededError(Exception):
    """Raised when a single request exceeds the per-request token ceiling."""

    def __init__(
        self,
        estimated_tokens: int,
        ceiling: int,
        plan_code: str | None = None,
        agent_type: str | None = None,
        company_id: str | None = None,
    ) -> None:
        self.estimated_tokens = estimated_tokens
        self.ceiling = ceiling
        self.plan_code = plan_code
        self.agent_type = agent_type
        self.company_id = company_id
        super().__init__(
            f"Request excede ceiling de tokens: "
            f"{estimated_tokens:,} estimados > {ceiling:,} permitidos "
            f"(plan={plan_code}, agent_type={agent_type})"
        )


# Limites diários por plan_code (tokens totais = input + output)
PLAN_DAILY_LIMITS: dict[str, int] = {
    "starter": 10_000,
    "pro": 100_000,
    "business": 500_000,
    "enterprise": -1,  # -1 = ilimitado
    # aliases comuns de plan_code
    "trial": 10_000,
    "free": 5_000,
    "basic": 10_000,
    "standard": 100_000,
    "premium": 500_000,
}

# Fallback quando plan_code não reconhecido
DEFAULT_DAILY_LIMIT = 10_000

PLAN_REQUEST_LIMITS: dict[str, int] = {
    "starter": 2_000,
    "pro": 10_000,
    "business": 25_000,
    "enterprise": 50_000,
    "trial": 2_000,
    "free": 2_000,
    "basic": 2_000,
    "standard": 10_000,
    "premium": 25_000,
}

DEFAULT_REQUEST_LIMIT = 2_000

AGENT_TYPE_REQUEST_OVERRIDES: dict[str, float] = {
    "AutonomousReActAgent": 2.0,
    "DeepAnalysisAgent": 2.0,
    "RAGAgent": 1.5,
    "ReportGeneratorAgent": 2.0,
    "ScreeningAgent": 1.5,
    # F11 Bug B (2026-05-24): candidate profile analysis (Pontos-chave/Análise
    # Detalhada/Resumo modal). System prompt + candidate data + LLM expected
    # output excede ceiling base — observado 5,913 tokens com candidate completo
    # + 8 skills + summary. Aumentado para 3.5x (7K ceiling) com margem.
    "ProfileAnalysisAgent": 3.5,
    # F11 Phase 5 (2026-05-24): bulk overrides para endpoints user-facing
    # que default 2K era cap muito baixo (auditoria sensor
    # check_llm_calls_agent_type detectou 27 sites).
    "EmailTemplateAgent": 3.0,
    "InterviewAgent": 3.0,
    "ArchetypeGenerationAgent": 3.0,
    "WSIReportAgent": 3.5,
    "ExperienceHighlightAgent": 2.5,
    # Internal services (F11 Phase 6, 2026-05-24)
    "InternalLLMAgent": 3.5,
    "WSIAgent": 3.5,
    "JobClassificationAgent": 2.5,
    "SearchAnalyticsAgent": 2.5,
    "JobQualificationAgent": 2.5,
    "JobTemplateAgent": 3.0,
    "WSIQuestionAdjusterAgent": 3.0,
    "InterviewSchedulingAgent": 2.5,
    "StageTransitionAgent": 3.0,
    "RecruiterAssistantAgent": 3.5,
    "KanbanAssistantAgent": 3.0,
    "LLMServiceAgent": 3.5,
    "SemanticSearchAgent": 2.5,
    "VoiceCompositeAgent": 3.0,
    "LLMClientAgent": 3.0,
    "AnalysisServiceAgent": 3.5,
    "CompanyBenefitsAgent": 2.5,
}

# TTL da chave Redis: 25h para cobrir edge case de meia-noite
_REDIS_TTL = 25 * 3600

# ---------------------------------------------------------------------------
# Task #1355 — In-memory caches (per-process, not shared across workers)
# ---------------------------------------------------------------------------

# Budget cache: company_id → (used_count, expires_at_monotonic)
_BUDGET_CACHE_TTL_S: float = 60.0
_budget_cache: dict[str, tuple[int, float]] = {}

# Plan cache: company_id → (plan_code, expires_at_monotonic)
_PLAN_MEM_CACHE_TTL_S: float = 300.0  # 5 min — plan changes are rare
_plan_mem_cache: dict[str, tuple[str | None, float]] = {}

# Degradation alert: emit at most once per 5 min per process
_DEGRADATION_ALERT_COOLDOWN_S = 300.0
_token_budget_degradation_alerted_at: float = 0.0


def _emit_token_budget_degradation_alert(reason: str) -> None:
    """CRITICAL log + Sentry on first degradation, rate-limited to 1× per 5 min."""
    global _token_budget_degradation_alerted_at
    now = time.monotonic()
    if (now - _token_budget_degradation_alerted_at) < _DEGRADATION_ALERT_COOLDOWN_S:
        return
    _token_budget_degradation_alerted_at = now
    logger.critical(
        "[TokenBudget] Redis degraded — operating without budget verification. "
        "redis_degraded=True reason=%s",
        reason,
    )
    try:
        import sentry_sdk
        sentry_sdk.capture_message(
            f"TokenBudget Redis degraded: {reason}",
            level="fatal",
            extras={"redis_degraded": True, "service": "token_budget"},
        )
    except Exception:
        pass


def _redis_key(company_id: str) -> str:
    """Chave Redis diária por tenant. Formato: token_budget:{company_id}:YYYY-MM-DD"""
    today = datetime.now(UTC).strftime("%Y-%m-%d")
    return f"token_budget:{company_id}:{today}"


# Tenants isentos de budget em desenvolvimento (2026-06-06).
_UNLIMITED_DEV_TENANTS: frozenset = frozenset(
    {"00000000-0000-4000-a000-000000000001"}
)


def _is_unlimited_dev_tenant(company_id: str) -> bool:
    """True se company_id e isento de budget no ambiente de desenvolvimento."""
    if os.environ.get("APP_ENV", "").lower() != "development":
        return False
    return company_id in _UNLIMITED_DEV_TENANTS


def get_plan_limit(plan_code: str | None) -> int:
    """Retorna o limite diário de tokens para o plan_code informado."""
    if not plan_code:
        return DEFAULT_DAILY_LIMIT
    normalized = plan_code.lower().strip()
    return PLAN_DAILY_LIMITS.get(normalized, DEFAULT_DAILY_LIMIT)


def get_request_limit(plan_code: str | None, agent_type: str | None = None) -> int:
    """Retorna o ceiling de tokens por request individual.

    Se ``agent_type`` possuir um override, o limite base é multiplicado
    pelo fator correspondente (ex: AutonomousReActAgent → 2×).
    """
    if not plan_code:
        base = DEFAULT_REQUEST_LIMIT
    else:
        normalized = plan_code.lower().strip()
        base = PLAN_REQUEST_LIMITS.get(normalized, DEFAULT_REQUEST_LIMIT)

    if agent_type:
        multiplier = AGENT_TYPE_REQUEST_OVERRIDES.get(agent_type, 1.0)
        base = int(base * multiplier)

    return base


def estimate_request_tokens(
    prompt: str,
    system: str | None = None,
    expected_output_tokens: int | None = None,
) -> int:
    """Estimativa rápida de tokens de um request (input + output esperado).

    Usa heurística de ~4 caracteres por token (média para texto misto PT/EN).
    ``expected_output_tokens`` pode ser fornecido explicitamente; caso
    contrário assume 25% do input como saída estimada.
    """
    input_chars = len(prompt or "")
    if system:
        input_chars += len(system)

    estimated_input = max(input_chars // 4, 1)

    if expected_output_tokens is not None and expected_output_tokens > 0:
        estimated_output = expected_output_tokens
    else:
        estimated_output = max(estimated_input // 4, 50)

    return estimated_input + estimated_output


def check_request_budget(
    plan_code: str | None,
    estimated_tokens: int,
    *,
    agent_type: str | None = None,
    company_id: str | None = None,
    user_id: str | None = None,
) -> tuple[bool, int, int]:
    """Verifica se um request individual está dentro do ceiling do plano."""
    ceiling = get_request_limit(plan_code, agent_type)
    allowed = estimated_tokens <= ceiling

    if not allowed:
        logger.warning(
            "[TokenBudget] Request bloqueado por ceiling individual: "
            "company_id=%s user_id=%s agent_type=%s "
            "estimated_tokens=%d ceiling=%d plan=%s",
            company_id,
            user_id,
            agent_type,
            estimated_tokens,
            ceiling,
            plan_code,
        )

    return allowed, estimated_tokens, ceiling


def check_request_budget_before_llm(
    prompt: str,
    system: str | None = None,
    *,
    plan_code: str | None = None,
    agent_type: str | None = None,
    company_id: str | None = None,
    user_id: str | None = None,
    expected_output_tokens: int | None = None,
) -> None:
    """
    Guardrail síncrono para ser chamado diretamente antes de qualquer
    chamada LLM (ex: dentro de ProviderContainer.generate_with_fallback).

    When ``plan_code`` is None (plan context unavailable), enforces a
    conservative default ceiling (DEFAULT_REQUEST_LIMIT) to ensure
    cost protection even under degraded conditions.

    Raises:
        RequestBudgetExceededError: se o request exceder o ceiling.
    """
    estimated = estimate_request_tokens(prompt, system, expected_output_tokens)
    allowed, estimated_tokens, ceiling = check_request_budget(
        plan_code,
        estimated,
        agent_type=agent_type,
        company_id=company_id,
        user_id=user_id,
    )

    if not allowed:
        raise RequestBudgetExceededError(
            estimated_tokens=estimated_tokens,
            ceiling=ceiling,
            plan_code=plan_code,
            agent_type=agent_type,
            company_id=company_id,
        )


async def check_budget(
    company_id: str,
    plan_code: str | None,
    *,
    redis_url: str | None = None,
) -> tuple[bool, int, int]:
    """
    Verifica se o tenant ainda tem budget disponível hoje.

    Task #1355 — consulta o cache em memória (TTL 60s) antes de ir ao Redis.
    Isso elimina a maioria dos GETs repetidos dentro do mesmo turno de chat.

    Returns:
        (allowed, used_today, daily_limit)
    """
    limit = get_plan_limit(plan_code)

    if limit == -1:
        return True, 0, -1

    if _is_unlimited_dev_tenant(company_id):
        return True, 0, limit

    # --- Cache em memória (hot path) ---
    now_mono = time.monotonic()
    cache_entry = _budget_cache.get(company_id)
    if cache_entry is not None:
        used_cached, expires_at = cache_entry
        if now_mono < expires_at:
            allowed = used_cached < limit
            if not allowed:
                logger.warning(
                    "[TokenBudget] Budget esgotado (cache): company_id=%s used=%d limit=%d plan=%s",
                    company_id, used_cached, limit, plan_code,
                )
            return allowed, used_cached, limit

    # --- Cache miss → Redis ---
    redis = await _get_redis(redis_url)
    if redis is None:
        _emit_token_budget_degradation_alert("Redis indisponível em check_budget")
        logger.warning(
            "[TokenBudget] Redis indisponível — permitindo chamada sem verificação de budget "
            "(company_id=%s)",
            company_id,
        )
        return True, 0, limit

    try:
        key = _redis_key(company_id)
        used = await redis.get(key)
        used_int = int(used) if used else 0
        # Preencher cache em memória
        _budget_cache[company_id] = (used_int, now_mono + _BUDGET_CACHE_TTL_S)
        allowed = used_int < limit
        if not allowed:
            logger.warning(
                "[TokenBudget] Budget esgotado: company_id=%s used=%d limit=%d plan=%s",
                company_id,
                used_int,
                limit,
                plan_code,
            )
        return allowed, used_int, limit
    except Exception as exc:
        logger.warning("[TokenBudget] Erro ao verificar budget (%s) — permitindo chamada", exc)
        return True, 0, limit
    finally:
        await redis.aclose()


async def increment_usage(
    company_id: str,
    tokens_used: int,
    *,
    redis_url: str | None = None,
) -> int:
    """
    Registra tokens consumidos por tenant no contador diário Redis.

    Task #1355 — após incremento bem-sucedido, invalida o cache em memória
    para que a próxima check_budget leia o valor atualizado do Redis.

    Returns:
        Total acumulado hoje após incremento.
    """
    if tokens_used <= 0:
        return 0

    redis = await _get_redis(redis_url)
    if redis is None:
        logger.warning("[TokenBudget] Redis indisponível — uso não registrado (company_id=%s)", company_id)
        return 0

    try:
        key = _redis_key(company_id)
        new_total = await redis.incrby(key, tokens_used)
        # Garantir TTL (só definir se não existe ainda)
        await redis.expire(key, _REDIS_TTL, xx=False)
        # Invalidar cache em memória para que o próximo check_budget leia o valor atualizado
        _budget_cache.pop(company_id, None)
        logger.debug(
            "[TokenBudget] Incrementado: company_id=%s +%d tokens → total=%d",
            company_id,
            tokens_used,
            new_total,
        )
        # UC-P1-08 + R-022: threshold alerts via budget_alert_service (80% and 100%)
        _ALERT_THRESHOLD = 0.80
        try:
            plan_code = await get_plan_for_company(company_id)
            limit = get_plan_limit(plan_code)
            if limit > 0:
                pct = new_total / limit
                if pct >= 1.0:
                    alert_threshold = 100
                elif pct >= _ALERT_THRESHOLD:
                    alert_threshold = 80
                else:
                    alert_threshold = 0
                if alert_threshold:
                    try:
                        import sentry_sdk as _sentry_sdk
                        _sentry_sdk.capture_message(
                            "token_budget_80pct" if alert_threshold == 80 else "token_budget_100pct",
                            level="warning",
                            extras={
                                "company_id": str(company_id),
                                "threshold_pct": alert_threshold,
                                "used": int(new_total),
                                "limit": int(limit),
                                "plan_code": plan_code,
                            },
                        )
                        import asyncio as _asyncio
                        from app.domains.credits.services.budget_alert_service import send_budget_alert
                        _asyncio.ensure_future(send_budget_alert(
                            company_id=str(company_id),
                            threshold_pct=alert_threshold,
                            used=int(new_total),
                            limit=int(limit),
                            plan_code=plan_code,
                        ))
                    except Exception as _ae:
                        logger.debug("[BudgetAlert] dispatch failed: %s", _ae)
        except Exception as _exc:
            logger.debug("[TOKEN-BUDGET] Could not check threshold: %s", _exc)
        return new_total
    except Exception as exc:
        logger.warning("[TokenBudget] Erro ao incrementar uso (%s)", exc)
        return 0
    finally:
        await redis.aclose()


async def get_budget_status(
    company_id: str,
    plan_code: str | None,
    *,
    redis_url: str | None = None,
) -> dict:
    """
    Retorna status completo do budget para dashboard admin.

    Returns:
        {
          "company_id": str,
          "plan_code": str,
          "daily_limit": int,         # -1 = ilimitado
          "used_today": int,
          "remaining": int,           # -1 = ilimitado
          "usage_pct": float,         # 0.0–100.0 (0.0 se ilimitado)
          "budget_exhausted": bool,
          "reset_at": str,            # ISO UTC meia-noite
        }
    """
    limit = get_plan_limit(plan_code)
    used = 0

    if limit != -1:
        redis = await _get_redis(redis_url)
        if redis is not None:
            try:
                key = _redis_key(company_id)
                val = await redis.get(key)
                used = int(val) if val else 0
            except Exception:
                pass
            finally:
                await redis.aclose()

    remaining = max(0, limit - used) if limit != -1 else -1
    usage_pct = round((used / limit) * 100, 2) if limit > 0 else 0.0
    exhausted = (limit != -1) and (used >= limit)

    # Próximo reset: meia-noite UTC
    now = datetime.now(UTC)
    reset_at = datetime(now.year, now.month, now.day, tzinfo=UTC)
    from datetime import timedelta
    reset_at = reset_at + timedelta(days=1)

    return {
        "company_id": company_id,
        "plan_code": plan_code or "unknown",
        "daily_limit": limit,
        "used_today": used,
        "remaining": remaining,
        "usage_pct": usage_pct,
        "budget_exhausted": exhausted,
        "reset_at": reset_at.isoformat(),
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Task #1355 — singleton Redis connection for token budget (reuse, no PING per call)
_redis_instance = None
_redis_last_ping_ok: float = 0.0
_REDIS_PING_INTERVAL_S = 60.0  # re-verify liveness at most once per minute

# TTL do cache de plan_code por company (1 hora — muda raramente)
_PLAN_CACHE_TTL = 3600


async def get_plan_for_company(company_id: str) -> str | None:
    """
    Retorna o plan_code da assinatura ativa de uma empresa.

    Task #1355 — verifica primeiro o cache em memória (_plan_mem_cache, TTL 5min)
    antes de ir ao Redis ou DB. Isso evita chamadas Redis extras dentro do mesmo
    turno de chat.

    Fluxo:
      1. Cache em memória (TTL 5 min)
      2. Redis cache (TTL 1h, chave: plan_cache:{company_id})
      3. DB query (Subscription.plan_code WHERE company_id AND status=ACTIVE)
      4. Fallback: None (budget service usa DEFAULT_DAILY_LIMIT=10k)
    """
    if _is_unlimited_dev_tenant(company_id):
        return "enterprise"

    # 1. Cache em memória
    now_mono = time.monotonic()
    mem_entry = _plan_mem_cache.get(company_id)
    if mem_entry is not None:
        plan_cached, expires_at = mem_entry
        if now_mono < expires_at:
            logger.debug("[TokenBudget] plan_code mem-cache hit: company_id=%s plan=%s", company_id, plan_cached)
            return plan_cached

    # 2. Redis cache
    redis = await _get_redis()
    if redis is not None:
        try:
            cached = await redis.get(f"plan_cache:{company_id}")
            if cached:
                logger.debug("[TokenBudget] plan_code redis-cache hit: company_id=%s plan=%s", company_id, cached)
                _plan_mem_cache[company_id] = (cached, now_mono + _PLAN_MEM_CACHE_TTL_S)
                await redis.aclose()
                return cached
        except Exception:
            pass
        finally:
            try:
                await redis.aclose()
            except Exception:
                pass

    # 3. DB query
    plan_code = None
    try:
        from lia_config.database import AsyncSessionLocal
        from lia_models.billing import Subscription
        from sqlalchemy import and_, select

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Subscription.plan_code)
                .where(
                    and_(
                        Subscription.company_id == company_id,
                        Subscription.status.in_(["active", "trialing"]),
                    )
                )
                .limit(1)
            )
            row = result.scalar_one_or_none()
            if row:
                plan_code = str(row)
    except Exception as exc:
        logger.debug("[TokenBudget] DB lookup para plan_code falhou (company_id=%s): %s", company_id, exc)

    # 4. Cachear resultado
    _plan_mem_cache[company_id] = (plan_code, now_mono + _PLAN_MEM_CACHE_TTL_S)
    if plan_code:
        try:
            redis2 = await _get_redis()
            if redis2 is not None:
                await redis2.set(f"plan_cache:{company_id}", plan_code, ex=_PLAN_CACHE_TTL)
                await redis2.aclose()
        except Exception:
            pass

    return plan_code


async def _get_redis(redis_url: str | None = None):
    """Cria conexão Redis.

    Task #1355 — PING removido desta função; a conexão usa socket timeouts
    curtos para detecção de falha na primeira operação real. PING era feito
    a cada invocação, gerando uma chamada extra por check_budget/increment_usage
    mesmo quando a conexão já estava saudável.

    Retorna None se indisponível.
    """
    try:
        import redis.asyncio as aioredis
        from lia_config.config import settings as _settings

        url = redis_url or getattr(_settings, "REDIS_URL", "redis://localhost:6379/0")
        client = aioredis.from_url(
            url,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=0.5,
            socket_timeout=0.5,
        )
        return client
    except Exception as exc:
        logger.warning("[TokenBudget] Não foi possível criar cliente Redis: %s", exc)
        return None
