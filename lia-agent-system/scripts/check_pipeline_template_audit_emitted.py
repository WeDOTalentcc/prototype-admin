#!/usr/bin/env python3
"""AST sensor — PipelineTemplateService write methods MUST emit audit_service.log_decision.

LGPD/SOX-equiv canonical (CLAUDE.md): toda mutação de tenant data exige trail
auditável via audit_service.log_decision(action=..., company_id=..., ...).
Pipeline templates configuram fluxo de triagem — mudança não auditada quebra
controle interno de processo seletivo.

Métodos públicos que DEVEM emitir audit:
  create, update, archive, clone, apply_to_vacancy

Sensor lida gracefully com Fase 1.4 ainda pendente: se service file não existe,
exit 0 com mensagem informativa (não fail).

Exit:
  0 — service file inexistente (Fase 1.4 pendente) OU todos métodos OK
  1 — service existe mas algum método não emite log_decision
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "app" / "domains" / "pipeline" / "services" / "pipeline_template_service.py"

METHODS_REQUIRING_AUDIT = frozenset({
    "create",
    "update",
    "archive",
    "clone",
    "apply_to_vacancy",
})

ACCEPTED_AUDIT_ATTRS = frozenset({"log_decision", "_emit_audit"})  # _emit_audit é wrapper canonical do service
# Receivers aceitos: audit_service.log_decision(...), self.audit.log_decision(...),
# self.audit_service.log_decision(...). Detectamos por attr.attr == log_decision.


def function_emits_audit(func: ast.AsyncFunctionDef | ast.FunctionDef) -> bool:
    for node in ast.walk(func):
        if isinstance(node, ast.Call):
            target = node.func
            if isinstance(target, ast.Attribute) and target.attr in ACCEPTED_AUDIT_ATTRS:
                return True
    return False


def main() -> int:
    if not TARGET.exists():
        print("✅ Pipeline template audit sensor: service file ainda não criado (Fase 1.4 pendente)")
        return 0

    source = TARGET.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        print(f"❌ Syntax error em {TARGET}: {e}")
        return 1

    service_class: ast.ClassDef | None = None
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "PipelineTemplateService":
            service_class = node
            break

    if service_class is None:
        print("❌ class PipelineTemplateService não encontrada em pipeline_template_service.py")
        return 1

    offenders: list[tuple[str, int]] = []
    checked = 0
    for item in service_class.body:
        if not isinstance(item, (ast.AsyncFunctionDef, ast.FunctionDef)):
            continue
        name = item.name
        if name.startswith("_"):
            continue
        if name not in METHODS_REQUIRING_AUDIT:
            continue
        checked += 1
        if not function_emits_audit(item):
            offenders.append((name, item.lineno))

    if offenders:
        print(f"❌ PipelineTemplateService: {len(offenders)} método(s) sem audit_service.log_decision:")
        for name, lineno in offenders:
            print(f"  PipelineTemplateService.{name} (linha {lineno}): falta log_decision no body.")
            print(f"  → Fix: adicionar audit_service.log_decision(action=\"pipeline_template_{name}\", company_id=..., ...) ao final do método.")
        return 1

    print(f"✅ Pipeline template audit emitted OK ({checked} métodos checados)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
