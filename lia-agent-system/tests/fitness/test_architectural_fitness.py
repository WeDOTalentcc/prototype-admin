"""
Architectural Fitness Functions — enforce structural invariants in CI.

These tests run on every PR and block merge if violated. They protect
consolidation decisions made in Sprint 3-5 (P35 items) from regression.

Baseline (2026-04-14): All 6 tests expected to pass after Sprint 3-5 work.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

# Root of the backend codebase
_ROOT = Path(__file__).resolve().parent.parent.parent  # lia-agent-system/
_APP = _ROOT / "app"
_CONFIG = _APP / "config"
_PROMPTS = _APP / "prompts"
_LIBS = _ROOT / "libs"


def _all_py_files(*dirs: Path) -> list[Path]:
    """Collect all .py files under given directories."""
    files = []
    for d in dirs:
        if d.exists():
            files.extend(d.rglob("*.py"))
    return files


# ────────────────────────────────────────────────────────────────────
# 1. No inline system prompts outside prompt directories
# ────────────────────────────────────────────────────────────────────

# Directories where system prompt text IS allowed
_PROMPT_ALLOWED_DIRS = {
    str(_PROMPTS),
    str(_CONFIG),
    str(_APP / "shared" / "prompts"),
    str(_APP / "domains" / "compliance_base.py"),  # fallback strings
}

# Patterns that indicate an inline system prompt
_INLINE_PROMPT_PATTERNS = [
    re.compile(r'""".*Você é (um|uma|meu|o|a) ', re.DOTALL),
    re.compile(r'""".*You are (a|an|my|the) (senior|expert|specialist)', re.DOTALL),
    re.compile(r"SYSTEM_PROMPT\s*=\s*f?\"\"\"", re.MULTILINE),
]


class TestNoInlineSystemPrompts:
    """System prompts must live in prompt files, not scattered in service code."""

    def _is_in_allowed_dir(self, path: Path) -> bool:
        path_str = str(path)
        # Allow prompt files and system_prompt files
        if "system_prompt" in path.name or "prompts" in path.name:
            return True
        if "interaction_patterns" in path.name:
            return True
        for allowed in _PROMPT_ALLOWED_DIRS:
            if path_str.startswith(allowed):
                return True
        return False

    def test_no_inline_system_prompts(self):
        """No inline system prompt strings outside designated prompt directories."""
        violations = []
        for py_file in _all_py_files(_APP / "services", _APP / "api", _APP / "jobs"):
            if self._is_in_allowed_dir(py_file):
                continue
            try:
                content = py_file.read_text(errors="ignore")
            except Exception:
                continue
            for pattern in _INLINE_PROMPT_PATTERNS:
                if pattern.search(content):
                    violations.append(str(py_file.relative_to(_ROOT)))
                    break

        assert not violations, (
            f"Inline system prompts found in {len(violations)} file(s). "
            f"Move to app/prompts/ or *_system_prompt.py:\n"
            + "\n".join(f"  - {v}" for v in violations)
        )


# ────────────────────────────────────────────────────────────────────
# 2. Protected attributes only in canonical YAML
# ────────────────────────────────────────────────────────────────────

_YAML_CANONICAL = _CONFIG / "protected_attributes.yaml"

# Pattern: Python list/set with 4+ protected attribute names
_HARDCODED_ATTRS_PATTERN = re.compile(
    r'(?:frozenset|set|\[|\{)\s*\(\s*\{?\s*["\']'
    r'(?:gender|genero|race|raca|disability|deficiencia|religion|religiao'
    r'|age|idade|ethnicity|etnia|marital|estado_civil|nationality|nacionalidade)'
    r'["\']',
    re.IGNORECASE,
)


class TestProtectedAttributesSSoT:
    """Protected attribute lists must come from config/protected_attributes.yaml."""

    def test_no_hardcoded_attribute_lists(self):
        """No hardcoded protected attribute lists outside the canonical YAML."""
        violations = []
        for py_file in _all_py_files(_APP, _LIBS):
            # Allow the YAML loader itself and the fallback in fairness_guard
            if "protected_attributes.py" in py_file.name:
                continue
            if "test_" in py_file.name:
                continue
            try:
                content = py_file.read_text(errors="ignore")
            except Exception:
                continue
            # Skip if it's a known fallback (fairness_guard has documented fallback)
            if "fairness_guard.py" in py_file.name and "# Fallback if YAML not available" in content:
                continue
            if _HARDCODED_ATTRS_PATTERN.search(content):
                violations.append(str(py_file.relative_to(_ROOT)))

        assert not violations, (
            f"Hardcoded protected attribute lists in {len(violations)} file(s). "
            f"Import from app.shared.compliance.protected_attributes instead:\n"
            + "\n".join(f"  - {v}" for v in violations)
        )


# ────────────────────────────────────────────────────────────────────
# 3. No PII in log statements
# ────────────────────────────────────────────────────────────────────

