"""Tests for scripts/check_tool_governance.py — G-GOV sensor."""
import textwrap
from pathlib import Path
import pytest

import sys, os
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
from check_tool_governance import _has, _is_true, _has_delete, check_file


def _make_tmp_registry(tmp_path: Path, content: str) -> Path:
    f = tmp_path / "fake_tool_registry.py"
    f.write_text(textwrap.dedent(content))
    return f


def test_gov1_pii_tool_without_pii_fields_raises(tmp_path):
    f = _make_tmp_registry(tmp_path, """
        from lia_agents_core.tool_adapter import ToolDefinition
        t = ToolDefinition(
            name="pii_tool",
            description="x",
            function=lambda: None,
            touches_pii=True,
        )
    """)
    violations = check_file(f, tmp_path)
    assert any("GOV-1" in v and "pii_tool" in v for v in violations)


def test_gov1_pii_tool_with_pii_fields_passes(tmp_path):
    f = _make_tmp_registry(tmp_path, """
        t = ToolDefinition(
            name="pii_tool",
            description="x",
            function=lambda: None,
            touches_pii=True,
            pii_output_fields=["name", "cpf"],
        )
    """)
    violations = check_file(f, tmp_path)
    assert not any("GOV-1" in v for v in violations)


def test_gov1_non_pii_tool_passes(tmp_path):
    f = _make_tmp_registry(tmp_path, """
        t = ToolDefinition(name="safe_tool", description="x", function=lambda: None)
    """)
    violations = check_file(f, tmp_path)
    assert not violations


def test_gov2_decision_tool_without_legal_basis_raises(tmp_path):
    f = _make_tmp_registry(tmp_path, """
        t = ToolDefinition(
            name="ranking_tool",
            description="x",
            function=lambda: None,
            affects_candidate_decision=True,
        )
    """)
    violations = check_file(f, tmp_path)
    assert any("GOV-2" in v and "ranking_tool" in v for v in violations)


def test_gov2_decision_tool_with_legal_basis_passes(tmp_path):
    f = _make_tmp_registry(tmp_path, """
        t = ToolDefinition(
            name="ranking_tool",
            description="x",
            function=lambda: None,
            affects_candidate_decision=True,
            lgpd_legal_basis="LEGITIMATE_INTEREST",
        )
    """)
    violations = check_file(f, tmp_path)
    assert not any("GOV-2" in v for v in violations)


def test_gov3_delete_tool_without_human_review_raises(tmp_path):
    f = _make_tmp_registry(tmp_path, """
        t = ToolDefinition(
            name="delete_doc",
            description="x",
            function=lambda: None,
            side_effects=["delete"],
        )
    """)
    violations = check_file(f, tmp_path)
    assert any("GOV-3" in v and "delete_doc" in v for v in violations)


def test_gov3_delete_tool_with_human_review_passes(tmp_path):
    f = _make_tmp_registry(tmp_path, """
        t = ToolDefinition(
            name="delete_doc",
            description="x",
            function=lambda: None,
            side_effects=["delete"],
            requires_human_review=True,
        )
    """)
    violations = check_file(f, tmp_path)
    assert not any("GOV-3" in v for v in violations)


def test_multiple_violations_in_one_file(tmp_path):
    f = _make_tmp_registry(tmp_path, """
        t1 = ToolDefinition(
            name="tool_a",
            description="x",
            function=lambda: None,
            touches_pii=True,
        )
        t2 = ToolDefinition(
            name="tool_b",
            description="x",
            function=lambda: None,
            affects_candidate_decision=True,
        )
    """)
    violations = check_file(f, tmp_path)
    assert len(violations) == 2
    assert any("GOV-1" in v for v in violations)
    assert any("GOV-2" in v for v in violations)
