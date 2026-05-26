"""PR-1 Onda 1 (2026-05-26) — runtime invariantes do state canonical do wizard.

Sensor de tempo de import — valida que as estruturas canonical do
`app/domains/job_creation/state.py` + `wizard_session_service` +
`wizard_tool_registry` permanecem coerentes entre si.

Garante que se alguém adicionar/remover uma stage runtime sem espelhar
no Literal de tipo (ou vice-versa), o test falha ANTES de chegar em
produção e quebrar checkpoint LangGraph silenciosamente.

Invariantes (4):

1. STAGE_ORDER ⊆ set(WizardStage.__args__) — todo stage runtime tem
   correspondente no Literal de tipo (type-safety).
2. HITL_STAGES ⊆ set(WizardStage.__args__) — todo HITL stage tem
   correspondente no Literal de tipo.
3. "pipeline_template_skipped" declarado em
   JobCreationState.__annotations__ — graph.py:1534 escreve esse campo
   no checkpoint LangGraph (TypedDict precisa declarar pra type-checker
   detectar regressão).
4. "pipeline-template" (kebab) presente em STAGE_TOOLS do
   wizard_tool_registry — consistency com outros stages de criação
   (jd-enrichment, wsi-questions).

Refs:
- Plano: ~/.claude/plans/cozy-hatching-stream.md
- Sensor estático: scripts/check_pipeline_template_node_canonical.py
"""
from __future__ import annotations

import typing


def test_stage_order_subset_of_wizard_stage_literal():
    """Invariante 1: todo stage runtime tem Literal type matching."""
    from app.domains.job_creation.state import STAGE_ORDER, WizardStage

    literal_values = set(typing.get_args(WizardStage))
    stage_order_set = set(STAGE_ORDER)

    missing = stage_order_set - literal_values
    assert not missing, (
        f"Stages em STAGE_ORDER mas SEM Literal type: {sorted(missing)}.\n"
        f"   Adicionar {sorted(missing)} ao Literal WizardStage em "
        f"app/domains/job_creation/state.py."
    )


def test_hitl_stages_subset_of_wizard_stage_literal():
    """Invariante 2: todo HITL stage tem Literal type matching."""
    from app.domains.job_creation.state import HITL_STAGES, WizardStage

    literal_values = set(typing.get_args(WizardStage))
    hitl_set = set(HITL_STAGES)

    missing = hitl_set - literal_values
    assert not missing, (
        f"Stages em HITL_STAGES mas SEM Literal type: {sorted(missing)}.\n"
        f"   Adicionar {sorted(missing)} ao Literal WizardStage em "
        f"app/domains/job_creation/state.py."
    )


def test_pipeline_template_skipped_declared_in_typeddict():
    """Invariante 3: pipeline_template_skipped declarado em JobCreationState.

    graph.py:1534 escreve esse campo no return do pipeline_template_node;
    sem declaração no TypedDict, checkpoint LangGraph perde silenciosamente
    e "Usar Padrão da Empresa" pode regredir em loops infinitos.
    """
    from app.domains.job_creation.state import JobCreationState

    annotations = JobCreationState.__annotations__
    assert "pipeline_template_skipped" in annotations, (
        "'pipeline_template_skipped' ausente do TypedDict JobCreationState.\n"
        "   graph.py:1534 escreve esse campo no checkpoint LangGraph.\n"
        "   Fix: adicionar `pipeline_template_skipped: Optional[bool]` "
        "entre pipeline_template_id e pipeline_template_score em state.py."
    )


def test_stage_tools_has_pipeline_template_kebab_key():
    """Invariante 4: 'pipeline-template' (kebab) em STAGE_TOOLS.

    NOTA: STAGE_TOOLS é hoje canonical documentation (não enforcement).
    get_stage_tools tem zero callers em produção. Entry kebab é
    consistency com convenção de outros stages de criação.
    """
    from app.domains.job_management.agents.wizard_tool_registry import STAGE_TOOLS

    assert "pipeline-template" in STAGE_TOOLS, (
        "'pipeline-template' (kebab) ausente de STAGE_TOOLS.\n"
        "   Fix: adicionar entry após \"jd-enrichment\" em "
        "app/domains/job_management/agents/wizard_tool_registry.py:\n"
        "   `\"pipeline-template\": [\"suggest_pipeline_stage_templates\", "
        "\"apply_pipeline_stage_template_to_vacancy\", "
        "\"create_custom_pipeline_stage_template\"]`"
    )
    expected_tools = {
        "suggest_pipeline_stage_templates",
        "apply_pipeline_stage_template_to_vacancy",
        "create_custom_pipeline_stage_template",
    }
    actual_tools = set(STAGE_TOOLS["pipeline-template"])
    missing = expected_tools - actual_tools
    assert not missing, (
        f"STAGE_TOOLS[pipeline-template] sem tools canonical: {sorted(missing)}."
    )
