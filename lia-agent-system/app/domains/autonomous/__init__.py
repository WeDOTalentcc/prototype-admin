"""Autonomous cross-domain agent (Tier 6 of CascadedRouter).

This domain intentionally has NO domain.py — by architectural design.

Why: autonomous is the cross-domain fallback. It is invoked by
CascadedRouter Tier 6 ONLY when no other domain resolved. Its "execution"
is to call domain agents via tools, so compliance flows through those
domain agents (each of which extends ComplianceDomainPrompt).

Compliance applied to autonomous requests (via infrastructure, not ComplianceDomainPrompt):

| Layer | Source | Applied |
|-------|--------|---------|
| Rate Limit | app/middleware/rate_limiter.py | Per-tenant + per-user |
| Prompt Injection | app/middleware/auth_enforcement.py:154 | Global on agent paths |
| PII Auto-Strip | libs/agents-core/lia_agents_core/langgraph_react_base.py | Per-message sanitization |
| FairnessGuard L1+L2 | libs/agents-core/lia_agents_core/enhanced_agent_mixin.py | Pre-check before ReAct loop |
| AuditCallback | libs/agents-core/lia_agents_core/langgraph_react_base.py:152 | Automatic on every invocation |
| Tenant isolation | agent_chat_ws.py injects _CURRENT_COMPANY_ID | IDOR prevention in tools |

Layer 3 (semantic bias) + FactChecker are NOT applied at the autonomous level — they
apply to the domain agents that autonomous calls (e.g., sourcing, pipeline, cv_screening).

Registry status: NOT registered in DomainRegistry (see DOMAIN_CATALOG.md).
"""

__domain_type__ = "deprecated"
