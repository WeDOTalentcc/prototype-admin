"""
Tenant Token Budget — controle de consumo de tokens por empresa.

Rastreia tokens usados no mês corrente via Redis.
Alerta quando o tenant atinge TENANT_TOKEN_BUDGET_ALERT_THRESHOLD (80%).
Bloqueia quando atinge 100% do orçamento configurado.

Per-request tracking: cada chamada ao orchestrator recebe um request_id
e registra custo individual para billing granular.

Chaves Redis:
  token_budget:{company_id}:{YYYY-MM}       → int (tokens usados no mês)
  req_cost:{company_id}:{request_id}         → hash (tokens_input, tokens_output, tokens_total, cost_usd)
  TTL automático: 32 dias (reset mensal implícito)
"""
import logging
import uuid
from datetime import UTC, datetime

from app.core.config import settings

logger = logging.getLogger(__name__)

_REDIS_KEY_PREFIX = "token_budget"
_REQ_COST_PREFIX = "req_cost"
_TTL_SECONDS = 32 * 24 * 3600
_REQ_TTL_SECONDS = 7 * 24 * 3600


def _budget_key(company_id: str) -> str:
    month = datetime.now(UTC).strftime("%Y-%m")
    return f"{_REDIS_KEY_PREFIX}:{company_id}:{month}"


def _request_key(company_id: str, request_id: str) -> str:
    return f"{_REQ_COST_PREFIX}:{company_id}:{request_id}"


def generate_request_id() -> str:
    return str(uuid.uuid4())


async def _get_redis():
    """Retorna cliente Redis async (aioredis ou redis.asyncio)."""
    try:
        import redis.asyncio as aioredis
        return await aioredis.from_url(settings.REDIS_URL, decode_responses=True, socket_connect_timeout=5, socket_timeout=5)
    except ImportError:
        try:
            import aioredis
            return await aioredis.from_url(settings.REDIS_URL, decode_responses=True, socket_connect_timeout=5, socket_timeout=5)
        except ImportError:
            return None


