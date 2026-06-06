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


def test_scoped_defs_nomes_dentro_do_escopo():
    allowed = {n.lower() for n in get_tools_for_scope("talent_funnel")}
    defs = get_scoped_tool_definitions("talent_funnel")
    for td in defs:
        assert td.name.lower() in allowed, f"{td.name} fora do escopo talent_funnel"


def test_scoped_defs_sem_duplicata_de_nome():
    defs = get_scoped_tool_definitions("job_table")
    nomes = [td.name for td in defs]
    assert len(nomes) == len(set(nomes)), "nao pode haver nome duplicado"
