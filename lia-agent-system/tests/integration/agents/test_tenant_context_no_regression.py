"""Task #972 (T-E canônica) — Bug-repro suite: "LIA pergunta company_id".

Origem do bug: a LIA respondia "Qual a empresa?" / "Preciso saber qual empresa"
mesmo com JWT válido apontando para uma Demo Company canônica. Caiu 2 vezes:
hotfix `fix-wizard-company-context.md` (wizard apenas) e regressão silenciosa
em outros agentes quando o helper `_compose_runtime_prompt` ainda não existia.

Esta suite garante que o bug NUNCA mais volte. Roda em CI a cada PR.

Cobertura (3 contratos × 16 agentes = matriz):

    1. POSITIVO — quando `tenant_context_snippet` está presente, o prompt
       renderizado contém os marcadores do tenant (nome, setor, plano).
       Prova que o snippet não é descartado pelo runtime composer.

    2. ANTI-PADRÃO — o prompt base do agente NÃO contém literais que
       fariam a LIA pedir empresa ao usuário. Regex catches:

         (?i)(qual.*empresa|qual.*id.*empresa|preciso.*empresa|me\\s+informe.*empresa|qual\\s+o\\s+id|informe.*company)

       Se algum future PR adicionar uma instrução do tipo "se não souber a
       empresa, pergunte ao usuário" no system prompt, este teste quebra
       imediatamente.

    3. FAIL-CLOSED — em strict-mode, agente invocado SEM tenant context
       resolvível levanta `MissingTenantContextError` em vez de degradar
       para "sua empresa"/"geral". Prova que a LIA nunca terá oportunidade
       de pedir empresa ao usuário — a request é rejeitada antes do LLM.

Anti-padrão histórico: "fix sem teste de regressão = bug volta".
Origem das duas quedas anteriores: replit.md "Funil de Talentos (canônico
719L)" cita 2 reversões análogas.
"""
from __future__ import annotations

import re

import pytest

from lia_agents_core.agent_interface import AgentInput

from app.shared.agents.tenant_aware_agent import (
    TenantAwareAgentMixin,
    reset_tenant_context_metrics,
)
from app.shared.exceptions.tenant_errors import MissingTenantContextError

# 12 agentes "standard" (override de _get_runtime_domain_instructions)
from app.domains.analytics.agents.analytics_react_agent import AnalyticsReActAgent
from app.domains.ats_integration.agents.ats_integration_react_agent import (
    ATSIntegrationReActAgent,
)
from app.domains.automation.agents.automation_react_agent import AutomationReActAgent
from app.domains.communication.agents.communication_react_agent import (
    CommunicationReActAgent,
)
from app.domains.company_settings.agents.company_react_agent import (
    CompanySettingsReActAgent,
)
from app.domains.cv_screening.agents.pipeline_react_agent import PipelineReActAgent
from app.domains.hiring_policy.agents.policy_react_agent import PolicyReActAgent
from app.domains.recruiter_assistant.agents.jobs_mgmt_react_agent import (
    JobsManagementReActAgent,
)
from app.domains.recruiter_assistant.agents.kanban_react_agent import KanbanReActAgent
from app.domains.recruiter_assistant.agents.talent_funnel_react_agent import (
    TalentFunnelReActAgent,
)
from app.domains.sourcing.agents.sourcing_react_agent import SourcingReActAgent
from app.domains.talent_pool.agents.talent_pool_agent import TalentPoolReActAgent

# Wizard (T-B piloto) — tenant_strict_override=True hardcoded
from app.domains.job_management.agents.wizard_react_agent import WizardReActAgent

# 2 agentes "CSS path" (override de _get_system_prompt em vez de runtime)
from app.domains.candidate_self_service.agents.candidate_react_agent import (
    CandidateSelfServiceAgent,
)
from app.domains.pipeline.agents.pipeline_transition_agent import (
    PipelineTransitionAgent,
)


# ─── Fixtures ───────────────────────────────────────────────────────────────

DEMO_COMPANY_UUID = "00000000-0000-4000-a000-000000000001"
DEMO_TENANT_NAME = "Demo Company T-E"
DEMO_SECTOR = "Tecnologia"
DEMO_PLAN = "enterprise"

