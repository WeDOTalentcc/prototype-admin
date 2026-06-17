"""
TDD — Red/Green: OfferConciergeAgent deve herdar TenantAwareAgentMixin.

Alinha OfferConciergeAgent com o pattern canonical dos demais agentes da
plataforma:
  SourcingReActAgent(TenantAwareAgentMixin, LangGraphReActBase, EnhancedAgentMixin)
  WizardReActAgent(TenantAwareAgentMixin, LangGraphReActBase, EnhancedAgentMixin)
  PipelineReActAgent(TenantAwareAgentMixin, LangGraphReActBase, EnhancedAgentMixin)
  ...
"""
from __future__ import annotations


def test_offer_concierge_inherits_tenant_aware_mixin():
    """OfferConciergeAgent deve herdar TenantAwareAgentMixin para multi-tenancy."""
    from app.domains.offer.agents.offer_concierge_agent import OfferConciergeAgent
    from app.shared.agents.tenant_aware_agent import TenantAwareAgentMixin

    assert issubclass(OfferConciergeAgent, TenantAwareAgentMixin), (
        "OfferConciergeAgent deve herdar TenantAwareAgentMixin (canonical pattern). "
        "MRO: (TenantAwareAgentMixin, LangGraphReActBase, EnhancedAgentMixin)"
    )


def test_offer_concierge_mro_order():
    """TenantAwareAgentMixin deve vir PRIMEIRO no MRO (antes de LangGraphReActBase)."""
    from app.domains.offer.agents.offer_concierge_agent import OfferConciergeAgent
    from app.shared.agents.tenant_aware_agent import TenantAwareAgentMixin
    from lia_agents_core.langgraph_react_base import LangGraphReActBase

    mro = OfferConciergeAgent.__mro__
    mixin_idx = next(
        (i for i, cls in enumerate(mro) if cls is TenantAwareAgentMixin), None
    )
    base_idx = next(
        (i for i, cls in enumerate(mro) if cls is LangGraphReActBase), None
    )

    assert mixin_idx is not None, "TenantAwareAgentMixin não encontrado no MRO"
    assert base_idx is not None, "LangGraphReActBase não encontrado no MRO"
    assert mixin_idx < base_idx, (
        f"TenantAwareAgentMixin (pos={mixin_idx}) deve vir ANTES de "
        f"LangGraphReActBase (pos={base_idx}) no MRO"
    )
