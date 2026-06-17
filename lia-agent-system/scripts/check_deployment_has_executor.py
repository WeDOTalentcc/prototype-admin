#!/usr/bin/env python3
"""Sensor (BLOCKING por default desde C1.2): todo trigger_mode de agent_deployments tem executor.

Fase 2.5 Onda C1-core.3 — harness guard do motor unificado (plano §C1).

PRINCÍPIO (harness-engineering, feedforward+feedback):
  Um deployment com um trigger_mode que NENHUM executor dispara é um "ghost
  deployment" — o recrutador acopla o agente à vaga/funil, marca ativo, e nada
  roda. É a classe de bug que motivou a Fase 2.5 inteira (motor não unificado).
  Este sensor garante que cada trigger_mode canonical tem um executor real
  (scheduler para on_schedule; event consumer para os event-based).

COMO FUNCIONA (computacional, não-inferencial):
  - Lê a matriz canonical VALID_TRIGGER_MODES_BY_TARGET de
    app/shared/trigger_mode_validation.py (single source of truth).
  - Para cada trigger_mode distinto, classifica em SCHEDULED vs EVENT_BASED.
  - SCHEDULED (on_schedule, scheduled): exige um scheduler que varra
    agent_deployments e dispare dispatch_agent_deployment_task — detectado por
    AST em app/jobs/tasks/agent_deployments.py (scan_impl + .delay()).
  - EVENT_BASED (on_apply, on_create, on_enter_stage, on_exit_stage,
    on_stuck_in_stage, on_stage_change): exige um event consumer que faça lookup
    em agent_deployments e dispare a dispatch task — detectado por AST nos
    consumers em app/jobs/consumers/.
  - manual: não precisa de executor automático (disparo via endpoint REST). OK.

PENDÊNCIA C1.2: o event consumer canonical de agent_deployments ainda não existe
  (será criado em C1.2). Por isso os trigger_modes event-based são reportados como
  "pendente C1.2" e o sensor roda WARN-ONLY por default. Promover a --blocking
  quando C1.2 fechar (o consumer existir + fizer lookup em agent_deployments).

Exit codes:
  0 — warn-only (sempre), ou blocking sem trigger_modes órfãos.
  1 — blocking com trigger_modes sem executor (> max).

Saída em PT-BR, otimizada pra consumo do LLM (instrução de fix embutida).
"""
from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DISPATCH_TASK_FILE = ROOT / "app" / "jobs" / "tasks" / "agent_deployments.py"
CONSUMERS_DIR = ROOT / "app" / "jobs" / "consumers"
TRIGGER_MATRIX_FILE = ROOT / "app" / "shared" / "trigger_mode_validation.py"

# Canonical scheduled modes (mirror agent_deployments._SCHEDULED_TRIGGER_MODES).
SCHEDULED_MODES = {"on_schedule", "scheduled"}
# manual = disparo via endpoint REST, sem executor automático.
MANUAL_MODES = {"manual"}

DISPATCH_TASK_NAME = "dispatch_agent_deployment_task"


