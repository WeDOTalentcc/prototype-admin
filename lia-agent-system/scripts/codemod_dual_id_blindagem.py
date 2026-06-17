#!/usr/bin/env python3
"""
codemod_dual_id_blindagem.py — canonical, reversible codemod that applies
the dual-ID route-shadowing *blindagem* (Task #455 / #470 / #489) to every
``app/api/v1`` router in bulk.

What it does
============
For every FastAPI route under ``/api/v1`` that carries a ``{*_id}`` path
parameter, the parameter MUST be constrained with
``Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)]`` (see
``app/api/v1/_path_patterns.py`` and ADR 003). Without the constraint, a
sibling static segment (e.g. ``/candidates/search``) can be silently
captured by an item handler (``GET /candidates/{candidate_id}``) and
surface as a misleading 404 — the Task #455 trap.

This tool fixes the *whole class* of latent traps mechanically:

  1. **Discovery via runtime introspection** (not blind regex). It imports
     the live ``app.main:app``, walks ``app.routes``, and for every
     ``APIRoute`` with ``{`` in its path collects the *path* parameters
     whose name ends in ``_id`` and that are NOT already constrained with
     ``DUAL_ID_PATH_PATTERN`` and are NOT typed ``UUID``. Crucially, it
     reads ``route.dependant.path_params`` — so it can NEVER mistake a
     ``company_id`` that arrives via ``Depends(require_company_id)`` /
     ``Header(...)`` / ``Query(...)`` for a path parameter. Only true path
     parameters are touched.

  2. **Source mapping** via ``inspect.getsourcefile(route.endpoint)`` plus
     the parameter *name*, so the libcst transform only rewrites the
     matching ``FunctionDef`` / parameter.

  3. **libcst transform** (concrete-syntax-tree, lossless) per file:
       * ``x_id: str``                          → ``x_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)]``
       * ``x_id: str = Path(...)``              → ``x_id: Annotated[str, Path(..., pattern=DUAL_ID_PATH_PATTERN)]`` (preserves description/examples)
       * ``x_id: str = Path(..., pattern=...)`` → pattern swapped to ``DUAL_ID_PATH_PATTERN``
       * ``x_id: Annotated[str, Path(...)]``    → ``pattern=`` injected/replaced inside the existing ``Path(...)``
     Adds the imports ``from typing import Annotated``, ``from fastapi import Path``,
     and ``from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, reorder_collection_before_item``
     if missing (idempotent merge — never duplicates).
     Appends ``reorder_collection_before_item(<router_var>)`` at module end
     for every ``APIRouter`` instance defined at module scope (once each).

  4. **Idempotent.** Running twice is a no-op: already-constrained params and
     an already-present ``reorder_collection_before_item(router)`` call are
     detected and skipped.

Safety
======
* Only PATH parameters (from ``route.dependant.path_params``) are eligible.
  Query/body/header/Depends params are structurally excluded.
* Defaults, descriptions, and examples on existing ``Path(...)`` are
  preserved; only ``pattern=`` is added or replaced.
* The codemod parses and re-renders with libcst (no text munging of
  signatures), so it cannot corrupt unrelated code.
* ``--dry-run`` prints the planned per-file param edits without writing.

Usage
=====
    python3 scripts/codemod_dual_id_blindagem.py            # apply
    python3 scripts/codemod_dual_id_blindagem.py --dry-run  # report only
    python3 scripts/codemod_dual_id_blindagem.py --check    # exit 1 if any
                                                            # router still
                                                            # needs blindagem

The structural sensor ``tests/api/test_dual_id_route_shadowing.py`` is the
ground-truth that this tool drives to baseline 0.
"""
from __future__ import annotations

import argparse
import inspect
import os
import sys
from collections import defaultdict
from typing import Iterable

import libcst as cst
import libcst.matchers as m

# ---------------------------------------------------------------------------
# Constants mirrored from app.api.v1._path_patterns so the tool can run even
# if the import graph is partially broken mid-edit. Verified for equality at
# import time below.
# ---------------------------------------------------------------------------
DUAL_ID_PATH_PATTERN = (
    r"^([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}|\d+)$"
)
PATTERN_HELPER_MODULE = "app.api.v1._path_patterns"
REORDER_CALL_NAME = "reorder_collection_before_item"


