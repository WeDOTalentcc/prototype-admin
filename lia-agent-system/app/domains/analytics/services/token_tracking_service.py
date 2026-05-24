"""
Token Tracking Service - Real-time token monitoring system.

This service provides:
- Real-time token usage recording
- Usage aggregation by user, company, and agent
- Cost estimation based on Claude/OpenAI pricing
- Limit checking and enforcement
"""
import logging
from datetime import datetime, timedelta
from typing import Any, cast
from uuid import UUID

import redis.asyncio as aioredis
from sqlalchemy import Float, and_, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from lia_models.ai_consumption import AI_LOG_RETENTION_DAYS, AiConsumption, AiCreditsBalance

logger = logging.getLogger(__name__)

ALERT_THRESHOLDS = [80, 100]

# P2-W3-AI-2: TOKEN_PRICES — precos per-1000-tokens (USD).
# Ultima atualizacao: 2026-05-24. Atualizar quando Anthropic/Google/OpenAI
# anunciarem mudancas em https://www.anthropic.com/pricing (Claude),
# https://ai.google.dev/pricing (Gemini), https://openai.com/pricing (GPT).
# Aliases legados (claude-3-*) mantidos para backward compat com registros historicos.
TOKEN_PRICES = {
    # --- Claude (Anthropic) --- versoes ativas 2026-05 ---
    "claude-sonnet-4-6": {"input": 0.003, "output": 0.015},
    "claude-haiku-4": {"input": 0.00025, "output": 0.00125},
    "claude-opus-4": {"input": 0.015, "output": 0.075},
    "claude-sonnet-4-5": {"input": 0.003, "output": 0.015},
    "claude-3.5-sonnet": {"input": 0.003, "output": 0.015},
    "claude-3.5-haiku": {"input": 0.0008, "output": 0.004},
    # Aliases legados (backward compat com registros historicos) ---
    "claude-3-sonnet": {"input": 0.003, "output": 0.015},
    "claude-3-haiku": {"input": 0.00025, "output": 0.00125},
    "claude-3-opus": {"input": 0.015, "output": 0.075},
    # --- GPT (OpenAI) ---
    "gpt-4o": {"input": 0.005, "output": 0.015},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    "gpt-4-turbo": {"input": 0.01, "output": 0.03},
    "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
    # --- Gemini (Google) ---
    "gemini-2.0-flash": {"input": 0.0001, "output": 0.0004},
    "gemini-2.5-pro": {"input": 0.00125, "output": 0.01},
    "gemini-1.5-pro": {"input": 0.00125, "output": 0.005},
    "gemini-1.5-flash": {"input": 0.000075, "output": 0.0003},
    "gemini-flash": {"input": 0.000075, "output": 0.0003},
}

DEFAULT_LIMITS = {
    "daily_tokens_per_user": 500000,
    "daily_tokens_per_company": 5000000,
    "monthly_cost_per_company": 500.00,
    "hourly_tokens_per_user": 100000,
    "requests_per_minute_per_user": 60,
}


