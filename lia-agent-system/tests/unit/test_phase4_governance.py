"""TDD red-phase — Sprint B Phase 4 governance gates.

Three concerns:

C2 — set_feature_flag must call AuditService.log_action so toggling
     learning_loops (and any other feature flag) leaves an LGPD Art. 20
     trail (decisão automatizada, direito de revisão).

C3 — _hook_conclusion_hired must push a BiasAuditSnapshot per hire so
     EU AI Act trail is push-driven instead of relying on the admin pull
     endpoint. Fail-soft: dispatch never blocks if bias audit fails.

C6 — context_aggregator_service._get_company_context multi-tenancy hole
     was already closed in Sprint 9. Sentinel test inspects the source
     to prevent regression.

Harness taxonomy: computational sensors. Error messages point to the
exact file + canonical fix when violated.
"""
from __future__ import annotations

import asyncio
import inspect
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ── C2 — Audit log on feature flag toggle ───────────────────────────────────


def _make_flag_request(flag_key: str = "learning_loops.bigfive_department_history",
                       is_enabled: bool = True,
                       company_id: str | None = "co-1"):
    from app.api.v1.lia_assistant_flags import FeatureFlagRequest
    return FeatureFlagRequest(
        flag_key=flag_key,
        is_enabled=is_enabled,
        company_id=company_id,
        rollout_percentage=100,
        category="learning_loops",
        created_by="user-42",
    )


def _make_user(user_id: str = "user-42", company_id: str = "co-1"):
    user = MagicMock()
    user.id = user_id
    user.company_id = company_id
    user.email = "rec@example.com"
    return user


def test_set_feature_flag_logs_audit_action_on_success():
    """C2: set_feature_flag must call AuditService.log_action with the
    flag change details. Without this, toggling sensitive flags like
    learning_loops.bigfive_department_history leaves no LGPD Art. 20
    trail."""
    from app.api.v1.lia_assistant_flags import set_feature_flag

    audit_log_mock = AsyncMock()
    ff_svc = MagicMock()
    ff_svc.set_flag = AsyncMock(return_value={
        "success": True,
        "flag_id": "ff-1",
        "flag_key": "learning_loops.bigfive_department_history",
        "is_enabled": True,
        "company_id": "co-1",
        "rollout_percentage": 100,
    })

    async def _run():
        with patch(
            "app.shared.compliance.audit_service.AuditService.log_action",
            new=audit_log_mock,
        ):
            await set_feature_flag(
                request=_make_flag_request(),
                db=AsyncMock(),
                current_user=_make_user(),
                ff_svc=ff_svc,
            )

    asyncio.run(_run())

    assert audit_log_mock.called, (
        "AuditService.log_action was not called by set_feature_flag. "
        "Wire it after a successful ff_svc.set_flag — required for "
        "LGPD Art. 20 (direito de revisão) trail on flag toggles."
    )


def test_set_feature_flag_logs_audit_with_actor_and_target():
    """C2: audit log payload must include actor (user_id) and target
    (flag_key) so the trail is queryable per actor and per flag."""
    from app.api.v1.lia_assistant_flags import set_feature_flag

    audit_log_mock = AsyncMock()
    ff_svc = MagicMock()
    ff_svc.set_flag = AsyncMock(return_value={
        "success": True,
        "flag_id": "ff-1",
        "flag_key": "learning_loops.bigfive_department_history",
        "is_enabled": True,
        "company_id": "co-1",
    })

    async def _run():
        with patch(
            "app.shared.compliance.audit_service.AuditService.log_action",
            new=audit_log_mock,
        ):
            await set_feature_flag(
                request=_make_flag_request(),
                db=AsyncMock(),
                current_user=_make_user(user_id="user-42"),
                ff_svc=ff_svc,
            )

    asyncio.run(_run())

    assert audit_log_mock.called
    kwargs = audit_log_mock.call_args.kwargs
    actor_str = str(kwargs.get("actor", ""))
    assert "user-42" in actor_str, (
        f"audit log_action actor={actor_str!r} doesn't contain "
        f"current_user.id. Pass actor=current_user.id (or wrapper)."
    )
    assert kwargs.get("action_type") == "feature_flag_change", (
        f"audit log_action action_type={kwargs.get('action_type')!r}, "
        f"expected 'feature_flag_change'."
    )
    target = str(kwargs.get("target_id", ""))
    assert "learning_loops" in target or "bigfive_department_history" in target, (
        f"audit log_action target_id={target!r} should reference "
        f"the flag_key being toggled."
    )


