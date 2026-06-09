"""
PolicyDomain — backward-compat shim for the deprecated `policy` domain.

The canonical implementation lives in `app.domains.hiring_policy.domain.HiringPolicyDomain`.
This file registers `domain_id = "policy"` in the DomainRegistry so callers that
reference "policy" (agent_model_config, handoff_tools, onboarding_settings_runner, etc.)
continue to resolve a domain instance without errors.

Scheduled for removal in Sprint VI.  See docs/TODO_POLICY_CONSOLIDATION.md.
"""
from __future__ import annotations

import logging
import warnings
from typing import Any

from app.domains.base import DomainAction, DomainContext, DomainResponse, IntentResult
from app.domains.compliance_base import ComplianceDomainPrompt
from app.domains.registry import register_domain

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Backward-compat: reuse actions declared in the canonical hiring_policy domain
# ---------------------------------------------------------------------------
def _get_hiring_policy_actions() -> list[DomainAction]:
    try:
        from app.domains.hiring_policy.domain import HIRING_POLICY_ACTIONS
        return HIRING_POLICY_ACTIONS
    except ImportError:
        return []


@register_domain
class PolicyDomain(ComplianceDomainPrompt):
    """Deprecated shim — delegates to HiringPolicyDomain.

    Registered as domain_id="policy" for backward compatibility with callers
    that reference the legacy "policy" domain identifier.  All real logic lives
    in app.domains.hiring_policy.domain.HiringPolicyDomain (domain_id="hiring_policy").

    UC-P1-21: this class MUST NOT be imported directly by new code; import from
    app.domains.hiring_policy instead.
    """

    _compliance_config = {'high_impact': True, 'fairness_action_type': 'policy_check'}

    domain_id = "policy"
    domain_name = "Policy (deprecated)"
    description = (
        "Configuração e gestão de políticas de contratação (shim de compatibilidade). "
        "Use app.domains.hiring_policy para novos desenvolvimentos."
    )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        warnings.warn(
            "PolicyDomain (domain_id='policy') is deprecated. "
            "Use HiringPolicyDomain (domain_id='hiring_policy') instead. "
            "Scheduled for removal in Sprint VI.",
            DeprecationWarning,
            stacklevel=2,
        )

    def get_allowed_actions(self) -> list[DomainAction]:
        return _get_hiring_policy_actions()

    async def process_intent(self, query: str, context: DomainContext) -> IntentResult:
        """Delegate intent processing to the canonical hiring_policy domain."""
        try:
            from app.domains.hiring_policy.domain import HiringPolicyDomain
            canonical = HiringPolicyDomain()
            return await canonical.process_intent(query, context)
        except Exception as exc:  # pragma: no cover
            logger.error("[policy shim] process_intent delegation failed: %s", exc, exc_info=True)
            return IntentResult(
                intent_id="policy.configure_policy",
                action_id="configure_policy",
                confidence=0.3,
                extracted_params={"raw_query": query},
                reasoning="Fallback after delegation failure",
            )

    async def execute_action(
        self, action_id: str, params: dict[str, Any], context: DomainContext
    ) -> DomainResponse:
        """Delegate action execution to the canonical hiring_policy domain."""
        try:
            from app.domains.hiring_policy.domain import HiringPolicyDomain
            canonical = HiringPolicyDomain()
            return await canonical.execute_action(action_id, params, context)
        except Exception as exc:  # pragma: no cover
            logger.error(
                "[policy shim] execute_action '%s' delegation failed: %s",
                action_id, exc, exc_info=True,
            )
            return DomainResponse.error_response(
                error=str(exc),
                message=f"Erro ao executar '{action_id}' via shim policy: {exc}",
                domain_id=self.domain_id,
                action_id=action_id,
            )
