"""Structural verifier + sweep for `Depends(require_company_id)` on every
FastAPI router endpoint under ``app/api/``.

Task #1143 — supersedes the marker-based ``check_require_company_id_coverage.py``
ratchet (which only counted comment strings).

A router endpoint counts as **gated** when ANY of the following hold:

  1. A function parameter is ``... = Depends(require_company_id)`` OR
     ``... = Depends(require_company_id_strict_match(...))`` (regardless
     of the parameter's name — ``company_id``, ``_gate``, ``tenant``…).
  2. The decorator carries ``dependencies=[Depends(require_company_id), ...]``
     or ``dependencies=[Depends(require_company_id_strict_match(...)), ...]``.
  3. The function lives in a PUBLIC file or matches an entry in
     ``PUBLIC_FUNCTIONS`` (auth bootstrap / webhook receive / OAuth
     callbacks / health / public WSI).

Modes:
  --verify (default): exit 1 if any non-public endpoint lacks a gate.
                      Prints one line per gap.
  --apply           : inject ``company_id: str = Depends(require_company_id)``
                      into every gap-endpoint signature + ensures the
                      helper import is present.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

import libcst as cst

ROOT = Path(__file__).resolve().parent.parent
API_DIR = ROOT / "app" / "api"

HELPER_NAME = "require_company_id"
STRICT_NAME = "require_company_id_strict_match"
HELPER_MODULE = "app.shared.security.require_company_id"

ROUTER_METHODS = frozenset({
    "get", "post", "put", "patch", "delete",
    "head", "options", "websocket",
})

# Files whose entire route surface is public (no JWT).
PUBLIC_FILES = frozenset({
    "app/api/v1/auth.py",
    "app/api/v1/openmic_webhook.py",
    "app/api/v1/mailgun_webhooks.py",
    "app/api/v1/merge_webhooks.py",
    "app/api/v1/whatsapp_webhook.py",
    "app/api/v1/external_webhooks.py",
    "app/api/v1/job_status_webhooks.py",
    "app/api/v1/twilio_voice.py",
    "app/api/v1/email_tracking.py",
    "app/api/v1/system_health.py",
    "app/api/v1/rails_health.py",
    "app/api/v1/health_langgraph.py",
    "app/api/v1/navigation_intent.py",
    "app/api/public/candidate_portal.py",
    "app/api/public/shared_searches.py",
    "app/api/wsi_endpoints.py",
})

# Specific functions in mixed files that are pre-JWT (OAuth callbacks,
# Teams app SSO, inbound provider webhooks).
PUBLIC_FUNCTIONS: dict[str, frozenset[str]] = {
    "app/api/v1/calendar.py": frozenset({
        "google_oauth_callback", "microsoft_oauth_callback",
    }),
    "app/api/v1/teams.py": frozenset({
        "teams_webhook", "teams_messages",
        "teams_auth_sso_page", "teams_auth_callback",
        "teams_manifest", "teams_manifest_zip",
    }),
    "app/api/v1/whatsapp.py": frozenset({
        "verify_webhook", "receive_webhook", "receive_twilio_webhook",
    }),
    # Inbound provider webhooks in otherwise-authenticated files.
    # Tenant is resolved from HMAC-signed payload, not JWT.
    "app/api/v1/ats.py": frozenset({
        "receive_ats_webhook",
    }),
    "app/api/v1/admin_platform.py": frozenset({
        "hubspot_webhook",
    }),
    "app/api/v1/billing.py": frozenset({
        "handle_iugu_webhook",
    }),
    "app/api/v1/interview_analysis.py": frozenset({
        "teams_meeting_webhook",
    }),
    "app/api/v1/workos.py": frozenset({
        "verify_scim_webhook", "scim_webhook",
    }),
}


# ---------------- AST helpers ----------------

def _is_dep_helper_value(value: cst.BaseExpression) -> bool:
    """``Depends(require_company_id)`` or
    ``Depends(require_company_id_strict_match(...))`` matcher."""
    if not isinstance(value, cst.Call):
        return False
    if not (isinstance(value.func, cst.Name) and value.func.value == "Depends"):
        return False
    for arg in value.args:
        inner = arg.value
        if isinstance(inner, cst.Name) and inner.value == HELPER_NAME:
            return True
        if isinstance(inner, cst.Call) and isinstance(inner.func, cst.Name) \
                and inner.func.value == STRICT_NAME:
            return True
    return False


def _has_router_decorator(node: cst.FunctionDef) -> Optional[str]:
    """Return the HTTP method (e.g. ``"post"``) if this function is a
    router endpoint, else None."""
    for dec in node.decorators:
        d = dec.decorator
        if isinstance(d, cst.Call) and isinstance(d.func, cst.Attribute):
            if d.func.attr.value in ROUTER_METHODS:
                return d.func.attr.value
        elif isinstance(d, cst.Attribute) and d.attr.value in ROUTER_METHODS:
            return d.attr.value
    return None


def _is_plain_gate_value(value: cst.BaseExpression) -> bool:
    """True ONLY for ``Depends(require_company_id)`` (not strict_match)."""
    if not isinstance(value, cst.Call):
        return False
    if not (isinstance(value.func, cst.Name) and value.func.value == "Depends"):
        return False
    for arg in value.args:
        inner = arg.value
        if isinstance(inner, cst.Name) and inner.value == HELPER_NAME:
            return True
    return False


def _extract_route_path(decorators) -> Optional[str]:
    for dec in decorators:
        call = dec.decorator
        if not isinstance(call, cst.Call):
            continue
        if not (isinstance(call.func, cst.Attribute)
                and call.func.attr.value in ROUTER_METHODS):
            continue
        for a in call.args:
            if isinstance(a.value, cst.SimpleString):
                return a.value.evaluated_value
    return None


_EXPLICIT_SOURCE_MARKERS = frozenset({"Path", "Query", "Body", "Form"})


def _has_explicit_company_id_input(node: cst.FunctionDef) -> bool:
    """True iff the endpoint declares a sibling ``company_id`` param sourced
    from path / query / body / form (explicit marker OR implicit scalar)."""
    route_path = _extract_route_path(node.decorators)
    all_params = (
        list(node.params.params)
        + list(node.params.kwonly_params)
        + list(node.params.posonly_params)
    )
    for p in all_params:
        if not (isinstance(p.name, cst.Name) and p.name.value == "company_id"):
            continue
        d = p.default
        # Explicit marker.
        if isinstance(d, cst.Call) and isinstance(d.func, cst.Name) \
                and d.func.value in _EXPLICIT_SOURCE_MARKERS:
            return True
        # Implicit scalar path/query (no FastAPI source, scalar annotation).
        if d is None:
            ann = p.annotation
            if ann is not None and isinstance(ann.annotation, cst.Name) \
                    and ann.annotation.value in ("str", "int", "UUID", "float"):
                return True
    return False


def _has_plain_gate(node: cst.FunctionDef) -> bool:
    all_params = (
        list(node.params.params)
        + list(node.params.kwonly_params)
        + list(node.params.posonly_params)
    )
    for p in all_params:
        if p.default is not None and _is_plain_gate_value(p.default):
            return True
    return False


def _has_gate(node: cst.FunctionDef) -> bool:
    # 1. Parameter-level dependency
    all_params = (
        list(node.params.params)
        + list(node.params.kwonly_params)
        + list(node.params.posonly_params)
    )
    for p in all_params:
        if p.default is not None and _is_dep_helper_value(p.default):
            return True
    # 2. Decorator-level dependencies=[...]
    for dec in node.decorators:
        d = dec.decorator
        if not isinstance(d, cst.Call):
            continue
        for arg in d.args:
            if arg.keyword is None or arg.keyword.value != "dependencies":
                continue
            val = arg.value
            if isinstance(val, cst.List):
                for el in val.elements:
                    if _is_dep_helper_value(el.value):
                        return True
            elif isinstance(val, cst.Tuple):
                for el in val.elements:
                    if _is_dep_helper_value(el.value):
                        return True
    return False


# ---------------- transformer / collector ----------------

class EnforceTransformer(cst.CSTTransformer):
    def __init__(self, file_rel: str) -> None:
        self.file_rel = file_rel
        self.public_func_set = PUBLIC_FUNCTIONS.get(file_rel, frozenset())
        self.gaps: list[str] = []
        self.strict_gaps: list[str] = []
        self.injected: int = 0

    def _is_public(self, func_name: str) -> bool:
        if self.file_rel in PUBLIC_FILES:
            return True
        return func_name in self.public_func_set

    def leave_FunctionDef(self, original_node, updated_node):
        method = _has_router_decorator(updated_node)
        if not method:
            return updated_node
        func_name = updated_node.name.value
        if self._is_public(func_name):
            return updated_node
        if _has_gate(updated_node):
            # Strict-match audit: when an endpoint declares an explicit
            # company_id input (path/query/body/form) but only uses the
            # plain gate, mismatch JWT-vs-payload would not 403.
            if _has_plain_gate(updated_node) and _has_explicit_company_id_input(updated_node):
                self.strict_gaps.append(
                    f"{self.file_rel}::{func_name} (@router.{method}) "
                    f"— has explicit company_id input + plain gate; "
                    f"use require_company_id_strict_match(...)"
                )
            return updated_node
        self.gaps.append(f"{self.file_rel}::{func_name} (@router.{method})")
        # Inject `company_id: str = Depends(require_company_id)` as the
        # last parameter. Default value makes it keyword — order safe.
        new_param = cst.Param(
            name=cst.Name("company_id"),
            annotation=cst.Annotation(annotation=cst.Name("str")),
            default=cst.Call(
                func=cst.Name("Depends"),
                args=[cst.Arg(value=cst.Name(HELPER_NAME))],
            ),
        )
        new_params = updated_node.params.with_changes(
            params=tuple(updated_node.params.params) + (new_param,)
        )
        self.injected += 1
        return updated_node.with_changes(params=new_params)


# ---------------- import injector ----------------

def _module_dotted(node) -> str:
    if isinstance(node, cst.Name):
        return node.value
    if isinstance(node, cst.Attribute):
        return f"{_module_dotted(node.value)}.{node.attr.value}"
    return ""


def _ensure_imports(tree: cst.Module) -> cst.Module:
    has_helper = False
    has_depends = False
    for stmt in tree.body:
        if not isinstance(stmt, cst.SimpleStatementLine):
            continue
        for sm in stmt.body:
            if isinstance(sm, cst.ImportFrom):
                mod = _module_dotted(sm.module) if sm.module else ""
                if mod == HELPER_MODULE and sm.names:
                    for alias in sm.names:
                        if isinstance(alias, cst.ImportAlias) and isinstance(
                            alias.name, cst.Name
                        ) and alias.name.value == HELPER_NAME:
                            has_helper = True
                if mod == "fastapi" and sm.names:
                    for alias in sm.names:
                        if isinstance(alias, cst.ImportAlias) and isinstance(
                            alias.name, cst.Name
                        ) and alias.name.value == "Depends":
                            has_depends = True

    new_imports: list[cst.SimpleStatementLine] = []
    if not has_depends:
        new_imports.append(cst.parse_statement("from fastapi import Depends\n"))  # type: ignore[arg-type]
    if not has_helper:
        new_imports.append(
            cst.parse_statement(
                f"from {HELPER_MODULE} import {HELPER_NAME}\n"
            )  # type: ignore[arg-type]
        )

    if not new_imports:
        return tree

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


# ---------------- file processor ----------------

def process_file(path: Path, apply: bool) -> dict:
    rel = path.relative_to(ROOT).as_posix()
    try:
        src = path.read_text(encoding="utf-8")
    except Exception as e:
        return {"path": rel, "error": f"read: {e}"}
    try:
        tree = cst.parse_module(src)
    except cst.ParserSyntaxError as e:
        return {"path": rel, "error": f"parse: {e}"}
    transformer = EnforceTransformer(rel)
    new_tree = tree.visit(transformer)
    base = {
        "path": rel,
        "gaps": transformer.gaps,
        "strict_gaps": transformer.strict_gaps,
        "injected": transformer.injected,
    }
    if transformer.injected == 0:
        return base
    new_tree = _ensure_imports(new_tree)
    new_src = new_tree.code
    import ast
    try:
        ast.parse(new_src)
    except SyntaxError as e:
        return {**base, "error": f"post_edit_parse: {e}"}
    if apply:
        path.write_text(new_src, encoding="utf-8")
    return base


def collect_files() -> list[Path]:
    return sorted(API_DIR.rglob("*.py"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true",
                    help="Inject the gate into endpoints missing it.")
    ap.add_argument("--verify", action="store_true",
                    help="(default) Verify only; exit 1 if any gap remains.")
    ap.add_argument("--strict", action="store_true",
                    help="Also block when an endpoint has explicit "
                         "company_id input + plain (non-strict_match) gate.")
    args = ap.parse_args()
    apply = args.apply

    all_gaps: list[str] = []
    all_strict_gaps: list[str] = []
    total_injected = 0
    errors: list[tuple[str, str]] = []
    for f in collect_files():
        r = process_file(f, apply=apply)
        if r.get("error"):
            errors.append((r["path"], r["error"]))
            continue
        all_gaps.extend(r.get("gaps", []))
        all_strict_gaps.extend(r.get("strict_gaps", []))
        total_injected += r.get("injected", 0)

    mode = "APPLY" if apply else "VERIFY"
    if apply:
        print(f"[enforce_require_company_id] mode={mode} "
              f"endpoints_injected={total_injected} files_scanned={len(collect_files())} "
              f"errors={len(errors)}")
    else:
        print(f"[enforce_require_company_id] mode={mode} "
              f"gap_endpoints={len(all_gaps)} "
              f"strict_match_gaps={len(all_strict_gaps)} "
              f"files_scanned={len(collect_files())} "
              f"errors={len(errors)}")
        for g in all_gaps[:50]:
            print(f"  GAP {g}")
        if len(all_gaps) > 50:
            print(f"  ... and {len(all_gaps) - 50} more")
        for g in all_strict_gaps[:50]:
            print(f"  STRICT-GAP {g}")
        if len(all_strict_gaps) > 50:
            print(f"  ... and {len(all_strict_gaps) - 50} more strict")
    for p, e in errors[:10]:
        print(f"  ERR {p}: {e}")
    if errors:
        return 2
    if not apply and all_gaps:
        return 1
    if not apply and args.strict and all_strict_gaps:
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
