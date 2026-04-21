"""Tests for tenant isolation block in SystemPromptBuilder.

Verifies that the LLM system prompt includes a multi-tenancy isolation
directive whenever ``company_id`` is provided to ``SystemPromptBuilder.build``.
"""
from __future__ import annotations

from app.shared.prompts.system_prompt_builder import SystemPromptBuilder


def test_tenant_isolation_block_present_when_company_id_provided():
    company_id = "00000000-0000-0000-0000-000000000abc"
    prompt = SystemPromptBuilder.build(
        agent_type="orchestrator",
        company_id=company_id,
    )
    assert "ISOLAMENTO DE TENANT" in prompt
    assert f"company_id={company_id}" in prompt


def test_tenant_isolation_block_absent_when_company_id_missing():
    prompt = SystemPromptBuilder.build(agent_type="orchestrator")
    assert "ISOLAMENTO DE TENANT" not in prompt


def test_tenant_isolation_propagates_through_conversational_helper():
    from app.api.v1.lia_assistant.conversational import _build_conversational_prompt

    company_id = "11111111-1111-1111-1111-111111111111"
    prompt = _build_conversational_prompt(
        message="oi",
        conversation_context="Início da conversa",
        company_id=company_id,
    )
    assert f"company_id={company_id}" in prompt
    assert "ISOLAMENTO DE TENANT" in prompt


def test_tenant_isolation_propagates_through_handle_process_question_signature():
    """The shared helper now accepts company_id and forwards it to the builder."""
    import inspect
    from app.api.v1.lia_assistant._shared import handle_process_question

    sig = inspect.signature(handle_process_question)
    assert "company_id" in sig.parameters


# Static guardrail: every runtime call to SystemPromptBuilder.build(...)
# must explicitly pass company_id=, otherwise the tenant-isolation block
# is silently dropped on that path.
_BUILDER_CALL_ALLOWLIST: set[str] = {
    # Thin wrapper that forwards **kwargs to SystemPromptBuilder.build,
    # so callers control whether company_id is supplied.
    "app/shared/prompts/agent_prompts.py",
}


def _iter_runtime_python_files():
    import os
    from pathlib import Path

    repo_root = Path(__file__).resolve().parents[2]
    app_dir = repo_root / "app"
    for dirpath, _dirnames, filenames in os.walk(app_dir):
        for name in filenames:
            if name.endswith(".py"):
                yield Path(dirpath) / name


def test_all_runtime_callsites_pass_company_id_to_system_prompt_builder():
    """AST scan: every SystemPromptBuilder.build(...) under app/ must include company_id=."""
    import ast

    offenders: list[str] = []
    for py_file in _iter_runtime_python_files():
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if not (
                isinstance(func, ast.Attribute)
                and func.attr == "build"
                and isinstance(func.value, ast.Name)
                and func.value.id == "SystemPromptBuilder"
            ):
                continue
            kw_names = {kw.arg for kw in node.keywords if kw.arg}
            if "company_id" in kw_names:
                continue
            rel = str(py_file)
            if any(rel.endswith(allow) for allow in _BUILDER_CALL_ALLOWLIST):
                continue
            offenders.append(f"{py_file}:{node.lineno}")

    assert not offenders, (
        "SystemPromptBuilder.build() called without company_id= at:\n  "
        + "\n  ".join(offenders)
    )
