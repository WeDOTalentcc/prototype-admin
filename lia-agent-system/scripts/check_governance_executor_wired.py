#!/usr/bin/env python3
"""
Sensor anti-regressão · W1-004 Phase A (2026-05-22)

Verifica que `ToolExecutor.execute()` em `app/tools/executor.py` integra os
3 governance steps minimum viable (sem exigir migração ToolContract):

Step 2 (multi-tenancy fail-closed):
  - context.company_id obrigatório (retorno ToolResult success=False quando ausente)

Step 7 (audit log per-call):
  - AuditService.log_action chamado para toda execute() (sucesso E falha)
  - asyncio.create_task pra não bloquear execução

Step 8 (metrics):
  - _emit_metrics chamado em sucesso E falha

Bonus: GovernanceExecutor (canonical 8-step pattern) preservada para
futuros callers que adotarem ToolContract.

Pattern violação detectada:
- Remover company_id check (regressão multi-tenancy)
- Remover AuditService.log_action calls (compliance gap)
- Remover _emit_metrics (observability gap)
- Deletar GovernanceExecutor class (perde-se canonical pattern)

Mensagem em PT-BR com fix sugerido em sintaxe exata (harness pattern CLAUDE.md).

Modo: BLOCKING por default. `--warn-only` para opt-out.
"""
from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EXECUTOR_FILE = REPO_ROOT / "app" / "tools" / "executor.py"


def _find_class(tree: ast.Module, name: str) -> ast.ClassDef | None:
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == name:
            return node
    return None


def _find_method(cls: ast.ClassDef, name: str) -> ast.AsyncFunctionDef | ast.FunctionDef | None:
    for node in cls.body:
        if isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)) and node.name == name:
            return node
    return None


def check_executor_file_present() -> list[str]:
    errors: list[str] = []
    if not EXECUTOR_FILE.exists():
        errors.append(
            f"❌ Arquivo ausente: {EXECUTOR_FILE.relative_to(REPO_ROOT)}\n"
            "   FIX: ToolExecutor + GovernanceExecutor devem viver em\n"
            "        app/tools/executor.py (canonical W1-004)"
        )
    return errors


def check_tool_executor_governance_wired() -> list[str]:
    """Verifica que ToolExecutor.execute() tem os 3 governance steps."""
    errors: list[str] = []
    if not EXECUTOR_FILE.exists():
        return errors

    src = EXECUTOR_FILE.read_text(encoding="utf-8")
    try:
        tree = ast.parse(src)
    except SyntaxError as exc:
        errors.append(f"❌ Syntax error em {EXECUTOR_FILE.name}: {exc}")
        return errors

    tool_exec = _find_class(tree, "ToolExecutor")
    if tool_exec is None:
        errors.append(
            "❌ Classe ToolExecutor não encontrada\n"
            "   FIX: restaurar class ToolExecutor em app/tools/executor.py"
        )
        return errors

    execute_method = _find_method(tool_exec, "execute")
    if execute_method is None:
        errors.append(
            "❌ Método ToolExecutor.execute não encontrado\n"
            "   FIX: restaurar async def execute(...) em ToolExecutor"
        )
        return errors

    execute_src = ast.unparse(execute_method)

    # Step 2: company_id fail-closed check
    has_company_id_check = (
        "context" in execute_src and "company_id" in execute_src
        and ("not context" in execute_src or "context is None" in execute_src
             or "context.company_id" in execute_src)
    )
    if not has_company_id_check:
        errors.append(
            "❌ ToolExecutor.execute NÃO enforça company_id fail-closed (Step 2)\n"
            f"   File: {EXECUTOR_FILE.relative_to(REPO_ROOT)}\n"
            "   Risco: tools rodam sem tenant context (multi-tenancy gap)\n"
            "   FIX: adicionar verificação no início do método:\n"
            "       if context is None or not context.company_id:\n"
            "           return ToolResult(\n"
            "               success=False,\n"
            "               error=\"company_id required for tool execution\",\n"
            "               tool_name=tool_name,\n"
            "           )"
        )

    # W1-004 Phase A refactor: audit + metrics centralizados em
    # `_emit_governance_signals` helper. Aceita ou inline OU helper-based.
    helper_method = _find_method(tool_exec, "_emit_governance_signals")
    if helper_method is not None:
        helper_src = ast.unparse(helper_method)
        execute_calls_helper = "_emit_governance_signals" in execute_src

        # Step 7 via helper
        helper_has_audit = (
            "log_action" in helper_src or "get_audit_service" in helper_src
        )
        if not (execute_calls_helper and helper_has_audit):
            errors.append(
                "❌ Step 7 (audit log) ausente · helper _emit_governance_signals\n"
                "   existe mas NÃO chama AuditService.log_action, ou execute()\n"
                "   NÃO chama o helper.\n"
                f"   File: {EXECUTOR_FILE.relative_to(REPO_ROOT)}\n"
                "   FIX: garantir helper invoca asyncio.create_task(\n"
                "        get_audit_service().log_action(...)) + execute() chama\n"
                "        _emit_governance_signals em todos os exits."
            )

        # Step 8 via helper
        helper_has_metrics = "_emit_metrics" in helper_src
        if not (execute_calls_helper and helper_has_metrics):
            errors.append(
                "❌ Step 8 (metrics) ausente · helper NÃO chama _emit_metrics OU\n"
                "   execute() NÃO chama o helper.\n"
                f"   File: {EXECUTOR_FILE.relative_to(REPO_ROOT)}\n"
                "   FIX: garantir helper invoca self._emit_metrics(tool_name,\n"
                "        success=result.success, elapsed_ms=result.execution_time_ms)"
            )
    else:
        # Fallback: inline pattern
        has_audit_call = (
            "audit_service" in execute_src.lower() or "log_action" in execute_src
            or "get_audit_service" in execute_src
        )
        if not has_audit_call:
            errors.append(
                "❌ ToolExecutor.execute NÃO chama AuditService (Step 7)\n"
                f"   File: {EXECUTOR_FILE.relative_to(REPO_ROOT)}\n"
                "   Risco: tool calls sem audit trail (LGPD Art 37 §1 gap)\n"
                "   FIX: adicionar antes do return:\n"
                "       asyncio.create_task(\n"
                "           get_audit_service().log_action(\n"
                "               trace_id=context.session_id or \"unknown\",\n"
                "               company_id=context.company_id,\n"
                "               action_type=\"tool_call\",\n"
                "               actor=context.user_id,\n"
                "               target_id=tool_name,\n"
                "               target_type=\"tool\",\n"
                "               metadata={\"agent_type\": agent_type, ...},\n"
                "           )\n"
                "       )"
            )

        has_metrics = "_emit_metrics" in execute_src or "emit_metrics" in execute_src
        if not has_metrics:
            errors.append(
                "❌ ToolExecutor.execute NÃO chama _emit_metrics (Step 8)\n"
                f"   File: {EXECUTOR_FILE.relative_to(REPO_ROOT)}\n"
                "   Risco: tool executions sem observability metric (canary gap)\n"
                "   FIX: adicionar antes do return:\n"
                "       self._emit_metrics(tool_name, success=result.success,\n"
                "                          elapsed_ms=result.execution_time_ms)"
            )

    return errors


