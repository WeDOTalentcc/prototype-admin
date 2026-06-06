"""Sensor (audit C1/#11 2026-06-05): exige recursion_limit explicito em TODA
chamada invoke/ainvoke do JobCreationGraph.

LangGraph aplica um recursion_limit default de 25 implicito. Para um grafo de
wizard com gates HITL e loop-backs, um ceiling explicito (a) documenta a
intencao de parada estrita e (b) barra runaway. Source-level: nao precisa de
checkpointer nem runtime.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # .../lia-agent-system
GRAPH_SRC = (ROOT / "app" / "domains" / "job_creation" / "graph.py").read_text(
    encoding="utf-8"
)


def _invoke_call_blocks() -> list[str]:
    """Extrai cada chamada ``self._graph.invoke(...)`` / ``.ainvoke(...)``
    balanceando parenteses (cobre chamadas multi-linha)."""
    blocks = []
    for m in re.finditer(r"self\._graph\.(a?invoke)\(", GRAPH_SRC):
        i = m.end()
        depth = 1
        while i < len(GRAPH_SRC) and depth:
            ch = GRAPH_SRC[i]
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
            i += 1
        blocks.append(GRAPH_SRC[m.start():i])
    return blocks


def test_all_graph_invocations_set_recursion_limit():
    blocks = _invoke_call_blocks()
    assert len(blocks) >= 4, (
        f"esperava >=4 chamadas invoke/ainvoke em graph.py, achei {len(blocks)} "
        "— o regex do sensor pode ter quebrado apos refactor."
    )
    missing = [b[:90].replace("\n", " ") for b in blocks if "recursion_limit" not in b]
    assert not missing, (
        "invoke/ainvoke do JobCreationGraph SEM recursion_limit explicito: "
        f"{missing}. "
        "-> Fix: em graph.py, passar "
        "config={**config, 'recursion_limit': WIZARD_RECURSION_LIMIT} em cada "
        "self._graph.invoke(...)/ainvoke(...). O default 25 implicito do LangGraph "
        "nao documenta a condicao de parada do wizard."
    )