# Snippet renderizado como TenantContextService.get_context().to_prompt_snippet().
# Inclui marcadores únicos pra detectar propagação no prompt final.
TENANT_SNIPPET = (
    f"Empresa: {DEMO_TENANT_NAME} ({DEMO_SECTOR})\n"
    f"Plano: {DEMO_PLAN}\n"
    f"Timezone: America/Sao_Paulo\n"
    f"company_id={DEMO_COMPANY_UUID}"
)

# Anti-padrões que NUNCA podem aparecer num system prompt renderizado de
# agente de recrutador. Se aparecerem, a LIA tem licença pra pedir empresa
# ao usuário — origem do bug que esta suite vigia.
ANTI_PATTERN_REGEX = re.compile(
    r"(?ix)("
    r"  qual\s+(é\s+)?a?\s*empresa\??"
    r"| qual\s+o?\s*id\s+da?\s*empresa"
    r"| preciso\s+saber\s+(qual\s+)?(é\s+)?a?\s*empresa"
    r"| me\s+informe\s+(qual\s+)?(a\s+)?empresa"
    r"| informe\s+(o\s+)?company[_\s]?id"
    r"| em\s+qual\s+empresa\s+você\s+trabalha"
    r")"
)

# Inventário canônico — 16 ReActAgents (T-B + T-D).
# Particionado por path de propagação:
#   - RUNTIME_PATH: snippet flui via _get_runtime_domain_instructions
#   - SYSTEM_PROMPT_PATH: snippet flui via _get_system_prompt (CSS, transition)
RUNTIME_PATH_AGENTS = [
    AnalyticsReActAgent,
    ATSIntegrationReActAgent,
    AutomationReActAgent,
    CommunicationReActAgent,
    CompanySettingsReActAgent,
    PipelineReActAgent,
    PolicyReActAgent,
    JobsManagementReActAgent,
    KanbanReActAgent,
    TalentFunnelReActAgent,
    SourcingReActAgent,
    TalentPoolReActAgent,
    WizardReActAgent,
]

SYSTEM_PROMPT_PATH_AGENTS = [
    CandidateSelfServiceAgent,
    PipelineTransitionAgent,
]

ALL_AGENTS = RUNTIME_PATH_AGENTS + SYSTEM_PROMPT_PATH_AGENTS

assert len(ALL_AGENTS) == 15, (
    f"Inventário canônico T-D quebrado: esperado 15 agentes, encontrado {len(ALL_AGENTS)}. "
    "Se um 16º ReActAgent foi adicionado sem seguir o padrão TenantAwareAgentMixin, "
    "esta suite precisa ser atualizada — caso contrário o bug 'LIA pergunta company_id' "
    "volta silenciosamente para o agente novo."
)


def _make_input_with_snippet(message: str = "Quais vagas estão abertas?") -> AgentInput:
    """AgentInput com snippet pré-injetado (rota feliz: SSE/WS handler já populou)."""
    return AgentInput(
        message=message,
        user_id="recruiter-1",
        company_id=DEMO_COMPANY_UUID,
        session_id="sess-t-e-bugrepro",
        context={
            "tenant_context_snippet": TENANT_SNIPPET,
            "memory_summary": "",
            "stage_context": "",
        },
    )


def _make_input_without_tenant(message: str = "Quais vagas estão abertas?") -> AgentInput:
    """AgentInput SEM snippet e SEM tenant_context — cenário fail-closed.

    Em strict-mode, este input deve fazer o agente recusar a request com
    `MissingTenantContextError` (preferível a degradar pra "sua empresa").
    """
    return AgentInput(
        message=message,
        user_id="recruiter-1",
        company_id=DEMO_COMPANY_UUID,
        session_id="sess-t-e-bugrepro-empty",
        context={"memory_summary": "", "stage_context": ""},
    )


@pytest.fixture(autouse=True)
def _reset_metrics():
    """Cada teste começa com contador zerado pra não vazar entre runs."""
    reset_tenant_context_metrics()
    yield
    reset_tenant_context_metrics()


# ─── Contrato 1: POSITIVO — snippet propaga ao prompt renderizado ──────────