def check_governance_executor_canonical_preserved() -> list[str]:
    """GovernanceExecutor (canonical 8-step) deve continuar existindo."""
    errors: list[str] = []
    if not EXECUTOR_FILE.exists():
        return errors

    src = EXECUTOR_FILE.read_text(encoding="utf-8")
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return errors

    gov_exec = _find_class(tree, "GovernanceExecutor")
    if gov_exec is None:
        errors.append(
            "❌ GovernanceExecutor (canonical 8-step pattern) foi deletada\n"
            f"   File: {EXECUTOR_FILE.relative_to(REPO_ROOT)}\n"
            "   Risco: perde-se pattern canonical pra tools com ToolContract\n"
            "   FIX: restaurar class GovernanceExecutor em executor.py\n"
            "        (consumida via governance_executor singleton)"
        )
        return errors

    # Doc deve mencionar 8 steps
    doc = ast.get_docstring(gov_exec) or ""
    if "8" not in doc or "step" not in doc.lower():
        errors.append(
            "⚠️  GovernanceExecutor docstring NÃO documenta 8-step pipeline\n"
            "   FIX: garantir que docstring liste:\n"
            "        1. validate, 2. tenant, 3. exec, 4. fairness,\n"
            "        5. PII, 6. schema, 7. audit, 8. metrics"
        )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--warn-only", action="store_true")
    args = parser.parse_args()

    errors: list[str] = []
    errors.extend(check_executor_file_present())
    errors.extend(check_tool_executor_governance_wired())
    errors.extend(check_governance_executor_canonical_preserved())

    # Split warnings (⚠) from fatal (❌)
    fatal = [e for e in errors if not e.lstrip().startswith("⚠")]
    warnings_list = [e for e in errors if e.lstrip().startswith("⚠")]

    for w in warnings_list:
        print(w, file=sys.stderr)
        print(file=sys.stderr)

    if fatal:
        print(
            f"W1-004 governance wiring drift · {len(fatal)} violation(s):",
            file=sys.stderr,
        )
        print(file=sys.stderr)
        for err in fatal:
            print(err, file=sys.stderr)
            print(file=sys.stderr)

        if args.warn_only:
            print("⚠️  WARN-ONLY mode: exit 0 despite violations", file=sys.stderr)
            return 0
        return 1

    print(
        "✅ ToolExecutor governance wired (W1-004 Phase A) · "
        "Step 2 (company_id fail-closed) + Step 7 (audit) + Step 8 (metrics)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
