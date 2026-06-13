"""
Contract tests for FairnessPolicyService.

Tests verify:
1. apply_input_filter removes blocked attributes
2. apply_input_filter removes PII fields
3. validate_query_filters detects banlist terms
4. validate_query_filters passes clean queries
5. allows_automated blocks final_rejection
6. allows_automated blocks low confidence
7. allows_automated permits high confidence
8. validate_tenant_override blocks softening
9. validate_tenant_override allows hardening
10. DEFAULT_PLATFORM_GENERAL_RULES all have required fields

Run: pytest tests/contract/test_fairness_policy_service.py -v
"""
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import pytest


# ---------------------------------------------------------------------------
# Helper: build minimal effective_policy for tests (no DB needed)
# ---------------------------------------------------------------------------

def _make_effective_policy():
    return {
        "blocked_attribute": [
            {
                "id": "rule-blocked-1",
                "scope": "platform_general",
                "is_locked": True,
                "body_json": {
                    "attributes": [
                        "gender", "genero", "raca", "race", "religiao", "religion",
                        "estado_civil", "marital_status", "idade_exata", "foto", "photo",
                    ],
                    "action": "reject_input",
                },
            }
        ],
        "mandatory_anonymization": [
            {
                "id": "rule-anon-1",
                "scope": "platform_general",
                "is_locked": True,
                "body_json": {
                    "fields": [
                        "cpf", "rg", "foto", "photo", "nome_completo", "email",
                        "telefone", "endereco", "data_nascimento",
                    ],
                    "strategy": "redact",
                },
            }
        ],
        "human_in_the_loop": [
            {
                "id": "rule-hitl-1",
                "scope": "platform_general",
                "is_locked": True,
                "body_json": {
                    "decision_types": ["final_rejection", "offer_extension", "blacklist"],
                    "bypass_allowed": False,
                },
            }
        ],
        "decision_threshold": [
            {
                "id": "rule-threshold-1",
                "scope": "platform_general",
                "is_locked": False,
                "body_json": {
                    "min_confidence": 0.75,
                    "applies_to": ["screening_score", "match_score"],
                },
            }
        ],
        "linguistic_banlist": [
            {
                "id": "rule-banlist-1",
                "scope": "platform_general",
                "is_locked": True,
                "body_json": {
                    "terms": ["boa aparencia", "bairros nobres", "perfil adequado"],
                },
            }
        ],
    }


# ---------------------------------------------------------------------------
# Import service (patching DB-heavy methods when needed)
# ---------------------------------------------------------------------------

@pytest.fixture
def service():
    """Returns a FairnessPolicyService instance without any DB calls."""
    import sys
    import os
    # Make sure the lia-agent-system path is available
    project_root = os.environ.get("LIA_PROJECT_ROOT", "/home/runner/workspace/lia-agent-system")
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    from app.shared.compliance.fairness_policy_service import FairnessPolicyService
    return FairnessPolicyService()


@pytest.fixture
def policy():
    return _make_effective_policy()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestApplyInputFilter:
    def test_apply_input_filter_removes_blocked_attributes(self, service, policy):
        """Dict with 'gender' field should be removed by blocked_attribute rule."""
        input_data = {
            "candidate_name": "João",
            "gender": "male",
            "experience_years": 5,
        }
        result = service.apply_input_filter(input_data, policy)
        assert "gender" not in result
        assert "candidate_name" in result
        assert "experience_years" in result

    def test_apply_input_filter_removes_pii_fields(self, service, policy):
        """Dict with 'cpf' field should be removed by mandatory_anonymization rule."""
        input_data = {
            "candidate_id": "abc123",
            "cpf": "123.456.789-00",
            "email": "joao@example.com",
            "score": 85,
        }
        result = service.apply_input_filter(input_data, policy)
        assert "cpf" not in result
        assert "email" not in result
        assert "candidate_id" in result
        assert "score" in result

    def test_apply_input_filter_does_not_mutate_original(self, service, policy):
        """Original dict must not be mutated."""
        input_data = {"gender": "male", "experience": 3}
        original_copy = dict(input_data)
        service.apply_input_filter(input_data, policy)
        assert input_data == original_copy


class TestValidateQueryFilters:
    def test_validate_query_filters_detects_banlist_term(self, service, policy):
        """Query with 'boa aparencia' should generate violation."""
        filters = {"query": "candidato com boa aparencia e experiencia"}
        violations = service.validate_query_filters(filters, policy)
        assert len(violations) > 0
        assert any("boa aparencia" in v.lower() for v in violations)

    def test_validate_query_filters_clean_query_passes(self, service, policy):
        """Clean query should return empty violations list."""
        filters = {"query": "candidato com experiência em Python e liderança de equipes"}
        violations = service.validate_query_filters(filters, policy)
        assert violations == []

    def test_validate_query_filters_empty_filters(self, service, policy):
        """Empty filters should return empty violations."""
        violations = service.validate_query_filters({}, policy)
        assert violations == []