@pytest.mark.parametrize(
    "cls",
    RUNTIME_PATH_AGENTS,
    ids=lambda c: c.__name__,
)
def test_runtime_prompt_contains_tenant_markers(cls):
    """Quando snippet está presente, o prompt renderizado deve conter o nome
    da empresa, setor e plano. Sem isso, a LIA não sabe que existe contexto
    de tenant e tem licença pra pedir empresa ao usuário."""
    inst = cls.__new__(cls)
    out = inst._get_runtime_domain_instructions(_make_input_with_snippet())

    assert isinstance(out, str) and out.strip(), (
        f"{cls.__name__}: prompt vazio — snippet T-E não pôde ser propagado."
    )
    assert DEMO_TENANT_NAME in out, (
        f"{cls.__name__}: nome da empresa '{DEMO_TENANT_NAME}' não aparece no prompt. "
        "Provável regressão: voltou a usar PromptComposer.for_domain_runtime direto "
        "em vez de self._compose_runtime_prompt(input, ...)."
    )
    assert DEMO_SECTOR in out and DEMO_PLAN in out, (
        f"{cls.__name__}: setor/plano do snippet sumiram no prompt final — "
        "o snippet pode estar sendo truncado/sobrescrito pelo composer."
    )


@pytest.mark.parametrize(
    "cls",
    SYSTEM_PROMPT_PATH_AGENTS,
    ids=lambda c: c.__name__,
)
def test_system_prompt_contains_tenant_markers(cls):
    """CSS + PipelineTransition: snippet flui via _get_system_prompt."""
    inst = cls.__new__(cls)
    out = inst._get_system_prompt(_make_input_with_snippet())

    assert isinstance(out, str) and out.strip(), f"{cls.__name__}: prompt vazio"
    assert DEMO_TENANT_NAME in out, (
        f"{cls.__name__}._get_system_prompt: nome da empresa sumiu — "
        "candidatos/transições voltam a ver 'qual a empresa?'."
    )


# ─── Contrato 2: ANTI-PADRÃO — system prompt não pede empresa ──────────────


@pytest.mark.parametrize(
    "cls",
    RUNTIME_PATH_AGENTS,
    ids=lambda c: c.__name__,
)
def test_runtime_prompt_has_no_ask_company_anti_pattern(cls):
    """Bug-repro core: o prompt renderizado NUNCA pode conter instruções
    do tipo 'se não souber a empresa, pergunte ao usuário'.

    Este teste é a prova final de não-regressão. Se um futuro PR adicionar
    uma frase como 'pergunte qual empresa' a um system prompt YAML, o build
    fica vermelho — exatamente o que faltou nas duas quedas anteriores.
    """
    inst = cls.__new__(cls)
    out = inst._get_runtime_domain_instructions(_make_input_with_snippet())

    matches = ANTI_PATTERN_REGEX.findall(out)
    assert not matches, (
        f"{cls.__name__}: ANTI-PADRÃO detectado no system prompt: {matches!r}\n"
        "O prompt instrui a LIA a pedir empresa ao usuário — exatamente o bug "
        "'LIA pergunta company_id'. Remova a instrução do YAML/template do agente."
    )


@pytest.mark.parametrize(
    "cls",
    SYSTEM_PROMPT_PATH_AGENTS,
    ids=lambda c: c.__name__,
)
def test_system_prompt_has_no_ask_company_anti_pattern(cls):
    """Idem para CSS + PipelineTransition (path _get_system_prompt)."""
    inst = cls.__new__(cls)
    out = inst._get_system_prompt(_make_input_with_snippet())

    matches = ANTI_PATTERN_REGEX.findall(out)
    assert not matches, (
        f"{cls.__name__}: ANTI-PADRÃO no system prompt: {matches!r}"
    )


# ─── Contrato 3: FAIL-CLOSED — strict-mode rejeita request sem tenant ──────


