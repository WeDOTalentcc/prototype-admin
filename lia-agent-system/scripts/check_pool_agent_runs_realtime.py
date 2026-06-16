#!/usr/bin/env python3
"""Sensor: TalentPoolReActAgent.process() DEVE gravar PoolAgentRun em tempo real.

Wave 0 Fix 1 (2026-05-27) — sensor BLOCKING canonical.

Recidiva proibida: runtime sourcing manual ("run now" via Studio) sem registro
em pool_agent_runs deixa histórico fantasma. Antes do Fix 1, só Celery beat
gravava — agora `TalentPoolReActAgent.process` também grava quando
`input.context["assignment_id"]` está presente.

O sensor é AST-based (não-inferencial — não usa LLM). Verifica:
  1. PoolAgentRunRepository é importado (lazy ou top-level) em talent_pool_agent.py
  2. process() method body referencia `repo.create(` e `update_status`
  3. process() body referencia `latency_ms` (runtime_metrics canonical)
  4. process() body referencia `assignment_id` (gate canonical)

Output otimizado pra consumo de LLM (instruções de fix embutidas em PT-BR).

Exit codes:
  0 — OK (Fix 1 wired correctly)
  1 — violação (recidiva: process() perdeu o wiring)
  2 — arquivo não encontrado (estrutura mudou — investigar)

Uso:
  python3 scripts/check_pool_agent_runs_realtime.py
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

TARGET_FILE = Path("app/domains/talent_pool/agents/talent_pool_agent.py")


def _find_process_method(tree: ast.AST) -> ast.AsyncFunctionDef | None:
    """Localiza a função process() na classe TalentPoolReActAgent."""
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "TalentPoolReActAgent":
            for item in node.body:
                if isinstance(item, ast.AsyncFunctionDef) and item.name == "process":
                    return item
    return None


def _process_body_text(method: ast.AsyncFunctionDef) -> str:
    """Serializa o corpo do método pra busca textual nas chamadas/refs."""
    return ast.unparse(method)


def main() -> int:
    if not TARGET_FILE.exists():
        sys.stderr.write(
            f"❌ Sensor ERRO: arquivo canonical não encontrado: {TARGET_FILE}\n"
            "→ Fix: investigar se TalentPoolReActAgent foi movido/renomeado.\n"
            "  Atualizar TARGET_FILE no sensor pra novo path.\n"
        )
        return 2

    src = TARGET_FILE.read_text()
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        sys.stderr.write(
            f"❌ Sensor ERRO: parse AST falhou em {TARGET_FILE}: {e}\n"
        )
        return 2

    method = _find_process_method(tree)
    if method is None:
        sys.stderr.write(
            f"❌ Sensor FALHA: método process() não encontrado em "
            "TalentPoolReActAgent.\n"
            "→ Fix: restaurar `async def process(self, input: AgentInput) -> "
            "AgentOutput` na classe TalentPoolReActAgent em "
            f"{TARGET_FILE} — método é entry-point canonical pra LangGraph "
            "ReAct loop + recording PoolAgentRun.\n"
        )
        return 1

    body = _process_body_text(method)

    violations: list[str] = []

    # Gate 1: gate canonical (não grava sem assignment_id)
    if "assignment_id" not in body:
        violations.append(
            "  - process() não referencia `assignment_id` (gate canonical).\n"
            "    → Fix: verificar `input.context.get(\"assignment_id\")` antes "
            "de criar PoolAgentRun.\n"
            "    Recidiva: gravação sem assignment quebra FK constraint "
            "(pool_agent_runs.assignment_id NOT NULL)."
        )

    # Gate 2: import + uso do repo
    if "PoolAgentRunRepository" not in src:
        violations.append(
            "  - PoolAgentRunRepository não importado em "
            f"{TARGET_FILE} (lazy ou top-level).\n"
            "    → Fix: `from app.domains.agent_studio.repositories."
            "pool_agent_run_repository import PoolAgentRunRepository` "
            "(lazy import dentro de process() é OK pra evitar circular)."
        )
    if "repo.create(" not in body and "PoolAgentRunRepository" in src:
        # Repo importado mas .create não chamado em process()
        violations.append(
            "  - process() não chama `repo.create(...)` pra gravar a run.\n"
            "    → Fix: chamar `await repo.create(assignment_id=..., "
            "company_id=input.company_id, trigger_source=..., "
            "dispatch_metadata={...})` quando assignment_id presente."
        )

    # Gate 3: update_status pra transition queued→running e success/error
    if "update_status" not in body:
        violations.append(
            "  - process() não chama `update_status(...)` (transition "
            "queued→running→success|error).\n"
            "    → Fix: após repo.create, chamar "
            "`await repo.update_status(run.id, \"running\")` e no final "
            "`await repo.update_status(run.id, \"success\", "
            "runtime_metrics={...})`."
        )

    # Gate 4: runtime_metrics com latency_ms
    if "latency_ms" not in body:
        violations.append(
            "  - process() não persiste `latency_ms` em runtime_metrics.\n"
            "    → Fix: medir `t_start = time.time()` antes de "
            "`_process_langgraph` e `elapsed_ms = int((time.time() - t_start) "
            "* 1000)` no path de success. Persist em runtime_metrics["
            "\"latency_ms\"]. Onda 4 KPI dashboard consome essa métrica."
        )

    if violations:
        sys.stderr.write(
            "❌ Sensor BLOCKING: TalentPoolReActAgent.process() perdeu o "
            "wiring de PoolAgentRun (Wave 0 Fix 1 — recidiva proibida).\n\n"
            "Violations:\n"
        )
        for v in violations:
            sys.stderr.write(v + "\n")
        sys.stderr.write(
            "\n"
            "Contexto: a Onda 0 do plano Fase 2 do Agent Studio fechou esse "
            "gap em 2026-05-27. Manual \"run now\" via Studio + scheduled\n"
            "invocations diretas devem gravar PoolAgentRun em tempo real.\n"
            "Sem essa gravação, KPI dashboard (Onda 4) reporta zeros e\n"
            "audit LGPD trail fica incompleto.\n\n"
            "Ver: ~/.claude/plans/steady-dazzling-shamir.md Onda 0 Fix #1.\n"
        )
        return 1

    print(
        "✅ Sensor OK: TalentPoolReActAgent.process() grava PoolAgentRun "
        "em tempo real."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
