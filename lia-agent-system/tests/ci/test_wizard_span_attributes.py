"""
CI gate: Wizard graph nodes + agent_chat_ws._get_agent must be instrumented.

This test enforces N-07/N-08 (ADR-019 §Promotion Gate #8, task #861) by:

1. AST-scanning `app/domains/job_creation/graph.py` to confirm every node
   function is wrapped with `@wizard_traced_node(...)`.
2. AST-scanning `app/api/v1/agent_chat_ws.py` to confirm `_get_agent` opens a
   span (`WIZARD_SPANS.AGENT_CHAT_GET_AGENT`) and finishes it.
3. Running the wizard nodes against a stub state and asserting that every
   resulting completed span passes `validate_span_attributes`.

Failures here indicate the observability gap reopened — fix by re-applying
the decorator or by passing tenant context into the WS dispatcher call.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

REPO_ROOT = Path("/home/runner/workspace/lia-agent-system")
GRAPH_FILE = REPO_ROOT / "app/domains/job_creation/graph.py"
WS_FILE = REPO_ROOT / "app/api/v1/agent_chat_ws.py"

# These are the wizard graph nodes that must carry the decorator. Order
# mirrors the StateGraph declaration in JobCreationGraph._build_graph.
EXPECTED_DECORATED_NODES: tuple[str, ...] = (
    "intake_node",
    "jd_enrichment_node",
    "bigfive_node",
    "salary_node",
    "competency_node",
    "wsi_questions_node",
    "eligibility_node",
    "review_node",
)


# ---------------------------------------------------------------------------
# AST helpers
# ---------------------------------------------------------------------------

def _decorator_names(node: ast.FunctionDef) -> set[str]:
    names: set[str] = set()
    for dec in node.decorator_list:
        if isinstance(dec, ast.Call):
            names.add(_attr_chain(dec.func))
        else:
            names.add(_attr_chain(dec))
    return names


def _attr_chain(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return f"{_attr_chain(node.value)}.{node.attr}"
    return ""


def _function_defs(path: Path) -> dict[str, ast.FunctionDef]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {
        n.name: n
        for n in ast.walk(tree)
        if isinstance(n, ast.FunctionDef)
    }


def _function_defs_with_nodes(graph_path: Path) -> dict[str, ast.FunctionDef]:
    """PR-10 (ONDA 3 sub-B): also scan nodes/<x>.py files that were
    extracted from graph.py during the refactor. Returns merged dict so the
    decorator check works whether the function lives in graph.py or in
    nodes/<x>.py.
    """
    out: dict[str, ast.FunctionDef] = dict(_function_defs(graph_path))
    nodes_dir = graph_path.parent / "nodes"
    if nodes_dir.is_dir():
        for sub in sorted(nodes_dir.glob("*.py")):
            if sub.name == "__init__.py":
                continue
            try:
                out.update(_function_defs(sub))
            except Exception:
                continue
    return out


# ---------------------------------------------------------------------------
# Static checks (cheap, run first)
# ---------------------------------------------------------------------------

class TestWizardGraphInstrumentation:
    """Every wizard node must be decorated with @wizard_traced_node."""

    @pytest.fixture(scope="class")
    def funcs(self) -> dict[str, ast.FunctionDef]:
        assert GRAPH_FILE.exists(), f"Graph file not found: {GRAPH_FILE}"
        # PR-10 (ONDA 3 sub-B): include nodes/ split files in the AST scan.
        return _function_defs_with_nodes(GRAPH_FILE)

    @pytest.mark.parametrize("node_name", EXPECTED_DECORATED_NODES)
    def test_node_has_wizard_traced_node_decorator(self, funcs, node_name):
        assert node_name in funcs, (
            f"Wizard node {node_name!r} missing from graph.py — "
            "check StateGraph.add_node calls."
        )
        decs = _decorator_names(funcs[node_name])
        assert "wizard_traced_node" in decs, (
            f"Node {node_name!r} is not decorated with @wizard_traced_node "
            f"(found decorators: {sorted(decs)}). N-07 regression — re-apply "
            "the decorator from app.shared.observability.span_validation."
        )


class TestAgentChatWsInstrumentation:
    """`_get_agent` must open a wizard.agent_chat.get_agent span."""

    @pytest.fixture(scope="class")
    def source(self) -> str:
        assert WS_FILE.exists(), f"WS file not found: {WS_FILE}"
        return WS_FILE.read_text(encoding="utf-8")

    def test_get_agent_opens_span(self, source):
        # Span name constant referenced (resilient to reformatting)
        assert "WIZARD_SPANS.AGENT_CHAT_GET_AGENT" in source, (
            "_get_agent must reference WIZARD_SPANS.AGENT_CHAT_GET_AGENT — "
            "N-07 regression, the span instrumentation was removed."
        )
        assert "tracer.create_span" in source, (
            "_get_agent must call tracer.create_span(...) to emit the span."
        )
        assert "finish_span(span" in source, (
            "_get_agent must finish the span (status=ok or error) on every "
            "exit path."
        )

    def test_get_agent_signature_accepts_tenant_context(self, source):
        # Defensive: callers must be able to pass tenant attrs.
        funcs = _function_defs(WS_FILE)
        assert "_get_agent" in funcs
        kw_names = {a.arg for a in funcs["_get_agent"].args.kwonlyargs}
        for required in ("company_id", "session_id", "user_id"):
            assert required in kw_names, (
                f"_get_agent signature missing keyword-only arg {required!r} "
                "— callers cannot propagate tenant context into the span."
            )

    def test_every_get_agent_callsite_passes_tenant_context(self):
        """No `_get_agent(...)` call may forget the kwargs.

        Code review follow-up: prior gate only verified the *signature*
        accepted tenant kwargs — a future caller could still skip them.
        This walks every call expression and asserts each one carries
        `company_id=`, `session_id=`, and `user_id=` as keyword arguments
        (the function definition itself excluded).
        """
        tree = ast.parse(WS_FILE.read_text(encoding="utf-8"))
        offenders: list[str] = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if not (isinstance(node.func, ast.Name) and node.func.id == "_get_agent"):
                continue
            kw_names = {kw.arg for kw in node.keywords if kw.arg}
            missing = {"company_id", "session_id", "user_id"} - kw_names
            if missing:
                offenders.append(
                    f"  - line {node.lineno}: missing kwargs {sorted(missing)}"
                )
        assert not offenders, (
            "Some _get_agent(...) calls do not propagate tenant context — the "
            "wizard.agent_chat.get_agent span will fail validate_span_attributes:\n"
            + "\n".join(offenders)
        )


# ---------------------------------------------------------------------------
# Runtime check: emitted spans pass validation
# ---------------------------------------------------------------------------

class TestEmittedWizardSpansAreValid:
    """Run a few nodes and confirm every emitted span passes the gate."""

    def test_runtime_spans_pass_validation(self, monkeypatch):
        from app.shared.observability import tracing as _t
        from app.shared.observability.span_validation import (
            validate_span_attributes,
        )
        from app.domains.job_creation import graph as g

        _t._completed_spans.clear()

        # Stub heavy services so the test stays hermetic.
        from app.domains.job_creation.services.intake_extractor import JobIntakePayload

        class _StubExtractor:
            def extract(self, *_a, **_kw):
                return JobIntakePayload()

            def extract_from_sources(self, *_a, **_kw):
                return JobIntakePayload()

        monkeypatch.setattr(g, "get_intake_extractor", lambda: _StubExtractor())
        monkeypatch.setattr(g, "emit_job_creation_audit", lambda *_a, **_kw: None)

        state = {
            "session_id": "session-ci",
            "user_id": "recruiter-ci",
            "workspace_id": 7,
            "raw_input": "Engenheiro Dados sênior, R$ 18-22k, remoto.",
            "user_query": "Engenheiro Dados sênior, R$ 18-22k, remoto.",
            "current_stage": "intake",
        }
        g.intake_node(dict(state))
        g.salary_node(dict(state, current_stage="salary"))
        g.eligibility_node(
            dict(state, current_stage="eligibility", eligibility_questions=[]),
        )

        wizard_spans = [
            s for s in _t._completed_spans
            if s["name"].startswith("wizard.job_creation.")
        ]
        assert wizard_spans, "no wizard spans emitted — instrumentation broke"

        failures = [
            (s["name"], r.reason())
            for s in wizard_spans
            for r in [validate_span_attributes(s)]
            if not r.is_valid
        ]
        assert not failures, "Span validation failures:\n" + "\n".join(
            f"  - {name}: {reason}" for name, reason in failures
        )
