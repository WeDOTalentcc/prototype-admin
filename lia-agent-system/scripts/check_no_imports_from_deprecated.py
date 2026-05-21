#!/usr/bin/env python3
"""Sensor canonical T-09: detecta imports de paths deprecated.

PREMISSA CORRIGIDA (Sprint 11, T-09 B+A combo 2026-05-21):
- `app.domains.policy/` é CANONICAL ATIVO (13 files, 2.343 LOC + 1.167 LOC v1 endpoints).
  hiring_policy/ (40 LOC) é STUB aspiracional — NÃO substitui policy/.
- `app.domains.autonomous/` é CANONICAL ATIVO (Tier 6 ReAct fallback do CascadedRouter,
  4 files, 2.218 LOC).
- Premissa V4 anterior ("policy/autonomous deprecated") foi confirmada errada via
  auditoria 2x (Agent #2 Sprint 8 + audit Sprint 11).
- Shim `app/services/policy_engine_service.py` + `app/shared/services/policy_engine_service.py`
  foram DELETADOS (T-09 Sprint 11 B+A combo) — callers usam canonical path direto.

Paths REAIS deprecated (única coisa que esse sensor monitora agora):
- `app.agents.policy_setup_agent` (shim — re-exporta de app.domains.policy.agents canonical)

Modo: BLOCKING (default). Use --warn-only para opt-out (legacy ratchet).

Uso:
    python scripts/check_no_imports_from_deprecated.py [--warn-only]
"""
from __future__ import annotations

import re
import sys
from pathlib import Path


FORBIDDEN_PATTERNS = [
    # Shim agent legacy (re-exporta de app.domains.policy.agents canonical)
    (
        re.compile(r"\bfrom\s+app\.agents\.policy_setup_agent\b"),
        "app.agents.policy_setup_agent (shim deprecated — use app.domains.policy.agents.agent)",
    ),
]

EXEMPT_MARKER = "DEPRECATED-IMPORT-EXEMPT"

# Self-imports do próprio path deprecated são OK (shim re-exporta canonical)
SELF_IMPORT_DIRS = (
    "app/agents/policy_setup_agent",
)

# Tests podem testar deprecated imports
TEST_DIRS = (
    "tests/",
    "app/tests/",
)


def check(strict: bool = True) -> int:  # [PROMOTED BLOCKING Sprint 8 T-09 → re-labeled Sprint 11]
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
        print("[T-09 ADR-019] OK -- 0 imports from deprecated paths")
        return 0

    print(f"[T-09 ADR-019] {len(violations)} imports from deprecated paths:")
    for rel, ln, line_text, msg in violations:
        print(f"  ⚠  {rel}:{ln}")
        print(f"     {line_text}")
        print(f"     -> {msg}")
    print()
    print("CORRECAO canonical:")
    print("  - app.agents.policy_setup_agent: usar app.domains.policy.agents.agent")
    print("    (PolicySetupAgent, policy_setup_agent são canonical em app.domains.policy.agents)")
    print("  - Para casos legítimos (test backward-compat, registration trigger):")
    print("    adicionar `# DEPRECATED-IMPORT-EXEMPT: <reason>` no fim da linha")
    print()
    mode = "BLOCKING" if strict else "WARN-ONLY"
    print(f"Mode: {mode}")
    return 0 if not strict else 1


if __name__ == "__main__":
    strict = "--warn-only" not in sys.argv  # [PROMOTED BLOCKING Sprint 8 T-09 → re-labeled Sprint 11]
    sys.exit(check(strict=strict))
