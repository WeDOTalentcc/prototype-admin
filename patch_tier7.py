#!/usr/bin/env python3
"""
P2.4: CascadedRouter Tier 7 — Studio Agent Matcher

Inserts between Tier 6 (AutonomousReAct) and Fallback (clarification).
When context has a job_id or talent_pool_id, checks for active Studio
agent deployments. If found, executes the agent and returns result.

Safety: confidence 0.7, max_steps enforced, fallback on error.
"""
import os

BASE = "/home/runner/workspace/lia-agent-system"
path = os.path.join(BASE, "app/orchestrator/cascaded_router.py")

with open(path) as f:
    content = f.read()

# 1. Update docstring to mention Tier 7
old_doc = '"""\nCascaded Router - 7-tier routing: memory → redis → vector → fast → LLM → autonomous → clarification.'
new_doc = '"""\nCascaded Router - 8-tier routing: memory → redis → vector → fast → LLM → autonomous → studio → clarification.'

if old_doc in content:
    content = content.replace(old_doc, new_doc, 1)
    print("OK: docstring updated to 8-tier")
else:
    print("SKIP: docstring")

# 2. Add studio_hits to stats
old_stats = '"autonomous_hits": 0,\n            "clarification_issued": 0,'
new_stats = '"autonomous_hits": 0,\n            "studio_agent_hits": 0,\n            "clarification_issued": 0,'

if old_stats in content:
    content = content.replace(old_stats, new_stats, 1)
    print("OK: stats updated")
else:
    print("SKIP: stats")

# 3. Insert Tier 7 between Tier 6 and Fallback
old_fallback = """        # Fallback final — clarification_needed (Gap #2)
        async with _tracer.start_span("router.fallback_clarification", attributes={
            "tier_name": "fallback_clarification", "service": "cascaded_router", "match_type": "clarification",
        }) as _fb_span:"""

new_tier7_plus_fallback = """        # Tier 7 — Studio Agent Matcher (custom agents bound to current context)
        _ctx = context or {}
        _ctx_job_id = _ctx.get("job_id") or _ctx.get("vacancy_id")
        _ctx_pool_id = _ctx.get("talent_pool_id")
        _ctx_company_id = _ctx.get("company_id")

        if (_ctx_job_id or _ctx_pool_id) and _ctx_company_id:
            async with _tracer.start_span("router.tier7_studio_agent", attributes={
                "tier_name": "tier7_studio_agent", "service": "cascaded_router",
                "match_type": "studio_deployment",
            }) as _t7_span:
                try:
                    _t0 = time.perf_counter()
                    from app.services.agent_deployment_service import agent_deployment_service
                    from lia_config.database import AsyncSessionLocal

                    _studio_deployments = []
                    async with AsyncSessionLocal() as _studio_db:
                        if _ctx_job_id:
                            _studio_deployments = await agent_deployment_service.find_active_deployments_for_trigger(
                                db=_studio_db,
                                company_id=_ctx_company_id,
                                target_type="job",
                                target_id=_ctx_job_id,
                                trigger_mode="manual",
                            )
                        if not _studio_deployments and _ctx_pool_id:
                            _studio_deployments = await agent_deployment_service.find_active_deployments_for_trigger(
                                db=_studio_db,
                                company_id=_ctx_company_id,
                                target_type="talent_pool",
                                target_id=_ctx_pool_id,
                                trigger_mode="manual",
                            )

                        if _studio_deployments:
                            _dep = _studio_deployments[0]
                            from sqlalchemy import select
                            from lia_models.custom_agent import CustomAgent
                            _agent_result = await _studio_db.execute(
                                select(CustomAgent).where(CustomAgent.id == _dep.agent_id)
                            )
                            _studio_agent = _agent_result.scalar_one_or_none()

                            if _studio_agent and _studio_agent.status == "active":
                                from app.domains.agent_studio.custom_agent_runtime import get_or_create_runtime

                                _runtime = get_or_create_runtime(
                                    agent_id=str(_studio_agent.id),
                                    agent_name=_studio_agent.name,
                                    system_prompt=_studio_agent.system_prompt,
                                    allowed_tools=_studio_agent.allowed_tools or [],
                                    domain=_studio_agent.domain or "general",
                                    max_steps=_studio_agent.max_steps or 8,
                                    temperature=_studio_agent.temperature or 0.7,
                                    model_override=_studio_agent.model_override,
                                    company_id=_ctx_company_id,
                                    enable_memory=getattr(_studio_agent, "enable_memory", True),
                                    excluded_tools=getattr(_studio_agent, "excluded_tools", None),
                                    context_level=getattr(_studio_agent, "context_level", "full"),
                                )

                                _output = await _runtime.execute(
                                    message=message,
                                    user_id=_ctx.get("user_id", ""),
                                    company_id=_ctx_company_id,
                                    session_id=session_id or "",
                                    context=_ctx,
                                )

                                _elapsed_ms = (time.perf_counter() - _t0) * 1000
                                self._stats["studio_agent_hits"] += 1

                                # Record deployment execution
                                await agent_deployment_service.record_execution(
                                    _studio_db, str(_dep.id)
                                )
                                await _studio_db.commit()

                                _t7_span.set_attribute("hit", "true")
                                _t7_span.set_attribute("confidence_score", "0.70")
                                _t7_span.set_attribute("domain_id", f"custom:{_studio_agent.name}")
                                _t7_span.set_attribute("agent_id", str(_studio_agent.id))
                                _t7_span.set_attribute("latency_ms", f"{_elapsed_ms:.2f}")

                                logger.info(
                                    "CascadedRouter: Tier 7 (studio) resolved '%s...' via agent=%s in %.0fms",
                                    message[:40], _studio_agent.name, _elapsed_ms,
                                )

                                _studio_result = RouteResult(
                                    domain_id=f"custom:{_studio_agent.name}",
                                    confidence=0.70,
                                    source="studio_agent",
                                    intent_details={
                                        "agent_id": str(_studio_agent.id),
                                        "agent_name": _studio_agent.name,
                                        "deployment_id": str(_dep.id),
                                        "response": _output.message,
                                    },
                                )
                                return _studio_result

                    _t7_span.set_attribute("hit", "false")
                    _t7_span.set_attribute("confidence_score", "0.0")
                    _t7_span.set_attribute("latency_ms", f"{(time.perf_counter() - _t0) * 1000:.2f}")
                except Exception as _studio_exc:
                    _t7_span.set_attribute("hit", "false")
                    _t7_span.set_attribute("error_detail", str(_studio_exc))
                    logger.warning("CascadedRouter: Tier 7 (studio) failed: %s", _studio_exc)

        # Fallback final — clarification_needed (Gap #2)
        async with _tracer.start_span("router.fallback_clarification", attributes={
            "tier_name": "fallback_clarification", "service": "cascaded_router", "match_type": "clarification",
        }) as _fb_span:"""

if old_fallback in content:
    content = content.replace(old_fallback, new_tier7_plus_fallback, 1)
    print("OK: Tier 7 inserted")
else:
    print("ERROR: Fallback pattern not found!")

with open(path, "w") as f:
    f.write(content)

# Verify syntax
import ast
try:
    ast.parse(content)
    print("OK: syntax valid")
except SyntaxError as e:
    print(f"ERROR: {e}")

print("\nTier 7 implementation complete!")
