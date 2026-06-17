#!/usr/bin/env python3
"""
Anti-regression sensor (Onda 4 B4, 2026-05-28): garantir que o endpoint
``GET /custom-agents/{agent_id}/kpis`` lê métricas pré-computadas de
``pool_agent_runs.runtime_metrics`` em vez de recomputar tokens/cost
chamando LLMService ou parseando text bruto.

## Por quê

Recomputar tokens/cost no caminho de query KPI é:
1. **Caro**: chama LLM ou roda tokenizer N vezes por execução listada.
2. **Inconsistente**: o orchestrator (TalentPoolReActAgent) é a fonte de
   verdade dos custos reais aceitos pelo gate de billing. Recomputar
   gera divergência de centavos com a balance.
3. **Anti-ADR-001**: services de leitura não devem ter side effects.

## O que este sensor detecta

Dentro do file ``app/api/v1/custom_agents.py``, na função
``get_agent_kpis`` (Onda 4 B1):

- Chamada a ``LLMService`` / ``litellm`` / ``tokenizer`` / ``encode``
- Recompute manual via soma de strings / count tokens em loops
- Import de ``app.shared.observability.token_tracking_service`` ou
  ``app.shared.llm.llm`` dentro da função

## O que ele NÃO bloqueia

- Acesso a ``run.runtime_metrics`` (objetivo do endpoint)
- Acesso a ``PoolAgentRunRepository`` ou repository methods agregadores
- Cálculos puros (avg, p95, sum) sobre os campos já presentes em
  runtime_metrics

## Modo de operação

BLOCKING por default. Exit 1 quando violation encontrada.

## --self-test

Roda um teste interno que injeta um snippet anti-pattern em memória e
verifica que o sensor o detecta. Útil para validar o sensor em CI.
"""
from __future__ import annotations

import argparse
import ast
import pathlib
import sys
from typing import Iterable

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
TARGET_FILE = REPO_ROOT / "app" / "api" / "v1" / "custom_agents.py"
TARGET_FUNCTION = "get_agent_kpis"

# Imports/symbols que indicam recompute manual de tokens/cost.
FORBIDDEN_NAMES = {
    "LLMService",
    "LiteLLMService",
    "litellm",
    "TokenTrackingService",
    "get_token_tracking_service",
    "tiktoken",
    "encode",
    "count_tokens",
}

# Module paths que NÃO devem ser importados dentro do endpoint kpis.
FORBIDDEN_MODULES = {
    "app.shared.llm.llm",
    "app.shared.observability.token_tracking_service",
    "litellm",
    "tiktoken",
}


class KpiEndpointVisitor(ast.NodeVisitor):
    """Visita corpo de get_agent_kpis e flagueia chamadas/imports forbidden."""

    def __init__(self) -> None:
        self.violations: list[str] = []
        self._inside_target = False

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        if node.name == TARGET_FUNCTION:
            self._inside_target = True
            self.generic_visit(node)
            self._inside_target = False
        else:
            self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        if node.name == TARGET_FUNCTION:
            self._inside_target = True
            self.generic_visit(node)
            self._inside_target = False
        else:
            self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:
        if self._inside_target:
            for alias in node.names:
                if alias.name in FORBIDDEN_MODULES:
                    self.violations.append(
                        f"linha {node.lineno}: import '{alias.name}' dentro de {TARGET_FUNCTION} "
                        f"sugere recompute manual. KPIs DEVEM ler de pool_agent_runs.runtime_metrics. "
                        f"→ Fix: remover import e usar run.runtime_metrics existente."
                    )
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if self._inside_target:
            module = node.module or ""
            if module in FORBIDDEN_MODULES or any(module.startswith(m + ".") for m in FORBIDDEN_MODULES):
                self.violations.append(
                    f"linha {node.lineno}: 'from {module} import ...' dentro de {TARGET_FUNCTION} "
                    f"sugere recompute manual. KPIs DEVEM ler de pool_agent_runs.runtime_metrics. "
                    f"→ Fix: remover import e ler runtime_metrics direto."
                )
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        if self._inside_target:
            name = _resolve_callable_name(node.func)
            if name and any(forbid in name for forbid in FORBIDDEN_NAMES):
                self.violations.append(
                    f"linha {node.lineno}: chamada a '{name}' dentro de {TARGET_FUNCTION} "
                    f"recomputa tokens/cost. KPIs DEVEM ler de runtime_metrics. "
                    f"→ Fix: usar run.runtime_metrics['cost_usd'] / ['tokens_input'] / ['tokens_output']."
                )
        self.generic_visit(node)


def _resolve_callable_name(func: ast.expr) -> str | None:
    """Best-effort: x.y.z() -> 'x.y.z'; Foo() -> 'Foo'."""
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        parts: list[str] = [func.attr]
        cur: ast.expr = func.value
        while isinstance(cur, ast.Attribute):
            parts.insert(0, cur.attr)
            cur = cur.value
        if isinstance(cur, ast.Name):
            parts.insert(0, cur.id)
        return ".".join(parts)
    return None


def scan_source(source: str, path: str = "<source>") -> list[str]:
    try:
        tree = ast.parse(source, filename=path)
    except SyntaxError as exc:
        return [f"{path}: SyntaxError: {exc}"]
    visitor = KpiEndpointVisitor()
    visitor.visit(tree)
    return visitor.violations


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Roda self-test injetando snippet anti-pattern em memória.",
    )
    args = parser.parse_args()

    if args.self_test:
        bad_source = '''
async def get_agent_kpis(agent_id, period, db, company_id):
    from app.shared.llm.llm import LLMService
    svc = LLMService()
    cost = svc.count_tokens("anything")
    return cost
'''
        violations = scan_source(bad_source, path="<self-test>")
        if not violations:
            print("self-test FAILED: sensor não detectou anti-pattern injetado")
            return 2
        print("self-test OK: sensor detectou", len(violations), "violations")
        for v in violations:
            print(f"  - {v}")
        return 1

    if not TARGET_FILE.exists():
        print(f"AVISO: {TARGET_FILE} não existe (endpoint ainda não implementado).")
        print("Sensor passa pois não há código pra auditar. Re-rodar pós-implementação.")
        return 0

    source = TARGET_FILE.read_text(encoding="utf-8")
    if f"async def {TARGET_FUNCTION}(" not in source and f"def {TARGET_FUNCTION}(" not in source:
        print(
            f"AVISO: função {TARGET_FUNCTION} não encontrada em {TARGET_FILE}. "
            "Sensor passa pois não há código pra auditar."
        )
        return 0

    violations = scan_source(source, path=str(TARGET_FILE))
    if violations:
        print("❌ check_kpi_endpoint_consumes_runtime_metrics: violations encontradas:")
        for v in violations:
            print(f"  - {v}")
        return 1
    print("✓ check_kpi_endpoint_consumes_runtime_metrics: OK (0 violations)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
