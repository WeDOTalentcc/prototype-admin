"""Sentinela #1099 — todo `ws_stage_payload` do wizard precisa expor `data.message`.

Origem: bug do template canned 4× (2026-05-15) cuja sequência de causas
chegou parcialmente da combinação "stage avança mas o frontend recebe um
payload sem `data.message`" — o `WizardSessionService._emit_silent_fallback`
então cunhava o `[ATENÇÃO: estado inconsistente]` (Task #1089 / T3) ou,
em paths anteriores, repetia o último template canned conhecido.

Esta sentinela faz uma análise estática (AST) de
`lia-agent-system/app/domains/job_creation/graph.py`, encontra TODO dict
literal cujo campo `"type"` seja `"wizard_stage"` e exige que o sub-dict
`"data"` contenha a chave `"message"` (mesmo que o valor seja uma f-string
ou expressão condicional — só verificamos a presença da chave).

Falha loud listando arquivo+linha de cada `ws_stage_payload` ofensor.

Cobre os 11 nós lineares + os 4 gate_nodes (15 nós no total). Hoje, com
o fix da Task #1097 + auditoria 2026-05, todos os nós satisfazem o
invariante. Esta sentinela impede regressão silenciosa.
"""

from __future__ import annotations

import ast
import inspect
from pathlib import Path
from typing import Iterator

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _graph_source_path() -> Path:
    from app.domains.job_creation import graph as graph_mod

    p = inspect.getsourcefile(graph_mod)
    assert p is not None, "Could not resolve graph.py source path"
    return Path(p)


def _wizard_source_paths() -> list[Path]:
    """PR-10 (ONDA 3 sub-B): wizard nodes were split out of graph.py into
    nodes/<x>.py files. Return graph.py + all nodes/*.py so AST scanners
    can still find every node and every ws_stage_payload literal.
    """
    graph_path = _graph_source_path()
    out = [graph_path]
    nodes_dir = graph_path.parent / "nodes"
    if nodes_dir.is_dir():
        for sub in sorted(nodes_dir.glob("*.py")):
            if sub.name != "__init__.py":
                out.append(sub)
    return out


def _is_str_const(node: ast.AST | None, value: str) -> bool:
    return isinstance(node, ast.Constant) and node.value == value


def _dict_key_value(d: ast.Dict, key: str) -> ast.AST | None:
    """Return the value node for ``key`` in a ``ast.Dict`` literal, or None."""
    for k, v in zip(d.keys, d.values):
        if _is_str_const(k, key):
            return v
    return None


def _dict_has_key(d: ast.Dict, key: str) -> bool:
    for k in d.keys:
        if _is_str_const(k, key):
            return True
    return False


def _walk_wizard_stage_dicts(tree: ast.AST) -> Iterator[ast.Dict]:
    """Yield every dict literal that has ``"type": "wizard_stage"``."""
    for node in ast.walk(tree):
        if not isinstance(node, ast.Dict):
            continue
        type_value = _dict_key_value(node, "type")
        if _is_str_const(type_value, "wizard_stage"):
            yield node


def _iter_top_level_stmts(fn: ast.FunctionDef) -> Iterator[ast.stmt]:
    """Yield statements in lexical order at the SAME scope as ``fn`` (skip nested
    functions/classes/lambdas/comprehensions). Includes statements inside
    if/for/while/try/with branches because Python doesn't have block scope —
    a name bound there IS visible at the function level after the statement
    runs. We still descend into those compound bodies to track the binding
    in lexical order.
    """
    stack: list[ast.stmt] = list(fn.body)
    while stack:
        # Pop in lexical order (front of list).
        stmt = stack.pop(0)
        yield stmt
        # Descend into compound statements that DON'T create a new scope.
        # Skip FunctionDef/AsyncFunctionDef/ClassDef/Lambda — those are new scopes.
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        children: list[ast.stmt] = []
        for attr in ("body", "orelse", "finalbody", "handlers"):
            inner = getattr(stmt, attr, None)
            if inner is None:
                continue
            for item in inner:
                if isinstance(item, ast.stmt):
                    children.append(item)
                elif isinstance(item, ast.ExceptHandler):
                    children.extend(item.body)
        # Preserve lexical order: prepend children before remaining stack.
        stack = children + stack


