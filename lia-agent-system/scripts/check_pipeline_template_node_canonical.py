#!/usr/bin/env python3
"""AST sensor — pipeline_template_node + STAGE_ORDER + HITL_STAGES canonical.

Sprint Pipeline Templates 2026-05-26 — Opção B (Paulo aprovou). Garantias:

1. `pipeline_template_node(state)` definido em app/domains/job_creation/graph.py
2. Node emite literal "suggest_pipeline_template" no source (ui_action canonical)
3. "pipeline_template" está em STAGE_ORDER de app/domains/job_creation/state.py
4. "pipeline_template" está em HITL_STAGES (requires_approval canonical)
5. builder.add_node("pipeline_template", pipeline_template_node) presente
6. add_edge("pipeline_template", "bigfive") presente (linear next stage)

Sensor blocking (baseline 0). Quebra = recriou o node ou removeu wiring canonical.

Exit:
  0 — todas as invariantes OK
  1 — violação canonical (mensagem com fix sugerido em PT-BR)
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GRAPH = ROOT / "app" / "domains" / "job_creation" / "graph.py"
STATE = ROOT / "app" / "domains" / "job_creation" / "state.py"


def _read(path: Path) -> str:
    if not path.exists():
        print(f"❌ Arquivo canonical ausente: {path}")
        print(f"   → Fix: restaurar {path.relative_to(ROOT)} do commit canonical.")
        sys.exit(1)
    return path.read_text()


def check_node_defined(graph_src: str) -> list[str]:
    """Invariante 1: pipeline_template_node existe como FunctionDef."""
    errs: list[str] = []
    tree = ast.parse(graph_src)
    found = False
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "pipeline_template_node":
            found = True
            # Sanity: assinatura aceita state
            if not node.args.args or node.args.args[0].arg != "state":
                errs.append(
                    "pipeline_template_node deve aceitar `state` como primeiro arg "
                    "(assinatura canonical: `def pipeline_template_node(state: JobCreationState)`)."
                )
            break
    if not found:
        errs.append(
            "pipeline_template_node ausente em app/domains/job_creation/graph.py.\n"
            "   → Fix: definir `def pipeline_template_node(state: JobCreationState) -> JobCreationState`\n"
            "     entre `jd_enrichment_node` e `bigfive_node`."
        )
    return errs


def check_ui_action_literal(graph_src: str) -> list[str]:
    """Invariante 2: literal 'suggest_pipeline_template' presente no source."""
    if '"suggest_pipeline_template"' not in graph_src and "'suggest_pipeline_template'" not in graph_src:
        return [
            "ui_action canonical 'suggest_pipeline_template' NÃO encontrado em graph.py.\n"
            "   → Fix: pipeline_template_node DEVE emitir ws_stage_payload['ui_action']='suggest_pipeline_template'\n"
            "     (frontend WizardPipelineTemplateCard depende desse literal)."
        ]
    return []


def check_stage_order(state_src: str) -> list[str]:
    """Invariante 3+4: pipeline_template em STAGE_ORDER e HITL_STAGES."""
    errs: list[str] = []
    if '"pipeline_template"' not in state_src:
        errs.append(
            "'pipeline_template' ausente em app/domains/job_creation/state.py.\n"
            "   → Fix: adicionar 'pipeline_template' em STAGE_ORDER (idx 2, entre jd_enrichment e bigfive)\n"
            "     E em HITL_STAGES."
        )
        return errs

    # Posicionamento canonical: idx 2 (entre jd_enrichment e bigfive)
    # Heurística estrutural: linha contendo "pipeline_template" deve estar entre
    # uma linha com "jd_enrichment" e uma linha com "bigfive".
    lines = state_src.splitlines()
    stage_order_block = []
    in_stage_order = False
    for line in lines:
        if "STAGE_ORDER" in line and "List[WizardStage]" in line:
            in_stage_order = True
            continue
        if in_stage_order:
            if line.strip().startswith("]"):
                break
            stage_order_block.append(line.strip())

    stages_clean = [s.strip(' ",') for s in stage_order_block if s.strip(' ",') and not s.strip().startswith("#")]
    if "pipeline_template" in stages_clean:
        idx = stages_clean.index("pipeline_template")
        if idx == 0 or stages_clean[idx - 1] != "jd_enrichment":
            errs.append(
                f"pipeline_template em posição errada em STAGE_ORDER (esperado APÓS jd_enrichment, atual='{stages_clean[idx-1] if idx>0 else '<start>'}').\n"
                "   → Fix: reordenar STAGE_ORDER → intake, jd_enrichment, pipeline_template, bigfive, ..."
            )
        if idx + 1 >= len(stages_clean) or stages_clean[idx + 1] != "bigfive":
            errs.append(
                f"pipeline_template em posição errada em STAGE_ORDER (esperado ANTES de bigfive, atual_next='{stages_clean[idx+1] if idx+1<len(stages_clean) else '<end>'}').\n"
                "   → Fix: reordenar STAGE_ORDER → ..., pipeline_template, bigfive, salary, ..."
            )
    else:
        errs.append(
            "'pipeline_template' não está na lista STAGE_ORDER parseada (verifique sintaxe).\n"
            "   → Fix: adicionar entry `\"pipeline_template\",` em STAGE_ORDER entre jd_enrichment e bigfive."
        )

    # HITL_STAGES — apenas verifica presença no source dentro do set HITL_STAGES.
    if "HITL_STAGES" in state_src:
        hitl_block_start = state_src.index("HITL_STAGES")
        hitl_block_end = state_src.find("}", hitl_block_start)
        hitl_block = state_src[hitl_block_start:hitl_block_end]
        if "pipeline_template" not in hitl_block:
            errs.append(
                "'pipeline_template' ausente do set HITL_STAGES em state.py.\n"
                "   → Fix: adicionar `\"pipeline_template\"` ao set HITL_STAGES (requires_approval canonical)."
            )
    return errs


def check_builder_wiring(graph_src: str) -> list[str]:
    """Invariante 5+6: builder.add_node + add_edge presentes."""
    errs: list[str] = []
    if 'add_node("pipeline_template"' not in graph_src:
        errs.append(
            "builder.add_node('pipeline_template', pipeline_template_node) ausente.\n"
            "   → Fix: em `create_job_creation_graph`, registrar o node antes de bigfive:\n"
            '     builder.add_node("pipeline_template", pipeline_template_node)'
        )
    if 'add_edge("pipeline_template", "bigfive")' not in graph_src:
        errs.append(
            "builder.add_edge('pipeline_template', 'bigfive') ausente.\n"
            "   → Fix: adicionar edge linear `add_edge(\"pipeline_template\", \"bigfive\")`\n"
            "     após routing blocks de jd_gate/jd_enrichment."
        )
    return errs


def main() -> int:
    graph_src = _read(GRAPH)
    state_src = _read(STATE)

    all_errs: list[str] = []
    all_errs.extend(check_node_defined(graph_src))
    all_errs.extend(check_ui_action_literal(graph_src))
    all_errs.extend(check_stage_order(state_src))
    all_errs.extend(check_builder_wiring(graph_src))

    if all_errs:
        print("❌ Sensor pipeline_template_node canonical FAILED")
        print(f"   ({len(all_errs)} violações)\n")
        for i, err in enumerate(all_errs, 1):
            print(f"  [{i}] {err}\n")
        return 1

    print("✅ Sensor pipeline_template_node canonical OK (6 invariantes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
