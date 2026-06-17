#!/usr/bin/env python3
"""Wave E Sensor 2 — Detecta payload={} ou candidateProfile={} literal em modais de operação IA.

Pattern anti-qualidade: passar objeto vazio literal como prop para modais que
executam operações IA (EvaluateWithTwin, VoiceInterview, calibração, etc.).
Resulta em chamadas IA sem contexto, produzindo outputs sem sentido ou erros.

Detecta:
- Props de componente com nome sugestivo de payload/perfil sendo passadas como {}
  literal: `candidateProfile={{}}`, `payload={{}}`, `agentConfig={{}}`, etc.
- Em arquivos pages-agent-studio/**/*.tsx

Honra marker: {/* SENSOR-EXEMPT: <reason> */} ou // SENSOR-EXEMPT: <reason>

Exit 0 = OK. Exit 1 = violations encontradas (BLOCKING).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "src" / "components" / "pages-agent-studio"

# Nomes de props que devem conter dados reais (não objeto vazio)
PAYLOAD_PROP_NAMES = [
    "candidateProfile",
    "candidate_profile",
    "agentConfig",
    "agent_config",
    "agentProfile",
    "jobContext",
    "job_context",
    "calibrationData",
    "calibration_data",
    "evaluationPayload",
    "voiceConfig",
    "voice_config",
    "interviewConfig",
    "interview_config",
]

# Pattern: propName={{}} — JSX prop com objeto vazio literal
JSX_EMPTY_OBJ_PROP_RE = re.compile(
    r'\b(?:' + "|".join(PAYLOAD_PROP_NAMES) + r')'
    r'\s*=\s*\{\{\}\}',
)

# Pattern mais genérico: qualquer prop "payload" ou "profile" com {}
GENERIC_PAYLOAD_RE = re.compile(
    r'\b(?:payload|profile|config)\s*=\s*\{\{\}\}',
)

EXEMPT_MARKER = "SENSOR-EXEMPT"


def check_file(path: Path) -> list[tuple[int, str]]:
    violations = []
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    for lineno, line in enumerate(lines, 1):
        if EXEMPT_MARKER in line:
            continue
        if JSX_EMPTY_OBJ_PROP_RE.search(line):
            prop_match = JSX_EMPTY_OBJ_PROP_RE.search(line)
            violations.append((
                lineno,
                f"Prop de payload passada como objeto vazio literal: {line.strip()!r}",
            ))
        elif GENERIC_PAYLOAD_RE.search(line):
            violations.append((
                lineno,
                f"Prop genérica de payload/profile/config passada como {{}}: {line.strip()!r}",
            ))
    return violations


def main() -> int:
    blocking = "--warn-only" not in sys.argv
    all_violations: list[tuple[Path, int, str]] = []

    for path in sorted(ROOT.rglob("*.tsx")):
        if "__tests__" in str(path) or ".next" in str(path):
            continue
        for lineno, msg in check_file(path):
            rel = path.relative_to(ROOT.parent.parent)
            all_violations.append((rel, lineno, msg))

    if not all_violations:
        print(f"[check_no_hardcoded_empty_payload] ✅ 0 violations — baseline limpo.")
        return 0

    print(f"[check_no_hardcoded_empty_payload] {'❌' if blocking else '⚠️'} {len(all_violations)} violation(s):\n")
    for rel_path, lineno, msg in all_violations:
        print(f"  [{rel_path}:{lineno}] {msg}")
        print(f"    → Fix: substituir {{}} pelo estado/prop com dados reais do contexto,")
        print(f"      ex: candidateProfile={{candidateData}} onde candidateData vem de useQuery.")
        print()

    if blocking:
        print(f"[check_no_hardcoded_empty_payload] BLOCKING — corrija antes de commitar.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