def _repo_root() -> str:
    # scripts/ lives directly under the lia-agent-system package root.
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ---------------------------------------------------------------------------
# Phase 1 — discover targets via runtime introspection.
#
# The *scope* of what must be blindado is owned by the structural sensor
# ``tests/api/test_dual_id_route_shadowing.py``, NOT by this tool. To keep
# the codemod and the sensor from ever drifting, we import the sensor's own
# authoritative sets:
#
#   * ``DUAL_ID_ROUTERS``       — the per-router allow-list (8 hand-picked +
#                                 the full Task #489 sweep). Each router in
#                                 this list must have every ``{*_id}`` path
#                                 param constrained (UUID / int / any pattern;
#                                 we always apply DUAL_ID_PATH_PATTERN).
#   * ``DUAL_ID_URL_PREFIXES``  — URL spaces (per ADR 003) where the param
#                                 MUST carry DUAL_ID_PATH_PATTERN *exactly*.
#
# Routers outside these sets are deliberately left untouched — constraining
# them is not required by the policy and would be over-reach (e.g. routers
# whose IDs are genuinely opaque tokens, not dual-ID entities).
# ---------------------------------------------------------------------------
def _load_sensor_scope():
    """Import the authoritative router list + URL prefixes from the sensor.

    Returns ``(routers, url_prefixes)`` where ``routers`` is a list of live
    ``APIRouter`` objects. Pytest ``ParameterSet`` objects (from
    ``pytest.param``) are unwrapped to their first value (the router).
    """
    import importlib

    sensor = importlib.import_module(
        "tests.api.test_dual_id_route_shadowing"
    )

    def _unwrap(entry):
        # pytest.param(...) → ParameterSet with ``.values``; plain router otherwise.
        values = getattr(entry, "values", None)
        if values is not None:
            return values[0]
        return entry

    routers = [_unwrap(e) for e in getattr(sensor, "DUAL_ID_ROUTERS", [])]
    url_prefixes = tuple(getattr(sensor, "DUAL_ID_URL_PREFIXES", ()))
    return routers, url_prefixes


def discover_targets() -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    """Return ``(file_to_params, file_to_routervars)``.

    ``file_to_params``: maps an absolute source file path → set of path
    parameter names (ending in ``_id``) that still need the constraint.

    ``file_to_routervars``: maps an absolute source file path → set of
    module-scope ``APIRouter`` variable names that should receive a
    ``reorder_collection_before_item(<var>)`` call.
    """
    from uuid import UUID

    from fastapi import APIRouter
    from fastapi.routing import APIRoute

    from app.api.v1 import _path_patterns as pp

    assert pp.DUAL_ID_PATH_PATTERN == DUAL_ID_PATH_PATTERN, (
        "DUAL_ID_PATH_PATTERN drifted from the helper module; update the "
        "codemod constant."
    )

    def _param_pattern(param) -> str | None:
        fi = getattr(param, "field_info", None)
        if fi is None:
            return None
        pat = getattr(fi, "pattern", None)
        if pat:
            return pat
        for meta in getattr(fi, "metadata", None) or []:
            mp = getattr(meta, "pattern", None)
            if mp:
                return mp
        return None

    def _src_under_v1(endpoint) -> str | None:
        try:
            src = inspect.getsourcefile(endpoint)
        except (TypeError, OSError):
            return None
        if not src:
            return None
        norm = os.path.abspath(src)
        if f"{os.sep}app{os.sep}api{os.sep}v1{os.sep}" not in (norm + os.sep):
            return None
        return norm

    routers, url_prefixes = _load_sensor_scope()

    file_to_params: dict[str, set[str]] = defaultdict(set)
    file_to_routervars: dict[str, set[str]] = defaultdict(set)

    # --- (a) per-router allow-list: every {*_id} path param needs a pattern.
    for router in routers:
        for route in router.routes:
            if not isinstance(route, APIRoute) or "{" not in route.path:
                continue
            norm = _src_under_v1(route.endpoint)
            if not norm:
                continue
            for param in route.dependant.path_params:
                if not param.name.endswith("_id"):
                    continue
                t = getattr(param, "type_", None)
                if t is UUID or t is int:
                    continue
                if _param_pattern(param):  # any pattern satisfies this set
                    continue
                file_to_params[norm].add(param.name)

    # --- (b) ADR-003 URL spaces: param MUST carry DUAL_ID_PATH_PATTERN exactly.
    from app.main import app  # noqa: PLC0415 — heavy import kept lazy

    for route in app.routes:
        if not isinstance(route, APIRoute) or "{" not in route.path:
            continue
        if not any(route.path.startswith(p) for p in url_prefixes):
            continue
        norm = _src_under_v1(route.endpoint)
        if not norm:
            continue
        for param in route.dependant.path_params:
            if not param.name.endswith("_id"):
                continue
            if getattr(param, "type_", None) is UUID:
                continue
            if _param_pattern(param) == DUAL_ID_PATH_PATTERN:
                continue
            file_to_params[norm].add(param.name)

    # Router variables: any module-scope APIRouter in a file that has work.
    for norm in list(file_to_params):
        modname = _module_name_for(norm)
        if not modname:
            continue
        try:
            module = sys.modules.get(modname) or __import__(
                modname, fromlist=["*"]
            )
        except Exception:
            continue
        for attr, val in vars(module).items():
            if isinstance(val, APIRouter):
                file_to_routervars[norm].add(attr)

    return file_to_params, file_to_routervars