@pytest.mark.parametrize(
    "cls",
    RUNTIME_PATH_AGENTS,
    ids=lambda c: c.__name__,
)
def test_strict_mode_raises_when_tenant_missing(cls, monkeypatch):
    """Em strict-mode, agente invocado sem tenant resolvível levanta
    `MissingTenantContextError` em vez de degradar.

    Esta é a garantia DURA contra "LIA pergunta company_id": mesmo se o
    prompt template estiver perfeito, sem tenant resolvido a request é
    rejeitada antes da chamada LLM. A LIA nunca tem oportunidade de
    perguntar empresa porque nem chega a falar.
    """
    monkeypatch.setenv("LIA_AGENT_TENANT_STRICT", "true")
    inst = cls.__new__(cls)
    inp = _make_input_without_tenant()

    with pytest.raises(MissingTenantContextError) as exc_info:
        inst._get_system_prompt(inp)

    # Detalhes auditáveis: agent name + company_id_raw + tenant_source.
    details = exc_info.value.details
    assert "agent" in details, (
        f"{cls.__name__}: MissingTenantContextError sem 'agent' em details — "
        "auditoria fica cega pra debug em prod."
    )
    assert details.get("tenant_source") == "system_prompt_hook", (
        f"{cls.__name__}: tenant_source incorreto ({details.get('tenant_source')!r}) — "
        "esperado 'system_prompt_hook' (defense-in-depth path)."
    )


# ─── Contrato 4: Wizard hardcoded strict — defesa contra rollback dev ──────


def test_wizard_strict_override_is_immutable_true():
    """Wizard tem `tenant_strict_override = True` HARDCODED — não respeita
    `LIA_AGENT_TENANT_STRICT=false` em dev. Justificativa: o wizard é a
    rota de entrada de criação de vaga; degradar tenant aqui contamina
    todos os artefatos downstream (Job, Pipeline, etc.).
    """
    assert WizardReActAgent.tenant_strict_override is True, (
        "Wizard PERDEU tenant_strict_override=True — agora pode degradar "
        "para 'sua empresa' em dev. Isso reabre o bug original do hotfix "
        "fix-wizard-company-context.md."
    )


def test_wizard_strict_in_dev_even_when_env_false(monkeypatch):
    """Mesmo com env OFF, wizard continua strict (override hardcoded)."""
    monkeypatch.setenv("LIA_AGENT_TENANT_STRICT", "false")
    monkeypatch.setenv("APP_ENV", "development")

    inst = WizardReActAgent.__new__(WizardReActAgent)
    with pytest.raises(MissingTenantContextError):
        inst._get_system_prompt(_make_input_without_tenant())


# ─── Contrato 5: Whitelist — snippet não é tratado como PII pelo prompt ────


def test_tenant_snippet_does_not_contain_candidate_pii():
    """O snippet renderizado por TenantContextService contém apenas dados
    da PESSOA JURÍDICA (nome empresa, setor, plano) — não dados de pessoa
    natural. Isto justifica o whitelist do FairnessGuard/PII strip: o
    snippet pode entrar no prompt sem ser mascarado.

    Este teste é um smoke contract: se alguém adicionar email/CPF ao
    snippet (via TenantContextService.to_prompt_snippet), este teste
    quebra e força revisão LGPD.
    """
    pii_patterns = [
        r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b",  # CPF
        r"[\w.+-]+@[\w-]+\.[\w.-]+",  # email
        r"\b\(?\d{2}\)?\s?9?\d{4}-?\d{4}\b",  # phone BR
    ]
    for pat in pii_patterns:
        assert not re.search(pat, TENANT_SNIPPET), (
            f"Snippet T-E contém PII de pessoa natural ({pat}). "
            "TenantContextService.to_prompt_snippet deve emitir só dados "
            "de pessoa jurídica (LGPD Art. 5 V). Whitelist do FairnessGuard "
            "depende desta invariante."
        )


# ─── Contrato 6: Inventário sentinel — 16 agentes ──────────────────────────


def test_inventory_sentinel_all_agents_inherit_mixin():
    """Sentinela: cada agente do inventário herda do mixin. Espelha o teste
    em test_tenant_aware_rollout_t_d.py mas ancorado nesta suite — se
    um agente futuro for adicionado SEM o mixin, ambas suítes quebram."""
    for cls in ALL_AGENTS:
        assert issubclass(cls, TenantAwareAgentMixin), (
            f"{cls.__name__} NÃO herda TenantAwareAgentMixin — bug-repro "
            "T-E não cobre este agente; LIA pode voltar a pedir empresa nele."
        )
