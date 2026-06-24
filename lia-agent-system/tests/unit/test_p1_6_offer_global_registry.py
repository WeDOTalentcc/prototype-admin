"""
tests/unit/test_p1_6_offer_global_registry.py

P1-6 (2026-06-18): offer lifecycle tools registered globally
TDD Red→Green: verifica que register_offer_global() popula o registry
com as 8 tools esperadas.
"""
import pytest

EXPECTED_OFFER_TOOLS = {
    "get_offer_status",
    "get_negotiation_context",
    "suggest_next_start_date",
    "escalate_offer_to_recruiter",
    "log_negotiation_event",
    "get_benefit_details",
    "draft_offer_response",
    "get_offer_learning_context",
}


def test_register_offer_global_returns_8():
    """register_offer_global() retorna 8 (count de tools registradas)."""
    from app.tools.registry import tool_registry
    from app.domains.offer.agents.offer_tool_registry import register_offer_global

    # Usa registry isolado para não poluir estado global
    from app.tools.registry import ToolRegistry
    isolated = ToolRegistry()

    # Patch temporário para usar registry isolado
    import app.tools.registry as _reg_mod
    original = _reg_mod.tool_registry
    _reg_mod.tool_registry = isolated
    try:
        count = register_offer_global()
    finally:
        _reg_mod.tool_registry = original

    assert count == 8, f"Esperado 8 tools, registrou {count}"


def test_offer_tools_all_present_after_register():
    """Todas as 8 tools esperadas aparecem no registry após register_offer_global()."""
    from app.tools.registry import ToolRegistry
    import app.tools.registry as _reg_mod
    from app.domains.offer.agents.offer_tool_registry import register_offer_global

    isolated = ToolRegistry()
    original = _reg_mod.tool_registry
    _reg_mod.tool_registry = isolated
    try:
        register_offer_global()
        registered_names = set(isolated.list_tools())
    finally:
        _reg_mod.tool_registry = original

    missing = EXPECTED_OFFER_TOOLS - registered_names
    assert not missing, (
        f"[P1-6] Tools faltando no registry apos register_offer_global(): {missing}. "
        f"Presentes: {registered_names}"
    )


def test_offer_tools_have_required_schema_fields():
    """Cada tool de offer tem name, description e parameters_schema não-vazio."""
    from app.tools.registry import ToolRegistry
    import app.tools.registry as _reg_mod
    from app.domains.offer.agents.offer_tool_registry import register_offer_global

    isolated = ToolRegistry()
    original = _reg_mod.tool_registry
    _reg_mod.tool_registry = isolated
    try:
        register_offer_global()
        tools = {name: isolated.get_tool(name) for name in isolated.list_tools()}
    finally:
        _reg_mod.tool_registry = original

    for name in EXPECTED_OFFER_TOOLS:
        td = tools[name]
        assert td.description, f"[P1-6] {name}: description vazia"
        schema = td.parameters_schema
        assert schema, f"[P1-6] {name}: parameters_schema vazio"
        assert schema.get("type") == "object", f"[P1-6] {name}: schema.type deve ser 'object'"
        assert "properties" in schema, f"[P1-6] {name}: schema sem 'properties'"