class TestAllowsAutomated:
    def _run(self, coro):
        return asyncio.get_event_loop().run_until_complete(coro)

    def test_allows_automated_blocks_final_rejection(self, service, policy):
        """decision_type='final_rejection' must return (False, reason)."""
        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.flush = AsyncMock()

        allowed, reason = self._run(
            service.allows_automated(
                decision_type="final_rejection",
                confidence=0.95,
                effective_policy=policy,
                tenant_id="11111111-1111-1111-1111-111111111111",
                domain="screening",
                db=mock_db,
            )
        )
        assert allowed is False
        assert "final_rejection" in reason.lower() or "humana" in reason.lower()

    def test_allows_automated_blocks_low_confidence(self, service, policy):
        """confidence=0.5 < threshold=0.75 must return (False, reason)."""
        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.flush = AsyncMock()

        allowed, reason = self._run(
            service.allows_automated(
                decision_type="screening_score",
                confidence=0.50,
                effective_policy=policy,
                tenant_id="11111111-1111-1111-1111-111111111111",
                domain="screening",
                db=mock_db,
            )
        )
        assert allowed is False
        assert "0.50" in reason or "confiança" in reason.lower() or "threshold" in reason.lower()

    def test_allows_automated_permits_high_confidence(self, service, policy):
        """confidence=0.9 > threshold=0.75 with allowed decision_type must return (True, '')."""
        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.flush = AsyncMock()

        allowed, reason = self._run(
            service.allows_automated(
                decision_type="interview_scheduling",
                confidence=0.90,
                effective_policy=policy,
                tenant_id="11111111-1111-1111-1111-111111111111",
                domain="screening",
                db=mock_db,
            )
        )
        assert allowed is True
        assert reason == ""


class TestValidateTenantOverride:
    def test_validate_tenant_override_blocks_softening(self, service):
        """Tenant trying to lower min_confidence below platform locked value must be rejected."""
        platform_rules = [
            {
                "rule_type": "decision_threshold",
                "is_locked": False,  # tunable but min is enforced
                "body_json": {"min_confidence": 0.75},
            }
        ]
        # Locked rule for blocked_attribute
        platform_rules_locked = [
            {
                "rule_type": "decision_threshold",
                "is_locked": True,
                "body_json": {"min_confidence": 0.75},
            }
        ]
        tenant_rules = [
            {
                "rule_type": "decision_threshold",
                "body_json": {"min_confidence": 0.60},  # softening!
            }
        ]
        errors = service.validate_tenant_override(tenant_rules, platform_rules_locked)
        assert len(errors) > 0
        assert any("min_confidence" in e for e in errors)

    def test_validate_tenant_override_allows_hardening(self, service):
        """Tenant raising min_confidence above platform value must be accepted."""
        platform_rules = [
            {
                "rule_type": "decision_threshold",
                "is_locked": True,
                "body_json": {"min_confidence": 0.75},
            }
        ]
        tenant_rules = [
            {
                "rule_type": "decision_threshold",
                "body_json": {"min_confidence": 0.90},  # hardening = OK
            }
        ]
        errors = service.validate_tenant_override(tenant_rules, platform_rules)
        assert errors == []

    def test_validate_tenant_override_blocks_removing_blocked_attrs(self, service):
        """Tenant trying to remove a locked blocked attribute must be rejected."""
        platform_rules = [
            {
                "rule_type": "blocked_attribute",
                "is_locked": True,
                "body_json": {"attributes": ["gender", "raca"], "action": "reject_input"},
            }
        ]
        tenant_rules = [
            {
                "rule_type": "blocked_attribute",
                "body_json": {"attributes": ["gender"]},  # missing 'raca'
            }
        ]
        errors = service.validate_tenant_override(tenant_rules, platform_rules)
        assert len(errors) > 0
        assert any("raca" in e for e in errors)


class TestDefaultRules:
    def test_default_rules_all_have_required_fields(self):
        """DEFAULT_PLATFORM_GENERAL_RULES must all have required fields with correct types."""
        import sys
        import os
        project_root = os.environ.get("LIA_PROJECT_ROOT", "/home/runner/workspace/lia-agent-system")
        if project_root not in sys.path:
            sys.path.insert(0, project_root)

        from lia_models.fairness_policies import DEFAULT_PLATFORM_GENERAL_RULES, PolicyScope, PolicyRuleType

        valid_scopes = {s.value for s in PolicyScope}
        valid_rule_types = {r.value for r in PolicyRuleType}

        assert len(DEFAULT_PLATFORM_GENERAL_RULES) > 0, "DEFAULT_PLATFORM_GENERAL_RULES must not be empty"

        for i, rule in enumerate(DEFAULT_PLATFORM_GENERAL_RULES):
            prefix = f"Rule[{i}]"
            assert "scope" in rule, f"{prefix}: missing 'scope'"
            assert "rule_type" in rule, f"{prefix}: missing 'rule_type'"
            assert "body_json" in rule, f"{prefix}: missing 'body_json'"
            assert "is_locked" in rule, f"{prefix}: missing 'is_locked'"
            assert rule["scope"] in valid_scopes, f"{prefix}: invalid scope '{rule['scope']}'"
            assert rule["rule_type"] in valid_rule_types, f"{prefix}: invalid rule_type '{rule['rule_type']}'"
            assert isinstance(rule["body_json"], dict), f"{prefix}: body_json must be dict"
            assert isinstance(rule["is_locked"], bool), f"{prefix}: is_locked must be bool"
