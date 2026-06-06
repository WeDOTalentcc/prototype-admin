"""
Sensor END-TO-END do def-assembly do agente federado (Fase 2 consolidação).

Contexto: a validação live 2026-06-06 (LIA_FEDERATED_PRIMARY on) pegou que
`get_scoped_tool_definitions` entregava 1-6 tools/escopo (GLOBAL=1, só
generate_report) porque o scope-set YAML (scope_config / tool_registry_metadata)
divergiu dos nomes reais dos 179 tools dos registries. O TDD anterior testou só
a LÓGICA de filtragem (passou) e deixou o end-to-end escapar — o federado
primário ficava SEM busca de candidato (não achava Felipe Almeida, que existe).

Este sensor testa o end-to-end REAL: cada escopo entrega tools USÁVEIS do
catálogo de verdade (não nomes-fantasma). Sem este sensor, NÃO re-ativar o
federado primário.
"""
import pytest

from app.shared.tool_catalog import get_scoped_tool_definitions
from app.tools.scope_config import PromptScope

SCOPE_FLOOR = 10    # cada escopo precisa de >= N tools usáveis
SCOPE_CEILING = 80  # bounded: bem abaixo dos 179 (economia de token/turno)

KEY_READS = {
    PromptScope.GLOBAL: {"search_candidates", "list_jobs", "get_pipeline_summary"},
    PromptScope.TALENT_FUNNEL: {
        "search_candidates", "view_candidate_profile", "rank_candidates",
    },
    PromptScope.JOB_TABLE: {"list_jobs", "view_job_details"},
    PromptScope.IN_JOB: {"get_pipeline_summary", "list_stage_candidates"},
}


def _names(scope):
    return {getattr(d, "name", None) for d in get_scoped_tool_definitions(scope)}


@pytest.mark.parametrize("scope", list(KEY_READS.keys()))
def test_escopo_entrega_tools_usaveis(scope):
    names = _names(scope)
    assert len(names) >= SCOPE_FLOOR, (
        f"escopo {scope.value} entregou só {len(names)} tools (<{SCOPE_FLOOR}). "
        f"def-assembly/registry-scope quebrado. names={sorted(n for n in names if n)}"
    )


@pytest.mark.parametrize("scope", list(KEY_READS.keys()))
def test_escopo_bounded(scope):
    names = _names(scope)
    assert len(names) <= SCOPE_CEILING, (
        f"escopo {scope.value} tem {len(names)} tools (>{SCOPE_CEILING}); "
        "deve ser bounded (economia de token vs 179)."
    )


@pytest.mark.parametrize("scope,reads", list(KEY_READS.items()))
def test_escopo_inclui_reads_chave(scope, reads):
    names = _names(scope)
    missing = reads - names
    assert not missing, (
        f"escopo {scope.value} sem reads essenciais: {sorted(missing)}. "
        "O federado primário não conseguirá buscar/listar nesse contexto."
    )


def test_global_tem_busca_de_candidato_e_vaga():
    """Regressão do bug live: GLOBAL (fallback sem página) DEVE ter busca de
    candidato, senão 'tem felipe almeida?' falha apesar de o candidato existir."""
    names = _names(PromptScope.GLOBAL)
    for essential in ("search_candidates", "list_candidates", "view_candidate_profile"):
        assert essential in names, f"GLOBAL sem {essential} (bug live 2026-06-06)"
