#!/usr/bin/env python3
"""
Onda 3 F8 (2026-05-28) — sensor canonical para labels de trigger mode em UI.

Princípio:
  Componentes que renderizam trigger modes (on_create, on_enter_stage, ...)
  DEVEM passar pelos canonical i18n keys:
    - jobs.agents.triggerMode.{mode}     (target_type ∈ job/talent_pool/candidate_list)
    - pipeline.stage.triggerMode.{mode}  (target_type = pipeline_stage)

Detecção context-aware:
  Flag uma linha quando ela contém:
    (a) uma label hardcoded canonical, E
    (b) um sinal contextual de trigger_mode no MESMO arquivo
        (trigger_mode, triggerMode, target_type, TRIGGER_MODES_BY_TARGET,
         TriggerMode, on_enter_stage, on_exit_stage, on_create, on_schedule, ...)

  Reduz falsos positivos da palavra "Manualmente" usada em contextos não
  relacionados a trigger_mode (e.g., "Criar vaga manualmente").

Modo:
  warn-only por default. Promover a blocking quando baseline = 0.

Output otimizado pra consumo de LLM (instrução de fix em linguagem natural).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

CANONICAL_MODES = {
    "on_create", "on_schedule", "manual", "on_apply",
    "on_enter_stage", "on_exit_stage", "on_stuck_in_stage", "on_stage_change",
}

# Hardcoded labels we should NEVER find in component JSX/source.
HARDCODED_PT_TRIGGER_SPECIFIC = {
    # Stage-specific labels (lower false positive risk)
    "Quando a vaga for criada",
    "Sob agendamento",
    "Quando candidato aplicar",
    "Entrar nesta etapa",
    "Sair desta etapa",
    "Ficar travado nesta etapa",
    "Houver qualquer mudança",
}
HARDCODED_EN_TRIGGER_SPECIFIC = {
    "When the job is created",
    "On schedule",
    "When a candidate applies",
    "Enter this stage",
    "Exit this stage",
    "Get stuck in this stage",
}

# Contextual signals: presence in same file means trigger_mode is being handled.
TRIGGER_MODE_SIGNALS = (
    "trigger_mode",
    "triggerMode",
    "TriggerMode",
    "TRIGGER_MODES_BY_TARGET",
    "on_enter_stage",
    "on_exit_stage",
    "on_create",
    "on_schedule",
    "on_apply",
    "on_stuck_in_stage",
    "on_stage_change",
)

ALLOWLIST = {
    "messages/pt-BR.json",
    "messages/en.json",
    "src/lib/agents/triggerModeLabels.ts",
    "scripts/check_trigger_mode_label_canonical.py",
}


def is_allowlisted(path: Path) -> bool:
    rel = path.relative_to(ROOT).as_posix()
    return rel in ALLOWLIST


def has_trigger_context(text: str) -> bool:
    return any(sig in text for sig in TRIGGER_MODE_SIGNALS)


def scan(targets: list[Path]) -> list[tuple[Path, int, str, str]]:
    violations: list[tuple[Path, int, str, str]] = []
    labels = HARDCODED_PT_TRIGGER_SPECIFIC | HARDCODED_EN_TRIGGER_SPECIFIC
    for f in targets:
        if is_allowlisted(f):
            continue
        try:
            text = f.read_text(encoding="utf-8")
        except Exception:
            continue
        # Only consider files that handle trigger_mode at all.
        if not has_trigger_context(text):
            continue
        for i, line in enumerate(text.splitlines(), start=1):
            for label in labels:
                if label in line:
                    violations.append((f, i, label, line.strip()[:160]))
    return violations


def iter_sources() -> list[Path]:
    out: list[Path] = []
    for ext in (".tsx", ".ts"):
        out.extend(SRC.rglob(f"*{ext}"))
    return [
        p for p in out
        if "__tests__" not in p.parts
        and not p.name.endswith(".test.tsx")
        and not p.name.endswith(".test.ts")
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blocking", action="store_true",
                        help="Exit 1 on any violation (default warn-only).")
    parser.add_argument("--json", action="store_true",
                        help="Emit JSON output.")
    args = parser.parse_args()

    files = iter_sources()
    violations = scan(files)

    if args.json:
        out = {
            "total": len(violations),
            "violations": [
                {"file": p.relative_to(ROOT).as_posix(), "line": ln, "label": lbl, "snippet": snip}
                for (p, ln, lbl, snip) in violations
            ],
        }
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        if not violations:
            print("[trigger-mode-label] ok — 0 violations.")
        else:
            print(f"[trigger-mode-label] {len(violations)} violation(s):\n")
            for (p, ln, lbl, snip) in violations:
                rel = p.relative_to(ROOT).as_posix()
                if any(k in lbl.lower() for k in ("etapa", "stage")):
                    ns = "pipeline.stage.triggerMode"
                else:
                    ns = "jobs.agents.triggerMode"
                print(f"  [{rel}:{ln}] hardcoded label: \"{lbl}\"")
                print(f"    snippet: {snip}")
                print(
                    f"    -> Fix: substituir por t('<mode>') via useTranslations('{ns}'). "
                    "Mode canonical em VALID_TRIGGER_MODES_BY_TARGET (backend) + "
                    "TRIGGER_MODES_BY_TARGET (frontend src/types/agents/job-agent.ts).\n"
                )
            print(f"Total: {len(violations)} violation(s).")

        mode = "blocking (exit 1)" if args.blocking else "warn-only (exit 0)"
        print(f"Modo: {mode}")

    if args.blocking and violations:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
