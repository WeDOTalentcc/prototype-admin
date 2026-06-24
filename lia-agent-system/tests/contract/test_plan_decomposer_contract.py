"""
Contract tests for PlanDecomposer — ensures canonical API surface.

Sensors:
  S1: decompose() requires keyword-only args (no positional)
  S2: user_message and enriched_context are both required (no default)
  S3: heuristic runs on user_message, not enriched_context
  S4: INVIOLABLE job creation guard
  S5: all callers of decompose() pass both required kwargs
"""

import ast
import inspect
import os
import re
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))


# ── S1: keyword-only signature ──────────────────────────────────────────────

def test_s1_decompose_is_keyword_only():
    """decompose() params after * must be keyword-only — no positional allowed."""
    from app.shared.execution.plan_decomposer import PlanDecomposer

    sig = inspect.signature(PlanDecomposer.decompose)
    params = list(sig.parameters.values())
    # Skip 'self'
    non_self = [p for p in params if p.name != "self"]
    for p in non_self:
        assert p.kind == inspect.Parameter.KEYWORD_ONLY, (
            f"decompose() param '{p.name}' must be KEYWORD_ONLY, got {p.kind.name}. "
            f"Use * in the signature to enforce keyword-only args."
        )


def test_s2_user_message_and_enriched_context_required():
    """user_message and enriched_context must NOT have defaults."""
    from app.shared.execution.plan_decomposer import PlanDecomposer

    sig = inspect.signature(PlanDecomposer.decompose)
    for name in ("user_message", "enriched_context"):
        param = sig.parameters.get(name)
        assert param is not None, f"decompose() missing required param '{name}'"
        assert param.default is inspect.Parameter.empty, (
            f"decompose() param '{name}' must NOT have a default value. "
            f"Both user_message and enriched_context are required — "
            f"optional params hide bugs when callers forget to pass them."
        )


# ── S3: heuristic isolation ─────────────────────────────────────────────────

def test_s3_heuristic_detects_multi_step_in_raw_message():
    """Heuristic must fire on raw user message, not on enriched context with history."""
    from app.shared.execution.plan_decomposer import _passes_heuristic

    raw = "liste as vagas ativas, liste os melhores candidatos das duas mais criticas e depois gere insights"
    enriched = (
        "Historico recente desta conversa:\n"
        "  [recrutador] oi\n  [LIA] ola!\n\n"
        f"Mensagem atual do recrutador: {raw}"
    )

    assert _passes_heuristic(raw) is True, "Heuristic must detect multi-step in raw message"
    # enriched might or might not pass — the point is we DON'T rely on it


def test_s3_heuristic_rejects_simple_messages():
    """Heuristic must reject simple greetings and questions."""
    from app.shared.execution.plan_decomposer import _passes_heuristic

    for msg in ["oi tudo bem?", "como está a vaga?", "sim", "obrigado", "ok", "entendi"]:
        assert _passes_heuristic(msg) is False, f"Heuristic should reject: '{msg}'"


# ── S4: INVIOLABLE guard ────────────────────────────────────────────────────

def test_s4_inviolable_job_creation_actions_present():
    """JOB_CREATION_ACTION_IDS must be a non-empty frozenset imported by decomposer."""
    from app.shared.execution.plan_decomposer import JOB_CREATION_ACTION_IDS

    assert isinstance(JOB_CREATION_ACTION_IDS, frozenset)
    assert len(JOB_CREATION_ACTION_IDS) >= 3
    assert "create_job" in JOB_CREATION_ACTION_IDS


# ── S5: caller audit — all decompose() call sites pass required kwargs ──────

def test_s5_all_callers_pass_required_kwargs():
    """Every call to .decompose() in the codebase must pass user_message= and enriched_context=."""
    base = os.path.join(os.path.dirname(__file__), "..", "..", "..")
    violations = []

    for root, dirs, files in os.walk(os.path.join(base, "app")):
        dirs[:] = [d for d in dirs if d not in ("__pycache__", ".git", "node_modules")]
        for fname in files:
            if not fname.endswith(".py"):
                continue
            fpath = os.path.join(root, fname)
            try:
                with open(fpath) as f:
                    source = f.read()
            except Exception:
                continue

            if ".decompose(" not in source:
                continue

            # Parse AST to find decompose calls
            try:
                tree = ast.parse(source, filename=fpath)
            except SyntaxError:
                continue

            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                # Match *.decompose(...)
                func = node.func
                if not (isinstance(func, ast.Attribute) and func.attr == "decompose"):
                    continue
                # Skip if it's a different decompose (e.g., decompose_task)
                # Check kwargs
                kwarg_names = {kw.arg for kw in node.keywords if kw.arg is not None}
                rel_path = os.path.relpath(fpath, base)
                # Must have both required kwargs
                if "user_message" not in kwarg_names:
                    violations.append(
                        f"{rel_path}:{node.lineno} — decompose() missing user_message= kwarg"
                    )
                if "enriched_context" not in kwarg_names:
                    violations.append(
                        f"{rel_path}:{node.lineno} — decompose() missing enriched_context= kwarg"
                    )

    assert not violations, (
        f"All decompose() callers must pass user_message= and enriched_context= as kwargs.\n"
        f"Violations:\n" + "\n".join(f"  {v}" for v in violations)
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