def _resolve_data_dict_literal(
    data_value: ast.AST, tree: ast.AST
) -> tuple[ast.Dict | None, str]:
    """Resolve ``data`` value to a literal ``ast.Dict`` if possible.

    Returns ``(dict_node, status)`` where status ∈ {"literal", "name_resolved",
    "name_unresolved", "non_literal"}. ``dict_node`` is the literal dict
    we will check for the ``message`` key; ``None`` when unresolvable.

    When ``data`` is a Name (e.g. ``"data": _wsi_stage_data``), we walk the
    enclosing function looking for the LAST ``Assign`` / ``AnnAssign`` to that
    name BEFORE the payload site (lexical dominator), restricted to the same
    scope (nested defs/classes are skipped). Mutations
    ``target_name["message"] = ...`` BEFORE the payload site are also accepted
    as proof that the key exists at runtime.
    """
    if isinstance(data_value, ast.Dict):
        return data_value, "literal"
    if not isinstance(data_value, ast.Name):
        return None, "non_literal"

    target_name = data_value.id
    use_lineno = data_value.lineno

    # Find the function enclosing the original Name reference.
    enclosing_fn: ast.FunctionDef | None = None
    candidates: list[ast.FunctionDef] = []
    for fn in ast.walk(tree):
        if isinstance(fn, ast.FunctionDef):
            for sub in ast.walk(fn):
                if sub is data_value:
                    candidates.append(fn)
                    break
    # Innermost enclosing function = smallest lineno-span containing use_lineno.
    if candidates:
        enclosing_fn = min(
            candidates,
            key=lambda f: (getattr(f, "end_lineno", f.lineno) or f.lineno) - f.lineno,
        )
    if enclosing_fn is None:
        return None, "name_unresolved"

    last_dict_binding: ast.Dict | None = None
    has_message_subscript_set = False

    for stmt in _iter_top_level_stmts(enclosing_fn):
        if stmt.lineno >= use_lineno:
            break  # only consider lexical dominators
        # Direct dict-literal binding (Assign / AnnAssign).
        if isinstance(stmt, ast.Assign):
            for tgt in stmt.targets:
                if isinstance(tgt, ast.Name) and tgt.id == target_name:
                    if isinstance(stmt.value, ast.Dict):
                        last_dict_binding = stmt.value
                    else:
                        # Reassigned to a non-dict — invalidate previous binding.
                        last_dict_binding = None
                # Subscript mutation: target_name["message"] = ...
                if (
                    isinstance(tgt, ast.Subscript)
                    and isinstance(tgt.value, ast.Name)
                    and tgt.value.id == target_name
                ):
                    slice_node = tgt.slice
                    # Py<3.9 wraps in ast.Index; py3.9+ uses the constant directly.
                    if isinstance(slice_node, ast.Index):  # type: ignore[attr-defined]
                        slice_node = slice_node.value  # type: ignore[attr-defined]
                    if _is_str_const(slice_node, "message"):
                        has_message_subscript_set = True
        elif isinstance(stmt, ast.AnnAssign):
            tgt = stmt.target
            if isinstance(tgt, ast.Name) and tgt.id == target_name:
                if isinstance(stmt.value, ast.Dict):
                    last_dict_binding = stmt.value
                else:
                    last_dict_binding = None

    if last_dict_binding is not None and (
        _dict_has_key(last_dict_binding, "message") or has_message_subscript_set
    ):
        return last_dict_binding, "name_resolved"
    if has_message_subscript_set:
        fake = ast.Dict(
            keys=[ast.Constant(value="message")],
            values=[ast.Constant(value="<runtime-set>")],
        )
        fake.lineno = use_lineno
        return fake, "name_resolved"
    if last_dict_binding is not None:
        # Dict bound but lacks message — return so caller flags it.
        return last_dict_binding, "name_resolved"

    return None, "name_unresolved"


# ---------------------------------------------------------------------------
# S1 — discovery: at least one wizard_stage payload exists in graph.py
# ---------------------------------------------------------------------------
def test_graph_contains_wizard_stage_payloads() -> None:
    """Smoke: garante que o AST scanner encontra os payloads canônicos.

    Hoje graph.py tem ~30 sites com ``ws_stage_payload`` (cobrem os 11 nós
    lineares + 4 gate_nodes + paths de fairness/erro). Se a contagem cair
    para zero, ou a constante for renomeada silenciosamente, este teste
    falha antes do invariante real (S2) — protege o próprio scanner.
    """
    payloads = []
    for src_path in _wizard_source_paths():
        tree = ast.parse(src_path.read_text(encoding="utf-8"))
        payloads.extend(_walk_wizard_stage_dicts(tree))
    assert len(payloads) >= 10, (
        f"Expected ≥10 wizard_stage dict literals in graph.py "
        f"(15 canonical nodes + fairness paths), found {len(payloads)}. "
        "Did the constant 'wizard_stage' get renamed? Update this sentinel."
    )


