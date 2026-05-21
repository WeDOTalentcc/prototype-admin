#!/usr/bin/env python3
"""Sensor canonical T-09 Fase 0: detecta imports de domains deprecated.

Domains deprecated (DOMAIN_CATALOG.md):
- app.domains.autonomous (legacy, supersedido por recruiter_assistant)
- app.domains.policy (supersedido por hiring_policy)

Plus shims em app/agents/ e app/shared/services/policy_engine_service.py.

Modo INICIAL: WARN-ONLY (Fase 0) — coletar telemetria 30 dias.
Promover BLOCKING após Fase 3 (migration completa).

Uso:
    python scripts/check_no_imports_from_deprecated.py [--strict]
"""
from __future__ import annotations

import re
import sys
from pathlib import Path


FORBIDDEN_PATTERNS = [
    (
        re.compile(r"\bfrom\s+app\.domains\.autonomous\b"),
        "app.domains.autonomous (use recruiter_assistant ou agent_studio)",
    ),
    (
        re.compile(r"\bimport\s+app\.domains\.autonomous\b"),
        "app.domains.autonomous (use recruiter_assistant ou agent_studio)",
    ),
    (
        re.compile(r"\bfrom\s+app\.domains\.policy\b"),
        "app.domains.policy (use app.domains.hiring_policy)",
    ),
    (
        re.compile(r"\bimport\s+app\.domains\.policy\b"),
        "app.domains.policy (use app.domains.hiring_policy)",
    ),
    (
        re.compile(r"\bfrom\s+app\.agents\.policy_setup_agent\b"),
        "app.agents.policy_setup_agent (shim deprecated)",
    ),
    (
        re.compile(r"\bfrom\s+app\.shared\.services\.policy_engine_service\b"),
        "app.shared.services.policy_engine_service (shim deprecated)",
    ),
]

EXEMPT_MARKER = "DEPRECATED-IMPORT-EXEMPT"

# Self-imports dos próprios deprecated paths são OK (eles importam entre si)
SELF_IMPORT_DIRS = (
    "app/domains/autonomous/",
    "app/domains/policy/",
)

# Tests podem testar deprecated imports
TEST_DIRS = (
    "tests/",
    "app/tests/",
)


def check(strict: bool = True) -> int:  # [PROMOTED BLOCKING Sprint 8 T-09]
    repo_root = Path(__file__).resolve().parent.parent
    app_dir = repo_root / "app"
    libs_dir = repo_root / "libs"
    scripts_dir = repo_root / "scripts"

    violations: list[tuple[str, int, str, str]] = []

    for base_dir in [app_dir, libs_dir, scripts_dir]:
        if not base_dir.exists():
            continue
        for py in base_dir.rglob("*.py"):
            if "__pycache__" in str(py):
                continue
            rel = str(py.relative_to(repo_root))

            # Skip self-imports + tests
            is_self = any(rel.startswith(d) for d in SELF_IMPORT_DIRS)
            is_test = any(rel.startswith(d) or "/tests/" in rel for d in TEST_DIRS)
            if is_self or is_test:
                continue

            try:
                content = py.read_text(encoding="utf-8")
            except Exception:
                continue

            lines = content.splitlines()
            for i, line in enumerate(lines, start=1):
                if EXEMPT_MARKER in line:
                    continue
                # Skip block comments / docstrings (best-effort)
                stripped = line.lstrip()
                if stripped.startswith("#"):
                    continue
                for pattern, target_msg in FORBIDDEN_PATTERNS:
                    if pattern.search(line):
                        violations.append((rel, i, line.strip()[:100], target_msg))
                        break

    if not violations:
        print("[T-09 ADR-019] OK -- 0 imports from deprecated domains")
        return 0

    print(f"[T-09 ADR-019] {len(violations)} imports from deprecated paths:")
    for rel, ln, line_text, msg in violations:
        print(f"  ⚠  {rel}:{ln}")
        print(f"     {line_text}")
        print(f"     -> {msg}")
    print()
    print("CORRECAO canonical:")
    print("  - autonomous: migrar para recruiter_assistant ou agent_studio")
    print("  - policy: migrar para hiring_policy")
    print("  - shims: deletar import, usar canonical")
    print("  - Para casos legítimos (Tier 6 router fallback): adicionar")
    print("    `# DEPRECATED-IMPORT-EXEMPT: <reason>` no fim da linha")
    print()
    mode = "BLOCKING" if strict else "WARN-ONLY"
    print(f"Mode: {mode}")
    return 0 if not strict else 1


if __name__ == "__main__":
    strict = "--warn-only" not in sys.argv  # [PROMOTED BLOCKING Sprint 8 T-09]
    sys.exit(check(strict=strict))
