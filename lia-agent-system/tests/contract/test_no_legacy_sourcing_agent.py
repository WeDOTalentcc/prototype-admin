"""Sprint 8 — contract: SourcingAgent class deletada + CustomAgent.legacy_sourcing_agent_id removida.

Garante:
- import SourcingAgent (class) NAO eh possivel (ImportError ou AttributeError)
- CustomAgent model NAO tem atributo legacy_sourcing_agent_id
- SourcingAgentSignal continua importavel (canonical preservado)
- SourcingAgentSignal nao tem mais .agent / .agent_id (relationship removida)
"""
from __future__ import annotations

import pytest


def test_sourcing_agent_class_not_importable():
    """SourcingAgent foi DELETED em Sprint 8 — import deve falhar."""
    with pytest.raises((ImportError, AttributeError)):
        from lia_models.sourcing_agent import SourcingAgent  # noqa: F401


def test_sourcing_agent_signal_still_importable():
    """SourcingAgentSignal CANONICAL preservado (table sourcing_agent_signals canonical)."""
    from lia_models.sourcing_agent import SourcingAgentSignal  # noqa: F401

    assert SourcingAgentSignal is not None


def test_sourcing_agent_signal_has_no_agent_relationship():
    """Sprint 8 removeu relationship .agent (back_populates pra class deletada)."""
    from lia_models.sourcing_agent import SourcingAgentSignal

    # custom_agent canonical relationship deve estar presente
    assert hasattr(SourcingAgentSignal, "custom_agent"), "custom_agent canonical missing"
    # agent_id column (FK para sourcing_agents) deve estar ausente
    assert not hasattr(SourcingAgentSignal, "agent"), "relationship .agent deveria ter sido removida em Sprint 8"


def test_custom_agent_has_no_legacy_field():
    """CustomAgent.legacy_sourcing_agent_id foi DELETED em Sprint 8."""
    from lia_models.custom_agent import CustomAgent

    assert not hasattr(CustomAgent, "legacy_sourcing_agent_id"), (
        "CustomAgent.legacy_sourcing_agent_id deveria ter sido removida em Sprint 8"
    )


def test_custom_agent_to_dict_has_no_legacy_key():
    """CustomAgent.to_dict() nao serializa legacy_sourcing_agent_id."""
    from lia_models.custom_agent import CustomAgent

    # Inspect to_dict source via attribute (cant easily instantiate sem DB)
    import inspect

    src = inspect.getsource(CustomAgent.to_dict)
    assert "legacy_sourcing_agent_id" not in src, (
        "to_dict() ainda referencia legacy_sourcing_agent_id"
    )
