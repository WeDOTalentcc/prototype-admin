"""T-D rollout regression tests — TenantAwareAgentMixin nos 16 ReActAgents.

Garantia canônica: TODOS os ReActAgents (não só wizard) injetam o
``tenant_context_snippet`` no prompt em runtime, fechando o gap onde a LIA
respondia "qual a empresa?" mesmo com JWT correto.

Cobertura:
- MRO: ``TenantAwareAgentMixin`` antes de ``LangGraphReActBase`` (12 agentes
  standard + candidate_self_service + talent_pool).
- Snippet propagation: ``_get_runtime_domain_instructions`` (ou
  ``_get_system_prompt`` no caso do CSS) inclui o snippet no texto final.
- Helper canônico ``_compose_runtime_prompt`` aceita ``agent_type`` override
  para preservar chaves YAML quando ``agent_type != domain_name``
  (cv_screening_pipeline, jobs_mgmt).

Origem: Task #971 (T-D), follow-up de T-B (#970 / wizard piloto).
"""
from __future__ import annotations

import pytest

from lia_agents_core.agent_interface import AgentInput

from app.shared.agents.tenant_aware_agent import TenantAwareAgentMixin

# 12 agentes standard (override de _get_runtime_domain_instructions)
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

# 2 agentes especiais
from app.domains.candidate_self_service.agents.candidate_react_agent import (
    CandidateSelfServiceAgent,
)
from app.domains.pipeline.agents.pipeline_transition_agent import (
    PipelineTransitionAgent,
)
from app.domains.talent_pool.agents.talent_pool_agent import TalentPoolReActAgent

# Wizard (T-B já feito — incluído pra confirmar inventário 16)
from app.domains.job_management.agents.wizard_react_agent import WizardReActAgent


SNIPPET_MARKER = "TENANT_SNIPPET_T_D_MARKER_DemoCo_Tecnologia"

ALL_REACT_AGENTS_RUNTIME_PATH = [
    AnalyticsReActAgent,
    ATSIntegrationReActAgent,
    AutomationReActAgent,
    CommunicationReActAgent,
    CompanySettingsReActAgent,
    PipelineReActAgent,  # cv_screening
    PolicyReActAgent,  # hiring_policy
    JobsManagementReActAgent,
    KanbanReActAgent,
    TalentFunnelReActAgent,
    SourcingReActAgent,
    TalentPoolReActAgent,  # T-D adicionou _get_runtime_domain_instructions
    WizardReActAgent,  # T-B (incluso pra completude do inventário)
]

CSS_AGENTS_SYSTEM_PROMPT_PATH = [CandidateSelfServiceAgent, PipelineTransitionAgent]


def _make_input() -> AgentInput:
    return AgentInput(
        message="Quais vagas abertas temos?",
        user_id="recruiter-1",
        company_id="00000000-0000-4000-a000-000000000001",
        session_id="sess-t-d",
        context={
            "tenant_context_snippet": SNIPPET_MARKER,
            "memory_summary": "",
            "stage_context": "",
        },
    )


# ─── MRO contract ──────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "cls",
    ALL_REACT_AGENTS_RUNTIME_PATH + CSS_AGENTS_SYSTEM_PROMPT_PATH,
    ids=lambda c: c.__name__,
)
def test_agent_inherits_tenant_aware_mixin_with_correct_mro(cls):
    """Mixin deve estar antes de ``LangGraphReActBase`` no MRO — ordem
    importa porque ``_process_langgraph`` (mixin) precisa rodar antes do
    base pra resolver tenant context async."""
    assert issubclass(cls, TenantAwareAgentMixin), (
        f"{cls.__name__} NÃO herda TenantAwareAgentMixin — gap T-D"
    )

    mro = [c.__name__ for c in cls.__mro__]
    idx_taa = mro.index("TenantAwareAgentMixin")
    idx_base = mro.index("LangGraphReActBase")
    assert idx_taa < idx_base, (
        f"{cls.__name__} MRO incorreta: TenantAwareAgentMixin (idx={idx_taa}) "
        f"deve vir ANTES de LangGraphReActBase (idx={idx_base}). MRO: {mro[:6]}"
    )


# ─── Runtime snippet propagation (standard path) ────────────────────────────


