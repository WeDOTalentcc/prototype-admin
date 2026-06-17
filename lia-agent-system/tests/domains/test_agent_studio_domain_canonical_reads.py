"""Sprint 7B-3a Part 2 Layer 1 — domain.py canonical reads tests."""
from __future__ import annotations

import pathlib

DOMAIN_PATH = (
    pathlib.Path(__file__).resolve().parents[2]
    / "app"
    / "domains"
    / "agent_studio"
    / "domain.py"
)


def _src() -> str:
    return DOMAIN_PATH.read_text()


def test_handle_get_agent_status_queries_custom_agent():
    """Test 6: _handle_get_agent_status (L~228) deve usar CustomAgent."""
    src = _src()
    # Legacy pattern: select(SourcingAgent).where(SourcingAgent.id == agent_id, SourcingAgent.company_id ...)
    assert "select(SourcingAgent).where(\n                        SourcingAgent.id == agent_id," not in src, (
        "_handle_get_agent_status ainda usa select(SourcingAgent) legacy"
    )
    # Should now reference CustomAgent + category='sourcing'
    src_get_status = src.split("_handle_get_agent_status")[1].split("async def ")[0]
    assert "CustomAgent" in src_get_status, (
        "_handle_get_agent_status não importa/usa CustomAgent"
    )
    assert "category" in src_get_status and "sourcing" in src_get_status, (
        "_handle_get_agent_status sem filter category='sourcing'"
    )


def test_handle_deactivate_agent_queries_custom_agent_for_sourcing_branch():
    """Test 7: _handle_deactivate_agent sourcing branch (L~845) usa CustomAgent."""
    src = _src()
    # Sourcing branch was: select(SourcingAgent).where(SourcingAgent.id == agent_id, ...)
    sourcing_branch = src.split("_handle_deactivate_agent")[1].split("async def ")[0]
    # The else branch (sourcing) must now use CustomAgent
    assert "from lia_models.sourcing_agent import SourcingAgent" not in sourcing_branch, (
        "_handle_deactivate_agent sourcing branch ainda importa SourcingAgent legacy"
    )
    # Should have second CustomAgent ref (the first is custom_agent branch already)
    custom_agent_refs = sourcing_branch.count("CustomAgent")
    assert custom_agent_refs >= 2, (
        f"_handle_deactivate_agent sourcing branch precisa de ref a CustomAgent "
        f"(além da já existente em custom_agent branch); encontrado {custom_agent_refs}"
    )
