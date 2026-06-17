"""
D3 — Bias Audit: Disparate Impact (Segunda Métrica EEOC)
Testa chi-square, p-value, eeoc_compliant flag e persistência no snapshot.
"""
import pytest
from unittest.mock import MagicMock, patch


class TestChiSquareTest:

    def test_chi_square_with_two_groups_significant(self):
        """Chi-square detecta diferença significativa entre dois grupos."""
        from app.shared.services.bias_audit_service import _chi_square_test

        groups = {
            "masculino": {"count": 100, "approved": 80, "rate": 0.80},
            "feminino": {"count": 100, "approved": 40, "rate": 0.40},
        }
        result = _chi_square_test(groups)
        assert "chi2" in result
        assert "p_value" in result
        assert "significant" in result
        assert result["chi2"] > 0
        assert result["p_value"] < 0.05
        assert result["significant"] is True

    def test_chi_square_with_equal_groups_not_significant(self):
        """Chi-square não detecta diferença quando grupos são iguais."""
        from app.shared.services.bias_audit_service import _chi_square_test

        groups = {
            "masculino": {"count": 50, "approved": 25, "rate": 0.50},
            "feminino": {"count": 50, "approved": 25, "rate": 0.50},
        }
        result = _chi_square_test(groups)
        assert result["significant"] is False
        assert result["p_value"] >= 0.05

    def test_chi_square_single_group_returns_not_significant(self):
        """Apenas 1 grupo: sem teste possível."""
        from app.shared.services.bias_audit_service import _chi_square_test

        groups = {"masculino": {"count": 50, "approved": 25, "rate": 0.50}}
        result = _chi_square_test(groups)
        assert result["significant"] is False
        assert result["p_value"] == 1.0

    def test_chi_square_without_scipy_uses_python_fallback(self):
        """Sem scipy, usa implementação Python pura (available=True, sem erro)."""
        from app.services import bias_audit_service as mod

        groups = {
            "a": {"count": 50, "approved": 40, "rate": 0.80},
            "b": {"count": 50, "approved": 10, "rate": 0.20},
        }
        with patch.object(mod, "_SCIPY_AVAILABLE", False):
            result = mod._chi_square_test(groups)

        assert result["available"] is True
        assert result["chi2"] > 0
        assert result["significant"] is True  # diferença grande → significativa


class TestEeocCompliant:

    def test_eeoc_compliant_when_ratio_ok_and_not_significant(self):
        """eeoc_compliant=True quando ratio >= 0.80 e não significativo."""
        from app.shared.services.bias_audit_service import _audit_dimension
        from unittest.mock import MagicMock

        evals = []
        for i in range(10):
            ev = MagicMock(); ev.score = 75.0
            cand = MagicMock(); cand.gender = "masculino"
            evals.append((ev, cand))
        for i in range(10):
            ev = MagicMock(); ev.score = 70.0
            cand = MagicMock(); cand.gender = "feminino"
            evals.append((ev, cand))

        result = _audit_dimension(evals, "gender", lambda c: c.gender)
        # ratio = 1.0 (ambos aprovam 100%) — eeoc_compliant deve ser True
        assert result.eeoc_compliant is True

    def test_eeoc_not_compliant_when_ratio_below_threshold(self):
        """eeoc_compliant=False quando ratio < 0.80."""
        from app.shared.services.bias_audit_service import _audit_dimension
        from unittest.mock import MagicMock

        evals = []
        for _ in range(20):
            ev = MagicMock(); ev.score = 80.0
            cand = MagicMock(); cand.gender = "masculino"
            evals.append((ev, cand))
        for _ in range(20):
            ev = MagicMock(); ev.score = 30.0  # reprovado
            cand = MagicMock(); cand.gender = "feminino"
            evals.append((ev, cand))

        result = _audit_dimension(evals, "gender", lambda c: c.gender)
        assert result.adverse_impact_ratio < 0.80
        assert result.eeoc_compliant is False


class TestSnapshotPersistsDisparateImpact:

    def test_save_snapshot_includes_disparate_impact(self):
        """save_snapshot inclui disparate_impact e eeoc_compliant em dimensions_json."""
        from app.shared.services.bias_audit_service import BiasAuditReport, DemographicAuditResult, BiasAuditService
        import json

        dim = DemographicAuditResult(
            dimension="gender",
            groups={"m": {"count": 10, "approved": 8, "rate": 0.8}},
            adverse_impact_ratio=1.0,
            below_threshold=False,
            alert_level="ok",
            disparate_impact={"chi2": 0.5, "p_value": 0.48, "significant": False, "available": True},
            eeoc_compliant=True,
        )
        report = BiasAuditReport(
            job_id="job-1",
            evaluated_at=__import__("datetime").datetime.utcnow(),
            total_candidates=10,
            dimensions=[dim],
            has_alerts=False,
        )

        import uuid
        service = BiasAuditService()
        captured = {}

        class FakeDb:
            def add(self, obj):
                captured["snapshot"] = obj
            async def flush(self):
                pass

        import asyncio
        asyncio.run(service.save_snapshot(FakeDb(), uuid.uuid4(), report))

        snap = captured["snapshot"]
        dims = json.loads(snap.dimensions_json)
        assert "disparate_impact" in dims[0]
        assert "eeoc_compliant" in dims[0]
        assert dims[0]["eeoc_compliant"] is True