def test_set_feature_flag_audit_failure_does_not_break_endpoint():
    """C2 fail-soft: if AuditService.log_action raises, set_feature_flag
    must still return successfully — the user got the toggle they asked
    for, even if the trail is missing."""
    from app.api.v1.lia_assistant_flags import set_feature_flag

    ff_svc = MagicMock()
    ff_svc.set_flag = AsyncMock(return_value={
        "success": True,
        "flag_id": "ff-1",
        "flag_key": "x",
        "is_enabled": True,
        "company_id": "co-1",
    })

    async def _run():
        with patch(
            "app.shared.compliance.audit_service.AuditService.log_action",
            new=AsyncMock(side_effect=RuntimeError("audit DB down")),
        ):
            return await set_feature_flag(
                request=_make_flag_request(),
                db=AsyncMock(),
                current_user=_make_user(),
                ff_svc=ff_svc,
            )

    response = asyncio.run(_run())
    assert response.success is True, (
        "set_feature_flag returned success=False when AuditService failed. "
        "Wrap log_action in try/except — the toggle succeeded, audit is "
        "best-effort (matches AuditService.log_action's own internal "
        "fail-soft pattern)."
    )


# ── C3 — Bias snapshot push on hire ─────────────────────────────────────────


def test_hook_conclusion_hired_pushes_bias_snapshot():
    """C3: after a candidate is hired, _hook_conclusion_hired must push a
    BiasAuditSnapshot for the job. Without this, the EU AI Act trail
    only exists if an admin manually pulls /admin_bias_audit endpoint."""
    import inspect
    from app.domains.communication.services import transition_dispatch_service

    source = inspect.getsource(
        transition_dispatch_service.TransitionDispatchService._hook_conclusion_hired
    )

    # Must reference bias snapshot creation explicitly
    has_snapshot_call = (
        "save_snapshot" in source
        or "BiasAuditService" in source
        or "bias_snapshot" in source.lower()
    )
    assert has_snapshot_call, (
        "_hook_conclusion_hired does not call BiasAuditService.save_snapshot. "
        "Add a fail-soft snapshot push after mark_filled — generates audit "
        "trail aligned with EU AI Act requirements without requiring admin "
        "pull. Use BiasAuditService.get_adverse_impact_by_job() to build "
        "the report, then save_snapshot()."
    )


def test_bias_snapshot_helper_exists_and_is_fail_soft():
    """C3: the snapshot push must be wrapped so a bias-audit failure
    doesn't break the hire-conclusion dispatch."""
    import inspect
    from app.domains.communication.services import transition_dispatch_service

    source = inspect.getsource(transition_dispatch_service)
    # Heuristic: snapshot push appears AND there's at least one try/except
    # nearby labeled as bias-related fail-soft.
    if "save_snapshot" not in source and "BiasAuditService" not in source:
        pytest.fail("snapshot helper not wired yet — see test above")

    # Find _push_bias_snapshot helper or inline try-block
    has_fail_soft_pattern = (
        "_push_bias_snapshot" in source
        or "bias snapshot failed" in source.lower()
        or "[ConclusionHired] bias" in source
    )
    assert has_fail_soft_pattern, (
        "Bias snapshot push exists but lacks an explicit fail-soft helper "
        "or try/except pattern marker. Add a helper "
        "_push_bias_snapshot(company_id, job_id) that wraps the call in "
        "try/except logging.warning, similar to the existing audit log "
        "fail-soft block."
    )


# ── C6 — context_aggregator multi-tenancy regression sentinel ───────────────


def test_context_aggregator_filters_by_company_id_in_company_context():
    """C6 (already-fixed Sprint 9 — sentinel guard): _get_company_context
    must scope CompanyProfile lookup by id == company_id, not by global
    is_active. Earlier code returned ANY active profile globally,
    propagating wrong-tenant data downstream.

    If this fails: someone reverted the multi-tenancy fix. Restore
    `.where(CompanyProfile.id == company_id)` as the FIRST filter.
    """
    from app.domains.ai.services.context_aggregator_service import (
        ContextAggregatorService,
    )

    source = inspect.getsource(ContextAggregatorService._get_company_context)
    assert "CompanyProfile.id == company_id" in source, (
        "_get_company_context no longer scopes the company query by id == "
        "company_id. Multi-tenancy regression: pre-Sprint-9 the lookup "
        "filtered only by is_active, returning ANY active profile globally. "
        "Re-add `.where(CompanyProfile.id == company_id)` as the first "
        "filter in the SELECT."
    )


def test_context_aggregator_lookup_does_not_have_global_is_active_fallback():
    """C6: same source must NOT contain a fallback path that drops the
    company_id filter. If we ever add a 'no profile found, use any active'
    branch, multi-tenancy breaks again.
    """
    from app.domains.ai.services.context_aggregator_service import (
        ContextAggregatorService,
    )

    source = inspect.getsource(ContextAggregatorService._get_company_context)
    # Negative: the order must be id-first then is_active. No standalone
    # `where(is_active).limit(1)` without an id filter on the same select.
    forbidden_patterns = [
        # The pre-Sprint-9 buggy form (no company_id):
        "select(CompanyProfile)\n            .where(CompanyProfile.is_active)\n            .limit(1)",
    ]
    for pattern in forbidden_patterns:
        assert pattern not in source, (
            f"Detected pre-Sprint-9 multi-tenancy regression pattern in "
            f"_get_company_context. The select(CompanyProfile) must scope "
            f"by company_id BEFORE is_active filter."
        )
