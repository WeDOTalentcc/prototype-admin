"""
Sensor tests: wizard panel resilience — defects #1 and #8.

#1: payload fallback must never produce empty dict (panel disappears).
#8: navigation intent must not fire mid-wizard (FE guard).
"""
import ast
import re


# ─── Defect #1: payload fallback resilience ──────────────────────────

SERVICE_PATH = (
    "/home/runner/workspace/lia-agent-system/app/domains/job_creation/"
    "services/wizard_session_service.py"
)


class TestWizardPayloadFallbackResilience:
    """Prevent regression of defect #1: panel disappears after payload build failure."""

    def test_no_empty_dict_in_except_block(self):
        """payload = {} in except block is FORBIDDEN — empty dict is falsy,
        SSE handler skips panel_update, panel disappears."""
        with open(SERVICE_PATH) as f:
            tree = ast.parse(f.read())

        for node in ast.walk(tree):
            if not isinstance(node, ast.ExceptHandler):
                continue
            for child in ast.walk(node):
                if isinstance(child, ast.Assign):
                    for target in child.targets:
                        if isinstance(target, ast.Name) and target.id == "payload":
                            if isinstance(child.value, ast.Dict) and not child.value.keys:
                                raise AssertionError(
                                    f"line {child.lineno}: payload = {{}} in except block. "
                                    f"Fix: build minimal valid payload with stage + data.message."
                                )

    def test_fallback_payload_has_wizard_stage_type(self):
        """Fallback payload must include 'wizard_stage' type for SSE handler recognition."""
        with open(SERVICE_PATH) as f:
            source = f.read()

        # Find except blocks related to payload build
        in_except = False
        found_wizard_stage = False
        for line in source.split("\n"):
            if "except Exception" in line and "BLE001" in line and "best-effort" in line:
                in_except = True
                continue
            if in_except:
                if "wizard_stage" in line:
                    found_wizard_stage = True
                    break
                # Exit except block when indentation drops
                if line.strip() and not line.startswith(" " * 12) and not line.startswith(" " * 8 + "#"):
                    if not line.startswith(" " * 8 + " "):
                        in_except = False

        assert found_wizard_stage, (
            "Except block for payload build must produce payload with "
            "'wizard_stage' type — otherwise SSE handler skips emission."
        )

    def test_fallback_payload_includes_stage_variable(self):
        """Fallback payload must reference the 'stage' variable for correct panel routing."""
        with open(SERVICE_PATH) as f:
            source = f.read()

        # The fallback should reference the already-derived stage variable
        in_except = False
        for line in source.split("\n"):
            if "except Exception" in line and "BLE001" in line and "best-effort" in line:
                in_except = True
                continue
            if in_except:
                if '"stage": stage' in line or "'stage': stage" in line:
                    return  # PASS
                if line.strip() and not line.startswith(" " * 8):
                    in_except = False

        raise AssertionError(
            "Fallback payload must reference 'stage' variable "
            "(derived before the try block) for correct panel routing."
        )


# ─── Defect #8: navigation intent wizard guard ──────────────────────

FE_PATH = (
    "/home/runner/workspace/plataforma-lia/src/components/"
    "unified-chat/UnifiedChat.tsx"
)


class TestNavigationIntentWizardGuard:
    """Prevent regression of defect #8: navigation deflection mid-wizard."""

    def test_nav_intent_guarded_by_dynamic_panel(self):
        """detectNavIntent must be guarded by !dynamicPanel check."""
        with open(FE_PATH) as f:
            source = f.read()

        # Find the detectNavIntent call and check it's guarded
        lines = source.split("\n")
        for i, line in enumerate(lines):
            if "detectNavIntent(text)" in line and ".then" in line:
                # Check this line or the preceding 2 lines for dynamicPanel guard
                context = "\n".join(lines[max(0, i - 2) : i + 1])
                assert "dynamicPanel" in context, (
                    f"Line {i + 1}: detectNavIntent(text) called without "
                    f"dynamicPanel guard — navigation will fire mid-wizard."
                )
                return

        raise AssertionError("detectNavIntent(text).then(...) not found in UnifiedChat.tsx")


# ─── Markdown suppression guide (system prompt) ─────────────────────

ORCHESTRATOR_PATH = (
    "/home/runner/workspace/lia-agent-system/app/domains/job_creation/"
    "orchestrator/wizard_orchestrator.py"
)


class TestMarkdownSuppressionGuide:
    """Sensor: system prompt must instruct LLM to NOT duplicate tool data as markdown."""

    def test_prompt_contains_cards_inline_section(self):
        """The 'cards inline' formatting section must exist in _SYSTEM_PROMPT_BASE."""
        with open(ORCHESTRATOR_PATH) as f:
            source = f.read()
        assert "cards inline" in source, (
            "_SYSTEM_PROMPT_BASE must contain 'cards inline' formatting section. "
            "Fix: add the markdown suppression guide to the system prompt."
        )

    def test_prompt_forbids_markdown_tables(self):
        """Prompt must explicitly forbid repeating tool data as markdown tables."""
        with open(ORCHESTRATOR_PATH) as f:
            source = f.read()
        assert "tabela markdown" in source.lower() or "NUNCA repita" in source, (
            "_SYSTEM_PROMPT_BASE must forbid markdown table duplication. "
            "Fix: add 'NUNCA repita os dados da tool como tabela markdown' rule."
        )

    def test_prompt_has_per_stage_suppression(self):
        """Prompt must have specific suppression rules for competencies, JD, and salary."""
        with open(ORCHESTRATOR_PATH) as f:
            source = f.read()
        for stage_keyword in ["competências", "JD", "salário"]:
            assert stage_keyword.lower() in source.lower(), (
                f"_SYSTEM_PROMPT_BASE must mention '{stage_keyword}' in "
                f"the markdown suppression section. Fix: add per-stage rule."
            )

    def test_prompt_has_exception_for_explicit_request(self):
        """Prompt must allow listing data when the recruiter explicitly asks."""
        with open(ORCHESTRATOR_PATH) as f:
            source = f.read()
        assert "PEDIR explicitamente" in source or "pedir explicitamente" in source.lower(), (
            "_SYSTEM_PROMPT_BASE must include exception clause for explicit requests. "
            "Fix: add 'se o recrutador PEDIR explicitamente' escape hatch."
        )
