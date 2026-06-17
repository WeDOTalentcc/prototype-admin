from pathlib import Path
"""Workforce Domain — planejamento de força de trabalho, headcount e previsão."""
import logging
from typing import Any

from app.domains.base import DomainAction, DomainContext, DomainResponse, IntentResult
from app.domains.compliance_base import ComplianceDomainPrompt
from app.domains.registry import register_domain
from app.shared.services.keyword_intent_matcher import KeywordIntentMatcher
import yaml as _yaml_imp

logger = logging.getLogger(__name__)

_capabilities_yaml_path = Path(__file__).parent / "config" / "capabilities.yaml"
_KEYWORD_ACTION_MAP: dict[str, str] = (
    _yaml_imp.safe_load(_capabilities_yaml_path.read_text()).get("intent_keywords", {})
    if _capabilities_yaml_path.exists()
    else {}
)

_matcher = KeywordIntentMatcher.from_keyword_map(_KEYWORD_ACTION_MAP, domain_id="workforce")


@register_domain
class WorkforceDomain(ComplianceDomainPrompt):

    _compliance_config = {"high_impact": False}
    domain_id = "workforce"
    domain_name = "Workforce Planning"

    def __init__(self):
        from app.domains.workforce.actions import WORKFORCE_ACTIONS
        self._actions = WORKFORCE_ACTIONS

    def get_allowed_actions(self) -> list[DomainAction]:
        from app.domains.workforce.actions import WORKFORCE_ACTIONS
        return WORKFORCE_ACTIONS

    def match_intent(self, query: str, context: DomainContext | None = None) -> IntentResult | None:
        return _matcher.match(query)

    def execute(self, action: str, params: dict[str, Any], context: DomainContext) -> DomainResponse:
        raise NotImplementedError(f"workforce.{action} — use tool registry directly")
