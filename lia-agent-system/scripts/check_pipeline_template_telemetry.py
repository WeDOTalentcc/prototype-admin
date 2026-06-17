#!/usr/bin/env python3
"""AST sensor - PipelineTemplateService + wizard tools MUST emit Prometheus counters.

Fase 5 canonical (Sprint Pipeline Templates 2026-05-26):
- pipeline_template_service.py: Counter "pipeline_template_apply_total" +
  "pipeline_template_mutation_total" devem ser importados de prometheus_client
  e cada metodo mutation/apply deve invocar .inc() (via helpers _inc_*).
- pipeline_template_wizard_tools.py: Counter "pipeline_template_suggest_shown_total"
  com .inc() em suggest_pipeline_template_db quando should_suggest=True.

Sem telemetria, regressao em apply/suggest fica invisivel ate Grafana detectar
divergencia funcional (igual REGRA 4 / fallback_metrics canary).

Exit:
  0 - todos counters presentes + ao menos uma chamada .inc()
  1 - counter ausente OU metodo sem .inc()
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVICE = ROOT / "app" / "domains" / "pipeline" / "services" / "pipeline_template_service.py"
TOOLS = ROOT / "app" / "domains" / "pipeline" / "tools" / "pipeline_template_wizard_tools.py"

SERVICE_REQUIRED_COUNTERS = {
    "_pipeline_template_apply_total",
    "_pipeline_template_mutation_total",
}
SERVICE_INC_HELPERS = {"_inc_apply", "_inc_mutation"}
SERVICE_METHODS_REQUIRING_INC = {
    "create": "_inc_mutation",
    "update": "_inc_mutation",
    "archive": "_inc_mutation",
    "clone": "_inc_mutation",
    "apply_to_vacancy": "_inc_apply",
}

TOOLS_REQUIRED_COUNTER = "_pipeline_template_suggest_shown_total"
TOOLS_INC_HELPER = "_inc_suggest_shown"
TOOLS_FUNC_REQUIRING_INC = "suggest_pipeline_template_db"


def parse(path: Path) -> ast.AST | None:
    if not path.exists():
        return None
    try:
        return ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError as e:
        print(f"X Syntax error em {path}: {e}")
        return None


def module_assigns_counters(tree: ast.AST, names: set[str]) -> set[str]:
    """Retorna o conjunto dos `names` que aparecem como targets de assign em modulo."""
    found: set[str] = set()
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and tgt.id in names:
                    found.add(tgt.id)
    return found


def imports_prometheus_counter(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "prometheus_client":
            for alias in node.names:
                if alias.name == "Counter":
                    return True
    return False


def function_calls_any(func: ast.FunctionDef | ast.AsyncFunctionDef, helper_names: set[str]) -> str | None:
    for node in ast.walk(func):
        if isinstance(node, ast.Call):
            target = node.func
            if isinstance(target, ast.Name) and target.id in helper_names:
                return target.id
    return None


def check_service() -> list[str]:
    errors: list[str] = []
    tree = parse(SERVICE)
    if tree is None:
        return [f"service file missing: {SERVICE}"]

    if not imports_prometheus_counter(tree):
        errors.append(
            f"{SERVICE.name}: nao importa Counter de prometheus_client.\n"
            "  -> Fix: 'from prometheus_client import Counter' (dentro de try/except fail-open)."
        )

    counters_found = module_assigns_counters(tree, SERVICE_REQUIRED_COUNTERS)
    missing_counters = SERVICE_REQUIRED_COUNTERS - counters_found
    for name in sorted(missing_counters):
        errors.append(
            f"{SERVICE.name}: counter modulo '{name}' ausente.\n"
            f"  -> Fix: declarar '{name} = Counter(...)' no module-level."
        )

    service_class: ast.ClassDef | None = None
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "PipelineTemplateService":
            service_class = node
            break
    if service_class is None:
        errors.append("PipelineTemplateService class nao encontrada.")
        return errors

    for item in service_class.body:
        if not isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if item.name not in SERVICE_METHODS_REQUIRING_INC:
            continue
        helper = SERVICE_METHODS_REQUIRING_INC[item.name]
        called = function_calls_any(item, {helper})
        if called is None:
            errors.append(
                f"{SERVICE.name}: metodo PipelineTemplateService.{item.name} "
                f"(linha {item.lineno}) nao chama '{helper}(...)'.\n"
                f"  -> Fix: invocar {helper}(company_id, ...) apos _emit_audit."
            )

    return errors


def check_tools() -> list[str]:
    errors: list[str] = []
    tree = parse(TOOLS)
    if tree is None:
        return [f"tools file missing: {TOOLS}"]

    if not imports_prometheus_counter(tree):
        errors.append(
            f"{TOOLS.name}: nao importa Counter de prometheus_client.\n"
            "  -> Fix: 'from prometheus_client import Counter' (try/except fail-open)."
        )

    counters_found = module_assigns_counters(tree, {TOOLS_REQUIRED_COUNTER})
    if TOOLS_REQUIRED_COUNTER not in counters_found:
        errors.append(
            f"{TOOLS.name}: counter '{TOOLS_REQUIRED_COUNTER}' ausente.\n"
            f"  -> Fix: declarar Counter no module-level (igual fallback_metrics.py)."
        )

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == TOOLS_FUNC_REQUIRING_INC:
            called = function_calls_any(node, {TOOLS_INC_HELPER})
            if called is None:
                errors.append(
                    f"{TOOLS.name}: funcao {TOOLS_FUNC_REQUIRING_INC} nao chama "
                    f"'{TOOLS_INC_HELPER}(...)'.\n"
                    f"  -> Fix: invocar {TOOLS_INC_HELPER}(top_score) quando should_suggest=True."
                )
            break
    else:
        errors.append(f"funcao {TOOLS_FUNC_REQUIRING_INC} nao encontrada em {TOOLS.name}.")

    return errors


def main() -> int:
    errors = check_service() + check_tools()
    if errors:
        print(f"X Pipeline template telemetry sensor: {len(errors)} violation(s):")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("OK Pipeline template telemetry sensor: counters + .inc() presentes (service + tools)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
