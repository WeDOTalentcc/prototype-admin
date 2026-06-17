"""Revert `Depends(require_company_id)` from endpoints that are PUBLIC.

Task #1143 — post-sweep correction.

The bulk sweep (apply_require_company_id.py) gates every endpoint with a
`Sprint follow-up` marker. Some of those endpoints are actually public
(reachable without JWT: auth bootstrap, webhook receivers, OAuth
callbacks, health checks, public WSI/data-subject flows). For those, the
gate would deny legitimate traffic with 401.

This script removes the injected `company_id: str = Depends(require_company_id)`
parameter and the helper import from:

  1. PUBLIC_FILES — files whose entire route surface is public.
  2. PUBLIC_FUNCTIONS — (file, function_name) overrides for files with
     mixed public/private routes (e.g. calendar OAuth callbacks).

Idempotent: re-running on a swept file is a no-op.
"""
from __future__ import annotations

import sys
from pathlib import Path

import libcst as cst

ROOT = Path(__file__).resolve().parent.parent
HELPER_NAME = "require_company_id"
HELPER_MODULE = "app.shared.security.require_company_id"

# Files whose every endpoint is reached WITHOUT a JWT.
# Mirrors PUBLIC_PATHS / PUBLIC_PREFIXES in app/middleware/auth_enforcement.py
# plus webhook-receive surfaces that resolve tenant via HMAC, not JWT.
PUBLIC_FILES = [
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
]

# Specific functions in mixed files that are OAuth callbacks /
# state-signed / pre-JWT. Keep the gate on the rest of the file.
PUBLIC_FUNCTIONS = {
    "app/api/v1/calendar.py": {
        "google_oauth_callback",
        "microsoft_oauth_callback",
        # google_oauth_auth_url / microsoft_oauth_auth_url take company_id
        # as a Query param — they pre-bind tenant before JWT context;
        # gating them as strict_match instead is done by wire_strict_match.py.
    },
    "app/api/v1/workos.py": set(),  # admin routes are NOT public — keep gated
    "app/api/v1/teams.py": {
        # Microsoft Teams app routes that auth via Teams SSO/state, not JWT.
        "teams_webhook",
        "teams_messages",
        "teams_auth_sso_page",
        "teams_auth_callback",
        "teams_manifest",
        "teams_manifest_zip",
    },
    "app/api/v1/webhooks.py": set(),  # webhook CRUD = authenticated user, keep gated
    "app/api/v1/whatsapp.py": {
        # GET/POST /webhook + /twilio-webhook = inbound provider
        "verify_webhook",
        "receive_webhook",
        "receive_twilio_webhook",
    },
    # Inbound provider webhooks in otherwise-authenticated files.
    # Tenant is resolved from HMAC-signed payload, not JWT.
    "app/api/v1/ats.py": {"receive_ats_webhook"},
    "app/api/v1/admin_platform.py": {"hubspot_webhook"},
    "app/api/v1/billing.py": {"handle_iugu_webhook"},
    "app/api/v1/interview_analysis.py": {"teams_meeting_webhook"},
    # SCIM provisioning webhooks — verified by WorkOS HMAC.
    "app/api/v1/workos.py": {"verify_scim_webhook", "scim_webhook"},
}


class RemoveGateTransformer(cst.CSTTransformer):
    def __init__(self, target_funcs: set[str] | None) -> None:
        """target_funcs=None means revert ALL functions in the file."""
        self.target_funcs = target_funcs
        self.removed_params: int = 0

    def _drop_param(self, params: cst.Parameters) -> cst.Parameters:
        kept = tuple(
            p for p in params.params
            if not (isinstance(p.name, cst.Name) and p.name.value == "company_id"
                    and isinstance(p.default, cst.Call)
                    and isinstance(p.default.func, cst.Name)
                    and p.default.func.value == "Depends"
                    and any(isinstance(a.value, cst.Name) and a.value.value == HELPER_NAME
                            for a in p.default.args))
        )
        if len(kept) != len(params.params):
            self.removed_params += 1
        return params.with_changes(params=kept)

    def leave_FunctionDef(self, original_node, updated_node):
        if self.target_funcs is not None and updated_node.name.value not in self.target_funcs:
            return updated_node
        return updated_node.with_changes(params=self._drop_param(updated_node.params))


