"""
Tenant Token Budget — controle de consumo de tokens por empresa.

Rastreia tokens usados no mês corrente via Redis.
Alerta quando o tenant atinge TENANT_TOKEN_BUDGET_ALERT_THRESHOLD (80%).
Bloqueia quando atinge 100% do orçamento configurado.

Chaves Redis:
  token_budget:{company_id}:{YYYY-MM}  → int (tokens usados no mês)
  TTL automático: 32 dias (reset mensal implícito)
"""
import logging
from datetime import datetime, timezone
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

_REDIS_KEY_PREFIX = "token_budget"
_TTL_SECONDS = 32 * 24 * 3600  # 32 dias — garante cobertura do mês


def _budget_key(company_id: str) -> str:
    month = datetime.now(timezone.utc).strftime("%Y-%m")
    return f"{_REDIS_KEY_PREFIX}:{company_id}:{month}"


async def _get_redis():
    """Retorna cliente Redis async (aioredis ou redis.asyncio)."""
    try:
        import redis.asyncio as aioredis
        return await aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    except ImportError:
        try:
            import aioredis
            return await aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        except ImportError:
            return None


class TenantBudget:
    """
    Controla o orçamento mensal de tokens por tenant (company_id).

    Uso:
        budget = TenantBudget()
        allowed = await budget.check_and_record(company_id, tokens_used)
    """

    def __init__(self, monthly_limit: int = settings.TENANT_TOKEN_BUDGET_DEFAULT):
        self.monthly_limit = monthly_limit
        self._alert_threshold = settings.TENANT_TOKEN_BUDGET_ALERT_THRESHOLD

    async def get_usage(self, company_id: str) -> int:
        """Retorna tokens usados no mês corrente para o tenant."""
        try:
            redis = await _get_redis()
            if redis is None:
                return 0
            async with redis:
                val = await redis.get(_budget_key(company_id))
                return int(val) if val else 0
        except Exception as exc:
            logger.debug("[TenantBudget] get_usage falhou: %s", exc)
            return 0

    async def record_usage(self, company_id: str, tokens: int) -> int:
        """
        Incrementa o contador de tokens do tenant.

        Returns:
            Total de tokens usados no mês após incremento.
        """
        if tokens <= 0:
            return await self.get_usage(company_id)

        try:
            redis = await _get_redis()
            if redis is None:
                return 0
            async with redis:
                key = _budget_key(company_id)
                total = await redis.incrby(key, tokens)
                await redis.expire(key, _TTL_SECONDS)
                return int(total)
        except Exception as exc:
            logger.debug("[TenantBudget] record_usage falhou: %s", exc)
            return 0

    async def check_and_record(
        self, company_id: str, tokens: int
    ) -> tuple[bool, int, Optional[str]]:
        """
        Verifica orçamento e registra uso.

        Returns:
            (allowed, total_used, warning_message)
            allowed=False quando 100% do budget foi atingido.
        """
        total = await self.record_usage(company_id, tokens)
        ratio = total / self.monthly_limit if self.monthly_limit > 0 else 0.0

        if ratio >= 1.0:
            logger.warning(
                "[TenantBudget] company=%s BLOQUEADO — %d/%d tokens (%.0f%%)",
                company_id, total, self.monthly_limit, ratio * 100,
            )
            return False, total, f"Orçamento mensal de tokens esgotado ({total}/{self.monthly_limit})"

        warning: Optional[str] = None
        if ratio >= self._alert_threshold:
            warning = (
                f"Atenção: {ratio:.0%} do orçamento mensal de tokens consumido "
                f"({total}/{self.monthly_limit})"
            )
            logger.warning("[TenantBudget] company=%s alerta em %.0f%%", company_id, ratio * 100)

        return True, total, warning

    async def get_status(self, company_id: str) -> dict:
        """Retorna status do orçamento do tenant para dashboards/API."""
        used = await self.get_usage(company_id)
        ratio = used / self.monthly_limit if self.monthly_limit > 0 else 0.0
        return {
            "company_id": company_id,
            "tokens_used": used,
            "tokens_limit": self.monthly_limit,
            "usage_ratio": round(ratio, 4),
            "usage_pct": round(ratio * 100, 1),
            "alert": ratio >= self._alert_threshold,
            "blocked": ratio >= 1.0,
            "month": datetime.now(timezone.utc).strftime("%Y-%m"),
        }


# Singleton compartilhado
tenant_budget = TenantBudget()