class TokenTrackingService:
    """
    Service for real-time token usage monitoring and limit enforcement.
    
    Features:
    - Record token usage per operation
    - Query usage by user, company, or agent type
    - Calculate cost estimates
    - Check and enforce usage limits
    """
    
    def __init__(self, db: AsyncSession):
        """
        Initialize TokenTrackingService.
        
        Args:
            db: AsyncSession for database operations
        """
        self.db = db
        self._custom_limits: dict[str, dict[str, Any]] = {}
    
    def set_custom_limits(self, company_id: str, limits: dict[str, Any]) -> None:
        """
        Set custom limits for a specific company.
        
        Args:
            company_id: Company identifier
            limits: Dictionary of limit overrides
        """
        self._custom_limits[company_id] = limits
    
    def get_limits(self, company_id: str | None = None) -> dict[str, Any]:
        """
        Get applicable limits for a company.
        
        Args:
            company_id: Optional company identifier
            
        Returns:
            Dictionary of limits (custom or default)
        """
        if company_id and company_id in self._custom_limits:
            merged = DEFAULT_LIMITS.copy()
            merged.update(self._custom_limits[company_id])
            return merged
        return DEFAULT_LIMITS.copy()
    
    async def record_apify_usage(
        self,
        company_id: str,
        user_id: str | None,
        candidate_id: str | None,
        operation: str,
        cost_usd: float,
        response_time_ms: int = 0,
        extra_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        import os
        rate = float(os.environ.get("APIFY_USD_TO_BRL_RATE", "5.50"))
        cost_cents_brl = int(round(cost_usd * rate * 100))
        try:
            try:
                _parsed_company_id = UUID(company_id)
            except (ValueError, AttributeError):
                logger.debug("[TokenTracking] Non-UUID company_id '%s', skipping ai_consumption", company_id)
                return {"skipped": True, "reason": "non_uuid_company_id"}
            try:
                _parsed_user_id = UUID(user_id) if user_id else None
            except (ValueError, AttributeError):
                _parsed_user_id = None
            consumption = AiConsumption(
                company_id=_parsed_company_id,
                user_id=_parsed_user_id,
                agent_type="apify_enrichment",
                operation=operation,
                model="apify",
                input_tokens=0,
                output_tokens=0,
                total_tokens=0,
                cost_cents=cost_cents_brl,
                candidate_id=UUID(candidate_id) if candidate_id else None,
                extra_data={
                    "cost_usd": cost_usd,
                    "exchange_rate": rate,
                    "response_time_ms": response_time_ms,
                    **(extra_data or {}),
                },
            )
            self.db.add(consumption)
            await self.db.commit()
            await self.db.refresh(consumption)

            logger.info(
                "[TokenTracking] Apify usage recorded: %s $%.4f (%d centavos BRL)",
                operation, cost_usd, cost_cents_brl,
            )
            return {
                "id": str(consumption.id),
                "cost_usd": cost_usd,
                "cost_cents_brl": cost_cents_brl,
                "agent_type": "apify_enrichment",
                "operation": operation,
            }
        except Exception as e:
            logger.error("Error recording Apify usage: %s", e, exc_info=True)
            await self.db.rollback()
            raise

    async def record_usage(
        self,
        user_id: str,
        company_id: str,
        agent_type: str,
        intent: str,
        input_tokens: int,
        output_tokens: int,
        model: str,
        latency_ms: float,
        candidate_id: str | None = None,
        vacancy_id: str | None = None,
        extra_data: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Record token usage for an AI operation.
        
        Args:
            user_id: User who triggered the operation
            company_id: Company/tenant identifier
            agent_type: Type of agent (e.g., 'sourcing', 'screening')
            intent: Intent/operation performed
            input_tokens: Number of input tokens used
            output_tokens: Number of output tokens generated
            model: Model used (e.g., 'claude-3-sonnet')
            latency_ms: Response latency in milliseconds
            candidate_id: Optional associated candidate
            vacancy_id: Optional associated job vacancy
            extra_data: Optional additional metadata
            
        Returns:
            Dict with recorded usage details and cost estimate
        """
        try:
            total_tokens = input_tokens + output_tokens
            cost_cents = self._calculate_cost_cents(model, input_tokens, output_tokens)
            
            consumption = AiConsumption(
                company_id=UUID(company_id),
                user_id=UUID(user_id) if user_id else None,
                agent_type=agent_type,
                operation=intent,
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=total_tokens,
                cost_cents=cost_cents,
                candidate_id=UUID(candidate_id) if candidate_id else None,
                vacancy_id=UUID(vacancy_id) if vacancy_id else None,
                extra_data={
                    "latency_ms": latency_ms,
                    "intent": intent,
                    **(extra_data or {})
                },
                # LGPD — política L-6: retenção de 365 dias para logs de IA
                scheduled_deletion_at=datetime.utcnow() + timedelta(days=AI_LOG_RETENTION_DAYS),
            )
            
            self.db.add(consumption)
            await self.db.commit()
            await self.db.refresh(consumption)
            
            logger.info(
                f"📊 Token usage recorded: {agent_type}/{intent} - "
                f"{total_tokens} tokens, ${cost_cents/100:.4f} cost, "
                f"{latency_ms:.0f}ms latency"
            )

            usage_result = {
                "id": str(consumption.id),
                "total_tokens": total_tokens,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost_cents": cost_cents,
                "cost_usd": cost_cents / 100,
                "latency_ms": latency_ms,
                "model": model,
                "agent_type": agent_type,
                "intent": intent,
                "created_at": consumption.created_at.isoformat() if consumption.created_at else None
            }

            # Verificar thresholds e disparar alertas se necessário (fire-and-forget)
            try:
                await self._check_and_alert_thresholds(company_id)
            except Exception as alert_err:
                logger.warning(f"Falha ao verificar thresholds de consumo de IA: {alert_err}")

            return usage_result

        except Exception as e:
            logger.error(f"Error recording token usage: {e}", exc_info=True)
            await self.db.rollback()
            raise
    
    async def get_usage_by_user(
        self, 
        user_id: str, 
        period: str = "day",
        company_id: str | None = None
    ) -> dict[str, Any]:
        """
        Get token usage summary for a specific user.
        
        Args:
            user_id: User identifier
            period: Time period - 'hour', 'day', 'week', 'month'
            company_id: Optional company filter
            
        Returns:
            Dict with usage statistics
        """
        start_date = self._get_period_start(period)
        
        conditions = [
            AiConsumption.user_id == UUID(user_id),
            AiConsumption.created_at >= start_date
        ]
        
        if company_id:
            conditions.append(AiConsumption.company_id == UUID(company_id))
        
        query = select(
            func.sum(AiConsumption.total_tokens).label('total_tokens'),
            func.sum(AiConsumption.input_tokens).label('input_tokens'),
            func.sum(AiConsumption.output_tokens).label('output_tokens'),
            func.sum(AiConsumption.cost_cents).label('total_cost_cents'),
            func.count(AiConsumption.id).label('total_operations'),
            func.avg(
                cast(
                    func.json_extract_path_text(AiConsumption.extra_data, 'latency_ms'),
                    Float
                )
            ).label('avg_latency_ms')
        ).where(and_(*conditions))
        
        result = await self.db.execute(query)
        stats = result.one()
        
        by_agent_query = select(
            AiConsumption.agent_type,
            func.sum(AiConsumption.total_tokens).label('tokens'),
            func.count(AiConsumption.id).label('operations')
        ).where(and_(*conditions)).group_by(AiConsumption.agent_type)
        
        by_agent_result = await self.db.execute(by_agent_query)
        by_agent = [
            {"agent_type": row.agent_type, "tokens": int(row.tokens or 0), "operations": int(row.operations or 0)}
            for row in by_agent_result.all()
        ]
        
        total_tokens = int(stats.total_tokens or 0)
        limits = self.get_limits(company_id)
        daily_limit = limits.get("daily_tokens_per_user", DEFAULT_LIMITS["daily_tokens_per_user"])
        
        return {
            "user_id": user_id,
            "period": period,
            "period_start": start_date.isoformat(),
            "total_tokens": total_tokens,
            "input_tokens": int(stats.input_tokens or 0),
            "output_tokens": int(stats.output_tokens or 0),
            "total_cost_cents": int(stats.total_cost_cents or 0),
            "total_cost_usd": round((stats.total_cost_cents or 0) / 100, 4),
            "total_operations": int(stats.total_operations or 0),
            "avg_latency_ms": round(float(stats.avg_latency_ms or 0), 2),
            "by_agent": by_agent,
            "daily_limit": daily_limit,
            "usage_percentage": round((total_tokens / daily_limit) * 100, 2) if period == "day" else None,
            "remaining_tokens": max(0, daily_limit - total_tokens) if period == "day" else None
        }
    
    async def get_usage_by_company(
        self, 
        company_id: str, 
        period: str = "day"
    ) -> dict[str, Any]:
        """
        Get token usage summary for a company.
        
        Args:
            company_id: Company identifier
            period: Time period - 'hour', 'day', 'week', 'month'
            
        Returns:
            Dict with company usage statistics
        """
        start_date = self._get_period_start(period)
        
        conditions = [
            AiConsumption.company_id == UUID(company_id),
            AiConsumption.created_at >= start_date
        ]
        
        query = select(
            func.sum(AiConsumption.total_tokens).label('total_tokens'),
            func.sum(AiConsumption.input_tokens).label('input_tokens'),
            func.sum(AiConsumption.output_tokens).label('output_tokens'),
            func.sum(AiConsumption.cost_cents).label('total_cost_cents'),
            func.count(AiConsumption.id).label('total_operations'),
            func.count(func.distinct(AiConsumption.user_id)).label('unique_users')
        ).where(and_(*conditions))
        
        result = await self.db.execute(query)
        stats = result.one()
        
        by_agent_query = select(
            AiConsumption.agent_type,
            func.sum(AiConsumption.total_tokens).label('tokens'),
            func.sum(AiConsumption.cost_cents).label('cost_cents'),
            func.count(AiConsumption.id).label('operations')
        ).where(and_(*conditions)).group_by(AiConsumption.agent_type)
        
        by_agent_result = await self.db.execute(by_agent_query)
        by_agent = [
            {
                "agent_type": row.agent_type, 
                "tokens": int(row.tokens or 0), 
                "cost_cents": int(row.cost_cents or 0),
                "operations": int(row.operations or 0)
            }
            for row in by_agent_result.all()
        ]
        
        by_model_query = select(
            AiConsumption.model,
            func.sum(AiConsumption.total_tokens).label('tokens'),
            func.sum(AiConsumption.cost_cents).label('cost_cents'),
            func.count(AiConsumption.id).label('operations')
        ).where(and_(*conditions)).group_by(AiConsumption.model)
        
        by_model_result = await self.db.execute(by_model_query)
        by_model = [
            {
                "model": row.model, 
                "tokens": int(row.tokens or 0), 
                "cost_cents": int(row.cost_cents or 0),
                "operations": int(row.operations or 0)
            }
            for row in by_model_result.all()
        ]
        
        total_tokens = int(stats.total_tokens or 0)
        total_cost_cents = int(stats.total_cost_cents or 0)
        limits = self.get_limits(company_id)
        daily_token_limit = limits.get("daily_tokens_per_company", DEFAULT_LIMITS["daily_tokens_per_company"])
        monthly_cost_limit = limits.get("monthly_cost_per_company", DEFAULT_LIMITS["monthly_cost_per_company"])
        
        return {
            "company_id": company_id,
            "period": period,
            "period_start": start_date.isoformat(),
            "total_tokens": total_tokens,
            "input_tokens": int(stats.input_tokens or 0),
            "output_tokens": int(stats.output_tokens or 0),
            "total_cost_cents": total_cost_cents,
            "total_cost_usd": round(total_cost_cents / 100, 4),
            "total_operations": int(stats.total_operations or 0),
            "unique_users": int(stats.unique_users or 0),
            "by_agent": by_agent,
            "by_model": by_model,
            "limits": {
                "daily_tokens": daily_token_limit,
                "monthly_cost_usd": monthly_cost_limit
            },
            "usage_percentage": round((total_tokens / daily_token_limit) * 100, 2) if period == "day" else None,
            "cost_percentage": round((total_cost_cents / 100 / monthly_cost_limit) * 100, 2) if period == "month" else None
        }
    
    async def get_usage_by_agent(
        self, 
        period: str = "day",
        company_id: str | None = None
    ) -> dict[str, Any]:
        """
        Get token usage grouped by agent type.
        
        Args:
            period: Time period - 'hour', 'day', 'week', 'month'
            company_id: Optional company filter
            
        Returns:
            Dict with usage by agent type
        """
        start_date = self._get_period_start(period)
        
        conditions = [AiConsumption.created_at >= start_date]
        
        if company_id:
            conditions.append(AiConsumption.company_id == UUID(company_id))
        
        query = select(
            AiConsumption.agent_type,
            func.sum(AiConsumption.total_tokens).label('total_tokens'),
            func.sum(AiConsumption.input_tokens).label('input_tokens'),
            func.sum(AiConsumption.output_tokens).label('output_tokens'),
            func.sum(AiConsumption.cost_cents).label('total_cost_cents'),
            func.count(AiConsumption.id).label('total_operations'),
            func.avg(
                cast(
                    func.json_extract_path_text(AiConsumption.extra_data, 'latency_ms'),
                    Float
                )
            ).label('avg_latency_ms')
        ).where(and_(*conditions)).group_by(AiConsumption.agent_type)
        
        result = await self.db.execute(query)
        rows = result.all()
        
        total_tokens_all = sum(row.total_tokens or 0 for row in rows)
        total_cost_all = sum(row.total_cost_cents or 0 for row in rows)
        
        agents = []
        for row in rows:
            tokens = int(row.total_tokens or 0)
            cost_cents = int(row.total_cost_cents or 0)
            agents.append({
                "agent_type": row.agent_type,
                "total_tokens": tokens,
                "input_tokens": int(row.input_tokens or 0),
                "output_tokens": int(row.output_tokens or 0),
                "total_cost_cents": cost_cents,
                "total_cost_usd": round(cost_cents / 100, 4),
                "total_operations": int(row.total_operations or 0),
                "avg_latency_ms": round(float(row.avg_latency_ms or 0), 2),
                "token_percentage": round((tokens / total_tokens_all) * 100, 2) if total_tokens_all > 0 else 0,
                "cost_percentage": round((cost_cents / total_cost_all) * 100, 2) if total_cost_all > 0 else 0
            })
        
        agents.sort(key=lambda x: x["total_tokens"], reverse=True)
        
        return {
            "period": period,
            "period_start": start_date.isoformat(),
            "company_id": company_id,
            "total_tokens": int(total_tokens_all),
            "total_cost_cents": int(total_cost_all),
            "total_cost_usd": round(total_cost_all / 100, 4),
            "agents": agents,
            "agent_count": len(agents)
        }
    
    async def get_cost_estimate(
        self, 
        usage: dict[str, Any],
        model: str | None = None
    ) -> float:
        """
        Calculate cost estimate for given usage.
        
        Args:
            usage: Dict with 'input_tokens' and 'output_tokens'
            model: Optional model to use for pricing
            
        Returns:
            Estimated cost in USD
        """
        input_tokens = usage.get("input_tokens", 0)
        output_tokens = usage.get("output_tokens", 0)
        
        if model and model in TOKEN_PRICES:
            cost_cents = self._calculate_cost_cents(model, input_tokens, output_tokens)
            return cost_cents / 100
        
        total_cost = 0.0
        by_model = usage.get("by_model", [])
        
        if by_model:
            for item in by_model:
                item_model = item.get("model", "claude-3-sonnet")
                item_input = item.get("input_tokens", 0)
                item_output = item.get("output_tokens", 0)
                cost_cents = self._calculate_cost_cents(item_model, item_input, item_output)
                total_cost += cost_cents / 100
        else:
            default_model = "claude-3-sonnet"
            cost_cents = self._calculate_cost_cents(default_model, input_tokens, output_tokens)
            total_cost = cost_cents / 100
        
        return round(total_cost, 4)
    
    async def check_limits(
        self, 
        user_id: str, 
        company_id: str
    ) -> tuple[bool, str]:
        """
        Check if user/company is within usage limits.
        
        Args:
            user_id: User identifier
            company_id: Company identifier
            
        Returns:
            Tuple of (is_within_limits: bool, message: str)
        """
        limits = self.get_limits(company_id)
        
        user_usage = await self.get_usage_by_user(user_id, period="day", company_id=company_id)
        user_daily_limit = limits.get("daily_tokens_per_user", DEFAULT_LIMITS["daily_tokens_per_user"])
        
        if user_usage["total_tokens"] >= user_daily_limit:
            return False, f"Limite diário de tokens do usuário atingido ({user_daily_limit:,} tokens)"
        
        hourly_usage = await self.get_usage_by_user(user_id, period="hour", company_id=company_id)
        hourly_limit = limits.get("hourly_tokens_per_user", DEFAULT_LIMITS["hourly_tokens_per_user"])
        
        if hourly_usage["total_tokens"] >= hourly_limit:
            return False, f"Limite por hora do usuário atingido ({hourly_limit:,} tokens)"
        
        company_usage = await self.get_usage_by_company(company_id, period="day")
        company_daily_limit = limits.get("daily_tokens_per_company", DEFAULT_LIMITS["daily_tokens_per_company"])
        
        if company_usage["total_tokens"] >= company_daily_limit:
            return False, f"Limite diário de tokens da empresa atingido ({company_daily_limit:,} tokens)"
        
        monthly_usage = await self.get_usage_by_company(company_id, period="month")
        monthly_cost_limit = limits.get("monthly_cost_per_company", DEFAULT_LIMITS["monthly_cost_per_company"])
        monthly_cost_usd = monthly_usage["total_cost_usd"]
        
        if monthly_cost_usd >= monthly_cost_limit:
            return False, f"Limite mensal de custo da empresa atingido (${monthly_cost_limit:.2f})"
        
        user_remaining_pct = ((user_daily_limit - user_usage["total_tokens"]) / user_daily_limit) * 100
        if user_remaining_pct < 10:
            return True, f"⚠️ Atenção: apenas {user_remaining_pct:.1f}% do limite diário restante"
        
        return True, "Dentro dos limites de uso"
    
    async def get_real_time_stats(
        self, 
        company_id: str,
        window_minutes: int = 5
    ) -> dict[str, Any]:
        """
        Get real-time usage statistics for the last N minutes.
        
        Args:
            company_id: Company identifier
            window_minutes: Time window in minutes
            
        Returns:
            Dict with real-time usage stats
        """
        start_time = datetime.now() - timedelta(minutes=window_minutes)
        
        conditions = [
            AiConsumption.company_id == UUID(company_id),
            AiConsumption.created_at >= start_time
        ]
        
        query = select(
            func.sum(AiConsumption.total_tokens).label('total_tokens'),
            func.count(AiConsumption.id).label('total_operations'),
            func.sum(AiConsumption.cost_cents).label('total_cost_cents'),
            func.avg(
                cast(
                    func.json_extract_path_text(AiConsumption.extra_data, 'latency_ms'),
                    Float
                )
            ).label('avg_latency_ms')
        ).where(and_(*conditions))
        
        result = await self.db.execute(query)
        stats = result.one()
        
        operations = int(stats.total_operations or 0)
        tokens_per_minute = (int(stats.total_tokens or 0) / window_minutes) if window_minutes > 0 else 0
        ops_per_minute = operations / window_minutes if window_minutes > 0 else 0
        
        return {
            "company_id": company_id,
            "window_minutes": window_minutes,
            "window_start": start_time.isoformat(),
            "total_tokens": int(stats.total_tokens or 0),
            "total_operations": operations,
            "total_cost_cents": int(stats.total_cost_cents or 0),
            "avg_latency_ms": round(float(stats.avg_latency_ms or 0), 2),
            "tokens_per_minute": round(tokens_per_minute, 2),
            "operations_per_minute": round(ops_per_minute, 2),
            "is_active": operations > 0
        }
    
    def _get_period_start(self, period: str) -> datetime:
        """Get the start datetime for a period."""
        now = datetime.now()
        
        if period == "hour":
            return now - timedelta(hours=1)
        elif period == "day":
            return now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "week":
            return now - timedelta(days=7)
        elif period == "month":
            return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            return now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    def _calculate_cost_cents(
        self, 
        model: str, 
        input_tokens: int, 
        output_tokens: int
    ) -> int:
        """
        Calculate cost in cents for token usage.
        
        Args:
            model: Model name
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            Cost in cents
        """
        prices = TOKEN_PRICES.get(model, TOKEN_PRICES.get("claude-3-sonnet"))
        
        if not prices:
            prices = {"input": 0.003, "output": 0.015}
        
        input_cost = (input_tokens / 1000) * prices["input"]
        output_cost = (output_tokens / 1000) * prices["output"]
        
        total_cost_usd = input_cost + output_cost
        cost_cents = int(total_cost_usd * 100)
        
        return cost_cents
        # ADR-001-EXEMPT: AiCreditsBalance + Company billing reads; isolated to token tracking service; promote to BillingRepository in Sprint 6

    async def _check_and_alert_thresholds(self, company_id: str) -> None:
        """
        Verifica se o consumo de IA da empresa cruzou um threshold (80% ou 100%)
        e dispara notificação se necessário.

        Usa Redis para evitar re-alertar no mesmo dia (SETNX com TTL 24h).
        """
        # Buscar saldo atual da empresa
        balance_query = select(AiCreditsBalance).where(
            AiCreditsBalance.company_id == UUID(company_id)
        )
        result = await self.db.execute(balance_query)
        balance = result.scalar_one_or_none()

        if not balance or balance.monthly_limit <= 0:
            return

        usage_pct = (balance.current_usage / balance.monthly_limit) * 100

        for threshold in ALERT_THRESHOLDS:
            if usage_pct < threshold:
                continue

            # Verificar via Redis se já alertamos hoje para este threshold
            try:
                redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
                redis_key = f"ai_alert:{company_id}:{threshold}"
                was_set = await redis_client.set(redis_key, "1", ex=86400, nx=True)
                await redis_client.aclose()
            except Exception as redis_err:
                logger.warning(f"Redis indisponível para dedup de alerta: {redis_err}")
                was_set = True  # Assume que não foi enviado se Redis falhou

            if not was_set:
                # Alerta já enviado hoje para este threshold
                # ADR-001-EXEMPT: AiCreditsBalance + Company billing reads; isolated to token tracking service; promote to BillingRepository in Sprint 6
                continue

            # Disparar notificação
            try:
                from app.services.notification_service import NotificationChannel, NotificationService, NotificationType
                notification_svc = NotificationService()

                # Buscar admin da empresa
                from lia_models.company import Company
                company_query = select(Company).where(Company.id == UUID(company_id))
                company_result = await self.db.execute(company_query)
                company = company_result.scalar_one_or_none()
                admin_user_id = str(company.admin_user_id) if company and company.admin_user_id else None

                if not admin_user_id:
                    logger.warning(f"Empresa {company_id} sem admin_user_id — alerta de IA não enviado")
                    continue

                is_critical = threshold >= 100
                title = (
                    f"🚨 Limite de IA atingido: {usage_pct:.0f}%"
                    if is_critical
                    else f"⚠️ Consumo de IA em {usage_pct:.0f}% do limite mensal"
                )
                message = (
                    f"Sua empresa usou {balance.current_usage:,} de {balance.monthly_limit:,} tokens "
                    f"({usage_pct:.1f}%). O consumo de IA foi bloqueado. "
                    f"Contate o suporte ou atualize seu plano."
                    if is_critical
                    else f"Sua empresa usou {balance.current_usage:,} de {balance.monthly_limit:,} tokens "
                    f"({usage_pct:.1f}%). Considere monitorar o uso para evitar interrupções."
                )

                await notification_svc.create_notification(
                    user_id=admin_user_id,
                    title=title,
                    message=message,
                    notification_type=NotificationType.URGENT if is_critical else NotificationType.WARNING,
                    category="ai_consumption",
                    source_agent="token_tracking",
                    source_trigger=f"threshold_{threshold}",
                    action_url="/configuracoes/ai-credits",
                    action_label="Ver consumo de IA",
                    channels=[NotificationChannel.BELL.value, NotificationChannel.EMAIL.value],
                )
                logger.info(f"📊 Alerta de IA disparado para empresa {company_id}: {usage_pct:.1f}% (threshold={threshold}%)")

            except Exception as notify_err:
                logger.error(f"Falha ao enviar alerta de consumo de IA: {notify_err}")


token_tracking_service: TokenTrackingService | None = None


def get_token_tracking_service(db: AsyncSession) -> TokenTrackingService:
    """
    Factory function to get TokenTrackingService instance.
    
    Args:
        db: AsyncSession for database operations
        
    Returns:
        TokenTrackingService instance
    """
    return TokenTrackingService(db)
