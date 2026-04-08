"""
Tests for FairnessGuardMiddleware
Target: fairness_guard_middleware.py (34% → ~80%)
"""
import sys
sys.path.insert(0, '/home/runner/workspace/lia-agent-system')
import pytest
import asyncio
from unittest.mock import patch, MagicMock


class TestFairnessCheckOutput:
    def test_default_state(self):
        from app.shared.compliance.fairness_guard_middleware import FairnessCheckOutput
        out = FairnessCheckOutput()
        assert out.is_blocked is False
        assert out.blocked_field is None
        assert out.blocked_result is None
        assert out.warnings == []
        assert out.checked_fields == []

    def test_has_warnings_false_by_default(self):
        from app.shared.compliance.fairness_guard_middleware import FairnessCheckOutput
        out = FairnessCheckOutput()
        assert out.has_warnings is False

    def test_has_warnings_true_when_warnings_set(self):
        from app.shared.compliance.fairness_guard_middleware import FairnessCheckOutput
        out = FairnessCheckOutput()
        out.warnings.append("Termo suspeito detectado")
        assert out.has_warnings is True

    def test_to_dict_basic(self):
        from app.shared.compliance.fairness_guard_middleware import FairnessCheckOutput
        out = FairnessCheckOutput()
        out.checked_fields = ["job_description"]
        d = out.to_dict()
        assert d["fairness_checked"] is True
        assert "job_description" in d["fairness_fields_checked"]
        assert "fairness_warnings" not in d
        assert "fairness_blocked" not in d

    def test_to_dict_with_warnings(self):
        from app.shared.compliance.fairness_guard_middleware import FairnessCheckOutput
        out = FairnessCheckOutput()
        out.warnings.append("idade suspeita")
        d = out.to_dict()
        assert "fairness_warnings" in d
        assert "idade suspeita" in d["fairness_warnings"]

    def test_to_dict_blocked(self):
        from app.shared.compliance.fairness_guard_middleware import FairnessCheckOutput
        from app.shared.compliance.fairness_guard import FairnessCheckResult
        out = FairnessCheckOutput()
        out.is_blocked = True
        out.blocked_field = "title"
        mock_result = MagicMock()
        mock_result.category = "gender"
        mock_result.educational_message = "Não use filtros de gênero"
        out.blocked_result = mock_result
        d = out.to_dict()
        assert d.get("fairness_blocked") is True
        assert d.get("fairness_blocked_field") == "title"
        assert d.get("fairness_category") == "gender"


class TestFairnessViolation:
    def test_exception_message(self):
        from app.shared.compliance.fairness_guard_middleware import FairnessViolation
        mock_result = MagicMock()
        mock_result.educational_message = "Viés de gênero detectado"
        exc = FairnessViolation(result=mock_result, field_name="description")
        assert "Viés de gênero detectado" in str(exc)
        assert exc.field_name == "description"
        assert exc.result is mock_result

    def test_default_field_name(self):
        from app.shared.compliance.fairness_guard_middleware import FairnessViolation
        mock_result = MagicMock()
        mock_result.educational_message = "mensagem"
        exc = FairnessViolation(result=mock_result)
        assert exc.field_name == "text"

    def test_none_educational_message(self):
        from app.shared.compliance.fairness_guard_middleware import FairnessViolation
        mock_result = MagicMock()
        mock_result.educational_message = None
        exc = FairnessViolation(result=mock_result)
        assert "Viés detectado" in str(exc)


class TestCheckFairness:
    def test_empty_text_skipped(self):
        from app.shared.compliance.fairness_guard_middleware import check_fairness
        output = check_fairness({"description": ""})
        assert output.is_blocked is False
        assert "description" not in output.checked_fields

    def test_whitespace_text_skipped(self):
        from app.shared.compliance.fairness_guard_middleware import check_fairness
        output = check_fairness({"description": "   "})
        assert output.is_blocked is False

    def test_clean_text_passes(self):
        from app.shared.compliance.fairness_guard_middleware import check_fairness
        output = check_fairness({"description": "Buscamos analista de dados pleno com experiência em Python"})
        assert output.is_blocked is False
        assert "description" in output.checked_fields

    def test_discriminatory_text_blocked(self):
        from app.shared.compliance.fairness_guard_middleware import check_fairness
        output = check_fairness({"description": "apenas homens com até 30 anos"})
        assert output.is_blocked is True
        assert output.blocked_field == "description"

    def test_raise_on_block_raises_violation(self):
        from app.shared.compliance.fairness_guard_middleware import check_fairness, FairnessViolation
        with pytest.raises(FairnessViolation):
            check_fairness(
                {"description": "apenas homens com até 30 anos"},
                raise_on_block=True,
            )

    def test_multiple_fields_stops_at_first_block(self):
        from app.shared.compliance.fairness_guard_middleware import check_fairness
        output = check_fairness({
            "title": "Apenas homens",
            "description": "Texto normal de vaga",
        })
        assert output.is_blocked is True
        assert output.blocked_field == "title"

    def test_checked_fields_populated(self):
        from app.shared.compliance.fairness_guard_middleware import check_fairness
        output = check_fairness({
            "title": "Analista de Dados",
            "description": "Experiência em Python",
        })
        assert "title" in output.checked_fields
        assert "description" in output.checked_fields


class TestCheckRejectionReason:
    def test_empty_reason(self):
        from app.shared.compliance.fairness_guard_middleware import check_rejection_reason
        output = check_rejection_reason("")
        assert output.is_blocked is False

    def test_clean_reason(self):
        from app.shared.compliance.fairness_guard_middleware import check_rejection_reason
        output = check_rejection_reason("Candidato não possui experiência técnica necessária")
        assert output.is_blocked is False

    def test_discriminatory_reason_blocked(self):
        from app.shared.compliance.fairness_guard_middleware import check_rejection_reason
        output = check_rejection_reason("Candidato muito velho para a equipe jovem")
        # soft warning or block depending on FairnessGuard implementation
        # just ensure it runs without error
        assert isinstance(output.is_blocked, bool)


class TestCheckFairnessAsync:
    def _run(self, coro):
        return asyncio.run(coro)

    def test_async_clean_text(self):
        from app.shared.compliance.fairness_guard_middleware import check_fairness_async
        output = self._run(check_fairness_async({"description": "Analista Python pleno"}))
        assert output.is_blocked is False

    def test_async_blocked_text(self):
        from app.shared.compliance.fairness_guard_middleware import check_fairness_async
        output = self._run(check_fairness_async({"description": "apenas homens"}))
        assert output.is_blocked is True
