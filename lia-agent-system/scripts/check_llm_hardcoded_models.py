#!/usr/bin/env python3
"""Sensor canonical: detecta model= hardcoded em chamadas LLM.

Regra LLM Tier canonical (Sprint D 2026-06-13):
  Modelos LLM devem ser resolvidos via ModelTierResolver, nao hardcoded.
  model="claude-sonnet-..." em agente = acoplamento que ignora tier policy e tenant override.

Detecta:
  - model="claude-..." ou model="gemini-..." hardcoded em app/domains/ e app/api/v1/
  - Excecoes: llm_models.py (definicoes), model_tier_resolver.py, fairness_guard.py, config.py

Modo: WARN-ONLY. Baseline estabelecido neste sprint.

Uso:
    python scripts/check_llm_hardcoded_models.py [--block]
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

MODEL_LITERAL_PATTERNS = [
    re.compile(r"claude-[a-z]+-\d"),
    re.compile(r"gemini-\d"),
    re.compile(r"gpt-4[o\-]"),
    re.compile(r"claude-opus"),
    re.compile(r"claude-haiku"),
    re.compile(r"claude-sonnet"),
]

EXEMPT_FILES = {
    "app/shared/llm_models.py",
    "app/shared/llm/model_tier_resolver.py",
    "app/shared/compliance/fairness_guard.py",
    "app/core/config.py",
    "app/shared/tenant_llm_context.py",
}

SCAN_DIRS = ["app/domains", "app/orchestrator", "app/api/v1"]


def check(block=False):
    repo_root = Path(__file__).resolve().parent.parent
    violations = []

    for scan_dir in SCAN_DIRS:
        target = repo_root / scan_dir
        if not target.exists():
            continue
        for py_file in target.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            rel = str(py_file.relative_to(repo_root))
            if rel in EXEMPT_FILES:
                continue
            try:
                source = py_file.read_text(encoding="utf-8")
            except Exception:
                continue
            for lineno, line in enumerate(source.splitlines(), 1):
                for pattern in MODEL_LITERAL_PATTERNS:
                    if pattern.search(line) and ("model=" in line or "model_name=" in line):
                        stripped = line.strip()
                        if stripped.startswith(("#", "import", "from", '"""', "'''")):
                            continue
                        violations.append((rel, lineno, stripped[:120]))
                        break

    if violations:
        print("[LLM-TIER] %d modelos hardcoded detectados:" % len(violations))
        for f, line, code in violations[:30]:
            print("  %s:%d -- %s" % (f, line, code))
        if len(violations) > 30:
            print("  ... e mais %d" % (len(violations) - 30))
        print()
        print("CORRECAO canonical:")
        print("  from app.shared.llm.model_tier_resolver import resolve_model_tier")
        print('  model = resolve_model_tier(domain="screening", confidence=confidence)')
        mode = "BLOCKING" if block else "WARN-ONLY"
        print("Mode: %s" % mode)
        return 1 if block else 0

    print("[LLM-TIER] OK -- 0 modelos hardcoded detectados")
    return 0


if __name__ == "__main__":
    sys.exit(check(block="--block" in sys.argv))
