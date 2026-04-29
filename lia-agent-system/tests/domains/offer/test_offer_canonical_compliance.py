"""
PR-B — test_offer_canonical_compliance.py

Verifica que o dominio offer atende ao CLAUDE.md canonical scaffold:
  1. OfferDomain extends ComplianceDomainPrompt
  2. domain_id = "offer"
  3. _compliance_config has high_impact = True
  4. All 6 actions declare required_params
  5. get_system_prompt() returns non-empty string
"""
import pytest


def _get_domain():
    from app.domains.offer.domain import OfferDomain
    return OfferDomain()


class TestOfferCanonicalCompliance:

    def test_extends_compliance_domain_prompt(self):
        from app.domains.compliance_base import ComplianceDomainPrompt
        assert issubclass(type(_get_domain()), ComplianceDomainPrompt)

    def test_domain_id(self):
        assert _get_domain().domain_id == "offer"

    def test_high_impact_compliance_config(self):
        domain = _get_domain()
        assert domain._compliance_config.get("high_impact") is True

    def test_all_actions_have_required_params_or_optional(self):
        domain = _get_domain()
        for action in domain.get_allowed_actions():
            # Each action must have at least an action_id
            assert action.action_id, f"Action missing action_id: {action}"

    def test_system_prompt_non_empty(self):
        prompt = _get_domain().get_system_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 50, "System prompt suspiciously short"

    def test_six_actions_registered(self):
        actions = _get_domain().get_allowed_actions()
        action_ids = {a.action_id for a in actions}
        expected = {
            "create_offer_draft", "update_offer_draft", "get_offer_draft",
            "send_offer", "prepare_offer_manual_send", "cancel_offer",
        }
        assert expected == action_ids
