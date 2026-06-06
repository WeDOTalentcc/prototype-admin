"""TDD Fase 2 inc.1: get_scoped_tool_definitions monta defs de todos os dominios
filtradas pelo escopo bounded. Pina que o federado carregaria ~bounded, nao 179."""
from app.shared.tool_catalog import (
    build_tool_catalog,
    get_scoped_tool_definitions,
    get_tools_for_scope,
)


def test_scoped_defs_bounded_e_nao_vazio():
    total = len(build_tool_catalog())
    for sc in ("talent_funnel", "job_table", "in_job"):
        defs = get_scoped_tool_definitions(sc)
        assert len(defs) > 0, f"{sc} nao deveria ser vazio"
        assert len(defs) <= 60, f"{sc} = {len(defs)} (esperado bounded <=60, << {total})"
        assert len(defs) < total


def test_scoped_defs_dentro_do_escopo_semantico():
    """Fase 2 (2026-06-06): escopo agora DERIVA do registry de origem
    (anti-drift), NAO do scope-set YAML que divergiu dos nomes reais (dava
    1-6 tools/escopo, bug live). Boundary semantica: talent_funnel tem os
    reads de candidato e nao puxa tool exclusiva de outro dominio."""
    names = {td.name for td in get_scoped_tool_definitions("talent_funnel")}
    assert {"search_candidates", "view_candidate_profile", "rank_candidates"} <= names
    assert "compare_jobs" not in names  # job_table-only, nao vaza pro funil


def test_scoped_defs_sem_duplicata_de_nome():
    defs = get_scoped_tool_definitions("job_table")
    nomes = [td.name for td in defs]
    assert len(nomes) == len(set(nomes)), "nao pode haver nome duplicado"
