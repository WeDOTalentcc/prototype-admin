"""
Token Budget Service — Rate limiting de LLM por tenant (André R6/P2).

Budget diário por plano, verificado via Redis antes de cada chamada LLM.
Isola consumo entre tenants — um tenant não bloqueia outro.

Planos:
  starter    → 10.000 tokens/dia
  pro        → 100.000 tokens/dia
  business   → 500.000 tokens/dia
  enterprise → ilimitado (-1)

Fluxo:
  1. check_budget(company_id, plan_code) → antes de chamar LLM
  2. increment_usage(company_id, tokens_used) → após chamada LLM
  3. get_budget_status(company_id, plan_code) → para dashboard admin
"""
import logging
from datetime import datetime, timezone
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# Limites diários por plan_code (tokens totais = input + output)
PLAN_DAILY_LIMITS: dict[str, int] = {
    "starter":    10_000,
    "pro":       100_000,
    "business":  500_000,
    "enterprise": -1,   # -1 = ilimitado
    # aliases comuns de plan_code
    "trial":     10_000,
    "free":       5_000,
    "basic":     10_000,
    "standard": 100_000,
    "premium":  500_000,
}

# Fallback quando plan_code não reconhecido
DEFAULT_DAILY_LIMIT = 10_000

# TTL da chave Redis: 25h para cobrir edge case de meia-noite
_REDIS_TTL = 25 * 3600


def _redis_key(company_id: str) -> str:
    """Chave Redis diária por tenant. Formato: token_budget:{company_id}:YYYY-MM-DD"""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return f"token_budget:{company_id}:{today}"


def get_plan_limit(plan_code: Optional[str]) -> int:
    """Retorna o limite diário de tokens para o plan_code informado."""
    if not plan_code:
        return DEFAULT_DAILY_LIMIT
    normalized = plan_code.lower().strip()
    return PLAN_DAILY_LIMITS.get(normalized, DEFAULT_DAILY_LIMIT)


async def check_budget(
    company_id: str,
    plan_code: Optional[str],
    *,
    redis_url: Optional[str] = None,
) -> Tuple[bool, int, int]:
    """
    Verifica se o tenant ainda tem budget disponível hoje.

    Args:
        company_id: ID da empresa (tenant).
        plan_code: Código do plano da assinatura ativa.
        redis_url: URL do Redis (usa REDIS_URL env se None).

    Returns:
        (allowed, used_today, daily_limit)
        - allowed: True se pode chamar LLM, False se budget esgotado.
        - used_today: tokens usados hoje.
        - daily_limit: limite do plano (-1 = ilimitado).
    """
    limit = get_plan_limit(plan_code)

    if limit == -1:
        # Plano enterprise — sem limite
        return True, 0, -1

    redis = await _get_redis(redis_url)
    if redis is None:
        # Redis indisponível → permitir com warning (graceful degradation)
        logger.warning(
            "[TokenBudget] Redis indisponível — permitindo chamada sem verificação de budget "
            "(company_id=%s)", company_id
        )
        return True, 0, limit

    try:
        key = _redis_key(company_id)
        used = await redis.get(key)
        used_int = int(used) if used else 0
        allowed = used_int < limit
        if not allowed:
            logger.warning(
                "[TokenBudget] Budget esgotado: company_id=%s used=%d limit=%d plan=%s",
                company_id, used_int, limit, plan_code,
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
    redis_url: Optional[str] = None,
) -> int:
    """
    Registra tokens consumidos por tenant no contador diário Redis.

    Args:
        company_id: ID da empresa.
        tokens_used: Tokens consumidos na chamada (input + output).
        redis_url: URL do Redis.

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
        logger.debug(
            "[TokenBudget] Incrementado: company_id=%s +%d tokens → total=%d",
            company_id, tokens_used, new_total,
        )
        return new_total
    except Exception as exc:
        logger.warning("[TokenBudget] Erro ao incrementar uso (%s)", exc)
        return 0
    finally:
        await redis.aclose()


async def get_budget_status(
    company_id: str,
    plan_code: Optional[str],
    *,
    redis_url: Optional[str] = None,
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
    now = datetime.now(timezone.utc)
    reset_at = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
    # avança 1 dia
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

_redis_instance = None

# TTL do cache de plan_code por company (1 hora — muda raramente)
_PLAN_CACHE_TTL = 3600


async def get_plan_for_company(company_id: str) -> Optional[str]:
    """
    Retorna o plan_code da assinatura ativa de uma empresa.

    Fluxo:
      1. Redis cache  →  TTL 1h  →  chave: plan_cache:{company_id}
      2. DB query (Subscription.plan_code WHERE company_id AND status=ACTIVE)
      3. Fallback: None (budget service usa DEFAULT_DAILY_LIMIT=10k)

    Nunca lança exception — falha silenciosamente retornando None.
    """
    # 1. Tentar Redis cache
    redis = await _get_redis()
    if redis is not None:
        try:
            cached = await redis.get(f"plan_cache:{company_id}")
            if cached:
                logger.debug("[TokenBudget] plan_code cache hit: company_id=%s plan=%s", company_id, cached)
                await redis.aclose()
                return cached
        except Exception:
            pass
        finally:
            try:
                await redis.aclose()
            except Exception:
                pass

    # 2. DB query
    plan_code = None
    try:
        from lia_config.database import AsyncSessionLocal
        from sqlalchemy import select, and_
        from app.models.billing import Subscription

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Subscription.plan_code).where(
                    and_(
                        Subscription.company_id == company_id,
                        Subscription.status.in_(["active", "trialing"]),
                    )
                ).limit(1)
            )
            row = result.scalar_one_or_none()
            if row:
                plan_code = str(row)
    except Exception as exc:
        logger.debug("[TokenBudget] DB lookup para plan_code falhou (company_id=%s): %s", company_id, exc)

    # 3. Cachear resultado (mesmo None não cacheia — evita cache negativo)
    if plan_code:
        try:
            redis2 = await _get_redis()
            if redis2 is not None:
                await redis2.set(f"plan_cache:{company_id}", plan_code, ex=_PLAN_CACHE_TTL)
                await redis2.aclose()
        except Exception:
            pass

    return plan_code


async def _get_redis(redis_url: Optional[str] = None):
    """Cria conexão Redis. Retorna None se indisponível."""
    try:
        import redis.asyncio as aioredis
        from lia_config.config import settings as _settings

        url = redis_url or getattr(_settings, "REDIS_URL", "redis://localhost:6379/0")
        client = aioredis.from_url(url, encoding="utf-8", decode_responses=True)
        await client.ping()
        return client
    except Exception as exc:
        logger.warning("[TokenBudget] Não foi possível conectar ao Redis: %s", exc)
        return None
