"""
Policy Engine - Enforces business rules, credit limits, and compliance

Validates requests against:
- Credit/token budgets per user/tenant
- Rate limiting policies
- Compliance requirements (LGPD)
- Business rule constraints
"""

import logging
import os
from typing import Any, Dict

logger = logging.getLogger(__name__)


def _get_db_connection():
    """Get a psycopg2 connection from DATABASE_URL. Returns None on failure."""
    try:
        import psycopg2
        db_url = os.environ.get("DATABASE_URL", "")
        if not db_url:
            return None
        conn = psycopg2.connect(db_url)
        return conn
    except Exception as e:
        logger.warning(f"PolicyEngine: DB connection failed: {e}")
        return None


class PolicyEngine:
    """Enforces business policies and constraints on agent operations."""
    
    # Whitelist of allowed usage types for SQL queries (prevents SQL injection)
    ALLOWED_USAGE_TYPES = {"chat_requests", "action_executions", "llm_calls"}
    
    # Default policies (can be overridden per tenant/user)
    DEFAULT_POLICIES = {
        "max_pearch_searches_per_day": 10,
        "max_voice_screenings_per_day": 20,
        "max_tokens_per_request": 50000,
        "max_concurrent_requests": 5,
        "allow_global_search": True,
        "require_approval_for_bulk_email": True
    }

    DEFAULT_USAGE_LIMITS = {
        "chat_requests": 1000,
        "action_executions": 500,
        "llm_calls": 5000,
    }
    
    def __init__(self, db_service=None):
        """Initialize Policy Engine with optional database service."""
        self.db = db_service
        self.policies = self.DEFAULT_POLICIES.copy()
        self.usage_limits = self.DEFAULT_USAGE_LIMITS.copy()
        
    async def validate_request(
        self, 
        intent: str, 
        user_id: str,
        context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Validate request against policies.
        
        Args:
            intent: Detected intent
            user_id: User making request
            context: Additional context (credits, usage stats)
            
        Returns:
            Dict with: allowed (bool), reason (str), constraints (dict)
        """
        try:
            # Check credit limits for Pearch searches
            if intent == "candidate_search":
                return await self._validate_search_request(user_id, context)
            
            # Check voice screening limits
            elif intent == "candidate_screening":
                return await self._validate_screening_request(user_id, context)
            
            # Check bulk communication policies
            elif intent == "communication":
                return await self._validate_communication_request(user_id, context)
            
            # Default: allow
            return {
                "allowed": True,
                "reason": "No policy restrictions apply",
                "constraints": {}
            }
            
        except Exception as e:
            logger.error(f"❌ Policy validation failed: {e}")
            # Fail-safe: allow on error but log
            return {
                "allowed": True,
                "reason": f"Policy check failed, allowing by default: {str(e)}",
                "constraints": {}
            }
    
    def _get_daily_usage(self, tenant_id: str, usage_type: str = "chat_requests") -> int | None:
        """Query api_usage_daily for the current day's count. Returns None if DB unavailable."""
        if usage_type not in self.ALLOWED_USAGE_TYPES:
            logger.warning(f"Invalid usage_type: {usage_type}")
            return 0
        
        conn = _get_db_connection()
        if not conn:
            return None
        try:
            with conn.cursor() as cur:
                cur.execute(
                    f"SELECT {usage_type} FROM api_usage_daily WHERE tenant_id = %s AND usage_date = CURRENT_DATE",
                    (tenant_id,)
                )
                row = cur.fetchone()
                return row[0] if row else 0
        except Exception as e:
            logger.warning(f"PolicyEngine: Failed to query usage for {tenant_id}: {e}")
            return None
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def _check_usage_limit(self, tenant_id: str, usage_type: str = "chat_requests") -> dict[str, Any]:
        """Check if tenant is within daily usage limits for a given usage type."""
        limit = self.usage_limits.get(usage_type, 1000)
        current_usage = self._get_daily_usage(tenant_id, usage_type)

        if current_usage is None:
            return {
                "allowed": True,
                "reason": f"Usage check unavailable, allowing by default (limit: {limit}/day)",
                "current_usage": 0,
                "limit": limit,
            }

        if current_usage >= limit:
            return {
                "allowed": False,
                "reason": f"Daily {usage_type} limit reached ({current_usage}/{limit})",
                "current_usage": current_usage,
                "limit": limit,
            }

        return {
            "allowed": True,
            "reason": f"Within daily limit ({current_usage}/{limit} {usage_type})",
            "current_usage": current_usage,
            "limit": limit,
        }

    def record_usage(self, tenant_id: str, usage_type: str = "chat_requests"):
        """Record API usage for rate tracking. Atomically increments the counter via UPSERT."""
        if usage_type not in self.ALLOWED_USAGE_TYPES:
            logger.warning(f"PolicyEngine: Invalid usage_type '{usage_type}', skipping")
            return

        conn = _get_db_connection()
        if not conn:
            logger.warning("PolicyEngine: Cannot record usage, DB unavailable")
            return
        try:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    INSERT INTO api_usage_daily (tenant_id, usage_date, {usage_type})
                    VALUES (%s, CURRENT_DATE, 1)
                    ON CONFLICT (tenant_id, usage_date)
                    DO UPDATE SET {usage_type} = api_usage_daily.{usage_type} + 1,
                                 updated_at = NOW()
                    """,
                    (tenant_id,)
                )
            conn.commit()
            logger.debug(f"PolicyEngine: Recorded {usage_type} usage for tenant {tenant_id}")
        except Exception as e:
            logger.warning(f"PolicyEngine: Failed to record usage for {tenant_id}: {e}")
            try:
                conn.rollback()
            except Exception:
                pass
        finally:
            try:
                conn.close()
            except Exception:
                pass

    async def _validate_search_request(
        self, 
        user_id: str, 
        context: dict[str, Any] | None
    ) -> dict[str, Any]:
        """Validate candidate search request against credit limits."""
        tenant_id = (context or {}).get("tenant_id", user_id)
        max_searches = self.policies["max_pearch_searches_per_day"]

        usage_check = self._check_usage_limit(tenant_id, "chat_requests")
        if not usage_check["allowed"]:
            return {
                "allowed": False,
                "reason": usage_check["reason"],
                "constraints": {}
            }

        return {
            "allowed": True,
            "reason": f"Within daily limit ({usage_check.get('current_usage', 0)}/{max_searches} searches)",
            "constraints": {
                "prefer_local_database": True,
                "max_pearch_credits": 5
            }
        }
    
    async def _validate_screening_request(
        self, 
        user_id: str,
        context: dict[str, Any] | None
    ) -> dict[str, Any]:
        """Validate screening request against daily limits."""
        tenant_id = (context or {}).get("tenant_id", user_id)
        max_screenings = self.policies["max_voice_screenings_per_day"]

        usage_check = self._check_usage_limit(tenant_id, "action_executions")
        if not usage_check["allowed"]:
            return {
                "allowed": False,
                "reason": usage_check["reason"],
                "constraints": {}
            }

        return {
            "allowed": True,
            "reason": f"Within daily limit ({usage_check.get('current_usage', 0)}/{max_screenings} screenings)",
            "constraints": {}
        }
    
    async def _validate_communication_request(
        self, 
        user_id: str,
        context: dict[str, Any] | None
    ) -> dict[str, Any]:
        """Validate communication request (bulk email approval)."""
        # Check if bulk operation requires approval
        is_bulk = context and context.get("recipient_count", 1) > 10
        
        if is_bulk and self.policies["require_approval_for_bulk_email"]:
            return {
                "allowed": False,
                "reason": "Bulk email (>10 recipients) requires manager approval",
                "constraints": {
                    "requires_approval": True
                }
            }
        
        return {
            "allowed": True,
            "reason": "Communication allowed",
            "constraints": {}
        }
    
    def update_policy(self, policy_key: str, value: Any):
        """Update a specific policy value."""
        if policy_key in self.policies:
            self.policies[policy_key] = value
            logger.info(f"🔧 Policy updated: {policy_key} = {value}")
        else:
            logger.warning(f"⚠️  Unknown policy key: {policy_key}")

    # Defaults por setor (Alpha 1 — setores WeDOTalent)
    SECTOR_DEFAULTS = {
        "tech": {
            "max_pearch_searches_per_day": 50,
            "max_voice_screenings_per_day": 100,
            "max_tokens_per_request": 100000,
            "max_concurrent_requests": 10,
            "allow_global_search": True,
            "require_approval_for_bulk_email": False,  # tech: menor burocracia
        },
        "varejo": {
            "max_pearch_searches_per_day": 200,
            "max_voice_screenings_per_day": 500,
            "max_tokens_per_request": 50000,
            "max_concurrent_requests": 20,
            "allow_global_search": True,
            "require_approval_for_bulk_email": True,
        },
        "logistica": {
            "max_pearch_searches_per_day": 300,
            "max_voice_screenings_per_day": 1000,
            "max_tokens_per_request": 50000,
            "max_concurrent_requests": 30,
            "allow_global_search": True,
            "require_approval_for_bulk_email": True,
        },
        "financeiro": {
            "max_pearch_searches_per_day": 20,
            "max_voice_screenings_per_day": 50,
            "max_tokens_per_request": 50000,
            "max_concurrent_requests": 5,
            "allow_global_search": False,  # financeiro: restrições regulatórias BCB 498
            "require_approval_for_bulk_email": True,
        },
        "saude": {
            "max_pearch_searches_per_day": 30,
            "max_voice_screenings_per_day": 80,
            "max_tokens_per_request": 50000,
            "max_concurrent_requests": 8,
            "allow_global_search": False,
            "require_approval_for_bulk_email": True,
        },
        "rpo": {
            "max_pearch_searches_per_day": 500,
            "max_voice_screenings_per_day": 2000,
            "max_tokens_per_request": 100000,
            "max_concurrent_requests": 50,
            "allow_global_search": True,
            "require_approval_for_bulk_email": False,
        },
    }

    def apply_industry_defaults(self, sector: str) -> dict:
        """
        Aplica defaults de política para o setor da empresa.

        Alpha 1 sectors: tech, varejo, logistica, financeiro, saude, rpo

        Args:
            sector: Setor da empresa (case-insensitive)

        Returns:
            Dict com as políticas aplicadas. Retorna DEFAULT_POLICIES se setor não reconhecido.
        """
        sector_key = (sector or "").lower().strip()
        defaults = self.SECTOR_DEFAULTS.get(sector_key, self.DEFAULT_POLICIES)
        self.policies.update(defaults)
        logger.info(f"PolicyEngine: applied {sector_key!r} defaults → {list(defaults.keys())}")
        return dict(self.policies)
