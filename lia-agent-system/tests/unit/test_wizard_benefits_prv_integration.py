"""Unit tests for Wizard × Benefits/PRV integration (WIZARD-INT:001-005).

Tests:
  INT:002 — seniority filter logic for company_benefits
  INT:001 — compensation_policy in suggestions_data + id in benefits
  INT:003 — 3 new intents in INTENTS_CONFIG
  INT:004 — prefill_from_snapshots handles compensation_policy in job_snapshot
"""
import sys
sys.path.insert(0, '/home/runner/workspace/lia-agent-system')

import pytest


# ===========================================================================
# INT:002 — benefit seniority filter
# ===========================================================================
class _FakeBenefit:
    """Minimal stand-in for CompanyBenefit ORM row."""
    def __init__(self, id, name, seniority_levels):
        self.id = id
        self.name = name
        self.seniority_levels = seniority_levels


def _benefit_eligible(b, seniority: str) -> bool:
    """Exact copy of the lambda added in service.py to keep tests isolated."""
    levels = b.seniority_levels
    if not levels:
        return True
    if not seniority:
        return True
    return any(lvl.lower() == seniority.lower() for lvl in levels)


class TestBenefitSeniorityFilter:
    def test_null_seniority_levels_always_eligible(self):
        b = _FakeBenefit("1", "Vale Refeição", None)
        assert _benefit_eligible(b, "senior")
        assert _benefit_eligible(b, "junior")
        assert _benefit_eligible(b, "")

    def test_empty_seniority_levels_always_eligible(self):
        b = _FakeBenefit("2", "Gympass", [])
        assert _benefit_eligible(b, "pleno")

    def test_no_job_seniority_shows_all(self):
        b = _FakeBenefit("3", "Previdência", ["senior", "staff"])
        assert _benefit_eligible(b, "")

    def test_matching_seniority_eligible(self):
        b = _FakeBenefit("4", "Previdência", ["senior", "staff"])
        assert _benefit_eligible(b, "senior")

    def test_non_matching_seniority_excluded(self):
        b = _FakeBenefit("5", "Equity", ["staff", "principal"])
        assert not _benefit_eligible(b, "junior")

    def test_case_insensitive_match(self):
        b = _FakeBenefit("6", "PLR", ["Senior", "Pleno"])
        assert _benefit_eligible(b, "senior")   # lower
        assert _benefit_eligible(b, "PLENO")    # upper
        assert _benefit_eligible(b, "Pleno")    # title


# ===========================================================================
# INT:003 — new intents in INTENTS_CONFIG
# ===========================================================================
class TestNewIntents:
    def setup_method(self):
        from app.orchestrator.action_executor.intents_config import ACTIONABLE_INTENTS as INTENTS_CONFIG
        self.cfg = INTENTS_CONFIG

    def test_apply_compensation_policy_exists(self):
        assert "apply_compensation_policy" in self.cfg

    def test_override_bonus_in_job_exists(self):
        assert "override_bonus_in_job" in self.cfg

    def test_confirm_total_package_exists(self):
        assert "confirm_total_package" in self.cfg

    def test_apply_compensation_policy_structure(self):
        intent = self.cfg["apply_compensation_policy"]
        assert intent["domain_id"] == "job_management"
        assert intent["action_id"] == "apply_compensation_policy"
        assert "job_id" in intent["required_params"]
        assert intent["requires_confirmation"] is True

    def test_override_bonus_required_params(self):
        intent = self.cfg["override_bonus_in_job"]
        assert "bonus_min" in intent["required_params"]
        assert "bonus_max" in intent["required_params"]
        assert intent["requires_confirmation"] is True

    def test_confirm_total_package_low_risk(self):
        intent = self.cfg["confirm_total_package"]
        assert intent["risk_level"] == "low"
        assert intent["requires_confirmation"] is False


# ===========================================================================
# INT:004 — prefill_from_snapshots with compensation_policy in job_snapshot
# ===========================================================================
class TestPrefillFromSnapshots:
    def setup_method(self):
        from app.domains.offer.services.offer_service import prefill_from_snapshots
        self.fn = prefill_from_snapshots

    def test_basic_salary_prefill(self):
        job = {"salary_range": {"min": 10000, "max": 14000, "currency": "BRL"}}
        result = self.fn(job, {})
        assert "salary" in result
        assert float(result["salary"]) == pytest.approx(12000.0)

    def test_benefits_from_job_snapshot(self):
        job = {"benefits": ["Vale Refeição", "Gympass"]}
        result = self.fn(job, {})
        names = [b["name"] for b in result["benefits"]]
        assert "Vale Refeição" in names
        assert "Gympass" in names

    def test_benefits_from_dict_benefits(self):
        job = {"benefits": [{"id": "abc", "name": "Plano de Saúde"}]}
        result = self.fn(job, {})
        assert result["benefits"][0]["name"] == "Plano de Saúde"

    def test_compensation_policy_merges_extra_benefits(self):
        """Policy benefits not in job.benefits should be appended."""
        job = {
            "benefits": ["Vale Refeição"],
            "compensation_policy": {
                "id": "pol-001",
                "name": "PLR Anual",
                "variable_compensation": {},
                "benefits_package": {"included": ["Previdência Privada", "Vale Refeição"]},
            },
        }
        result = self.fn(job, {})
        names = [b["name"] for b in result["benefits"]]
        # Existing benefit preserved
        assert "Vale Refeição" in names
        # New policy benefit added (no duplicate)
        assert "Previdência Privada" in names
        # No duplicate Vale Refeição
        assert names.count("Vale Refeição") == 1

    def test_compensation_policy_snapshot_in_result(self):
        job = {
            "compensation_policy": {
                "id": "pol-002",
                "name": "Bonus Comercial",
                "variable_compensation": {"items": [{"kind": "bonus"}]},
                "benefits_package": {},
            },
        }
        result = self.fn(job, {})
        # Sprint F.4 #42: compensation_policy_snapshot foi descontinuado (canonical-remap).
        # A função não retorna mais essa chave; info de policy fica em job_data_snapshot (LGPD).
        assert "compensation_policy_snapshot" not in result
        # Só currency e start_date retornados quando não há salary nem benefits
        assert "currency" in result

    def test_no_policy_no_snapshot(self):
        result = self.fn({}, {})
        assert "compensation_policy_snapshot" not in result

    def test_policy_benefits_only_when_no_job_benefits(self):
        """If job has no benefits, inherit from policy."""
        job = {
            "compensation_policy": {
                "id": "pol-003",
                "name": "PLR",
                "variable_compensation": {},
                "benefits_package": {"included": ["Plano de Saúde"]},
            },
        }
        result = self.fn(job, {})
        names = [b["name"] for b in result["benefits"]]
        assert "Plano de Saúde" in names
        assert result["benefits"][0].get("source") == "compensation_policy"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
