"""Sensor canonical (2026-06-04) — wiring "criar vaga a partir de fonte".

Pina o "agentic glue" da decisao Paulo (Opcao A, camada A2 = recruiter_copilot
conduz a identificacao da fonte):

  recrutador: "criar vaga a partir de um modelo"
    -> _is_create_from_source DEFERE o bootstrap do wizard vazio
    -> Phase 1.5: recruiter_copilot chama list_job_creation_sources, mostra
       as opcoes (ID + recrutador + gestor), pergunta qual
    -> chama start_creation_from_source(source_type, source_id)
       -> template: emite a diretiva ui_action='start_wizard_seeded' com
          seed_source={type,id} (semente do WizardSessionService.seed_initial_state)
       -> vacancy: ainda nao wired -> mensagem honesta (sem fabricar)

Cada assert fala com um LLM futuro: a mensagem de falha diz EXATAMENTE o que
regrediu e onde corrigir.
"""
import pytest


# ── 1. Tool existe e NAO pede company_id no payload (multi-tenancy canonical) ──
def test_start_creation_from_source_tool_exists_no_company_id_param():
    from app.domains.job_management.agents.wizard_tool_registry import (
        TOOL_DEFINITIONS,
    )
    td = next(
        (t for t in TOOL_DEFINITIONS if t.name == "start_creation_from_source"),
        None,
    )
    assert td is not None, (
        "tool 'start_creation_from_source' ausente de TOOL_DEFINITIONS — "
        "adicione-a em wizard_tool_registry.py ao lado de "
        "list_job_creation_sources (TOOL_DEFINITIONS.append(ToolDefinition(...)))."
    )
    props = td.parameters.get("properties", {})
    assert "company_id" not in props, (
        "REGRA 2 Pydantic / multi-tenancy: 'company_id' NAO pode ser parametro "
        "da tool — vem do ContextVar JWT via @tool_handler. Remova-o de "
        "parameters.properties de start_creation_from_source."
    )
    assert set(props.keys()) >= {"source_type", "source_id"}, (
        "start_creation_from_source deve declarar 'source_type' e 'source_id' "
        f"em parameters.properties; achei: {sorted(props.keys())}."
    )


# ── 2. Ambas as tools federadas no recruiter_copilot (chat global) ──
def test_both_tools_federated_into_recruiter_copilot():
    from app.domains.recruiter_assistant.agents.recruiter_copilot_tool_registry import (
        get_recruiter_copilot_tool_names,
    )
    names = set(get_recruiter_copilot_tool_names())
    for required in ("list_job_creation_sources", "start_creation_from_source"):
        assert required in names, (
            f"{required!r} ausente no set FEDERADO do chat global: o recrutador "
            f"nao consegue criar vaga a partir de fonte pelo chat. Adicione "
            f"('wizard', {required!r}) ao _FEDERATION_SPEC em "
            f"recruiter_copilot_tool_registry.py. Set atual: {sorted(names)}."
        )


# ── 3. Comportamento: template emite diretiva com seed_source carregando o id ──
@pytest.mark.asyncio
async def test_template_emits_seed_source_directive():
    from app.middleware.auth_enforcement import _current_company_id
    from app.domains.job_management.agents.wizard_tool_registry import (
        _wrap_start_creation_from_source,
    )
    token = _current_company_id.set(  # noqa: harness-test-only
        "00000000-0000-0000-0000-000000000001"
    )
    try:
        result = await _wrap_start_creation_from_source(
            source_type="template", source_id="tpl-123",
        )
    finally:
        _current_company_id.reset(token)

    assert result.get("success") is True, (
        "template path deve retornar success=True; recebi: " + repr(result)
    )
    data = result.get("data") or {}
    assert data.get("ui_action") == "start_wizard_seeded", (
        "template path deve emitir a diretiva ui_action='start_wizard_seeded' "
        "em data — e o seam que o caller (orchestrator) consome para semear a "
        f"sessao do wizard. Recebi data={data!r}."
    )
    seed = data.get("seed_source") or {}
    assert seed.get("type") == "template" and seed.get("id") == "tpl-123", (
        "seed_source deve carregar {type:'template', id:<source_id>} para o "
        "WizardSessionService.seed_initial_state casar a fonte. Recebi "
        f"seed_source={seed!r}."
    )


# ── 3b. Comportamento: vacancy ainda nao wired -> honesto, sem fabricar ──
@pytest.mark.asyncio
async def test_vacancy_returns_honest_not_yet():
    from app.middleware.auth_enforcement import _current_company_id
    from app.domains.job_management.agents.wizard_tool_registry import (
        _wrap_start_creation_from_source,
    )
    token = _current_company_id.set(  # noqa: harness-test-only
        "00000000-0000-0000-0000-000000000001"
    )
    try:
        result = await _wrap_start_creation_from_source(
            source_type="vacancy", source_id="vac-999",
        )
    finally:
        _current_company_id.reset(token)

    data = result.get("data") or {}
    assert data.get("not_yet") is True, (
        "vacancy producer ainda NAO esta wired — a tool deve sinalizar "
        "data.not_yet=True e oferecer template, JAMAIS fabricar uma sessao a "
        "partir de vaga (CLAUDE.md REGRA 4 anti-silent-fallback / proveniencia "
        f"honesta). Recebi data={data!r}."
    )
    assert "ui_action" not in data, (
        "vacancy path NAO deve emitir ui_action='start_wizard_seeded' enquanto "
        "o producer de vaga nao estiver wired."
    )


# ── 4. from-source detector (GUIDE feedforward) — guard de bootstrap ──
def test_plain_create_still_bootstraps():
    from app.orchestrator.execution.main_orchestrator import (
        _is_create_from_source,
    )
    assert _is_create_from_source("criar uma vaga") is False, (
        "REGRESSAO: 'criar uma vaga' (intent simples) deve continuar "
        "bootstrapando o wizard vazio como hoje — _is_create_from_source NAO "
        "pode capturar frases simples de criacao. Veja "
        "_is_create_from_source em main_orchestrator.py e mantenha o detector "
        "conservador (so frases claras de 'a partir de fonte')."
    )
    assert _is_create_from_source("nova vaga de backend") is False, (
        "REGRESSAO: 'nova vaga de ...' deve seguir bootstrapando o wizard "
        "vazio. _is_create_from_source esta capturando demais."
    )


def test_from_source_phrasing_defers_bootstrap():
    from app.orchestrator.execution.main_orchestrator import (
        _is_create_from_source,
    )
    for phrase in (
        "criar vaga a partir de um modelo",
        "quero criar uma vaga usando template",
        "criar vaga baseada na vaga do gestor Joao",
        "abrir vaga a partir de uma vaga existente",
        "criar vaga usando um arquetipo",
    ):
        assert _is_create_from_source(phrase) is True, (
            f"'{phrase}' deveria DEFERIR o bootstrap do wizard vazio (deixar a "
            f"Phase 1.5 / recruiter_copilot identificar a fonte). "
            f"_is_create_from_source retornou False — amplie (conservadoramente) "
            f"as frases em main_orchestrator.py:_is_create_from_source."
        )
