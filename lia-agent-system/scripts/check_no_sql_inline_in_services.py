#!/usr/bin/env python3
"""Sensor: services/ MUST NOT contain raw SQL inline (ADR-001).

ADR-001 — Repository Pattern (canonized 2026-05-06)
====================================================================

Services MUST NOT call `db.execute(text(...))`, `sa_text(...)`, or
`sqlalchemy.text(...)` for SQL queries. All SQL belongs in
`repositories/` (a layer below services). Cross-domain reads also via
the corresponding domain's repository, not raw SQL in the consuming
service.

Why:
- Multi-tenancy guard placement (`_require_company_id`) only works
  in the repository layer
- SQL refactor / DB migration safety (single chokepoint)
- Easier mocking in unit tests
- DB driver portability

Mode:
  - warn (default — Sprint 5.1 baseline ratchet, ~36 pre-existing hits
    documented as Caminho C policy)
  - --block after Sprint 5.4 backfill of 3 zero-repo domains

Allowlist:
  - tests/, scripts/, alembic/, migrations/
  - Files marked `# ADR-001-EXEMPT: <reason>` (legitimate SQL inline,
    e.g. Rails-owned table with schema variability)
  - Service files NOT under `app/domains/*/services/` (only domains)

This sensor uses pure regex — fast (~50ms across 200 files). AST would
catch slight formatting variations but adds dependency without value.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVICES_DIR = ROOT / "app" / "domains"

# Patterns that indicate raw SQL in a service file
PATTERNS = (
    re.compile(r"\bdb\.execute\s*\(\s*(?:sa\.)?text\s*\("),       # db.execute(text("..."))
    re.compile(r"\bsa_text\s*\("),                                 # sa_text("...")
    re.compile(r"\bsqlalchemy\.text\s*\("),                        # sqlalchemy.text("...")
    re.compile(r"\bdb\.execute\s*\(\s*\"\"\""),                    # db.execute("""SELECT ...""")
    re.compile(r"\bdb\.execute\s*\(\s*'''"),                       # db.execute('''SELECT ...''')
)

EXEMPT_MARKER = "ADR-001-EXEMPT"


def is_service_file(path: Path) -> bool:
    """`app/domains/*/services/*.py` only."""
    try:
        rel = path.relative_to(ROOT)
    except ValueError:
        return False
    parts = rel.parts
    return (
        len(parts) >= 4
        and parts[0] == "app"
        and parts[1] == "domains"
        and parts[3] == "services"
        and parts[-1].endswith(".py")
    )


# === Wave 2 audit 2026-05-21: extend coverage para agent layer em app/services/ ===
# Estes arquivos historicamente escaparam dos sensores ADR-001 porque vivem fora
# de app/domains/*/services/. Audit Agent B encontrou ~40+ violations entre eles.
# Wave 3 vai refatorar via repos canonical.
AGENT_LAYER_SERVICE_FILES = frozenset({
    "agent_marketplace_service.py",
    "sourcing_agent_orchestrator.py",
    "twin_inference_service.py",
    "twin_knowledge_indexer.py",
    "agent_approval_service.py",
    "agent_version_service.py",
    "multi_strategy_search.py",
    "agent_deployment_service.py",
    "agent_quality_evaluator.py",
    "agent_quality_gate.py",
})


def is_agent_layer_service(path):
    """Detect app/services/<agent_layer>.py files (audit Wave 2 2026-05-21 extension)."""
    try:
        rel = path.relative_to(ROOT)
    except ValueError:
        return False
    parts = rel.parts
    return (
        len(parts) == 3
        and parts[0] == "app"
        and parts[1] == "services"
        and parts[2] in AGENT_LAYER_SERVICE_FILES
    )


def has_exempt_marker(src: str) -> bool:
    return EXEMPT_MARKER in src


def scan_file(path: Path) -> list[tuple[int, str]]:
    findings: list[tuple[int, str]] = []
    try:
        src = path.read_text(encoding="utf-8")
    except Exception:
        return findings

    if has_exempt_marker(src):
        return findings

    for lineno, line in enumerate(src.splitlines(), start=1):
        for pat in PATTERNS:
            if pat.search(line):
                findings.append((lineno, line.strip()[:120]))
                break
    return findings


def main() -> int:
    # Sprint 7 (2026-05-07): promoted to blocking by default after sensor reached
    # 0 violations via Sprint 6 ScreeningQuestionSetRepository + WsiRepository
    # extension + Sprint 7 top-5 select() refactor. Use --warn-only to opt out
    # for legacy ratchet on branches that haven't caught up.
    warn_only = "--warn-only" in sys.argv
    block = not warn_only

    if not SERVICES_DIR.exists():
        print(f"[ADR-001 SQL sensor] WARN: {SERVICES_DIR} does not exist")
        return 0

    candidates = sorted(p for p in SERVICES_DIR.rglob("*.py") if is_service_file(p))
    # Wave 2 2026-05-21 extension: agent layer em app/services/.
    # Esses sao "warn-only" mesmo em block mode — Wave 3 vai fechar via repos canonical.
    agent_layer_dir = ROOT / "app" / "services"
    agent_files = []
    if agent_layer_dir.exists():
        agent_files = sorted(
            p for p in agent_layer_dir.rglob("*.py") if is_agent_layer_service(p)
        )
    candidates = candidates + agent_files
    agent_files_set = set(agent_files)
    findings_by_file: dict[Path, list[tuple[int, str]]] = {}
    total = 0
    blocking_total = 0  # Wave 2 extension: agent_layer findings count as warn-only
    for f in candidates:
        f_findings = scan_file(f)
        if f_findings:
            findings_by_file[f] = f_findings
            total += len(f_findings)
            if f not in agent_files_set:
                blocking_total += len(f_findings)

    if blocking_total == 0:
        if total > 0:
            # Agent layer findings exist but are warn-only — print briefly + exit 0
            agent_findings_count = total - blocking_total
            print(f"[ADR-001] WARN: {agent_findings_count} findings in app/services/ agent layer (warn-only, Wave 3 close):")
            for f, items in findings_by_file.items():
                if f in agent_files_set:
                    for ln, txt in items[:2]:  # show first 2 per file
                        try:
                            rel_f = f.relative_to(ROOT)
                        except ValueError:
                            rel_f = f
                        print(f"  {rel_f}:{ln}: {txt}")
        return 0
    # Replaced original `if total == 0:` block — original below is now dead but kept for compatibility
    if False:
        print(
            f"[ADR-001 SQL sensor] OK — scanned {len(candidates)} service files, "
            "0 raw SQL inline."
        )
        return 0

    for f, hits in findings_by_file.items():
        rel = f.relative_to(ROOT)
        for ln, snippet in hits:
            print(f"[ADR-001 SQL] {rel}:{ln}: {snippet}")

    print(
        f"\n[ADR-001 SQL sensor] Summary: {total} raw SQL hits across "
        f"{len(findings_by_file)} service files (of {len(candidates)} scanned).\n"
        "Per ADR-001: services MUST NOT call db.execute(text(...)) — move SQL\n"
        "to a repository in the same domain (`app/domains/<domain>/repositories/`).\n\n"
        "Caminho C policy: legacy hits stay warn-only; new code must be clean.\n"
        "Add `# ADR-001-EXEMPT: <reason>` comment for legitimate exceptions\n"
        "(e.g. Rails-owned tables with schema variability).\n",
        file=sys.stderr,
    )

    if block:
        print("[ADR-001 SQL sensor] BLOCKING mode (default since Sprint 7) — failing build.")
        return 1
    print("[ADR-001 SQL sensor] WARN-ONLY mode (opt-out via --warn-only flag).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
