"""Balde-3 fix (2026-06-04): handoffs delegate_to_* DEVEM ter categoria canonical.

Root cause (systematic-debugging): no live, o supervisor NAO chamava delegate_to_policy
("quais politicas?" -> compunha de get_company_config). Motivo: handoffs caiam em
category OTHER -> a secao Capabilities do system prompt os despejava em "OUTROS (sem
categoria canonical)", framing de segunda-classe -> LLM nao os selecionava. Fix: categoria
DELEGACAO + tagline intent->tool. Pina o mapeamento.
"""
from app.tools.categories import (
    category_for_tool, ToolCategory, CATEGORY_TAGLINES, DISPLAY_ORDER,
)

DELEGATES = [
    "delegate_to_pipeline", "delegate_to_talent_pool", "delegate_to_sourcing",
    "delegate_to_communication", "delegate_to_analytics", "delegate_to_company_settings",
    "delegate_to_policy", "delegate_to_ats_integration",
    "delegate_to_job_management",
]


def test_all_delegates_mapped_not_other():
    for name in DELEGATES:
        cat = category_for_tool(name)
        assert cat == ToolCategory.DELEGACAO, f"{name} -> {cat} (esperado DELEGACAO)"
        assert cat != ToolCategory.OTHER


def test_delegacao_has_tagline_and_display_order():
    assert ToolCategory.DELEGACAO in CATEGORY_TAGLINES
    assert CATEGORY_TAGLINES[ToolCategory.DELEGACAO].strip(), "tagline nao pode ser vazia"
    assert ToolCategory.DELEGACAO in DISPLAY_ORDER
    # a tagline deve ensinar pelo menos o mapeamento de politica (o caso live)
    assert "delegate_to_policy" in CATEGORY_TAGLINES[ToolCategory.DELEGACAO]



def test_autonomous_is_not_a_supervisor_handoff_target():
    """Gap autonomous (2026-06-08): a entrada 'autonomous' foi removida do mapa de
    handoff do supervisor. Era um bug de governanca: a descricao dizia "acoes
    pendentes" (semantica do AutonomousAgentService / proactive actions) mas o
    delegate_to_autonomous resolvia o AutonomousReActAgent (ReAct cross-domain,
    legado redundante, Tier 6 removido). Ver AI_LAYER_TREE.md 12.3.
    """
    from app.orchestrator.supervisor.handoff_tools import DOMAINS

    assert "autonomous" not in DOMAINS, (
        "'autonomous' nao deve ser destino de handoff do supervisor — e legado "
        "redundante (Tier 6 removido) e a descricao estava desalinhada com o agente "
        "que delegate_to_autonomous realmente invocava (ver AI_LAYER_TREE.md 12.3)"
    )

    from app.tools.categories import category_for_tool, ToolCategory
    # delegate_to_autonomous nao deve mais existir como categoria de delegacao
    assert category_for_tool("delegate_to_autonomous") != ToolCategory.DELEGACAO, (
        "delegate_to_autonomous nao deve mais estar mapeado como DELEGACAO"
    )
