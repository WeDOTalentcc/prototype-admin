#!/usr/bin/env python3
"""Sensor: tool schemas (parameters.properties) MUST NOT contain tenant context.

ADR-029 §2 — Canonical Tool Schemas
====================================

Tool schemas sent to the LLM at function-calling time must contain ONLY
user-facing parameters. Tenant context (`company_id`, `tenant_id`,
`organization_id`, `workspace_id`) belongs to the runtime context wrapper
(ADR-029 §3 RuntimeContext / ContextVar), NOT to the JSON schema the LLM sees.

Why:
- LLM seeing `company_id` in schema → asks the user for it (UX bug)
- LLM-provided tenant ID → tenant escalation surface (security bug)
- Multi-tenancy invariant (CLAUDE.md REGRA 1): `company_id` always
  comes from JWT/session ContextVar, never payload

This sensor is AST-based to avoid false positives on string mentions
(e.g. `description="company_id is auto-injected"`).

Mode:
  - warn (default Sprint 1, while fixes are landing)
  - --block after Sprint 1B remediation completes

Usage:
  python scripts/check_no_tenant_in_tool_schemas.py [--block]

Exit codes:
  0 = no findings, or warn-only mode
  1 = findings + --block flag

Allowlist:
  - tests/, scripts/, alembic/, migrations/, docs/, libs/
  - Files with marker `# SENSOR-EXEMPT: TOOL-TENANT-OK <reason>`
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Tenant-context keys that must NEVER appear in tool schema properties
TENANT_KEYS = frozenset({
    "company_id",
    "tenant_id",
    "organization_id",
    "workspace_id",  # workspace_id is the legacy Rails tenant field
})

ALLOWED_PREFIXES = (
    "tests/",
    "app/tests/",
    "scripts/",
    "alembic/",
    "migrations/",
    "docs/",
    "libs/",
)

EXEMPT_MARKER = "SENSOR-EXEMPT: TOOL-TENANT-OK"


def is_allowlisted(path: Path) -> bool:
    rel = str(path.relative_to(ROOT))
    return any(rel.startswith(p) for p in ALLOWED_PREFIXES)


def has_exempt_marker(src: str) -> bool:
    return EXEMPT_MARKER in src


def find_violations_in_dict(parameters_node: ast.Dict) -> list[tuple[int, str, str]]:
    """Scan a `parameters={...}` dict for tenant key leaks in properties/required."""
    findings: list[tuple[int, str, str]] = []

    for k_node, v_node in zip(parameters_node.keys, parameters_node.values):
        if not (isinstance(k_node, ast.Constant) and isinstance(k_node.value, str)):
            continue
        key_name = k_node.value

        if key_name == "properties" and isinstance(v_node, ast.Dict):
            for prop_key in v_node.keys:
                if isinstance(prop_key, ast.Constant) and isinstance(prop_key.value, str):
                    if prop_key.value in TENANT_KEYS:
                        findings.append((
                            prop_key.lineno,
                            "LEAK",
                            f"tool schema 'properties' contains tenant key "
                            f"'{prop_key.value}' (LLM will see this — ADR-029 §2 violation)",
                        ))

        elif key_name == "required" and isinstance(v_node, (ast.List, ast.Tuple)):
            for req_item in v_node.elts:
                if isinstance(req_item, ast.Constant) and isinstance(req_item.value, str):
                    if req_item.value in TENANT_KEYS:
                        findings.append((
                            req_item.lineno,
                            "REQUIRED-LEAK",
                            f"tool schema 'required' lists tenant key "
                            f"'{req_item.value}' "
                            f"(LLM forced to provide — critical ADR-029 §2 violation)",
                        ))

    return findings


def scan_file(path: Path) -> list[tuple[int, str, str]]:
    findings: list[tuple[int, str, str]] = []
    try:
        src = path.read_text(encoding="utf-8")
    except Exception:
        return findings

    if has_exempt_marker(src):
        return findings

    if not any(k in src for k in TENANT_KEYS):
        return findings

    try:
        tree = ast.parse(src, filename=str(path))
    except SyntaxError:
        return findings

    for node in ast.walk(tree):
        if isinstance(node, ast.keyword):
            if node.arg in ("parameters", "parameters_schema"):
                if isinstance(node.value, ast.Dict):
                    findings.extend(find_violations_in_dict(node.value))

    return findings


def main() -> int:
    block = "--block" in sys.argv

    candidates: list[Path] = []
    for pattern in (
        "**/agents/*tool_registry*.py",
        "**/tools/*_tools.py",
        "**/agents/*tools*.py",
    ):
        candidates.extend((ROOT / "app").glob(pattern))

    legacy_dir = ROOT / "app/tools"
    if legacy_dir.exists():
        candidates.extend(legacy_dir.glob("*.py"))

    candidates = [c for c in candidates if not is_allowlisted(c) and "__pycache__" not in str(c)]
    candidates = sorted(set(candidates))

    total_leak = 0
    total_required = 0
    files_with_findings = 0

    for f in candidates:
        findings = scan_file(f)
        if findings:
            files_with_findings += 1
            rel = f.relative_to(ROOT)
            for ln, severity, msg in findings:
                print(f"[ADR-029 sensor] {severity} {rel}:{ln}: {msg}")
                if severity == "REQUIRED-LEAK":
                    total_required += 1
                else:
                    total_leak += 1

    if total_leak == 0 and total_required == 0:
        print(
            f"[ADR-029 sensor] OK — scanned {len(candidates)} tool files, "
            "0 tenant key leaks in schemas."
        )
        return 0

    print(
        f"\n[ADR-029 sensor] Summary: {total_leak} LEAK + {total_required} REQUIRED-LEAK "
        f"across {files_with_findings} files (of {len(candidates)} scanned).\n"
        "Per ADR-029 §2: tool schemas must contain ONLY user-facing parameters.\n"
        "Tenant context (company_id, tenant_id, organization_id, workspace_id)\n"
        "must come from RuntimeContext / ContextVar — NEVER from LLM-generated args.\n\n"
        "Fix: remove the tenant key from `parameters.properties` AND `parameters.required`.\n"
        "Handler should read `company_id` from `_current_company_id` ContextVar (set by middleware),\n"
        "not from the LLM tool-call argument.\n",
        file=sys.stderr,
    )

    if block:
        return 1

    print("[ADR-029 sensor] WARN-ONLY mode — not blocking. Pass --block after Sprint 1B remediation.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
