from app.domains.compliance_base import ComplianceDomainPrompt
from app.domains.registry import register_domain

from .actions import ACTIONS


@register_domain
class {DomainName}Domain(ComplianceDomainPrompt):
    domain_id = "{domain_name}"
    domain_name = "{DomainName}"
    description = "TODO: one-line description"
    version = "1.0.0"

    def get_allowed_actions(self):
        return ACTIONS

    def get_system_prompt(self, **kwargs):
        base = "You are a specialized assistant for {domain_name}."
        return super().get_system_prompt(base)

    async def process_intent(self, query, context):
        from app.domains.base import IntentResult
        return IntentResult(
            intent_id=f"{self.domain_id}_default",
            action_id=ACTIONS[0].id if ACTIONS else None,
            confidence=0.5,
            extracted_params={},
            reasoning="Default intent — implement domain-specific logic",
        )

    async def execute_action(self, action_id, params, context):
        from app.domains.base import DomainResponse
        handler_map = {
            # "action_id": self._handle_action,
        }
        handler = handler_map.get(action_id)
        if handler:
            return await handler(params, context)
        return DomainResponse.error_response(f"Unknown action: {action_id}")