def _load_canonical_trigger_modes() -> set[str]:
    """Extrai todos os trigger_modes da matriz canonical (AST, sem import)."""
    try:
        tree = ast.parse(TRIGGER_MATRIX_FILE.read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        return set()
    modes: set[str] = set()
    for node in ast.walk(tree):
        # Captura strings dentro de frozenset({...}) e Literal[...] da matriz.
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            v = node.value
            if v in SCHEDULED_MODES or v in MANUAL_MODES or v.startswith("on_"):
                modes.add(v)
    return modes


def _file_dispatches_deployment_task(path: Path) -> bool:
    """True se o arquivo varre agent_deployments E dispara dispatch_agent_deployment_task."""
    try:
        src = path.read_text(encoding="utf-8")
        tree = ast.parse(src)
    except (OSError, SyntaxError):
        return False
    references_table = "agent_deployment" in src.lower()
    dispatches = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr in ("delay", "apply_async"):
            val = node.value
            # dispatch_agent_deployment_task.delay(...)
            if isinstance(val, ast.Name) and val.id == DISPATCH_TASK_NAME:
                dispatches = True
            if isinstance(val, ast.Attribute) and val.attr == DISPATCH_TASK_NAME:
                dispatches = True
    return references_table and dispatches


def _scheduler_exists() -> bool:
    """Scheduler canonical = scan_impl em agent_deployments.py que dispara a task."""
    if not DISPATCH_TASK_FILE.exists():
        return False
    return _file_dispatches_deployment_task(DISPATCH_TASK_FILE)


def _event_consumer_exists() -> bool:
    """Event consumer canonical = consumer que faz lookup em agent_deployments e dispara."""
    if not CONSUMERS_DIR.exists():
        return False
    for path in CONSUMERS_DIR.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        if _file_dispatches_deployment_task(path):
            return True
    return False


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    # C1.2 (2026-05-29): event consumer canonical existe -> sensor BLOCKING por
    # default. --warn-only opt-out para branches legadas durante migracao.
    parser.add_argument("--blocking", action="store_true", default=True)
    parser.add_argument(
        "--warn-only",
        dest="warn_only",
        action="store_true",
        help="opt-out do modo blocking (default desde C1.2).",
    )
    parser.add_argument("--max-violations", type=int, default=0)
    args = parser.parse_args(argv)

    # --warn-only sobrescreve o default blocking.
    blocking = args.blocking and not args.warn_only

    modes = _load_canonical_trigger_modes()
    if not modes:
        print(
            "[deployment-executor sensor] AVISO: não consegui ler a matriz canonical "
            f"em {TRIGGER_MATRIX_FILE.relative_to(ROOT)}. Skip (não bloqueia).",
            file=sys.stderr,
        )
        return 0

    scheduled = {m for m in modes if m in SCHEDULED_MODES}
    event_based = {m for m in modes if m not in SCHEDULED_MODES and m not in MANUAL_MODES}

    has_scheduler = _scheduler_exists()
    has_consumer = _event_consumer_exists()

    print(
        "[deployment-executor sensor] trigger_modes canonical="
        f"{sorted(modes)}; scheduler={'OK' if has_scheduler else 'AUSENTE'}; "
        f"event_consumer={'OK' if has_consumer else 'pendente C1.2'}."
    )

    violations: list[str] = []

    # SCHEDULED modes precisam do scheduler (C1-core — você cria).
    if scheduled and not has_scheduler:
        for m in sorted(scheduled):
            violations.append(
                f"trigger_mode '{m}' (scheduled) sem scheduler. "
                f"Fix: scan_agent_deployment_cron_schedules em "
                f"app/jobs/tasks/agent_deployments.py deve varrer agent_deployments "
                f"is_active+on_schedule e chamar {DISPATCH_TASK_NAME}.delay()."
            )

    # EVENT_BASED modes precisam do consumer (C1.2 — pendente).
    if event_based and not has_consumer:
        pendentes = sorted(event_based)
        print(
            "[deployment-executor sensor] PENDENTE C1.2 — event consumer canonical de "
            "agent_deployments ainda não existe. trigger_modes event-based aguardando "
            f"executor: {pendentes}.\n"
            "  Fix (C1.2): criar consumer em app/jobs/consumers/ que escuta os eventos "
            "de plataforma (candidate_applied, stage_changed), faz lookup em "
            f"agent_deployments pelo trigger_mode e chama {DISPATCH_TASK_NAME}.delay(). "
            "Quando existir, promover este sensor a --blocking.",
            file=sys.stderr,
        )
        # Pendência C1.2 NÃO conta como violation blocking (decisão de plano:
        # warn-only inicial; promove BLOCKING quando C1.2 fechar).

    for v in violations:
        print(f"[deployment-executor sensor] VIOLATION: {v}", file=sys.stderr)

    if not violations and (not event_based or has_consumer):
        print("[deployment-executor sensor] OK — todo trigger_mode tem executor.")

    if blocking and len(violations) > args.max_violations:
        print(
            f"\n[deployment-executor sensor] BLOCKING: {len(violations)} > "
            f"max {args.max_violations}.",
            file=sys.stderr,
        )
        return 1
    if not blocking and (violations or (event_based and not has_consumer)):
        print(
            "[deployment-executor sensor] WARN-ONLY — não bloqueia. Promover a "
            "--blocking quando C1.2 (event consumer) fechar.",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
