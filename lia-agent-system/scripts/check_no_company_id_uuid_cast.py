#!/usr/bin/env python3
"""
Sensor canonical: detecta `CAST(:co AS uuid)` em queries que tocam tabelas
onde `company_id` é varchar (não uuid).

Contexto F10 FU-2 (2026-05-24): 29+ sites em 6 handlers usavam
`CAST(:co AS uuid)` em queries contra tabelas onde `company_id` é
`character varying`. Postgres rejeitava com:
    operator does not exist: character varying = uuid

Quebrava SILENCIOSAMENTE TODO chat-action de update (qualquer campo exceto
`name`, que tem endpoint dedicado). Origem provável: copy-paste antes de
2026-05-XX quando a coluna era uuid e foi migrada pra varchar.

Schema canonical (2026-05-24):
- 150 tabelas: `company_id character varying` (vacancy_candidates, candidates,
  job_vacancies, interviews, candidate_*, etc — hot path)
- 93 tabelas: `company_id uuid` (compliance_*, data_*, sox_*, governance tier)

Este sensor sinaliza sites onde `CAST(:co AS uuid)` (ou `CAST(:co2 AS uuid)`)
aparece em queries que tocam tabelas varchar conhecidas (`vacancy_candidates`,
`job_vacancies`, `candidates`, `interviews`). Não verifica TODOS os usos de
CAST (alguns são corretos contra tabelas uuid) — só pinning das tabelas hot.

Modes:
  --warn-only (default): exit 0, lista violations
  --blocking: exit 1 se houver violations
"""
import argparse
import re
import sys
from pathlib import Path

# Tabelas onde company_id é varchar (CAST AS uuid quebra).
# Lista canônica derivada de information_schema 2026-05-24.
VARCHAR_TABLES = {
    "vacancy_candidates",
    "job_vacancies",
    "candidates",
    "interviews",
    "candidate_experiences",
    "candidate_education",
    "candidate_attachments",
    "candidate_lists",
    "candidate_favorites",
    "candidate_hidden",
    "candidate_stage_history",
    "candidate_quarantines",
    "communication_history",
    "communication_logs",
    "audit_logs",
    "agent_execution_logs",
    "agent_quotas",
}

# Pattern: lines with CAST(:co AS uuid) — focus on params named `co`, `co2`,
# or `company_id` (the canonical company_id param names). CAST(:cid AS uuid)
# / CAST(:jid AS uuid) etc are correct because candidate_id/job_id ARE uuid.
CAST_PATTERN = re.compile(
    r"CAST\(:(co|co2|company_id|companyid|company)\s+AS\s+uuid\)",
    re.IGNORECASE,
)


def find_violations(root: Path) -> list[tuple[str, int, str, str]]:
    """Return [(file, lineno, table, line)] for violations."""
    violations: list[tuple[str, int, str, str]] = []
    for py_file in root.rglob("*.py"):
        if "__pycache__" in py_file.parts or "tests" in py_file.parts:
            continue
        try:
            lines = py_file.read_text(encoding="utf-8").splitlines()
        except (UnicodeDecodeError, OSError):
            continue
        for i, line in enumerate(lines):
            if not CAST_PATTERN.search(line):
                continue
            # Skip comments — pattern appears in docstrings explaining the bug.
            stripped = line.lstrip()
            if stripped.startswith("#") or stripped.startswith("//"):
                continue
            # Require SQL keyword on the same line or 1 above — filters out
            # docstring mentions like "The CAST(:co AS uuid) raised ...".
            sql_window = "\n".join(lines[max(0, i - 1) : i + 1]).upper()
            if not re.search(r"\b(WHERE|AND|JOIN|FROM|INSERT INTO|UPDATE|DELETE|SELECT|VALUES|SET)\b", sql_window):
                continue
            # Look at this line + 5 above for varchar table mention
            window = "\n".join(lines[max(0, i - 5) : i + 1]).lower()
            for table in VARCHAR_TABLES:
                # Require word boundary to avoid false positives
                if re.search(rf"\b{re.escape(table)}\b", window):
                    violations.append((str(py_file), i + 1, table, line.strip()))
                    break
    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blocking", action="store_true", help="Exit 1 on violations.")
    parser.add_argument("--root", default="app", help="Root dir to scan.")
    args = parser.parse_args()

    root = Path(args.root)
    if not root.exists():
        print(f"❌ Root dir not found: {root}", file=sys.stderr)
        return 2

    print("check_no_company_id_uuid_cast.py")
    print(f"Scanning {root} for CAST(:* AS uuid) in queries on varchar tables...\n")

    violations = find_violations(root)
    if not violations:
        print("✅ 0 violations — nenhum CAST(:* AS uuid) em queries hot-path varchar.")
        return 0

    for fp, ln, table, line in violations:
        print(f"  ❌ {fp}:{ln} (table=`{table}` is varchar)")
        print(f"     {line[:120]}")
        print(f"     → Fix: remover o CAST(:co AS uuid) — passar :co direto.")
        print(f"            Coluna company_id em `{table}` é character varying, não uuid.")
        print()

    print(f"Total: {len(violations)} violation(s).")
    return 1 if args.blocking else 0


if __name__ == "__main__":
    sys.exit(main())
