#!/usr/bin/env python3
"""SENSOR canonical (harness-engineering -- guide + sensor computacional):
detecta missing imports (F821) em nodes/*.py do job_creation usando ruff
como engine.

Bug class historico (Fix J + Pendencia 5, 2026-05-27):
  PR-10 split (commit 5da1828f7 e cadeia) moveu nodes de graph.py para
  nodes/*.py mas SISTEMATICAMENTE esqueceu imports canonical:
  - resolve_seniority (services/seniority_resolver)
  - evaluate_wizard_policy (graph.py, circular -> lazy)
  - WSI_DEFAULT_DISTRIBUTION_COMPACT_PLENO (internal/constants)
  - _emit_wizard_step_audit (internal/audit)
  - _emit_pipeline_template_audit (internal/audit)
  - _apply_pipeline_template_to_state (internal/pipeline_template_helpers)
  - PipelineTemplateAuditAction (audit_actions)
  - classify_llm_exception_reason (helpers/llm_exceptions)
  - emit_audit_fire_and_forget (helpers/async_audit)
  - run_coro_in_threadpool (helpers/async_audit)
  - _wizard_dispatch (graph.py top-level alias)
  - _PUBLISH_DUAL_CONFIRMATION_TTL_S (graph.py, lazy)
  - _REVIEW_VALID_TARGET_SECTIONS (internal/constants)
  - emit_policy_block_audit (graph.py, lazy)
  - lia_wizard_fairness_l4_check_failed_total (graph.py, lazy)
  - Optional (typing)

  Total: 23+ NameError ATIVOS pos PR-10 split corrigidos por Fix J +
  Pendencia 5. Sem sensor estatico permanente, bug-class pode reaparecer
  no proximo refactor/split.

Estrategia: usar `ruff check --select F821` como engine (Python scope
analysis correta, sem falso positivos de implementacao caseira). Wrapper
canonical roda ruff filtrado em nodes/ + output otimizado para consumo
de LLM (file:line + sugestao de fix com origem canonical).

Honra escape hatch:
  Comentario `# noqa: F821` standard do ruff suprime na linha de uso.
  Use APENAS quando symbol e dinamico/intencional (raro).

Uso:
    python3 scripts/check_no_undefined_names_in_nodes.py            # BLOCKING default
    python3 scripts/check_no_undefined_names_in_nodes.py --warn     # warn-only
    python3 scripts/check_no_undefined_names_in_nodes.py --json     # JSON output

Baseline esperado: 0 violations (Fix J + Pendencia 5 zeraram).

Skill canonica: harness-engineering [guide computacional + sensor].
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCAN_ROOT = REPO_ROOT / "app" / "domains" / "job_creation" / "nodes"

# Mapeamento canonical conhecido: symbol -> origem canonical (file:linha)
# Acelera fix automatico sugerido no output do sensor.
CANONICAL_ORIGINS: dict[str, str] = {
    "resolve_seniority": "app.domains.job_creation.services.seniority_resolver",
    "evaluate_wizard_policy": "LAZY: from app.domains.job_creation.graph import evaluate_wizard_policy",
    "emit_policy_block_audit": "LAZY: from app.domains.job_creation.graph import emit_policy_block_audit",
    "lia_wizard_fairness_l4_check_failed_total": "LAZY: from app.domains.job_creation.graph import lia_wizard_fairness_l4_check_failed_total",
    "_PUBLISH_DUAL_CONFIRMATION_TTL_S": "LAZY: from app.domains.job_creation.graph import _PUBLISH_DUAL_CONFIRMATION_TTL_S",
    "_wizard_dispatch": "from app.domains.job_creation import dispatch_messages as _wizard_dispatch",
    "_REVIEW_VALID_TARGET_SECTIONS": "app.domains.job_creation.internal.constants",
    "_emit_wizard_step_audit": "app.domains.job_creation.internal.audit",
    "_emit_pipeline_template_audit": "app.domains.job_creation.internal.audit",
    "_apply_pipeline_template_to_state": "app.domains.job_creation.internal.pipeline_template_helpers",
    "WSI_DEFAULT_DISTRIBUTION_COMPACT_PLENO": "app.domains.job_creation.internal.constants",
    "PipelineTemplateAuditAction": "app.domains.job_creation.audit_actions",
    "classify_llm_exception_reason": "app.domains.job_creation.helpers.llm_exceptions",
    "emit_audit_fire_and_forget": "app.domains.job_creation.helpers.async_audit",
    "run_coro_in_threadpool": "app.domains.job_creation.helpers.async_audit",
    "Optional": "typing",
    "Any": "typing",
    "Dict": "typing",
    "List": "typing",
}


def run_ruff() -> list[dict]:
    """Executa `ruff check --select F821 --output-format=json` em SCAN_ROOT."""
    try:
        proc = subprocess.run(
            [
                sys.executable, "-m", "ruff", "check",
                str(SCAN_ROOT),
                "--select", "F821",
                "--output-format=json",
                "--no-cache",
            ],
            capture_output=True, text=True, cwd=str(REPO_ROOT),
            timeout=60,
        )
    except FileNotFoundError:
        print("ERROR: ruff not installed. Install via pip install ruff.")
        sys.exit(2)
    except subprocess.TimeoutExpired:
        print("ERROR: ruff timed out (>60s).")
        sys.exit(2)

    # ruff returns exit 1 when violations found; output goes to stdout
    if not proc.stdout.strip():
        return []
    try:
        data = json.loads(proc.stdout)
        return [v for v in data if v.get("code") == "F821"]
    except json.JSONDecodeError:
        print(f"ERROR: failed to parse ruff JSON output. stdout: {proc.stdout[:500]}")
        sys.exit(2)


def format_finding(violation: dict) -> str:
    name_match = violation.get("message", "").split("`")
    name = name_match[1] if len(name_match) >= 2 else "?"
    rel = Path(violation["filename"]).relative_to(REPO_ROOT)
    loc = violation.get("location", {})
    line = loc.get("row", "?")
    col = loc.get("column", "?")

    suggestion = CANONICAL_ORIGINS.get(name)
    fix_hint = (
        f" -> Fix sugerido: {suggestion}"
        if suggestion
        else " -> Encontre origem canonical: grep -rn 'def NAME\\|^NAME\\s*=' app/domains/job_creation/"
    ).replace("NAME", name)
    return f"  {rel}:{line}:{col} -- undefined {name!r}{fix_hint}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--warn", action="store_true", help="Warn-only mode (exit 0).")
    parser.add_argument("--json", action="store_true", help="JSON output.")
    args = parser.parse_args()

    findings = run_ruff()

    if args.json:
        print(json.dumps({
            "violations": findings,
            "total": len(findings),
            "engine": "ruff F821",
        }, indent=2))
        return 0 if not findings or args.warn else 1

    if not findings:
        print("[check_no_undefined_names_in_nodes] OK -- baseline 0 preserved (ruff F821).")
        return 0

    print("[check_no_undefined_names_in_nodes] VIOLATIONS (ruff F821):")
    print()
    for v in findings:
        print(format_finding(v))
    print()
    print(f"Total: {len(findings)} undefined names in nodes/*.py.")
    print()
    print("Fix steps canonical:")
    print("  1. Pra cada symbol N reportado, verificar origem em CANONICAL_ORIGINS")
    print("     deste sensor (mapping conhecido) OU rodar:")
    print("     grep -rn 'def N\\|class N\\|^N\\s*=' app/domains/job_creation/")
    print("  2. Adicionar import top-level (se symbol vive em services/, internal/,")
    print("     helpers/, audit_actions, typing -- nao ha circular import).")
    print("  3. Usar LAZY import dentro da node function se symbol vive em graph.py")
    print("     (circular import risk).")
    print("  4. Symbol dinamico/intencional? Adicionar `# noqa: F821` na linha de uso.")
    print()
    print("Audit history: Fix J (commit 1d0f23e24) + Pendencia 3 (329cd3ff0) +")
    print("  Pendencia 5 (este sensor) corrigiram 23+ NameError pos PR-10 split.")

    return 0 if args.warn else 1


if __name__ == "__main__":
    sys.exit(main())
