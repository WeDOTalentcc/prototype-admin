"""TDD Fase 1: scope_for_context (page/domain -> PromptScope) + escopo bounded.
Pina que o scoping do agente federado NARROWS de verdade (vs tool_catalog quebrado=166)."""
from app.tools.scope_config import (
    PromptScope,
    get_tools_for_scope,
    scope_for_context,
)


def test_page_vagas_job_table():
    assert scope_for_context(page_type="vagas") == PromptScope.JOB_TABLE


def test_page_funil_e_candidatos_talent():
    assert scope_for_context(page_type="funil") == PromptScope.TALENT_FUNNEL
    assert scope_for_context(page_type="candidatos") == PromptScope.TALENT_FUNNEL


def test_page_kanban_in_job():
    assert scope_for_context(page_type="kanban") == PromptScope.IN_JOB


def test_page_prevalece_sobre_domain():
    assert scope_for_context(page_type="vagas", resolved_domain="talent") == PromptScope.JOB_TABLE


def test_domain_fallback():
    assert scope_for_context(resolved_domain="jobs_management") == PromptScope.JOB_TABLE
    assert scope_for_context(resolved_domain="talent_funnel") == PromptScope.TALENT_FUNNEL


def test_default_global():
    assert scope_for_context() == PromptScope.GLOBAL
    assert scope_for_context(page_type="configuracoes", resolved_domain="xpto") == PromptScope.GLOBAL


def test_case_insensitive():
    assert scope_for_context(page_type="VAGAS") == PromptScope.JOB_TABLE


def test_escopos_sao_bounded():
    # Sensor (review Claude.ai): cada escopo bounded << catalogo (179). Pin que o
    # scoping ESTREITA de verdade — falha se alguem apontar pro getter quebrado.
    for sc in (PromptScope.TALENT_FUNNEL, PromptScope.JOB_TABLE, PromptScope.IN_JOB):
        n = len(get_tools_for_scope(sc))
        assert 0 < n <= 60, f"{sc.value} = {n} tools (esperado bounded <=60, << 179)"
    assert len(get_tools_for_scope(PromptScope.GLOBAL)) <= 20
