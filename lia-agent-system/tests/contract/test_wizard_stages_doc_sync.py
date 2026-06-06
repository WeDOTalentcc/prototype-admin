"""Sensor (audit C6/#9 2026-06-05): mantem o CLAUDE.md do lia-agent-system em
sincronia com os stages reais do JobCreationGraph.

Pega o drift que motivou o item: ``pipeline_template`` existe em graph.py
(``add_node("pipeline_template", ...)``) mas estava AUSENTE da lista de stages
documentada (~linha 639). Guide (doc) que mente sobre o harness e perde valor.

Computacional: extrai os nomes de ``add_node(...)`` do grafo (exceto os guard
nodes ``*_gate``, que sao HITL, nao stages de produto) e exige que cada um
apareca no CLAUDE.md. Falha alto com instrucao de fix embutida (consumo LLM).
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # .../lia-agent-system
GRAPH = ROOT / "app" / "domains" / "job_creation" / "graph.py"
CLAUDE_MD = ROOT / "CLAUDE.md"


def _core_stage_nodes() -> list[str]:
    src = GRAPH.read_text(encoding="utf-8")
    names = re.findall(r'add_node\(\s*"([^"]+)"', src)
    # *_gate sao guard-nodes HITL (intake_gate, jd_gate, ...), nao stages
    return [n for n in names if not n.endswith("_gate")]


def test_claude_md_lists_all_core_wizard_stages():
    stages = _core_stage_nodes()
    assert stages, (
        "nenhum add_node encontrado em graph.py — o regex do sensor quebrou; "
        "revisar _core_stage_nodes antes de confiar neste resultado."
    )
    doc = CLAUDE_MD.read_text(encoding="utf-8")
    missing = [s for s in stages if s not in doc]
    assert not missing, (
        "CLAUDE.md (lia-agent-system) dessincronizado com os stages reais do "
        f"JobCreationGraph. Presentes em graph.py via add_node mas AUSENTES no doc: "
        f"{missing}. "
        "-> Fix: atualizar a linha de stages do wizard (~639) em "
        "lia-agent-system/CLAUDE.md para listar TODOS estes nomes na ordem de "
        "execucao do grafo "
        "(intake -> jd_enrichment -> pipeline_template -> bigfive -> salary -> "
        "competency -> wsi_questions -> eligibility -> review -> publish -> "
        "calibration -> handoff)."
    )
