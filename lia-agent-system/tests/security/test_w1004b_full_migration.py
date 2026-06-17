"""
W1-004-B Full Migration Regression Suite
Verifies that all 3 tool_registry files have zero SQL inline blocks.
This is the BLOCKING sentinel for ADR-001 compliance in agents/.
"""
import re
from pathlib import Path

TOOL_REGISTRIES = [
    "app/domains/recruiter_assistant/agents/kanban_tool_registry.py",
    "app/domains/recruiter_assistant/agents/jobs_mgmt_tool_registry.py",
    "app/domains/recruiter_assistant/agents/talent_tool_registry.py",
]

ROOT = Path(__file__).resolve().parents[2]  # lia-agent-system/


def test_zero_sql_inline_all_registries():
    """No text(\"\"\" blocks in any of the 3 migrated registries."""
    for path_str in TOOL_REGISTRIES:
        path = ROOT / path_str
        assert path.exists(), f"Expected file not found: {path}"
        content = path.read_text()
        matches = re.findall(r'text\("""', content)
        assert len(matches) == 0, (
            f"{path_str}: {len(matches)} SQL inline blocks found. "
            "W1-004-B regression: file was migrated and must stay clean."
        )


def test_zero_fstring_sql_all_registries():
    """No text(f\"\"\" f-string SQL injection vectors."""
    for path_str in TOOL_REGISTRIES:
        path = ROOT / path_str
        content = path.read_text()
        matches = re.findall(r'text\(f"""', content)
        assert len(matches) == 0, (
            f"{path_str}: f-string SQL found. "
            "F-string SQL is an injection vector — use parameterized queries."
        )


def test_no_cross_tenant_bypass_pattern():
    """No ':cid = \\'\\'' cross-tenant bypass in any registry."""
    for path_str in TOOL_REGISTRIES:
        path = ROOT / path_str
        content = path.read_text()
        bypass_patterns = [":cid = ''", "= '' OR", "OR '' ="]
        for pattern in bypass_patterns:
            assert pattern not in content, (
                f"{path_str}: cross-tenant bypass pattern found: {pattern!r}. "
                "This was the P0 security issue fixed in W1-004-B commit 1 (ffc553046)."
            )


def test_no_db_execute_text_all_registries():
    """No db.execute(text(...)) raw SQL pattern in any migrated registry."""
    for path_str in TOOL_REGISTRIES:
        path = ROOT / path_str
        content = path.read_text()
        # Matches db.execute(text( or session.execute(text(
        matches = re.findall(r'\b(?:db|session)\.execute\s*\(\s*text\s*\(', content)
        assert len(matches) == 0, (
            f"{path_str}: {len(matches)} db/session.execute(text(...)) calls found. "
            "Use repository methods instead per ADR-001."
        )


def test_all_registries_exist():
    """All 3 migrated registry files exist at expected paths."""
    for path_str in TOOL_REGISTRIES:
        path = ROOT / path_str
        assert path.exists(), (
            f"Registry file missing: {path_str}. "
            "W1-004-B migration expects this file to exist."
        )
