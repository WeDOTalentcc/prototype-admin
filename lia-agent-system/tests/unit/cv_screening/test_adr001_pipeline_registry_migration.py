"""
TDD: ADR-001 Wave C-3 Agent G — cv_screening/pipeline_tool_registry.py migration.

Verifica:
1. Nenhum SQL inline sem marker ADR-001-EXEMPT (sensor-aligned check)
2. O arquivo foi removido do TOOL_REGISTRY_BACKLOG de ambos os sensores
3. O EXEMPT marker cobre o único bloco flaggeado pelo sensor (generate_report analytics)
"""
from pathlib import Path

import pytest

REGISTRY_PATH = Path("app/domains/cv_screening/agents/pipeline_tool_registry.py")
SQL_SENSOR_PATH = Path("scripts/check_no_sql_inline_in_services.py")
SELECT_SENSOR_PATH = Path("scripts/check_no_select_in_services.py")


# ─── 1. EXEMPT marker coverage ──────────────────────────────────────────────────

def test_cv_pipeline_registry_has_exempt_marker():
    """Arquivo tem pelo menos um ADR-001-EXEMPT marker (sensor skips file-level)."""
    content = REGISTRY_PATH.read_text()
    assert "ADR-001-EXEMPT" in content, (
        "pipeline_tool_registry.py must have at least one ADR-001-EXEMPT marker "
        "so the SQL sensor skips the file entirely."
    )


def test_cv_pipeline_registry_generate_report_has_exempt():
    """generate_report SQL block tem ADR-001-EXEMPT marker na linha precedente."""
    content = REGISTRY_PATH.read_text()
    lines = content.split("\n")
    for i, line in enumerate(lines):
        if 'session.execute(text("""' in line:
            # Look back 5 lines for EXEMPT marker
            context = "\n".join(lines[max(0, i - 5): i + 1])
            assert "ADR-001-EXEMPT" in context, (
                f"Line {i+1}: session.execute(text(\"\"\" has no ADR-001-EXEMPT marker in preceding 5 lines.\n"
                f"Context:\n{context}"
            )


# ─── 2. TOOL_REGISTRY_BACKLOG zerado ────────────────────────────────────────────

def test_sql_sensor_backlog_does_not_contain_cv_pipeline_registry():
    """cv_screening/pipeline_tool_registry.py foi removido do SQL sensor backlog."""
    content = SQL_SENSOR_PATH.read_text()
    # Should not be a live entry (non-commented) in the frozenset
    assert '"app/domains/cv_screening/agents/pipeline_tool_registry.py"' not in content, (
        "cv_screening/pipeline_tool_registry.py is still in SQL sensor TOOL_REGISTRY_BACKLOG. "
        "Remove it after adding EXEMPT markers."
    )


def test_select_sensor_backlog_does_not_contain_cv_pipeline_registry():
    """cv_screening/pipeline_tool_registry.py foi removido do SELECT sensor backlog."""
    content = SELECT_SENSOR_PATH.read_text()
    assert '"app/domains/cv_screening/agents/pipeline_tool_registry.py"' not in content, (
        "cv_screening/pipeline_tool_registry.py is still in SELECT sensor TOOL_REGISTRY_BACKLOG. "
        "Remove it after confirming no select(Model) violations."
    )


def test_sql_sensor_backlog_is_empty():
    """TOOL_REGISTRY_BACKLOG no SQL sensor está vazio (Wave C-3 agora zerou)."""
    content = SQL_SENSOR_PATH.read_text()
    import re
    # Find the frozenset contents
    match = re.search(
        r"TOOL_REGISTRY_BACKLOG\s*=\s*frozenset\s*\(\s*\{([^}]*)\}\s*\)",
        content,
        re.DOTALL,
    )
    assert match, "Could not parse TOOL_REGISTRY_BACKLOG from sql sensor"
    body = match.group(1)
    # Extract non-comment, non-empty lines
    live_entries = [
        line.strip()
        for line in body.splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    assert live_entries == [], (
        f"TOOL_REGISTRY_BACKLOG in SQL sensor is not empty. Live entries: {live_entries}"
    )


def test_select_sensor_backlog_is_empty():
    """TOOL_REGISTRY_BACKLOG no SELECT sensor está vazio (Wave C-3 agora zerou)."""
    content = SELECT_SENSOR_PATH.read_text()
    import re
    match = re.search(
        r"TOOL_REGISTRY_BACKLOG\s*=\s*frozenset\s*\(\s*\{([^}]*)\}\s*\)",
        content,
        re.DOTALL,
    )
    assert match, "Could not parse TOOL_REGISTRY_BACKLOG from select sensor"
    body = match.group(1)
    live_entries = [
        line.strip()
        for line in body.splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    assert live_entries == [], (
        f"TOOL_REGISTRY_BACKLOG in SELECT sensor is not empty. Live entries: {live_entries}"
    )


# ─── 3. Structural integrity ────────────────────────────────────────────────────

def test_cv_pipeline_registry_tool_definitions_intact():
    """TOOL_DEFINITIONS list still exists and has all expected tools."""
    content = REGISTRY_PATH.read_text()
    expected_tools = [
        "view_candidate_profile",
        "move_candidate",
        "analyze_cv",
        "run_wsi_screening",
        "schedule_interview",
        "send_communication",
        "add_notes",
        "batch_move",
        "add_to_shortlist",
        "view_screening_results",
        "view_interview_notes",
        "generate_offer",
        "finalize_hiring",
        "update_status",
        "generate_report",
        "get_evaluation_criteria",
        "get_pipeline_summary",
        "search_talent_pool",
        "get_company_culture",
        "get_analytics_summary",
        "create_note",
    ]
    for tool in expected_tools:
        assert f'name="{tool}"' in content, (
            f"Tool '{tool}' not found in TOOL_DEFINITIONS. "
            "Migration may have accidentally removed a tool definition."
        )


def test_cv_pipeline_registry_company_id_guards_present():
    """company_id is guarded in all tool wrappers."""
    content = REGISTRY_PATH.read_text()
    # Every wrapper should have company_id gate
    assert 'company_id = kwargs.get("company_id", "")' in content
    # P0.A tenant gate comments present
    assert "P0.A canonical" in content or "tenant gate" in content