class TenantBudget:
    """
    Controla o orçamento mensal de tokens por tenant (company_id).

    Uso:
        budget = TenantBudget()
        request_id = generate_request_id()
        allowed = await budget.check_and_record(company_id, tokens_used, request_id=request_id)
    """

    def __init__(self, monthly_limit: int = settings.TENANT_TOKEN_BUDGET_DEFAULT):
        self.monthly_limit = monthly_limit
        self._alert_threshold = settings.TENANT_TOKEN_BUDGET_ALERT_THRESHOLD
        self._per_request_threshold = settings.TENANT_PER_REQUEST_TOKEN_THRESHOLD

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

    async def record_request_cost(
        self,
        company_id: str,
        request_id: str,
        tokens_input: int = 0,
        tokens_output: int = 0,
        cost_usd: float = 0.0,
        model: str | None = None,
    ) -> None:
        """Persist per-request cost breakdown in Redis."""
        try:
            redis = await _get_redis()
            if redis is None:
                return
            async with redis:
                key = _request_key(company_id, request_id)
                await redis.hset(key, mapping={
                    "tokens_input": str(tokens_input),
                    "tokens_output": str(tokens_output),
                    "tokens_total": str(tokens_input + tokens_output),
                    "cost_usd": str(round(cost_usd, 6)),
                    "model": model or "",
                    "timestamp": datetime.now(UTC).isoformat(),
                })
                await redis.expire(key, _REQ_TTL_SECONDS)
        except Exception as exc:
            logger.debug("[TenantBudget] record_request_cost falhou: %s", exc)

    async def get_request_cost(self, company_id: str, request_id: str) -> dict | None:
        """Retrieve per-request cost from Redis."""
        try:
            redis = await _get_redis()
            if redis is None:
                return None
            async with redis:
                key = _request_key(company_id, request_id)
                data = await redis.hgetall(key)
                if not data:
                    return None
                return {
                    "request_id": request_id,
                    "tokens_input": int(data.get("tokens_input", 0)),
                    "tokens_output": int(data.get("tokens_output", 0)),
                    "tokens_total": int(data.get("tokens_total", 0)),
                    "cost_usd": float(data.get("cost_usd", 0)),
                    "model": data.get("model", ""),
                    "timestamp": data.get("timestamp", ""),
                }
        except Exception as exc:
            logger.debug("[TenantBudget] get_request_cost falhou: %s", exc)
            return None

    async def check_and_record(
        self,
        company_id: str,
        tokens: int,
        request_id: str | None = None,
        tokens_input: int = 0,
        tokens_output: int = 0,
        cost_usd: float = 0.0,
        model: str | None = None,
    ) -> tuple[bool, int, str | None]:
        """
        Verifica orçamento e registra uso.

        Args:
            company_id: Tenant identifier.
            tokens: Total tokens consumed.
            request_id: Unique per-request identifier for granular tracking.
            tokens_input: Input tokens for cost breakdown.
            tokens_output: Output tokens for cost breakdown.
            cost_usd: Estimated cost in USD.
            model: LLM model used.

        Returns:
            (allowed, total_used, warning_message)
            allowed=False quando 100% do budget foi atingido.
        """
        if request_id:
            await self.record_request_cost(
                company_id, request_id,
                tokens_input=tokens_input,
                tokens_output=tokens_output,
                cost_usd=cost_usd,
                model=model,
            )

        if tokens > self._per_request_threshold:
            logger.warning(
                "[TenantBudget] company=%s request=%s PER-REQUEST alert — %d tokens (threshold=%d)",
                company_id, request_id or "?", tokens, self._per_request_threshold,
            )
            await self._send_budget_alert(
                company_id,
                f"Alerta: request {request_id or '?'} consumiu {tokens} tokens "
                f"(threshold individual: {self._per_request_threshold})",
                ratio=0.0,
                alert_type="per_request",
                request_id=request_id,
            )

        total = await self.record_usage(company_id, tokens)
        ratio = total / self.monthly_limit if self.monthly_limit > 0 else 0.0

        if ratio >= 1.0:
            logger.warning(
                "[TenantBudget] company=%s BLOQUEADO — %d/%d tokens (%.0f%%)",
                company_id, total, self.monthly_limit, ratio * 100,
            )
            return False, total, f"Orçamento mensal de tokens esgotado ({total}/{self.monthly_limit})"

        warning: str | None = None
        if ratio >= self._alert_threshold:
            warning = (
                f"Atenção: {ratio:.0%} do orçamento mensal de tokens consumido "
                f"({total}/{self.monthly_limit})"
            )
            logger.warning("[TenantBudget] company=%s alerta em %.0f%%", company_id, ratio * 100)

        if warning:
            await self._send_budget_alert(company_id, warning, ratio)

        return True, total, warning

    async def _send_budget_alert(
        self,
        company_id: str,
        message: str,
        ratio: float,
        alert_type: str = "monthly",
        request_id: str | None = None,
    ) -> None:
        """Envia notificação Bell+log quando orçamento de tokens atinge threshold (fail-safe)."""
        try:
            from app.services.notification_service import notification_service
            metadata: dict = {
                "usage_ratio": round(ratio, 4),
                "monthly_limit": self.monthly_limit,
                "alert_type": alert_type,
            }
            if request_id:
                metadata["request_id"] = request_id
            await notification_service.send(
                company_id=company_id,
                event_type="token_budget_alert",
                title="Alerta de Orçamento de Tokens",
                body=message,
                severity="warning" if ratio < 1.0 else "critical",
                channels=["bell"],
                metadata=metadata,
            )
        except Exception as exc:
            logger.debug("[TenantBudget] _send_budget_alert falhou (fail-safe): %s", exc)

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
            "month": datetime.now(UTC).strftime("%Y-%m"),
            "per_request_threshold": self._per_request_threshold,
        }

    def get_provider_container(self, company_id: str):
        """
        Return the LLM ProviderContainer configured for this tenant.

        Delegates to TenantProviderRegistry, which sources provider config
        from tool_permissions.yaml (per-tenant llm_provider + llm_fallback_order).

        This wires tenant token budget management with per-tenant provider
        selection (Task #125).

        Usage in orchestration paths:
            budget = TenantBudget()
            container = budget.get_provider_container(company_id)
            result = await container.generate_with_fallback(prompt)
            await budget.check_and_record(company_id, tokens_used, request_id=req_id)
        """
        try:
            from app.shared.providers.llm_factory import TenantProviderRegistry
            return TenantProviderRegistry.get_instance().get_container(company_id)
        except Exception as exc:
            logger.warning(
                "[TenantBudget] Could not get provider container for company=%s: %s",
                company_id, exc,
            )
            return None


tenant_budget = TenantBudget()
