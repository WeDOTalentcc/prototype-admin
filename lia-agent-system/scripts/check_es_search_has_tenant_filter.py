#!/usr/bin/env python3
"""AST sensor — every ``es.search``/``es.count`` callsite in ``app/`` must
have its ``body=`` (or ``query=``) wrapped by
``app.shared.search.with_tenant_filter(...)`` (Task #1147).

Multi-tenancy invariant (CLAUDE.md REGRA 1): Elasticsearch has no RLS
equivalent, so a search without ``{"term": {"company_id": cid}}`` returns
documents across tenants. This sensor walks every Python file under
``app/`` and flags ``await <client>.search(...)`` / ``await <client>.count(...)``
calls where the body argument is NOT a name that was produced by a
``with_tenant_filter(...)`` call earlier in the same function.

Heuristic (intentionally conservative — false-positives go to allowlist):

1. Find every ``await <name>.search(...)`` / ``<name>.count(...)`` node.
2. Skip if ``<name>`` is in :data:`SAFE_CLIENT_NAMES` (re/regex/etc.) or
   if the call is clearly a SQLAlchemy ``func.count(...)``/``select.count()``.
3. Capture the body argument: ``body=<X>`` (preferred), ``query=<X>``
   (elasticsearch-py 8.x style), or the first positional dict.
4. Walk the enclosing function backwards; if ``<X>`` was last assigned
   from ``with_tenant_filter(...)`` (or the callsite uses
   ``TenantAwareElasticsearchClient``), the sensor passes.

Allowlist:
    Entries in ``scripts/.es_search_allowlist.txt`` (relative path or
    ``relative_path:lineno``) opt out of the check — intended for
    health probes and admin cross-tenant audit paths only.

Modes:
    --block (default in CI): exit 1 on first uncovered callsite.
    --warn: exit 0, list offenders on stderr.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path
from typing import Iterator

ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "app"
ALLOWLIST_FILE = ROOT / "scripts" / ".es_search_allowlist.txt"

WRAPPER_FUNC = "with_tenant_filter"
TENANT_CLIENT_CLASS = "TenantAwareElasticsearchClient"
INTERCEPTED_METHODS = {"search", "count"}

# Receiver names we treat as "definitely not Elasticsearch" so we don't
# flag every ``re.search`` / ``str.count`` / ``names.count`` in the repo.
SAFE_RECEIVERS = {
    "re",
    "regex",
    "pattern",
    "self",  # repos/services with their own .search/.count
}

# Module-level names that, when called as ``X.search(...)``, are obviously
# SQLAlchemy / itertools / repository abstractions — not ES.
SAFE_SUFFIXES = (
    "_PATTERNS",
    "_RE",
    "_PATTERN",
    "_REGEX",
)


def load_allowlist() -> set[str]:
    """Load file-level and line-level allowlist entries."""
    out: set[str] = set()
    if not ALLOWLIST_FILE.exists():
        return out
    for raw in ALLOWLIST_FILE.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        out.add(line)
    return out


def iter_py_files(root: Path) -> Iterator[Path]:
    for path in root.rglob("*.py"):
        # Skip tests + generated caches; they're not production callsites.
        parts = set(path.parts)
        if "__pycache__" in parts or "tests" in parts:
            continue
        yield path


def _is_es_call(call: ast.Call) -> tuple[bool, str | None]:
    """Return (is_candidate, method_name) for an ES-shaped call node.

    A call is considered ES-shaped if it is ``<recv>.search(...)`` or
    ``<recv>.count(...)`` AND it matches one of the canonical ES client
    signatures:

    - **Kwarg form (8.x):** has ``index=`` and/or ``body=`` / ``query=``.
      Any non-ES ``.search`` API in this codebase (``re.search``,
      ``str.count``, ``RAGPipelineService.search(query=)``,
      ``knowledge_base.search("text")``) lacks ALL of these kwargs.
    - **Positional form (7.x):** exactly two positional args where the
      first is a string literal/Name (index name) and the second is a
      dict literal or Name (query body). E.g.
      ``await client.search("candidates", {...})``.

    Receivers in :data:`SAFE_RECEIVERS` are excluded up front so we never
    chase ``re.search(...)`` etc.
    """
    fn = call.func
    if not isinstance(fn, ast.Attribute):
        return False, None
    method = fn.attr
    if method not in INTERCEPTED_METHODS:
        return False, None

    # Reject obvious non-ES receivers.
    recv = fn.value
    if isinstance(recv, ast.Name) and recv.id in SAFE_RECEIVERS:
        return False, None
    if isinstance(recv, ast.Name) and any(
        recv.id.endswith(suf) for suf in SAFE_SUFFIXES
    ):
        return False, None

    kw_names = {kw.arg for kw in call.keywords if kw.arg}
    # ``index=`` is the highly distinctive ES marker. ``body=`` is also
    # an ES-shaped marker on its own — at the time of writing, NO non-ES
    # ``.search``/``.count`` API in this codebase uses ``body=`` as a
    # kwarg (verified by grep). Including it on its own closes the
    # bypass where someone writes ``es.search(body=...)`` without
    # ``index=``. ``query=`` is intentionally excluded as a sole trigger
    # because RAG / search services share that kwarg name.
    if "index" in kw_names or "body" in kw_names:
        return True, method

    # Positional ES form: (index_str, body_dict_literal).
    # We intentionally restrict args[1] to a Dict literal (or a Call to
    # ``with_tenant_filter(...)``) — using a Name there would otherwise
    # collide with regex-style ``pattern.search(text, pos)`` and other
    # 2-positional APIs that have nothing to do with ES. Real ES code
    # using a variable for the body invariably also uses ``body=`` /
    # ``query=`` kwargs (caught by the kwarg branch above).
    if (
        len(call.args) == 2
        and isinstance(call.args[0], ast.Constant)
        and isinstance(call.args[0].value, str)
        and isinstance(call.args[1], (ast.Dict, ast.Call))
    ):
        return True, method

    return False, None


def _extract_body_node(call: ast.Call) -> ast.expr | None:
    """Return the AST node passed as ``body=`` / ``query=`` / 2nd positional."""
    for kw in call.keywords:
        if kw.arg in ("body", "query"):
            return kw.value
    # Positional ES form: client.search("index", {...}) → body is args[1].
    if len(call.args) >= 2:
        return call.args[1]
    if call.args:
        return call.args[0]
    return None


def _is_wrapper_call(node: ast.expr | None) -> bool:
    """True iff ``node`` is a Call to ``with_tenant_filter(...)``."""
    if not isinstance(node, ast.Call):
        return False
    target = node.func
    if isinstance(target, ast.Name) and target.id == WRAPPER_FUNC:
        return True
    if isinstance(target, ast.Attribute) and target.attr == WRAPPER_FUNC:
        return True
    return False


def _collect_wrapper_assignments(
    func: ast.AsyncFunctionDef | ast.FunctionDef,
) -> list[tuple[int, str]]:
    """Return list of (lineno, var_name) for every assignment
    ``var = with_tenant_filter(...)`` (or ``var: T = with_tenant_filter(...)``)
    found anywhere inside ``func``. Sorted by lineno.

    AugAssign / multiple-target tuple assignments are conservatively
    treated as NOT wrapping (the caller's responsibility to use a single
    target assignment).
    """
    out: list[tuple[int, str]] = []
    for node in ast.walk(func):
        if isinstance(node, ast.Assign) and _is_wrapper_call(node.value):
            if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                out.append((node.lineno, node.targets[0].id))
        elif isinstance(node, ast.AnnAssign) and _is_wrapper_call(node.value):
            if isinstance(node.target, ast.Name):
                out.append((node.lineno, node.target.id))
    out.sort()
    return out


def _collect_non_wrapper_assignments(
    func: ast.AsyncFunctionDef | ast.FunctionDef,
) -> list[tuple[int, str]]:
    """Return list of (lineno, var_name) for every assignment whose RHS is
    NOT a ``with_tenant_filter(...)`` call. Used to detect reassignments
    that invalidate a previous wrapper assignment.
    """
    out: list[tuple[int, str]] = []
    for node in ast.walk(func):
        if isinstance(node, ast.Assign):
            if _is_wrapper_call(node.value):
                continue
            for tgt in node.targets:
                if isinstance(tgt, ast.Name):
                    out.append((node.lineno, tgt.id))
        elif isinstance(node, ast.AugAssign) and isinstance(node.target, ast.Name):
            out.append((node.lineno, node.target.id))
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.value is None or _is_wrapper_call(node.value):
                continue
            out.append((node.lineno, node.target.id))
    out.sort()
    return out


def _function_provides_wrapper(
    func: ast.AsyncFunctionDef | ast.FunctionDef,
    body_node: ast.expr,
    call_lineno: int,
) -> bool:
    """True iff ``body_node`` at line ``call_lineno`` was produced by
    ``with_tenant_filter(...)``.

    Strict dataflow rules (no false negatives — see Task #1147 review):

    1. **Inline:** ``body=with_tenant_filter(q, cid)`` → pass.
    2. **Name lineage:** ``body=<Name>`` passes ONLY if the most-recent
       reaching assignment to ``<Name>`` BEFORE ``call_lineno`` was
       ``<Name> = with_tenant_filter(...)`` AND there is no later
       non-wrapper assignment / AugAssign to ``<Name>`` between that
       wrapper assignment and the call site.
    3. Anything else (dict literal, attribute access, call to another
       function, etc.) → fail.

    Wrapper calls that appear *after* the ES call don't count (line-order
    check). Wrapper calls that target a DIFFERENT variable also don't
    count (name match required).
    """
    if _is_wrapper_call(body_node):
        return True

    if not isinstance(body_node, ast.Name):
        return False

    var_name = body_node.id
    wrapper_assigns = [
        ln for (ln, name) in _collect_wrapper_assignments(func)
        if name == var_name and ln < call_lineno
    ]
    if not wrapper_assigns:
        return False
    last_wrap = max(wrapper_assigns)

    # Any non-wrapper reassignment between last_wrap and call_lineno invalidates.
    for ln, name in _collect_non_wrapper_assignments(func):
        if name == var_name and last_wrap < ln < call_lineno:
            return False
    return True


def _enclosing_function(
    tree: ast.AST, target: ast.Call
) -> ast.AsyncFunctionDef | ast.FunctionDef | None:
    for node in ast.walk(tree):
        if isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
            if any(child is target for child in ast.walk(node)):
                return node
    return None


def scan_file(path: Path) -> list[tuple[int, str]]:
    """Return list of (lineno, message) for offending callsites in ``path``."""
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    # Module-level escape hatch: if the module imports
    # ``TenantAwareElasticsearchClient``, callers in it have already routed
    # through the runtime interceptor — the wrapper requirement still holds,
    # but we use this to recognise modules that DEFINE the client itself
    # (avoid the false-positive on tenant_aware_es_query.py).
    if path.resolve() == (
        ROOT / "app" / "shared" / "search" / "tenant_aware_es_query.py"
    ).resolve():
        return []

    offenders: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        ok, method = _is_es_call(node)
        if not ok:
            continue
        body = _extract_body_node(node)
        if body is None:
            # No body kwarg at all → safe-ish (could be a count with only
            # index=). We still require explicit wrap; flag it.
            offenders.append(
                (
                    node.lineno,
                    f"es {method}(...) with no body/query kwarg — wrap with with_tenant_filter()",
                )
            )
            continue
        enclosing = _enclosing_function(tree, node)
        if enclosing is None:
            offenders.append(
                (
                    node.lineno,
                    f"module-level es {method}(...) — must be inside a function that calls with_tenant_filter()",
                )
            )
            continue
        if not _function_provides_wrapper(enclosing, body, node.lineno):
            offenders.append(
                (
                    node.lineno,
                    f"es {method}(...) body not produced by with_tenant_filter()",
                )
            )
    return offenders


def main(argv: list[str]) -> int:
    block = "--warn" not in argv
    allow = load_allowlist()
    all_offenders: list[tuple[Path, int, str]] = []
    for path in iter_py_files(APP_DIR):
        rel = path.relative_to(ROOT).as_posix()
        if rel in allow:
            continue
        for lineno, msg in scan_file(path):
            if f"{rel}:{lineno}" in allow:
                continue
            all_offenders.append((path, lineno, msg))

    if not all_offenders:
        print("[check_es_search_has_tenant_filter] ✅ all es.search/es.count callsites wrap with_tenant_filter()")
        return 0

    print(
        "[check_es_search_has_tenant_filter] ❌ "
        f"{len(all_offenders)} offending callsite(s):",
        file=sys.stderr,
    )
    for path, lineno, msg in all_offenders:
        rel = path.relative_to(ROOT).as_posix()
        print(f"  {rel}:{lineno}: {msg}", file=sys.stderr)
    print(
        "\nFix: import `with_tenant_filter` from app.shared.search and wrap the "
        "query body. Health/admin paths can be allowlisted in "
        "scripts/.es_search_allowlist.txt (one entry per line, with justification "
        "comment above).",
        file=sys.stderr,
    )
    return 1 if block else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
