"""Sentinela #1099 — todo payload de wizard expõe `data.message`.

Origem: bug do template canned 4× (2026-05-15) — stage avança mas o frontend
recebe um payload sem `data.message`, e o `WizardSessionService` cunhava o
`[ATENÇÃO: estado inconsistente]` (Task #1089/T3) ou repetia o último template.

PR-10 (canonical-fix, registrado 2026-06-03): o literal
`{"type": "wizard_stage", "data": {...}}` foi CONSOLIDADO no produtor único
`app/domains/job_creation/helpers/ws_payload_builder.py::build_ws_stage_payload`,
que FALHA-LOUD (`raise ValueError`) quando `data['message']` está ausente/vazio.
Os nodes agora CHAMAM o helper (24 call sites) em vez de escrever o dict inline.

Por isso esta sentinela mudou de "escanear dict literais inline" (que migraram
pro produtor → o scan achava 0 e dava falso-verde vacuamente) para:
  S1 — ≥10 call sites de build_ws_stage_payload nas wizard sources (smoke).
  S2 — anti-pattern: NENHUM dict literal `wizard_stage` inline (tudo via helper).
  S3 — o produtor enforça `data.message` (raise em ausente E vazio).
  S4 — as 15 funções de node canônicas existem.
"""

from __future__ import annotations

import ast
import inspect
from pathlib import Path
from typing import Iterator

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _graph_source_path() -> Path:
    from app.domains.job_creation import graph as graph_mod

    p = inspect.getsourcefile(graph_mod)
    assert p is not None, "Could not resolve graph.py source path"
    return Path(p)


def _wizard_source_paths() -> list[Path]:
    """PR-10: wizard nodes foram extraídos de graph.py para nodes/<x>.py.
    Retorna graph.py + todos nodes/*.py para os scanners AST.
    """
    graph_path = _graph_source_path()
    out = [graph_path]
    nodes_dir = graph_path.parent / "nodes"
    if nodes_dir.is_dir():
        for sub in sorted(nodes_dir.glob("*.py")):
            if sub.name != "__init__.py":
                out.append(sub)
    return out


def _is_str_const(node: ast.AST | None, value: str) -> bool:
    return isinstance(node, ast.Constant) and node.value == value


def _dict_key_value(d: ast.Dict, key: str) -> ast.AST | None:
    for k, v in zip(d.keys, d.values):
        if _is_str_const(k, key):
            return v
    return None


def _walk_wizard_stage_dicts(tree: ast.AST) -> Iterator[ast.Dict]:
    """Yield todo dict literal com ``"type": "wizard_stage"``."""
    for node in ast.walk(tree):
        if not isinstance(node, ast.Dict):
            continue
        if _is_str_const(_dict_key_value(node, "type"), "wizard_stage"):
            yield node


def _count_builder_call_sites() -> int:
    """Conta chamadas a build_ws_stage_payload nas wizard sources (AST)."""
    count = 0
    for src_path in _wizard_source_paths():
        tree = ast.parse(src_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                fn = node.func
                name = fn.id if isinstance(fn, ast.Name) else getattr(fn, "attr", None)
                if name == "build_ws_stage_payload":
                    count += 1
    return count


# ---------------------------------------------------------------------------
# S1 — smoke: ≥10 nodes emitem payload via build_ws_stage_payload
# ---------------------------------------------------------------------------
def test_graph_contains_wizard_stage_payloads() -> None:
    """PR-10: o smoke certo é contar call sites do helper canônico (não dict
    literais inline, que não existem mais). Se cair a zero ou o helper for
    renomeado, falha antes do invariante real.
    """
    sites = _count_builder_call_sites()
    assert sites >= 10, (
        f"Esperava >=10 chamadas a build_ws_stage_payload nas wizard sources "
        f"(15 nodes canônicos + paths), encontrou {sites}. O helper foi "
        "renomeado, ou os nodes pararam de emitir payload? Atualize o sentinel."
    )


# ---------------------------------------------------------------------------
# S2 — anti-pattern: nenhum dict literal wizard_stage inline (tudo via helper)
# ---------------------------------------------------------------------------
def test_no_inline_wizard_stage_dict_literals() -> None:
    """Canonical-fix: ninguém reconstrói o payload inline. Todo
    `{"type":"wizard_stage"}` deve vir de build_ws_stage_payload — um literal
    inline nas wizard sources é bypass do produtor (regressão do PR-10) e
    escapa do gate fail-loud de data.message.
    """
    offenders: list[str] = []
    for src_path in _wizard_source_paths():
        tree = ast.parse(src_path.read_text(encoding="utf-8"))
        for d in _walk_wizard_stage_dicts(tree):
            offenders.append(f"{src_path.name}:L{d.lineno}")
    assert not offenders, (
        "Dict literal {'type':'wizard_stage'} inline detectado (bypass do helper "
        "build_ws_stage_payload, que enforça data.message). Use o helper. "
        "Offenders: " + ", ".join(offenders)
    )


# ---------------------------------------------------------------------------
# S3 — INVARIANTE no produtor: build_ws_stage_payload exige data.message
# ---------------------------------------------------------------------------
def test_builder_enforces_data_message() -> None:
    """O invariante #1099 vive no produtor único: build_ws_stage_payload
    levanta ValueError quando data['message'] está ausente OU é string vazia.
    Testar o produtor é mais forte que escanear consumidores (uma fonte de
    verdade). Cobertura detalhada do builder em tests/wizard/test_ws_payload_builder.py.
    """
    from app.domains.job_creation.helpers.ws_payload_builder import (
        build_ws_stage_payload,
    )

    # ausente -> fail-loud
    with pytest.raises(ValueError):
        build_ws_stage_payload(stage="intake", data={"foo": "bar"}, requires_approval=False)

    # vazia -> fail-loud
    with pytest.raises(ValueError):
        build_ws_stage_payload(stage="salary", data={"message": ""}, requires_approval=False)

    # presente -> ok, type canônico
    payload = build_ws_stage_payload(
        stage="intake", data={"message": "olá"}, requires_approval=False
    )
    assert payload["type"] == "wizard_stage"
    assert payload["data"]["message"] == "olá"


# ---------------------------------------------------------------------------
# S4 — inventário: toda função de node canônica existe
# ---------------------------------------------------------------------------
CANONICAL_NODE_NAMES = (
    # 11 linear nodes
    "intake_node",
    "jd_enrichment_node",
    "bigfive_node",
    "salary_node",
    "competency_node",
    "wsi_questions_node",
    "eligibility_node",
    "review_node",
    "publish_node",
    "calibration_node",
    "handoff_node",
    # 4 gate nodes (HITL interrupts)
    "jd_gate_node",
    "competency_gate_node",
    "wsi_questions_gate_node",
    "review_gate_node",
)


@pytest.mark.parametrize("node_name", CANONICAL_NODE_NAMES)
def test_canonical_node_function_exists(node_name: str) -> None:
    found = False
    for src_path in _wizard_source_paths():
        tree = ast.parse(src_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == node_name:
                found = True
                break
        if found:
            break
    assert found, (
        f"Função de node canônica '{node_name}' não encontrada em graph.py nem "
        "nodes/*.py. Foi renomeada/removida? Atualize CANONICAL_NODE_NAMES."
    )