def _drop_helper_import_if_unused(tree: cst.Module) -> cst.Module:
    """If the file no longer references require_company_id, drop the import."""
    code = tree.code
    # Count usages outside of import lines.
    code_no_imports = "\n".join(
        line for line in code.splitlines()
        if not (line.lstrip().startswith("from " + HELPER_MODULE)
                or line.lstrip().startswith("from app.shared.security"))
    )
    if HELPER_NAME in code_no_imports:
        return tree

    new_body = []
    for stmt in tree.body:
        if isinstance(stmt, cst.SimpleStatementLine):
            keep_inner = []
            for s in stmt.body:
                if isinstance(s, cst.ImportFrom):
                    mod = _mod(s.module) if s.module else ""
                    if mod == HELPER_MODULE:
                        continue
                keep_inner.append(s)
            if keep_inner:
                new_body.append(stmt.with_changes(body=keep_inner))
        else:
            new_body.append(stmt)
    return tree.with_changes(body=tuple(new_body))


def _mod(node) -> str:
    if isinstance(node, cst.Name):
        return node.value
    if isinstance(node, cst.Attribute):
        return f"{_mod(node.value)}.{node.attr.value}"
    return ""


def process_file(rel_path: str, target_funcs: set[str] | None, apply: bool) -> dict:
    p = ROOT / rel_path
    if not p.exists():
        return {"path": rel_path, "skipped_missing": True}
    src = p.read_text()
    if HELPER_NAME not in src:
        return {"path": rel_path, "skipped_no_gate": True}
    try:
        tree = cst.parse_module(src)
    except cst.ParserSyntaxError as e:
        return {"path": rel_path, "error": f"parse_error: {e}"}
    transformer = RemoveGateTransformer(target_funcs)
    new_tree = tree.visit(transformer)
    if transformer.removed_params == 0:
        return {"path": rel_path, "skipped_no_change": True}
    new_tree = _drop_helper_import_if_unused(new_tree)
    new_src = new_tree.code

    import ast
    try:
        ast.parse(new_src)
    except SyntaxError as e:
        return {"path": rel_path, "error": f"post_edit_parse_error: {e}"}

    if apply and new_src != src:
        p.write_text(new_src)
    return {"path": rel_path, "reverted": transformer.removed_params}


def main() -> int:
    apply = "--apply" in sys.argv
    totals = {"files": 0, "reverted": 0, "errors": 0}
    for f in PUBLIC_FILES:
        r = process_file(f, target_funcs=None, apply=apply)
        if r.get("error"):
            totals["errors"] += 1
            print(f"  ERR {f}: {r['error']}")
        elif r.get("reverted"):
            totals["files"] += 1
            totals["reverted"] += r["reverted"]
            print(f"  REVERT-FILE {f}: {r['reverted']} function(s)")
    for f, funcs in PUBLIC_FUNCTIONS.items():
        if not funcs:
            continue
        r = process_file(f, target_funcs=funcs, apply=apply)
        if r.get("error"):
            totals["errors"] += 1
            print(f"  ERR {f}: {r['error']}")
        elif r.get("reverted"):
            totals["files"] += 1
            totals["reverted"] += r["reverted"]
            print(f"  REVERT-FUNC {f}: {r['reverted']} function(s)")
    mode = "APPLY" if apply else "DRY-RUN"
    print(f"[revert_public_endpoints] mode={mode} files={totals['files']} "
          f"functions={totals['reverted']} errors={totals['errors']}")
    return 0 if totals["errors"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