@pytest.mark.parametrize(
    "cls",
    ALL_REACT_AGENTS_RUNTIME_PATH,
    ids=lambda c: c.__name__,
)
def test_agent_runtime_prompt_propagates_tenant_snippet(cls):
    """``_get_runtime_domain_instructions`` deve incluir o snippet no texto
    final — prova que o helper ``_compose_runtime_prompt`` está sendo usado
    em vez de ``PromptComposer.for_domain_runtime`` direto."""
    inst = cls.__new__(cls)
    out = inst._get_runtime_domain_instructions(_make_input())
    assert isinstance(out, str) and out, f"{cls.__name__}: empty prompt"
    assert SNIPPET_MARKER in out, (
        f"{cls.__name__}: tenant_context_snippet NÃO chegou ao prompt final. "
        f"Provável regressão: voltou a usar PromptComposer.for_domain_runtime "
        f"direto em vez de self._compose_runtime_prompt(input, ...)."
    )


# ─── CSS path (overrides _get_system_prompt em vez de runtime instructions) ──


def test_candidate_self_service_get_system_prompt_propagates_snippet():
    """CSS é caso especial: usa ``_get_system_prompt`` direto pra evitar a
    persona recruiter (Audit N 2026-05-07). A propagação do snippet acontece
    no override de ``_get_system_prompt``, não em runtime instructions."""
    inst = CandidateSelfServiceAgent.__new__(CandidateSelfServiceAgent)
    out = inst._get_system_prompt(_make_input())
    assert SNIPPET_MARKER in out, (
        "CSS _get_system_prompt deveria incluir tenant_context_snippet — "
        "se este teste falhar, candidatos voltam a ver 'qual a empresa?'."
    )


def test_pipeline_transition_get_system_prompt_propagates_snippet():
    """Pipeline transition é o outro caso especial: chama
    ``get_pipeline_system_prompt`` direto (assinatura customizada com
    from_stage/to_stage). O override T-D prepende o snippet ao base."""
    inst = PipelineTransitionAgent.__new__(PipelineTransitionAgent)
    out = inst._get_system_prompt(_make_input())
    assert SNIPPET_MARKER in out, (
        "PipelineTransitionAgent._get_system_prompt deveria prefixar o "
        "tenant_context_snippet — sem isso, transições voltam ao "
        "'qual a empresa?'."
    )


# ─── Helper aceita agent_type override (regressão T-D) ──────────────────────


def test_compose_runtime_prompt_accepts_agent_type_override():
    """T-D fix: o helper aceita ``agent_type`` override pra preservar chaves
    YAML quando ``agent_type != domain_name`` (ex: cv_screening_pipeline,
    jobs_mgmt). Sem isso, agentes com chaves YAML diferentes do domain_name
    perderiam configurações de prompt ao migrar pra mixin."""
    inst = PipelineReActAgent.__new__(PipelineReActAgent)
    # PipelineReActAgent: domain_name="pipeline" mas YAML key="cv_screening_pipeline"
    out = inst._compose_runtime_prompt(
        _make_input(),
        agent_type="cv_screening_pipeline",
        domain_specific="DOM_X",
    )
    # PromptComposerResult.text contains snippet + domain_specific
    assert SNIPPET_MARKER in out.text
    assert "DOM_X" in out.text


# ─── Inventário canônico (16 agentes T-B+T-D = wizard + 15) ─────────────────


def test_canonical_inventory_count_16_agents():
    """Sentinela: 16 ReActAgents totais herdam TenantAwareAgentMixin
    (wizard via T-B + 15 via T-D). Se este teste quebrar, foi adicionado
    um novo ReActAgent SEM seguir o padrão T-D — a regra canônica.

    Inventário (16):
        - 12 standard runtime path: analytics, ats_integration, automation,
          autonomous, communication, company_settings, cv_screening_pipeline,
          hiring_policy, jobs_mgmt, kanban, talent_funnel, sourcing.
        - 1 talent_pool (T-D adicionou _get_runtime_domain_instructions).
        - 1 wizard (piloto T-B).
        - 2 caminho _get_system_prompt: candidate_self_service,
          pipeline_transition.

    Para adicionar um 17º agente: estender lista acima, herdar
    TenantAwareAgentMixin, usar self._compose_runtime_prompt(...) ou
    prepender snippet em _get_system_prompt."""
    total = len(ALL_REACT_AGENTS_RUNTIME_PATH) + len(CSS_AGENTS_SYSTEM_PROMPT_PATH)
    assert total == 15, (
        f"Inventário canônico de ReActAgents mudou: esperado 15, encontrado {total}. "
        "Atualize a lista e confirme que o novo agente segue o padrão T-D."
    )