def _module_name_for(abspath: str) -> str | None:
    root = _repo_root()
    if not abspath.startswith(root):
        return None
    rel = abspath[len(root) + 1 :]
    if not rel.endswith(".py"):
        return None
    rel = rel[: -len(".py")]
    return rel.replace(os.sep, ".")


# ---------------------------------------------------------------------------
# Phase 2 — libcst transform.
# ---------------------------------------------------------------------------
ANNOTATED_PATH = cst.parse_expression(
    "Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)]"
)


def _is_str_annotation(ann: cst.BaseExpression | None) -> bool:
    return isinstance(ann, cst.Name) and ann.value == "str"


def _path_pattern_arg() -> cst.Arg:
    return cst.Arg(
        keyword=cst.Name("pattern"),
        value=cst.Name("DUAL_ID_PATH_PATTERN"),
        equal=cst.AssignEqual(
            whitespace_before=cst.SimpleWhitespace(""),
            whitespace_after=cst.SimpleWhitespace(""),
        ),
    )


def _inject_pattern_into_path_call(call: cst.Call) -> cst.Call:
    """Return a ``Path(...)`` call with ``pattern=DUAL_ID_PATH_PATTERN`` set
    (replacing any existing ``pattern=``), other args preserved."""
    new_args: list[cst.Arg] = []
    replaced = False
    for arg in call.args:
        if (
            arg.keyword is not None
            and isinstance(arg.keyword, cst.Name)
            and arg.keyword.value in ("pattern", "regex")
        ):
            new_args.append(_path_pattern_arg())
            replaced = True
        else:
            new_args.append(arg)
    if not replaced:
        new_args.append(_path_pattern_arg())
    # Normalise trailing-comma whitespace by relying on libcst defaults.
    cleaned: list[cst.Arg] = []
    for i, a in enumerate(new_args):
        cleaned.append(a.with_changes(comma=cst.MaybeSentinel.DEFAULT))
    return call.with_changes(args=cleaned)


