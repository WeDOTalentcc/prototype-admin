"""
DelegationFallbackHandler - Handles cases where an action is not found
in a domain's _ACTION_TOOL_MAP and would be silently delegated.

Provides:
- Logging of unmapped actions for monitoring
- User-friendly response instead of silent pass-through
- Learning signal for future action mapping
"""
import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)

_unmapped_actions_log: list = []
MAX_LOG_SIZE = 1000


class DelegationFallbackHandler:
    @staticmethod
    def handle(
        action_id: str,
        domain_id: str,
        params: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        logger.warning(
            f"[DELEGATION-FALLBACK] Action '{action_id}' not found in "
            f"domain '{domain_id}' _ACTION_TOOL_MAP. Delegating to agent. "
            f"Params keys: {list(params.keys())}"
        )

        entry = {
            "action_id": action_id,
            "domain_id": domain_id,
            "param_keys": list(params.keys()),
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": (context or {}).get("user_id"),
        }

        if len(_unmapped_actions_log) >= MAX_LOG_SIZE:
            _unmapped_actions_log.pop(0)
        _unmapped_actions_log.append(entry)

        return {
            "action_id": action_id,
            "params": params,
            "delegate_to_agent": True,
            "fallback_handled": True,
            "message": (
                f"A ação '{action_id}' será processada pelo agente de IA. "
                f"Se não obtiver resultado, tente reformular sua solicitação."
            ),
        }

    @staticmethod
    def get_unmapped_actions_stats() -> dict[str, Any]:
        from collections import Counter
        if not _unmapped_actions_log:
            return {"total": 0, "by_domain": {}, "by_action": {}}
        domains = Counter(e["domain_id"] for e in _unmapped_actions_log)
        actions = Counter(e["action_id"] for e in _unmapped_actions_log)
        return {
            "total": len(_unmapped_actions_log),
            "by_domain": dict(domains.most_common(10)),
            "by_action": dict(actions.most_common(10)),
        }
