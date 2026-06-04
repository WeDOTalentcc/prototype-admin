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
    "delegate_to_policy", "delegate_to_autonomous", "delegate_to_ats_integration",
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