# ---------------------------------------------------------------------------
# S2 — INVARIANT: every wizard_stage payload's data dict has a "message" key
# ---------------------------------------------------------------------------
def test_every_wizard_stage_payload_has_data_message() -> None:
    # PR-10 (ONDA 3 sub-B): scan graph.py + nodes/*.py.
    offenders: list[str] = []
    for src_path in _wizard_source_paths():
        source = src_path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        for payload_dict in _walk_wizard_stage_dicts(tree):
            data_value = _dict_key_value(payload_dict, "data")
            line = payload_dict.lineno

            if data_value is None:
                offenders.append(
                    f"L{line}: ws_stage_payload missing 'data' key entirely"
                )
                continue

            resolved, status = _resolve_data_dict_literal(data_value, tree)
            if resolved is None:
                offenders.append(
                    f"L{line}: ws_stage_payload.data could not be resolved "
                    f"(type={type(data_value).__name__}, status={status}). "
                    "Inline the dict or bind it to a name in the same function "
                    "via assignment to a dict literal."
                )
                continue

            if not _dict_has_key(resolved, "message"):
                snippet = ast.get_source_segment(source, payload_dict) or ""
                snippet_head = snippet.splitlines()[0][:120] if snippet else "?"
                origin = (
                    f"resolved via {data_value.id} @ L{resolved.lineno}"
                    if status == "name_resolved" and isinstance(data_value, ast.Name)
                    else "literal"
                )
                offenders.append(
                    f"L{line}: ws_stage_payload.data ({origin}) has no 'message' "
                    f"key (starts: {snippet_head!r})"
                )

    assert not offenders, (
        "Wizard ws_stage_payload(s) without data.message detected. "
        "Each payload reaches the FE via WebSocket and an empty/missing "
        "data.message triggers the silent-fallback path "
        "(WizardSessionService._emit_silent_fallback / Task #1089 T3) or, "
        "historically, the canned-template-4× regression (Task #1097). "
        "Add a contextual data.message string. Offenders:\n  - "
        + "\n  - ".join(offenders)
    )


# ---------------------------------------------------------------------------
# S3 — anti-pattern: data.message must NEVER be a literal empty string
# ---------------------------------------------------------------------------
def test_no_wizard_stage_payload_has_empty_string_message() -> None:
    # PR-10 (ONDA 3 sub-B): scan graph.py + nodes/*.py.
    offenders: list[str] = []
    for src_path in _wizard_source_paths():
        tree = ast.parse(src_path.read_text(encoding="utf-8"))
        for payload_dict in _walk_wizard_stage_dicts(tree):
            data_value = _dict_key_value(payload_dict, "data")
            if not isinstance(data_value, ast.Dict):
                continue
            message_value = _dict_key_value(data_value, "message")
            if message_value is None:
                continue  # caught by S2
            if _is_str_const(message_value, ""):
                offenders.append(
                    f"L{payload_dict.lineno}: data.message is an empty string literal"
                )

    assert not offenders, (
        "Wizard ws_stage_payload with literally empty data.message:\n  - "
        + "\n  - ".join(offenders)
    )


# ---------------------------------------------------------------------------
# S4 — discovery: every canonical node function appears in the file.
#      Lightweight inventory check — keeps this sentinel honest if a node
#      is renamed/removed.
# ---------------------------------------------------------------------------
CANONICAL_NODE_NAMES = (
    # 11 linear nodes
    "intake_node",
    "jd_enrichment_node",
    "bigfive_node",
    "salary_node",
    "competency_node",
    "wsi_questions_node",
    "eligibility_node",
    "review_node",
    "publish_node",
    "calibration_node",
    "handoff_node",
    # 4 gate nodes (HITL interrupts)
    "jd_gate_node",
    "competency_gate_node",
    "wsi_questions_gate_node",
    "review_gate_node",
)


@pytest.mark.parametrize("node_name", CANONICAL_NODE_NAMES)
def test_canonical_node_function_exists(node_name: str) -> None:
    # PR-10 (ONDA 3 sub-B): scan graph.py + nodes/*.py.
    found = False
    for src_path in _wizard_source_paths():
        tree = ast.parse(src_path.read_text(encoding="utf-8"))
        if any(
            isinstance(n, ast.FunctionDef) and n.name == node_name
            for n in ast.walk(tree)
        ):
            found = True
            break
    assert found, (
        f"Canonical wizard node '{node_name}' missing from graph.py or nodes/*.py. "
        "If renamed/removed, update CANONICAL_NODE_NAMES in this sentinel "
        "AND docs/architecture/wizard-flow.md §2."
    )
