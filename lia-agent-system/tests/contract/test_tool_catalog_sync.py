"""Sensor Fase 1 — catálogo canônico de tools (reconciliação A/B).

GUIDE: fonte única de metadata, derivada dos domain registries (B) + overlay de
scope (A). Anti-drift: todo tool dos registries canônicos tem entrada; scope
honesto (inferred flag); colisões de nome rastreadas.
"""
import pytest
from pydantic import ValidationError

from app.shared.tool_catalog import (
    ToolMeta,
    _CANONICAL_SOURCES,
    build_tool_catalog,
    get_tools_for_scope,
)


def test_catalog_cobre_todos_os_tools_dos_registries_canonicos():
    """Zero órfão: todo tool das fontes carregadas está no catálogo."""
    from app.shared.tool_catalog import _load_sources

    cat = build_tool_catalog()
    for key, tools in _load_sources().items():
        for td in tools:
            assert td.name in cat, f"tool {td.name} ({key}) ausente do catálogo"
            assert key in cat[td.name].source_registries


def test_todas_fontes_canonicas_carregam():
    """Regressao: toda fonte declarada em _CANONICAL_SOURCES deve importar."""
    from app.shared.tool_catalog import _CANONICAL_SOURCES, _load_sources

    loaded = _load_sources()
    missing = set(_CANONICAL_SOURCES) - set(loaded)
    assert not missing, f"fontes que falharam ao carregar: {missing}"


def test_meta_shape_valido():
    cat = build_tool_catalog()
    assert "list_jobs" in cat
    m = cat["list_jobs"]
    assert m.domain
    assert m.scope in ("TALENT_FUNNEL", "JOB_TABLE", "IN_JOB", "GLOBAL")
    assert m.permission in ("read", "write")
    assert isinstance(m.requires_company_id, bool)


def test_scope_honesto_inferred_reflete_yaml():
    """Se um tool está no YAML-A, scope_inferred=False; senão True (não fabrica)."""
    from app.shared.tool_catalog import _scope_overlay

    overlay = _scope_overlay()
    cat = build_tool_catalog()
    for name, meta in cat.items():
        if name in overlay:
            assert meta.scope_inferred is False
            assert meta.scope == overlay[name]
        else:
            assert meta.scope_inferred is True


def test_write_tools_marcadas_por_side_effects():
    """batch_move_candidates / pause_job têm side_effects -> permission=write."""
    cat = build_tool_catalog()
    # pelo menos uma tool de escrita conhecida do núcleo
    write_names = {"batch_move_candidates", "pause_job", "reopen_job"}
    present = write_names & set(cat.keys())
    assert present, "nenhuma tool de escrita conhecida no catálogo"
    for n in present:
        assert cat[n].permission == "write", f"{n} deveria ser write"


def test_get_tools_for_scope_inclui_global():
    cat = build_tool_catalog()
    global_names = {m.name for m in cat.values() if m.scope == "GLOBAL"}
    scoped = set(get_tools_for_scope("TALENT_FUNNEL"))
    assert global_names <= scoped, "GLOBAL deve estar sempre disponível"


def test_toolmeta_extra_forbid():
    with pytest.raises(ValidationError):
        ToolMeta(name="x", domain="d", bogus=1)


def test_read_tools_nao_marcadas_write():
    """Regressao: side_effects e lista; read tools nao podem virar write."""
    cat = build_tool_catalog()
    for n in ["list_jobs", "view_job_details", "get_pipeline_summary", "view_candidate_profile"]:
        if n in cat:
            assert cat[n].permission == "read", f"{n} deveria ser read"


def test_governanca_capturada():
    """batch_move_candidates afeta decisao de candidato (HITL/fairness)."""
    cat = build_tool_catalog()
    if "batch_move_candidates" in cat:
        assert cat["batch_move_candidates"].affects_candidate_decision is True


def test_autonomous_nunca_vence_colisao():
    """autonomous re-implementa tools de outros dominios; em colisao de nome o
    dominio CANONICO deve ser a fonte primaria (autonomous = menor prioridade)."""
    cat = build_tool_catalog()
    for name, m in cat.items():
        if len(m.source_registries) > 1 and "autonomous" in m.source_registries:
            assert m.source_registries[0] != "autonomous", (
                f"{name}: autonomous nao deveria ser primaria (regs: {m.source_registries})"
            )
