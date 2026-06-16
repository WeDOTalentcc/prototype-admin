"""Sensor #2 (audit 2026-06-05): gate do modo de triagem.

Pina que o sistema NAO escolhe o modo silenciosamente: se screening_mode nao foi
definido, generate_wsi_questions devolve erro pedindo para PERGUNTAR (via
set_screening_mode) -- nunca cai em default 'compact'.
"""
from app.domains.job_creation.orchestrator.wizard_service_tools import (
    _wsi_generate_core,
)
from app.domains.job_creation.orchestrator.wizard_tools import ToolContext


def _ctx():
    return ToolContext(company_id="c1", user_id="u1", workspace_id=None)


def _state_pronto_sem_modo():
    # jd gerada + salario tratado, mas SEM screening_mode definido.
    return {
        "jd_enriched": {"about_role": "x", "responsabilidades": ["a"]},
        "salary_confirmed": True,
        "confirmed_technical_competencies": [{"skill": "Python"}],
        "confirmed_behavioral_competencies": [{"competencia": "Comunicacao"}],
        "parsed_seniority": "senior",
    }


def test_sem_modo_pede_para_perguntar():
    res = _wsi_generate_core(_state_pronto_sem_modo(), {}, _ctx())
    assert res.error
    msg = res.llm_message.lower()
    assert "modo" in msg
    assert "set_screening_mode" in res.llm_message


def test_gate_modo_vem_antes_do_servico_llm():
    # Sem modo, o gate retorna ANTES de chamar o WSIService (sem LLM/timeout).
    # Se chamasse o servico, levantaria/timeout em ambiente de teste.
    res = _wsi_generate_core(_state_pronto_sem_modo(), {}, _ctx())
    assert res.error
    assert "perguntas de triagem" not in (res.state_updates or {})


def test_salario_nao_tratado_tem_prioridade():
    st = _state_pronto_sem_modo()
    st.pop("salary_confirmed")
    res = _wsi_generate_core(st, {}, _ctx())
    assert res.error
    # gate de salario vem antes do gate de modo.
    assert "sal" in res.llm_message.lower()
