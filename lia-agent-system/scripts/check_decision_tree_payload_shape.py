#!/usr/bin/env python3
"""Sensor: CustomAgentRuntime._state_to_output DEVE popular reasoning_trace.

Onda 1 B5.1 (2026-05-27) — sensor BLOCKING canonical.

Recidiva proibida: Wave 0 deixou AgentOutput.reasoning_trace=None.
Onda 1 B2 wired build_reasoning_trace(messages) no _state_to_output do
CustomAgentRuntime. Se alguém remover ou comentar essa lógica, a Sala de
Controle (4ª aba do Studio) volta a mostrar payload vazio em todas as
execuções de agentes custom.

O sensor é AST-based (não-inferencial — não usa LLM). Verifica:
  1. custom_agent_runtime.py importa ou referencia build_reasoning_trace
  2. _state_to_output method body referencia reasoning_trace
  3. _state_to_output método retorna AgentOutput com kwarg reasoning_trace
  4. reasoning_trace_builder.py existe (helper canonical)
  5. reasoning_trace_builder.FORBIDDEN_LGPD_FIELDS contém pelo menos
     {cpf, raca, religiao, genero, estado_civil}

Output otimizado pra consumo de LLM (instruções de fix embutidas em PT-BR).

Exit codes:
  0 — OK (B2 wired correctly)
  1 — violação (recidiva: _state_to_output perdeu o wiring)
  2 — arquivo não encontrado (estrutura mudou — investigar)

Uso:
  python3 scripts/check_decision_tree_payload_shape.py
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

RUNTIME_FILE = Path("app/domains/agent_studio/custom_agent_runtime.py")
BUILDER_FILE = Path("app/domains/agent_studio/reasoning_trace_builder.py")

LGPD_REQUIRED_FORBIDDEN = {
    "cpf",
    "raca",
    "religiao",
    "genero",
    "estado_civil",
}


def _find_method(tree: ast.AST, class_name: str, method_name: str) -> ast.FunctionDef | None:
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for item in node.body:
                if (
                    isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and item.name == method_name
                ):
                    return item
    return None


def main() -> int:
    if not RUNTIME_FILE.exists():
        sys.stderr.write(
            f"❌ Sensor ERRO: arquivo canonical não encontrado: {RUNTIME_FILE}\n"
            "→ Fix: CustomAgentRuntime foi movido/renomeado? Atualizar "
            "RUNTIME_FILE no sensor.\n"
        )
        return 2

    if not BUILDER_FILE.exists():
        sys.stderr.write(
            f"❌ Sensor BLOCKING: helper canonical sumiu: {BUILDER_FILE}\n"
            "→ Fix: restaurar reasoning_trace_builder.py (Onda 1 B2).\n"
            "  Modulo expoe build_reasoning_trace(messages, max_steps) +\n"
            "  FORBIDDEN_LGPD_FIELDS frozenset.\n"
        )
        return 1

    runtime_src = RUNTIME_FILE.read_text()
    try:
        tree = ast.parse(runtime_src)
    except SyntaxError as e:
        sys.stderr.write(f"❌ Sensor ERRO: parse AST falhou: {e}\n")
        return 2

    method = _find_method(tree, "CustomAgentRuntime", "_state_to_output")
    if method is None:
        sys.stderr.write(
            "❌ Sensor BLOCKING: método _state_to_output não encontrado em "
            "CustomAgentRuntime.\n"
            f"→ Fix: restaurar em {RUNTIME_FILE}. Onda 1 B2 wired "
            "build_reasoning_trace lá.\n"
        )
        return 1

    body = ast.unparse(method)

    violations: list[str] = []

    if "build_reasoning_trace" not in runtime_src:
        violations.append(
            "  - CustomAgentRuntime não importa build_reasoning_trace.\n"
            "    → Fix: dentro de _state_to_output adicionar:\n"
            "      from app.domains.agent_studio.reasoning_trace_builder "
            "import build_reasoning_trace\n"
            "      reasoning_trace = build_reasoning_trace(messages, max_steps=20)"
        )
    if "reasoning_trace" not in body:
        violations.append(
            "  - _state_to_output body não menciona reasoning_trace.\n"
            "    → Fix: chamar build_reasoning_trace(messages, max_steps=20) "
            "e passar resultado em AgentOutput(reasoning_trace=...)."
        )
    # Stricter check: AgentOutput call deve incluir reasoning_trace kwarg
    if "reasoning_trace=" not in body:
        violations.append(
            "  - AgentOutput() em _state_to_output NÃO inclui kwarg "
            "reasoning_trace=...\n"
            "    → Fix: alterar a construção do AgentOutput de retorno pra:\n"
            "      return AgentOutput(\n"
            "          message=response,\n"
            "          actions=actions,\n"
            "          confidence=0.8,\n"
            "          reasoning_trace=reasoning_trace,  # ← Onda 1 B2\n"
            "          metadata={...},\n"
            "      )"
        )

    # Builder sanity: FORBIDDEN_LGPD_FIELDS contém todos os 5 canonical
    builder_src = BUILDER_FILE.read_text()
    if "FORBIDDEN_LGPD_FIELDS" not in builder_src:
        violations.append(
            f"  - {BUILDER_FILE} não exporta FORBIDDEN_LGPD_FIELDS.\n"
            "    → Fix: restaurar frozenset canonical declarado em B2.\n"
            f"    Deve incluir: {sorted(LGPD_REQUIRED_FORBIDDEN)}"
        )
    else:
        missing = [
            f for f in LGPD_REQUIRED_FORBIDDEN if f not in builder_src
        ]
        if missing:
            violations.append(
                "  - FORBIDDEN_LGPD_FIELDS está incompleto. Faltam:\n"
                f"    {missing}\n"
                f"    → Fix: adicionar esses tokens em {BUILDER_FILE} "
                "FORBIDDEN_LGPD_FIELDS frozenset.\n"
                "    Sensor B5.2 (LGPD audit) também checa isso na response.\n"
                "    Veja CLAUDE.md ADR-LGPD-001."
            )

    if violations:
        sys.stderr.write(
            "❌ Sensor BLOCKING: Studio Control Room decision tree wiring "
            "perdeu integridade (Onda 1 B2 — recidiva proibida).\n\n"
            "Violations:\n"
        )
        for v in violations:
            sys.stderr.write(v + "\n")
        sys.stderr.write(
            "\n"
            "Contexto: Onda 1 do plano Fase 2 do Agent Studio (2026-05-27)\n"
            "wired AgentOutput.reasoning_trace nos agentes canonical pra\n"
            "alimentar a Sala de Controle (4ª aba). Sem isso, recruiter\n"
            "abre o DecisionTreeDrawer e vê tela vazia — UX broken + audit\n"
            "LGPD trail incompleto.\n\n"
            "Ver: ~/.claude/plans/steady-dazzling-shamir.md Onda 1 B2+B5.\n"
        )
        return 1

    print(
        "✅ Sensor OK: CustomAgentRuntime._state_to_output popula "
        "reasoning_trace com FORBIDDEN_LGPD_FIELDS canonical."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
