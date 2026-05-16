"""Sweep FastAPI v1 endpoints to add explicit `Depends(require_company_id)` gate.

Task #1143 — Multi-tenant Ownership Foundation.

Looks for functions whose body contains a leading comment matching
`Sprint follow-up: add _require_company_id explicit gate` and:

  1. Inserts a parameter `company_id: str = Depends(require_company_id)`
     into the function signature (kw-only, last).
  2. Rewrites the marker comment to reflect that the gate is now active.
  3. Ensures the helper import is present at module top.

Files in `tests/.allowlist_public_endpoints.txt` (one path-substring per
line) are skipped — those are the auth-pre-JWT / health / webhook /
OAuth callback / public WSI endpoints that intentionally have no JWT.

Idempotent: re-running on a swept file is a no-op (no marker → skip).
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import List, Tuple

import libcst as cst
from libcst import matchers as m

ROOT = Path(__file__).resolve().parent.parent
API_DIR = ROOT / "app" / "api"
ALLOWLIST = ROOT / "tests" / ".allowlist_public_endpoints.txt"

TODO_MARKER_RE = re.compile(
    r"Sprint follow-up:\s*add\s*_require_company_id\s*explicit\s*gate", re.IGNORECASE
)
NEW_COMMENT = (
    "# multi-tenancy: gated via Depends(require_company_id) "
    "+ Postgres RLS runtime (Task #1143)"
)
HELPER_IMPORT_MODULE = "app.shared.security.require_company_id"
HELPER_NAME = "require_company_id"


def load_allowlist() -> List[str]:
    if not ALLOWLIST.exists():
        return []
    out = []
    for raw in ALLOWLIST.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        out.append(line)
    return out


def is_allowlisted(path: Path, allowlist: List[str]) -> bool:
    s = str(path.as_posix())
    return any(needle in s for needle in allowlist)


# ------- libcst transformer -------

class EndpointGateTransformer(cst.CSTTransformer):
    def __init__(self) -> None:
        self.modified_functions: int = 0
        self.skipped_already_gated: int = 0

    def _has_marker(self, body: cst.IndentedBlock) -> Tuple[bool, int]:
        """Find the index of the first body statement whose leading_lines
        contains the TODO marker comment.
        Returns (found, stmt_index)."""
        for idx, stmt in enumerate(body.body):
            for ll in stmt.leading_lines:
                if ll.comment and TODO_MARKER_RE.search(ll.comment.value):
                    return True, idx
        return False, -1

    def _already_has_param(self, params: cst.Parameters) -> bool:
        for p in list(params.params) + list(params.kwonly_params):
            if isinstance(p.name, cst.Name) and p.name.value == "company_id":
                return True
        return False

    def _strip_marker(self, body: cst.IndentedBlock) -> cst.IndentedBlock:
        """Remove the TODO marker comment lines (or rewrite to NEW_COMMENT)."""
        new_stmts = []
        replaced = False
        for stmt in body.body:
            new_leading = []
            for ll in stmt.leading_lines:
                if ll.comment and TODO_MARKER_RE.search(ll.comment.value):
                    if not replaced:
                        new_leading.append(
                            cst.EmptyLine(
                                indent=True,
                                whitespace=ll.whitespace,
                                comment=cst.Comment(value=NEW_COMMENT),
                                newline=ll.newline,
                            )
                        )
                        replaced = True
                    # else: drop duplicate marker lines
                else:
                    new_leading.append(ll)
            new_stmts.append(stmt.with_changes(leading_lines=new_leading))
        return body.with_changes(body=new_stmts)

    def _inject_param(self, params: cst.Parameters) -> cst.Parameters:
        new_param = cst.Param(
            name=cst.Name("company_id"),
            annotation=cst.Annotation(annotation=cst.Name("str")),
            default=cst.Call(
                func=cst.Name("Depends"),
                args=[cst.Arg(value=cst.Name(HELPER_NAME))],
            ),
        )
        # Append to the end of regular params (FastAPI treats it as keyword
        # since it has a default — order doesn't matter).
        return params.with_changes(params=tuple(params.params) + (new_param,))

    def _process_func(self, node):
        body = node.body
        if not isinstance(body, cst.IndentedBlock):
            return node
        found, _ = self._has_marker(body)
        if not found:
            return node
        if self._already_has_param(node.params):
            self.skipped_already_gated += 1
            new_body = self._strip_marker(body)
            return node.with_changes(body=new_body)
        new_params = self._inject_param(node.params)
        new_body = self._strip_marker(body)
        self.modified_functions += 1
        return node.with_changes(params=new_params, body=new_body)

    def leave_FunctionDef(self, original_node, updated_node):
        return self._process_func(updated_node)


# ------- import injector -------

def _ensure_imports(tree: cst.Module) -> cst.Module:
    """Add `from app.shared.security.require_company_id import require_company_id`
    and `from fastapi import Depends` if missing."""
    has_helper = False
    has_depends = False
    for stmt in tree.body:
        if not isinstance(stmt, cst.SimpleStatementLine):
            continue
        for sm in stmt.body:
            if isinstance(sm, cst.ImportFrom):
                mod = _module_dotted(sm.module) if sm.module else ""
                if mod == HELPER_IMPORT_MODULE:
                    for alias in sm.names or []:
                        if isinstance(alias, cst.ImportAlias) and isinstance(
                            alias.name, cst.Name
                        ) and alias.name.value == HELPER_NAME:
                            has_helper = True
                if mod == "fastapi":
                    for alias in sm.names or []:
                        if isinstance(alias, cst.ImportAlias) and isinstance(
                            alias.name, cst.Name
                        ) and alias.name.value == "Depends":
                            has_depends = True

    if has_helper and has_depends:
        return tree

    new_imports: list[cst.SimpleStatementLine] = []
    if not has_depends:
        new_imports.append(
            cst.parse_statement("from fastapi import Depends\n")  # type: ignore[arg-type]
        )
    if not has_helper:
        new_imports.append(
            cst.parse_statement(
                f"from {HELPER_IMPORT_MODULE} import {HELPER_NAME}\n"
            )  # type: ignore[arg-type]
        )

    # Insert after the last top-level import.
    last_import_idx = -1
    for i, stmt in enumerate(tree.body):
        if isinstance(stmt, cst.SimpleStatementLine) and any(
            isinstance(s, (cst.Import, cst.ImportFrom)) for s in stmt.body
        ):
            last_import_idx = i
    insert_at = last_import_idx + 1 if last_import_idx >= 0 else 0
    new_body = list(tree.body)
    for offset, imp in enumerate(new_imports):
        new_body.insert(insert_at + offset, imp)
    return tree.with_changes(body=tuple(new_body))


def _module_dotted(node) -> str:
    if isinstance(node, cst.Name):
        return node.value
    if isinstance(node, cst.Attribute):
        return f"{_module_dotted(node.value)}.{node.attr.value}"
    return ""


# ------- file processor -------

def process_file(path: Path, apply: bool) -> dict:
    src = path.read_text()
    if not TODO_MARKER_RE.search(src):
        return {"path": str(path), "skipped_no_marker": True}

    try:
        tree = cst.parse_module(src)
    except cst.ParserSyntaxError as e:
        return {"path": str(path), "error": f"parse_error: {e}"}

    transformer = EndpointGateTransformer()
    new_tree = tree.visit(transformer)
    if transformer.modified_functions == 0 and transformer.skipped_already_gated == 0:
        return {
            "path": str(path),
            "warning": "marker_present_but_no_function_matched",
            "remaining_markers": len(TODO_MARKER_RE.findall(new_tree.code)),
        }
    new_tree = _ensure_imports(new_tree)
    new_src = new_tree.code

    # Sanity: ast.parse the result.
    try:
        import ast
        ast.parse(new_src)
    except SyntaxError as e:
        return {"path": str(path), "error": f"post_edit_parse_error: {e}"}

    if apply and new_src != src:
        path.write_text(new_src)

    return {
        "path": str(path),
        "modified_functions": transformer.modified_functions,
        "skipped_already_gated": transformer.skipped_already_gated,
        "remaining_markers": len(TODO_MARKER_RE.findall(new_src)),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="Write changes (default: dry-run).")
    ap.add_argument("--path", help="Process a single file (relative to lia-agent-system/).")
    args = ap.parse_args()

    allowlist = load_allowlist()
    if args.path:
        files = [ROOT / args.path]
    else:
        files = sorted(API_DIR.rglob("*.py"))

    totals = {"modified": 0, "errors": 0, "files_touched": 0, "files_seen": 0}
    error_paths = []
    for f in files:
        if not f.is_file():
            continue
        if is_allowlisted(f, allowlist):
            continue
        totals["files_seen"] += 1
        r = process_file(f, apply=args.apply)
        if r.get("skipped_no_marker"):
            continue
        if r.get("error"):
            totals["errors"] += 1
            error_paths.append((str(f), r["error"]))
            continue
        if r.get("modified_functions", 0) > 0:
            totals["modified"] += r["modified_functions"]
            totals["files_touched"] += 1

    mode = "APPLY" if args.apply else "DRY-RUN"
    print(f"[apply_require_company_id] mode={mode}")
    print(f"  files scanned: {totals['files_seen']}")
    print(f"  files touched: {totals['files_touched']}")
    print(f"  functions gated: {totals['modified']}")
    print(f"  errors: {totals['errors']}")
    for p, e in error_paths[:20]:
        print(f"    ERR {p}: {e}")
    return 0 if totals["errors"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
