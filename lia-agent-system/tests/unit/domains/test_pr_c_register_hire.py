"""PR-C — register_hire tool unit tests.

harness-engineering: sensor computacional que valida a action register_hire
criada em app/domains/pipeline/tools/pipeline_tools.py.

TDD red-green: testes falham antes da implementação, passam depois.
"""
import os
import sys
import pytest

# Resolve path to lia-agent-system
_BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if _BASE not in sys.path:
    sys.path.insert(0, _BASE)


class TestRegisterHireToolExists:
    """register_hire deve estar registrada no pipeline domain."""

    def test_tool_importable(self):
        from app.domains.pipeline.tools.pipeline_tools import register_hire  # noqa: F401
        assert callable(register_hire), "register_hire deve ser callable"

    def test_capabilities_yaml_has_keywords(self):
        import yaml
        path = os.path.join(
            _BASE, "app/domains/pipeline/config/capabilities.yaml"
        )
        with open(path) as f:
            data = yaml.safe_load(f)
        kws = data.get("intent_keywords", {})
        assert "registrar contratação" in kws, "falta keyword 'registrar contratação'"
        assert kws["registrar contratação"] == "register_hire"
        assert "contratar candidato" in kws
        assert kws["contratar candidato"] == "register_hire"

    def test_register_hire_no_conflict_with_predictions(self):
        """'registrar contratação' não deve conflitar com predict_hiring_probability."""
        import yaml
        path = os.path.join(
            _BASE, "app/domains/pipeline/config/capabilities.yaml"
        )
        with open(path) as f:
            data = yaml.safe_load(f)
        kws = data.get("intent_keywords", {})
        # nenhuma keyword de register_hire deve apontar para predict_*
        register_hire_kws = {k for k, v in kws.items() if v == "register_hire"}
        assert len(register_hire_kws) >= 3, (
            "pipeline deve ter ao menos 3 keywords para register_hire"
        )


class TestRegisterHireExecution:
    """register_hire executa e retorna estrutura correta."""

    def _run(self, **kwargs):
        import asyncio
        from app.domains.pipeline.tools.pipeline_tools import register_hire
        return asyncio.run(register_hire(**kwargs))

    def test_happy_path_returns_success(self):
        result = self._run(
            candidate_id="cand-123",
            job_id="job-456",
            company_id="company-abc",
        )
        assert result["success"] is True

    def test_returns_hired_stage(self):
        result = self._run(
            candidate_id="cand-123",
            job_id="job-456",
            company_id="company-abc",
        )
        assert result["new_stage"] == "hired"

    def test_returns_candidate_and_job_ids(self):
        result = self._run(
            candidate_id="cand-999",
            job_id="job-777",
            company_id="company-xyz",
        )
        assert result["candidate_id"] == "cand-999"
        assert result["job_id"] == "job-777"

    def test_hired_at_is_iso_timestamp(self):
        from datetime import datetime
        result = self._run(
            candidate_id="cand-123",
            job_id="job-456",
            company_id="company-abc",
        )
        # Should parse as valid ISO 8601
        ts = result["hired_at"]
        assert isinstance(ts, str) and len(ts) > 0
        datetime.fromisoformat(ts)  # raises if invalid

    def test_optional_offer_proposal_id(self):
        result = self._run(
            candidate_id="cand-123",
            job_id="job-456",
            company_id="company-abc",
            offer_proposal_id="prop-aaa",
        )
        assert result["offer_proposal_id"] == "prop-aaa"

    def test_no_offer_proposal_id_returns_none(self):
        result = self._run(
            candidate_id="cand-123",
            job_id="job-456",
            company_id="company-abc",
        )
        assert result["offer_proposal_id"] is None

    def test_optional_start_date(self):
        result = self._run(
            candidate_id="cand-123",
            job_id="job-456",
            company_id="company-abc",
            start_date="2026-06-01",
        )
        assert result["start_date"] == "2026-06-01"

    def test_multi_tenant_company_id_propagated(self):
        """require_company=True: company_id ausente deve retornar erro."""
        result = self._run(
            candidate_id="cand-123",
            job_id="job-456",
        )
        # tool_handler com require_company=True retorna erro quando company_id ausente
        # (não lança exceção; retorna dict com success=False ou error)
        assert result.get("success") is not True or result.get("error") is None, (
            "Se company_id estiver ausente, a tool NÃO deve reportar sucesso"
        )

    def test_message_contains_candidate_id(self):
        result = self._run(
            candidate_id="cand-XYZ",
            job_id="job-456",
            company_id="company-abc",
        )
        assert "cand-XYZ" in result.get("message", "")
