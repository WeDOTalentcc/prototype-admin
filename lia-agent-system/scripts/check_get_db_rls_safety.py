#!/usr/bin/env python3
"""
Sensor canonical (F11 2026-05-24): detecta endpoints que usam Depends(get_db)
mas escrevem em tabelas RLS-protected.

Contexto: PostgreSQL RLS policies (`WITH CHECK company_id = app_current_company_id()`)
bloqueiam INSERT/UPDATE/DELETE quando `app.company_id` GUC está NULL. Sessions
de `get_db` NÃO setam esse GUC; só `get_tenant_db` faz. Endpoints que escrevem
em tables com RLS habilitado precisam usar `get_tenant_db`.

Schema canonical (2026-05-24):
- 150 tables com RLS enabled (candidates, vacancy_candidates, job_vacancies,
  interviews, candidate_*, communication_*, agent_*, audit_logs, etc.)
- Fix: Depends(get_db) → Depends(get_tenant_db) em endpoints afetados

Modes:
  default (warn-only): exit 0
  --blocking: exit 1 if violations exist

Honra marker `# RLS-SAFE-EXEMPT: <reason>` na linha da assinatura da função
(casos raros como endpoints que só fazem CREATE TABLE em init que tem fallback).
"""
import argparse
import ast
import re
import sys
from pathlib import Path
from collections import defaultdict


# Tables with RLS enabled — verified 2026-05-24 via pg_class.relrowsecurity
RLS_TABLES = {
    "candidate_experience_highlights", "candidates", "vacancy_candidates",
    "job_vacancies", "interviews", "interview_notes", "candidate_attachments",
    "candidate_lists", "candidate_favorites", "candidate_hidden",
    "candidate_stage_history", "candidate_quarantines", "candidate_experiences",
    "candidate_education", "candidate_opt_outs", "communication_history",
    "communication_logs", "agent_execution_logs", "agent_quotas", "audit_logs",
    "ai_consumption", "ai_credits_balance", "lia_field_toggles",
    "conversation_memories", "graph_sessions", "approval_requests", "approvers",
    "company_culture_profiles", "company_benefits", "company_hiring_policies",
    "company_webhook_secrets", "data_subject_requests", "consent_events",
    "consent_records", "fairness_audit_log", "policy_evaluation_logs",
    "shared_searches", "ats_connections", "ats_stage_mappings",
    "ideal_profiles", "calibration_events", "calibration_weights",
    "bigfive_department_profiles",
}

SQL_WRITE_RE = re.compile(r"\b(INSERT INTO|UPDATE|DELETE FROM)\s+(\w+)", re.IGNORECASE)
REPO_WRITE_RE = re.compile(r"\.(save|insert|upsert|update|delete|create|store|persist)\w*\(")


def function_uses_get_db(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    for default in node.args.defaults + node.args.kw_defaults:
        if not (isinstance(default, ast.Call) and isinstance(default.func, ast.Name)):
            continue
        if default.func.id == "Depends" and default.args:
            first = default.args[0]
            if isinstance(first, ast.Name) and first.id == "get_db":
                return True
    return False


def function_uses_tenant_db(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    for default in node.args.defaults + node.args.kw_defaults:
        if not (isinstance(default, ast.Call) and isinstance(default.func, ast.Name)):
            continue
        if default.func.id == "Depends" and default.args:
            first = default.args[0]
            if isinstance(first, ast.Name) and first.id == "get_tenant_db":
                return True
    return False


def find_violations(root: Path) -> list[tuple[str, int, str, set[str], bool]]:
    """Returns [(file, lineno, function_name, write_tables, has_repo_write)]"""
    violations = []
    for py_file in root.rglob("*.py"):
        if "__pycache__" in py_file.parts or "tests" in py_file.parts:
            continue
        try:
            source = py_file.read_text(encoding="utf-8")
            tree = ast.parse(source)
        except (SyntaxError, UnicodeDecodeError):
            continue
        source_lines = source.splitlines()

        for node in ast.walk(tree):
            if not isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
                continue
            if not function_uses_get_db(node):
                continue

            # Honor exempt marker on function signature line
            sig_window = "\n".join(source_lines[max(0, node.lineno - 2):node.lineno + 2])
            if "RLS-SAFE-EXEMPT" in sig_window:
                continue

            func_source = ast.get_source_segment(source, node) or ""

            # Detect direct SQL writes to RLS tables
            direct_writes = set()
            for m in SQL_WRITE_RE.finditer(func_source):
                table = m.group(2).lower()
                if table in RLS_TABLES:
                    direct_writes.add(table)

            # Detect repo write calls (heuristic — repo may write to RLS table internally)
            has_repo_write = bool(REPO_WRITE_RE.search(func_source))

            if direct_writes or has_repo_write:
                violations.append((
                    str(py_file),
                    node.lineno,
                    node.name,
                    direct_writes,
                    has_repo_write,
                ))
    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blocking", action="store_true", help="Exit 1 on violations.")
    parser.add_argument("--root", default="/home/runner/workspace/lia-agent-system/app", help="App root.")
    parser.add_argument("--direct-only", action="store_true",
                        help="Only report direct SQL writes (skip repo .save heuristic)")
    args = parser.parse_args()

    root = Path(args.root)
    if not root.exists():
        print(f"❌ Root not found: {root}", file=sys.stderr)
        return 2

    print("check_get_db_rls_safety.py")
    print(f"Scanning {root} for Depends(get_db) writing to RLS-protected tables...\n")

    violations = find_violations(root)
    if args.direct_only:
        violations = [v for v in violations if v[3]]  # filter to direct only

    if not violations:
        print("✅ 0 violations — todos endpoints write-RLS usam get_tenant_db.")
        return 0

    by_file = defaultdict(list)
    for fp, lineno, fname, tables, has_repo in violations:
        by_file[fp].append((lineno, fname, tables, has_repo))

    for fp in sorted(by_file):
        rel_fp = fp.replace("/home/runner/workspace/lia-agent-system/", "")
        print(f"  ❌ {rel_fp}")
        for lineno, fname, tables, has_repo in by_file[fp]:
            kind = ", ".join(sorted(tables)) if tables else "(via repo write helper)"
            print(f"     L{lineno} {fname}() → writes: {kind}")
        print(f"     → Fix: Depends(get_db) → Depends(get_tenant_db) (em app.core.database)")
        print(f"     → Reason: RLS policy `(company_id)::text = app_current_company_id()`")
        print(f"              bloqueia escrita quando GUC NULL. get_tenant_db seta GUC via")
        print(f"              set_tenant_context.")
        print()

    print(f"Total: {len(violations)} endpoint(s) em risco.")
    return 1 if args.blocking else 0


if __name__ == "__main__":
    sys.exit(main())
