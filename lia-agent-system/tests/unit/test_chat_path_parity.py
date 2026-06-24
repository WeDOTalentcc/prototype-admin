"""Tests for Phase 0-32: Chat Path Parity (GAP-00-001)."""
import subprocess
import sys
from pathlib import Path

import pytest

# tests/unit/test_chat_path_parity.py → parents[2] = lia-agent-system/
REPO_ROOT = Path(__file__).resolve().parents[2]
ORCH_PATH = REPO_ROOT / "app/orchestrator/execution/main_orchestrator.py"
CHAT_PATH = REPO_ROOT / "app/api/v1/chat.py"
SSE_PATH = REPO_ROOT / "app/api/v1/agent_chat_sse.py"
SCRIPTS_DIR = REPO_ROOT / "scripts"


# ── Sensor tests ──────────────────────────────────────────────────────────────

class TestParitySensor:
    """scripts/check_chat_path_parity.py — verifies all 3 paths have all 4 gates."""

    def test_sensor_script_exists(self):
        assert (SCRIPTS_DIR / "check_chat_path_parity.py").is_file()

    def test_sensor_exits_zero_clean(self):
        result = subprocess.run(
            ["python3", str(SCRIPTS_DIR / "check_chat_path_parity.py")],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        assert result.returncode == 0, f"Parity sensor found violations:\n{result.stdout}"

    def test_sensor_reports_zero_violations(self):
        result = subprocess.run(
            ["python3", str(SCRIPTS_DIR / "check_chat_path_parity.py"), "--json"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        import json
        data = json.loads(result.stdout)
        assert data["ok"] is True, f"Violations found: {data['violations']}"
        assert len(data["violations"]) == 0


# ── Gate presence: static source analysis ────────────────────────────────────

class TestChatLegacyGates:
    """chat.py (/stream + POST /chat) must have all 4 gates."""

    def _content(self):
        return CHAT_PATH.read_text()

    def test_fairness_guard_present(self):
        assert "FairnessGuard" in self._content()

    def test_fairness_log_check_present(self):
        assert "log_check" in self._content(), \
            "chat.py missing FairnessGuard.log_check() — audit trail absent"

    def test_daily_budget_present(self):
        content = self._content()
        assert any(s in content for s in ["check_budget", "budget_exhausted", "LIA-BUDGET"]), \
            "chat.py missing daily token budget check (GAP-00-001)"

    def test_lgpd_consent_present(self):
        content = self._content()
        assert any(s in content for s in [
            "consent_revoked", "ConsentCheckerService", "LIA-CONSENT", "check_candidate_consent",
        ]), "chat.py missing LGPD consent gate (GAP-00-001)"

    def test_budget_in_stream_endpoint(self):
        content = self._content()
        fg_idx = content.find("LIA-P01")
        budget_idx = content.find("LIA-BUDGET]")
        assert fg_idx > 0 and budget_idx > fg_idx, \
            "Budget check not found after FairnessGuard in /stream endpoint"

    def test_budget_in_rest_endpoint(self):
        assert "LIA-BUDGET-REST" in self._content(), \
            "Budget check missing from POST /chat REST endpoint"


class TestSseCanonicalGates:
    """agent_chat_sse.py must have all 4 gates."""

    def _content(self):
        return SSE_PATH.read_text()

    def test_fairness_guard_present(self):
        assert "FairnessGuard" in self._content()

    def test_fairness_log_check_present(self):
        assert "log_check" in self._content()

    def test_daily_budget_present(self):
        content = self._content()
        assert any(s in content for s in ["check_budget", "budget_exhausted"]), \
            "agent_chat_sse.py missing daily token budget check"

    def test_lgpd_consent_present(self):
        content = self._content()
        assert any(s in content for s in [
            "consent_blocked", "ConsentCheckerService", "check_candidate_consent",
        ]), "agent_chat_sse.py missing LGPD consent gate"


class TestMainOrchestratorGates:
    """main_orchestrator.py (supervisor) must have all 4 gates."""

    def _content(self):
        return ORCH_PATH.read_text()

    def test_fairness_guard_present(self):
        assert "FairnessGuard" in self._content()

    def test_fairness_log_check_present(self):
        assert "log_check" in self._content(), \
            "main_orchestrator.py missing FairnessGuard.log_check() — audit trail absent"

    def test_daily_budget_present(self):
        content = self._content()
        assert any(s in content for s in [
            "token_budget_gate", "check_budget", "LIA-BUDGET", "budget_exhausted",
        ]), "main_orchestrator.py missing daily token budget check (GAP-00-001)"

    def test_lgpd_consent_present(self):
        content = self._content()
        assert any(s in content for s in [
            "lgpd_consent_gate", "consent_revoked", "ConsentCheckerService",
        ]), "main_orchestrator.py missing LGPD consent gate (GAP-00-001)"

    def test_ai_credit_gate_preserved(self):
        """check_credit_budget (monthly AI credits) must NOT be removed."""
        assert "check_credit_budget" in self._content(), \
            "main_orchestrator.py: check_credit_budget removed — monthly AI credit gate broken"


# ── Parity completeness check ─────────────────────────────────────────────────

class TestParityCompleteness:
    """All 3 paths must have the same set of gates."""

    def test_all_three_paths_have_budget(self):
        """No path bypasses budget exhaustion."""
        for path, content in [
            ("chat_legacy", CHAT_PATH.read_text()),
            ("chat_sse", SSE_PATH.read_text()),
            ("main_orch", ORCH_PATH.read_text()),
        ]:
            has_budget = any(s in content for s in [
                "check_budget", "budget_exhausted", "token_budget_gate", "LIA-BUDGET",
            ])
            assert has_budget, f"Path {path} missing daily budget check — recruiter can bypass limit"

    def test_all_three_paths_have_fairness(self):
        """No path allows discriminatory queries through."""
        for path, content in [
            ("chat_legacy", CHAT_PATH.read_text()),
            ("chat_sse", SSE_PATH.read_text()),
            ("main_orch", ORCH_PATH.read_text()),
        ]:
            assert "FairnessGuard" in content, \
                f"Path {path} missing FairnessGuard — CLT Art.373-A not enforced"

    def test_all_three_paths_have_consent(self):
        """No path processes LGPD-revoked candidate data."""
        for path, content in [
            ("chat_legacy", CHAT_PATH.read_text()),
            ("chat_sse", SSE_PATH.read_text()),
            ("main_orch", ORCH_PATH.read_text()),
        ]:
            has_consent = any(s in content for s in [
                "consent_revoked", "ConsentCheckerService",
                "check_candidate_consent", "lgpd_consent_gate", "LIA-CONSENT",
            ])
            assert has_consent, \
                f"Path {path} missing LGPD consent gate — Art.7/18 not enforced"