_PII_IN_LOG_PATTERN = re.compile(
    r'(?:logger\.\w+|logging\.\w+|print)\s*\('
    r'[^)]*'
    r'(?:\.email[^_\.]|\.cpf[^_\.]|\.phone[^_\.]|\.mobile_phone|\.secondary_phone'
    r'|\.full_name|\.nome_completo|candidate_email=|candidate_phone=)',
    re.IGNORECASE,
)

# Allowlist: files where PII in logs is intentional (masking, test, audit)
_PII_LOG_ALLOWLIST = {
    "pii_masking.py",
    "test_",
    "consent_gate.py",  # audit logging
    "lgpd_cleanup_service.py",  # deletion logging
}


class TestNoPIIInLogs:
    """Log statements must not contain raw PII fields."""

    def test_no_pii_in_logs(self):
        """No candidate email, CPF, phone, or full name in logger/print calls."""
        violations = []
        for py_file in _all_py_files(_APP):
            if any(allow in py_file.name for allow in _PII_LOG_ALLOWLIST):
                continue
            try:
                content = py_file.read_text(errors="ignore")
            except Exception:
                continue
            for i, line in enumerate(content.splitlines(), 1):
                if _PII_IN_LOG_PATTERN.search(line):
                    violations.append(f"{py_file.relative_to(_ROOT)}:{i}")

        assert not violations, (
            f"PII in log statements ({len(violations)} occurrences). "
            f"Use PII masking or log candidate_id instead:\n"
            + "\n".join(f"  - {v}" for v in violations[:20])
        )


# ────────────────────────────────────────────────────────────────────
# 4. Compliance blocks loaded from YAML
# ────────────────────────────────────────────────────────────────────

class TestComplianceBlocksFromYAML:
    """Compliance blocks must be loaded from YAML, not hardcoded."""

    def test_compliance_base_loads_yaml(self):
        """compliance_base.py loads from compliance_block.yaml."""
        cb_file = _APP / "domains" / "compliance_base.py"
        content = cb_file.read_text()
        assert "compliance_block.yaml" in content, (
            "compliance_base.py does not reference compliance_block.yaml"
        )
        assert "guardrails_block.yaml" in content, (
            "compliance_base.py does not reference guardrails_block.yaml"
        )

    def test_yaml_files_exist(self):
        """Canonical YAML files exist."""
        compliance = _APP / "prompts" / "shared" / "compliance_block.yaml"
        guardrails = _APP / "prompts" / "shared" / "guardrails_block.yaml"
        protected = _CONFIG / "protected_attributes.yaml"
        fairness_pc = _CONFIG / "fairness_post_check.yaml"

        for path in [compliance, guardrails, protected, fairness_pc]:
            assert path.exists(), f"Missing canonical YAML: {path.relative_to(_ROOT)}"


# ────────────────────────────────────────────────────────────────────
# 5. All ReAct agents have max_iterations
# ────────────────────────────────────────────────────────────────────

_MAX_ITER_PATTERN = re.compile(r"max_iterations|recursion_limit|max_steps", re.IGNORECASE)


class TestReActAgentsHaveMaxIterations:
    """Every ReAct agent must have a configured iteration limit."""

    def test_all_agents_have_max_iterations(self):
        """ReAct agents must configure max_iterations to prevent infinite loops."""
        agents_dir = _APP / "domains"
        violations = []
        for py_file in agents_dir.rglob("*_react_agent.py"):
            try:
                content = py_file.read_text(errors="ignore")
            except Exception:
                continue
            if "class " in content and "ReAct" in content:
                if not _MAX_ITER_PATTERN.search(content):
                    violations.append(str(py_file.relative_to(_ROOT)))

        assert not violations, (
            f"{len(violations)} ReAct agent(s) without max_iterations:\n"
            + "\n".join(f"  - {v}" for v in violations)
        )


# ────────────────────────────────────────────────────────────────────
# 6. Consent check before communication
# ────────────────────────────────────────────────────────────────────

class TestConsentCheckBeforeCommunication:
    """Communication service must check consent before sending."""

    def test_validate_can_send_checks_consent(self):
        """validate_can_send() in CommunicationService calls consent gate."""
        comm_svc = _APP / "domains" / "communication" / "services" / "communication_service.py"
        content = comm_svc.read_text()
        assert "consent_gate" in content.lower() or "CommunicationConsentGate" in content, (
            "CommunicationService.validate_can_send() does not reference consent gate. "
            "LGPD requires consent check before any outbound communication."
        )

    def test_consent_gate_module_exists(self):
        """The consent_gate.py module exists in communication services."""
        gate = _APP / "domains" / "communication" / "services" / "consent_gate.py"
        assert gate.exists(), "consent_gate.py not found — LGPD consent enforcement missing"

    def test_consent_gate_is_fail_closed(self):
        """ConsentCheckerService uses fail-closed on errors."""
        checker = _APP / "domains" / "lgpd" / "services" / "consent_checker_service.py"
        content = checker.read_text()
        assert "allowed=False" in content and "check_error" in content, (
            "ConsentCheckerService exception handler must be fail-closed (allowed=False on error)"
        )