class _DualIdTransformer(cst.CSTTransformer):
    def __init__(self, target_params: set[str]) -> None:
        self.target_params = target_params
        self.changed_params: set[str] = set()

    def leave_Param(
        self, original: cst.Param, updated: cst.Param
    ) -> cst.Param:
        name = updated.name.value
        if name not in self.target_params:
            return updated
        ann_node = updated.annotation.annotation if updated.annotation else None

        # Case A: ``x_id: str`` (optionally ``= Path(...)`` default).
        if _is_str_annotation(ann_node):
            default = updated.default
            if isinstance(default, cst.Call) and m.matches(
                default, m.Call(func=m.Name("Path"))
            ):
                # ``x_id: str = Path(...)`` → fold into Annotated, drop default.
                new_path = _inject_pattern_into_path_call(default)
                new_ann = cst.Annotation(
                    annotation=cst.Subscript(
                        value=cst.Name("Annotated"),
                        slice=[
                            cst.SubscriptElement(
                                slice=cst.Index(value=cst.Name("str"))
                            ),
                            cst.SubscriptElement(
                                slice=cst.Index(value=new_path)
                            ),
                        ],
                    )
                )
                self.changed_params.add(name)
                return updated.with_changes(
                    annotation=new_ann,
                    default=None,
                    equal=cst.MaybeSentinel.DEFAULT,
                )
            # Plain ``x_id: str`` (no Path default).
            self.changed_params.add(name)
            return updated.with_changes(
                annotation=cst.Annotation(annotation=ANNOTATED_PATH)
            )

        # Case B: ``x_id: Annotated[str, Path(...)]``.
        if isinstance(ann_node, cst.Subscript) and m.matches(
            ann_node.value, m.Name("Annotated")
        ):
            elements = list(ann_node.slice)
            new_elements: list[cst.SubscriptElement] = []
            injected = False
            for el in elements:
                idx = el.slice
                if isinstance(idx, cst.Index) and isinstance(
                    idx.value, cst.Call
                ) and m.matches(idx.value.func, m.Name("Path")):
                    new_call = _inject_pattern_into_path_call(idx.value)
                    new_elements.append(
                        el.with_changes(slice=cst.Index(value=new_call))
                    )
                    injected = True
                else:
                    new_elements.append(el)
            if not injected:
                # ``Annotated[str]`` or ``Annotated[str, Query(...)]`` etc.
                # Only add a Path metadata if first element is ``str``.
                if new_elements and isinstance(
                    new_elements[0].slice, cst.Index
                ) and _is_str_annotation(new_elements[0].slice.value):
                    new_elements.append(
                        cst.SubscriptElement(
                            slice=cst.Index(
                                value=cst.parse_expression(
                                    "Path(pattern=DUAL_ID_PATH_PATTERN)"
                                )
                            )
                        )
                    )
                    injected = True
            if injected:
                self.changed_params.add(name)
                return updated.with_changes(
                    annotation=cst.Annotation(
                        annotation=ann_node.with_changes(slice=new_elements)
                    )
                )

        return updated


# ---- import + reorder-call management on the module body ------------------
def _has_import_from(module: cst.Module, modname: str, name: str) -> bool:
    for stmt in module.body:
        if isinstance(stmt, cst.SimpleStatementLine):
            for small in stmt.body:
                if isinstance(small, cst.ImportFrom):
                    mod = _dotted(small.module)
                    if mod == modname and small.names is not None and not (
                        isinstance(small.names, cst.ImportStar)
                    ):
                        for alias in small.names:
                            if alias.name.value == name:
                                return True
    return False


def _dotted(node: cst.BaseExpression | None) -> str:
    if node is None:
        return ""
    if isinstance(node, cst.Name):
        return node.value
    if isinstance(node, cst.Attribute):
        return f"{_dotted(node.value)}.{node.attr.value}"
    return ""


def _import_line(text: str) -> cst.SimpleStatementLine:
    parsed = cst.parse_statement(text)
    assert isinstance(parsed, cst.SimpleStatementLine)
    return parsed


def _has_reorder_call(module: cst.Module, router_var: str) -> bool:
    target = f"{REORDER_CALL_NAME}({router_var})"
    for stmt in module.body:
        if isinstance(stmt, cst.SimpleStatementLine):
            for small in stmt.body:
                if isinstance(small, cst.Expr) and isinstance(
                    small.value, cst.Call
                ):
                    if m.matches(
                        small.value.func, m.Name(REORDER_CALL_NAME)
                    ):
                        if small.value.args and m.matches(
                            small.value.args[0].value, m.Name(router_var)
                        ):
                            return True
    return False


def transform_file(
    path: str, params: set[str], router_vars: Iterable[str]
) -> tuple[bool, set[str]]:
    """Apply the codemod to one file. Returns ``(changed, params_changed)``."""
    with open(path, encoding="utf-8") as fh:
        source = fh.read()
    module = cst.parse_module(source)

    transformer = _DualIdTransformer(params)
    new_module = module.visit(transformer)

    need_reorder = [
        rv
        for rv in router_vars
        if not _has_reorder_call(new_module, rv)
    ]

    if not transformer.changed_params and not need_reorder:
        return False, set()

    # --- ensure imports (only when we actually changed something) ----------
    new_body = list(new_module.body)

    imports_needed: list[str] = []
    if transformer.changed_params:
        if not _has_import_from(new_module, "typing", "Annotated"):
            imports_needed.append("from typing import Annotated")
        if not _has_import_from(new_module, "fastapi", "Path"):
            imports_needed.append("from fastapi import Path")
    helper_names_needed = []
    if transformer.changed_params and not _has_import_from(
        new_module, PATTERN_HELPER_MODULE, "DUAL_ID_PATH_PATTERN"
    ):
        helper_names_needed.append("DUAL_ID_PATH_PATTERN")
    if need_reorder and not _has_import_from(
        new_module, PATTERN_HELPER_MODULE, REORDER_CALL_NAME
    ):
        helper_names_needed.append(REORDER_CALL_NAME)
    if helper_names_needed:
        imports_needed.append(
            f"from {PATTERN_HELPER_MODULE} import "
            + ", ".join(helper_names_needed)
        )

    # Insert new imports after the last existing top-level import.
    if imports_needed:
        last_import_idx = -1
        for i, stmt in enumerate(new_body):
            if isinstance(stmt, cst.SimpleStatementLine) and any(
                isinstance(s, (cst.Import, cst.ImportFrom)) for s in stmt.body
            ):
                last_import_idx = i
        insert_at = last_import_idx + 1
        for offset, text in enumerate(imports_needed):
            new_body.insert(insert_at + offset, _import_line(text))

    # Append reorder calls at module end.
    for rv in need_reorder:
        call_stmt = cst.parse_statement(f"{REORDER_CALL_NAME}({rv})\n")
        # ensure a blank line before for readability
        new_body.append(call_stmt)

    new_module = new_module.with_changes(body=new_body)

    with open(path, "w", encoding="utf-8") as fh:
        fh.write(new_module.code)
    return True, transformer.changed_params


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--check",
        action="store_true",
        help="exit 1 if any router still needs blindagem (no writes)",
    )
    args = parser.parse_args(argv)

    sys.path.insert(0, _repo_root())

    file_to_params, file_to_routervars = discover_targets()

    if not file_to_params:
        print("No dual-ID path params need blindagem. Baseline is 0.")
        return 0

    total_params = sum(len(v) for v in file_to_params.values())
    print(
        f"Discovered {total_params} unconstrained dual-ID path params "
        f"across {len(file_to_params)} file(s)."
    )

    if args.check:
        for f, ps in sorted(file_to_params.items()):
            print(f"  NEEDS: {f}: {', '.join(sorted(ps))}")
        return 1

    if args.dry_run:
        for f, ps in sorted(file_to_params.items()):
            rv = file_to_routervars.get(f, set())
            print(f"  {f}")
            print(f"      params : {', '.join(sorted(ps))}")
            print(f"      routers: {', '.join(sorted(rv)) or '(none)'}")
        return 0

    files_changed = 0
    params_changed = 0
    reorders_added = 0
    for f, ps in sorted(file_to_params.items()):
        rv = file_to_routervars.get(f, set())
        changed, changed_params = transform_file(f, ps, rv)
        if changed:
            files_changed += 1
            params_changed += len(changed_params)
            reorders_added += len(rv)
            print(
                f"  fixed {f}: params={sorted(changed_params)} "
                f"routers={sorted(rv)}"
            )

    print(
        f"\nDone. files_changed={files_changed} "
        f"params_constrained={params_changed} "
        f"reorder_calls_ensured={reorders_added}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
