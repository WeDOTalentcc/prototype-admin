"""
T4 (#991) — Tenant Demo Fallback regression suite.

Canonical no-regression tests for ``app.shared.security.tenant_demo_fallback``
+ the two refactored endpoints in ``app.api.v1.company``:

- ``GET  /company/profile``     (was: silently returned Demo profile)
- ``POST /company/onboarding``  (was: silently overwrote Demo profile)

These tests are the moral siblings of
``tests/integration/agents/test_tenant_context_no_regression.py`` (T-E):
they encode the bug-class invariant so a future refactor that
re-introduces the silent fallback breaks the build instead of breaking
prod.

Coverage matrix:
1. POSITIVE   — Demo user reading own Demo profile still works.
2. ANTI-LEAK  — real-tenant user without profile gets 404, NOT Demo.
3. ANTI-LEAK  — real-tenant onboarding never overwrites Demo profile.
4. TELEMETRY  — Prometheus counter + in-memory snapshot increment on drift.
5. SENTINEL   — source-grep guard against re-introducing
   ``profile_repo.get_default()`` inside ``get_company_profile``.
"""
from __future__ import annotations

import re
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.shared.security import tenant_demo_fallback as tdf


# ─── Unit: helper module ──────────────────────────────────────────────
class TestDemoFallbackHelper:
    def setup_method(self) -> None:
        tdf.reset_demo_fallback_snapshot()

    @pytest.mark.parametrize(
        "value,expected",
        [
            (tdf.DEMO_COMPANY_UUID, True),
            (tdf.DEMO_COMPANY_SLUG, True),
            ("DEMO_COMPANY", True),  # case-insensitive
            ("acme-corp", False),
            ("00000000-0000-4000-a000-000000000002", False),
            ("", False),
            (None, False),
        ],
    )
    def test_is_demo_caller(self, value, expected) -> None:
        assert tdf.is_demo_caller(value) is expected

    def test_record_demo_fallback_increments_snapshot(self) -> None:
        tdf.record_demo_fallback(
            endpoint="get_company_profile",
            reason="missing_profile_for_real_tenant",
            user_company_id="acme-corp",
        )
        snap = tdf.get_demo_fallback_snapshot()
        assert snap == {"get_company_profile:missing_profile_for_real_tenant": 1}

    def test_last_24h_count_tracks_events(self) -> None:
        assert tdf.get_last_24h_count() == 0
        tdf.record_demo_fallback(
            endpoint="get_company_profile",
            reason="missing_profile_for_real_tenant",
        )
        tdf.record_demo_fallback(
            endpoint="submit_onboarding",
            reason="cross_tenant_company_profile_write_attempt",
        )
        assert tdf.get_last_24h_count() == 2

    def test_record_demo_fallback_increments_prometheus(self) -> None:
        if tdf._FALLBACK_COUNTER is None:
            pytest.skip("prometheus_client not installed in this env")
        before = tdf._FALLBACK_COUNTER.labels(
            reason="missing_profile_for_real_tenant",
            endpoint="get_company_profile",
        )._value.get()
        tdf.record_demo_fallback(
            endpoint="get_company_profile",
            reason="missing_profile_for_real_tenant",
            user_company_id="acme-corp",
        )
        after = tdf._FALLBACK_COUNTER.labels(
            reason="missing_profile_for_real_tenant",
            endpoint="get_company_profile",
        )._value.get()
        assert after == before + 1


# ─── Endpoint logic: get_company_profile ──────────────────────────────
class TestGetCompanyProfileNoFallback:
    """Exercise the route function directly with mocked deps —
    avoids spinning up FastAPI/httpx for a logic-only assertion."""

    def setup_method(self) -> None:
        tdf.reset_demo_fallback_snapshot()

    @pytest.mark.asyncio
    async def test_real_tenant_without_profile_gets_404_not_demo(self) -> None:
        from fastapi import HTTPException

        from app.api.v1.company import get_company_profile

        repo = MagicMock()
        repo.get_by_client_account = AsyncMock(return_value=None)
        repo.get_by_id = AsyncMock(return_value=None)
        repo.get_default = AsyncMock(return_value=MagicMock(id="demo", is_default=True))
        user = MagicMock(company_id="acme-corp")

        with pytest.raises(HTTPException) as exc:
            await get_company_profile(
                company_id=None, profile_repo=repo, current_user=user,
            )

        assert exc.value.status_code == 404
        detail = exc.value.detail
        assert isinstance(detail, dict)
        assert detail["code"] == "COMPANY_PROFILE_NOT_FOUND"
        assert "/configuracoes/minha-empresa" in detail["hint_route"]
        # Critical: get_default MUST NOT have been called for a real tenant.
        repo.get_default.assert_not_called()
        # Telemetry recorded.
        snap = tdf.get_demo_fallback_snapshot()
        assert snap.get("get_company_profile:missing_profile_for_real_tenant") == 1

    @pytest.mark.asyncio
    async def test_real_tenant_cannot_read_demo_profile_by_explicit_id(self) -> None:
        """T4 #991 — explicit-ID Demo IDOR: real tenant passing the
        Demo UUID in ``?company_id=`` MUST get 403, not the Demo data.
        Demo profile typically has null ``client_account_id`` so the
        legacy cross-tenant check would otherwise bypass it."""
        from fastapi import HTTPException

        from app.api.v1.company import get_company_profile

        demo_profile = MagicMock(
            id=tdf.DEMO_COMPANY_UUID,
            is_default=True,
            client_account_id=None,
            name="Demo",
        )
        repo = MagicMock()
        repo.get_by_id = AsyncMock(return_value=demo_profile)
        repo.get_by_client_account = AsyncMock(return_value=None)
        repo.get_default = AsyncMock(return_value=demo_profile)
        user = MagicMock(id="u-acme", company_id="acme-corp")

        with pytest.raises(HTTPException) as exc:
            await get_company_profile(
                company_id=tdf.DEMO_COMPANY_UUID,
                profile_repo=repo, current_user=user,
            )

        assert exc.value.status_code == 403
        assert exc.value.detail["code"] == "CROSS_TENANT_DEMO_PROFILE_FORBIDDEN"
        snap = tdf.get_demo_fallback_snapshot()
        assert snap.get(
            "get_company_profile:cross_tenant_demo_profile_read_attempt"
        ) == 1

    @pytest.mark.asyncio
    async def test_demo_user_still_resolves_demo_profile(self) -> None:
        from app.api.v1.company import get_company_profile

        demo_profile = MagicMock(id=tdf.DEMO_COMPANY_UUID, is_default=True)
        repo = MagicMock()
        repo.get_by_client_account = AsyncMock(return_value=None)
        repo.get_by_id = AsyncMock(return_value=None)
        repo.get_default = AsyncMock(return_value=demo_profile)
        user = MagicMock(company_id=tdf.DEMO_COMPANY_SLUG)

        result = await get_company_profile(
            company_id=None, profile_repo=repo, current_user=user,
        )

        assert result is demo_profile
        repo.get_default.assert_awaited_once()


# ─── Endpoint logic: submit_onboarding ────────────────────────────────
class TestSubmitOnboardingNoOverwrite:
    def setup_method(self) -> None:
        tdf.reset_demo_fallback_snapshot()

    @pytest.mark.asyncio
    async def test_real_tenant_does_not_overwrite_demo_profile(self) -> None:
        from app.api.v1.company import submit_onboarding

        # Simulate get_by_client_account returning the Demo profile (the
        # historical bug class — wrong join leaks Demo into a real tenant).
        demo_profile = MagicMock(id=tdf.DEMO_COMPANY_UUID, is_default=True, name="Demo")
        new_profile = MagicMock(
            id="11111111-1111-4111-a111-111111111111",
            name="Acme Corp",
            additional_data={},
        )
        repo = MagicMock()
        repo.get_by_id = AsyncMock(return_value=None)
        repo.get_by_client_account = AsyncMock(return_value=demo_profile)
        repo.get_default = AsyncMock(return_value=demo_profile)
        repo.create = AsyncMock(return_value=new_profile)
        repo.update = AsyncMock(return_value=demo_profile)
        cp_repo = MagicMock()
        user = MagicMock(company_id="acme-corp")

        data = MagicMock(
            company_name="Acme Corp",
            trade_name=None, cnpj=None, address=None, sector=None,
            employee_count=None, website=None, linkedin_url=None,
            logo_url=None, responsible_email=None, responsible_phone=None,
            company_id=None, culture_profile=None,
            hiring_volume=None, job_types=None, current_ats=None,
            main_challenges=None, main_priority=None,
            platform_expectations=None, communication_channels=None,
            allow_lia_contact=None, additional_notes=None,
            responsible_name=None, responsible_position=None,
            preferred_contact_time=None, work_model=None,
        )

        result = await submit_onboarding(
            data=data, profile_repo=repo, cp_repo=cp_repo, current_user=user,
        )

        # Update on Demo profile MUST NOT happen.
        repo.update.assert_not_called()
        # New profile must be created and linked to the real tenant.
        repo.create.assert_awaited_once()
        create_args = repo.create.call_args
        create_data = create_args.args[0] if create_args.args else create_args.kwargs["create_data"]
        assert create_data["is_default"] is False
        assert create_data["client_account_id"] == "acme-corp"
        # Telemetry recorded the prevented Demo overwrite.
        snap = tdf.get_demo_fallback_snapshot()
        assert snap.get("submit_onboarding:non_demo_user_targeting_demo_profile") == 1
        assert result["company_id"] == str(new_profile.id)


    @pytest.mark.asyncio
    async def test_real_tenant_cannot_target_other_tenant_profile_by_id(self) -> None:
        """IDOR guard: user A cannot pass company_id of tenant B's profile
        and have ``submit_onboarding`` overwrite it."""
        from fastapi import HTTPException

        from app.api.v1.company import submit_onboarding

        target_id = "22222222-2222-4222-a222-222222222222"
        foreign_profile = MagicMock(
            id=target_id,
            is_default=False,
            client_account_id="other-tenant",
            name="Other Corp",
            additional_data={},
        )
        repo = MagicMock()
        repo.get_by_id = AsyncMock(return_value=foreign_profile)
        repo.get_by_client_account = AsyncMock(return_value=None)
        repo.get_default = AsyncMock(return_value=None)
        repo.create = AsyncMock()
        repo.update = AsyncMock()
        cp_repo = MagicMock()
        user = MagicMock(company_id="acme-corp")

        data = MagicMock(
            company_name="Acme Corp", trade_name=None, cnpj=None, address=None,
            sector=None, employee_count=None, website=None, linkedin_url=None,
            logo_url=None, responsible_email=None, responsible_phone=None,
            company_id=target_id, culture_profile=None,
            hiring_volume=None, job_types=None, current_ats=None,
            main_challenges=None, main_priority=None,
            platform_expectations=None, communication_channels=None,
            allow_lia_contact=None, additional_notes=None,
            responsible_name=None, responsible_position=None,
            preferred_contact_time=None, work_model=None,
        )

        with pytest.raises(HTTPException) as exc:
            await submit_onboarding(
                data=data, profile_repo=repo, cp_repo=cp_repo, current_user=user,
            )

        # T4 #991 — HTTPException re-raise contract: 403 must surface
        # as 403, NEVER wrapped into 500 by the generic handler.
        assert exc.value.status_code == 403, (
            f"403 was wrapped into {exc.value.status_code} — generic "
            "except Exception block is swallowing structured errors."
        )
        assert exc.value.detail["code"] == "CROSS_TENANT_PROFILE_WRITE_FORBIDDEN"
        repo.update.assert_not_called()
        repo.create.assert_not_called()
        snap = tdf.get_demo_fallback_snapshot()
        assert snap.get(
            "submit_onboarding:cross_tenant_company_profile_write_attempt"
        ) == 1

    @pytest.mark.asyncio
    async def test_real_tenant_explicit_demo_write_returns_403(self) -> None:
        """T4 #991 — explicit Demo write IDOR. Real tenant POSTing
        onboarding with ``data.company_id = DEMO_UUID`` MUST get 403
        (not silently degrade into create-new)."""
        from fastapi import HTTPException

        from app.api.v1.company import submit_onboarding

        demo_profile = MagicMock(
            id=tdf.DEMO_COMPANY_UUID, is_default=True,
            client_account_id=None, name="Demo",
        )
        repo = MagicMock()
        repo.get_by_id = AsyncMock(return_value=demo_profile)
        repo.get_by_client_account = AsyncMock(return_value=None)
        repo.get_default = AsyncMock(return_value=demo_profile)
        repo.create = AsyncMock()
        repo.update = AsyncMock()
        cp_repo = MagicMock()
        user = MagicMock(id="u-acme", company_id="acme-corp")

        data = MagicMock(
            company_name="Acme", trade_name=None, cnpj=None, address=None,
            sector=None, employee_count=None, website=None, linkedin_url=None,
            logo_url=None, responsible_email=None, responsible_phone=None,
            company_id=tdf.DEMO_COMPANY_UUID, culture_profile=None,
            hiring_volume=None, job_types=None, current_ats=None,
            main_challenges=None, main_priority=None,
            platform_expectations=None, communication_channels=None,
            allow_lia_contact=None, additional_notes=None,
            responsible_name=None, responsible_position=None,
            preferred_contact_time=None, work_model=None,
        )

        with pytest.raises(HTTPException) as exc:
            await submit_onboarding(
                data=data, profile_repo=repo, cp_repo=cp_repo, current_user=user,
            )

        assert exc.value.status_code == 403
        assert exc.value.detail["code"] == "CROSS_TENANT_DEMO_PROFILE_FORBIDDEN"
        repo.create.assert_not_called()
        repo.update.assert_not_called()
        snap = tdf.get_demo_fallback_snapshot()
        assert snap.get(
            "submit_onboarding:cross_tenant_demo_profile_write_attempt"
        ) == 1

    @pytest.mark.asyncio
    async def test_demo_caller_uses_demo_fallback_not_create(self) -> None:
        """Demo dev caller (company_id='demo_company') must resolve the
        seeded Demo profile, not attempt to create a new one with the
        slug as ``client_account_id`` (which would fail UUID coercion)."""
        from app.api.v1.company import submit_onboarding

        demo_profile = MagicMock(
            id=tdf.DEMO_COMPANY_UUID, is_default=True, name="Demo",
            additional_data={},
        )
        repo = MagicMock()
        repo.get_by_id = AsyncMock(return_value=None)
        repo.get_by_client_account = AsyncMock(return_value=None)
        repo.get_default = AsyncMock(return_value=demo_profile)
        repo.create = AsyncMock()
        repo.update = AsyncMock(return_value=demo_profile)
        cp_repo = MagicMock()
        user = MagicMock(company_id=tdf.DEMO_COMPANY_SLUG)

        data = MagicMock(
            company_name="Demo", trade_name=None, cnpj=None, address=None,
            sector=None, employee_count=None, website=None, linkedin_url=None,
            logo_url=None, responsible_email=None, responsible_phone=None,
            company_id=None, culture_profile=None,
            hiring_volume=None, job_types=None, current_ats=None,
            main_challenges=None, main_priority=None,
            platform_expectations=None, communication_channels=None,
            allow_lia_contact=None, additional_notes=None,
            responsible_name=None, responsible_position=None,
            preferred_contact_time=None, work_model=None,
        )

        await submit_onboarding(
            data=data, profile_repo=repo, cp_repo=cp_repo, current_user=user,
        )

        repo.get_default.assert_awaited_once()
        repo.create.assert_not_called()
        repo.update.assert_awaited_once()
        snap = tdf.get_demo_fallback_snapshot()
        assert snap.get("submit_onboarding:demo_caller_dev_fallback") == 1


# ─── Source-grep sentinels ─────────────────────────────────────────────
class TestSourceSentinels:
    """Static guards: re-introducing ``get_default()`` in either route
    is a regression. Break the build at import time, not at runtime."""

    COMPANY_PY = Path(__file__).resolve().parents[2] / "app" / "api" / "v1" / "company.py"

    def test_company_py_exists(self) -> None:
        assert self.COMPANY_PY.exists(), self.COMPANY_PY

    def test_get_company_profile_has_no_unguarded_get_default(self) -> None:
        src = self.COMPANY_PY.read_text(encoding="utf-8")
        # Extract the get_company_profile body (until next @router or
        # next top-level def).
        match = re.search(
            r"async def get_company_profile\(.*?\)\s*:\s*\n(.*?)(?=\n@router|\nasync def |\ndef )",
            src, flags=re.DOTALL,
        )
        assert match, "could not locate get_company_profile body"
        body = match.group(1)
        # ``get_default()`` may appear ONLY inside an ``is_demo_caller``
        # guarded branch. Assert that any get_default call is preceded
        # (within 5 lines) by ``is_demo_caller``.
        for m in re.finditer(r"profile_repo\.get_default\(\)", body):
            window_start = max(0, m.start() - 400)
            window = body[window_start:m.start()]
            assert "is_demo_caller" in window, (
                "Regression: profile_repo.get_default() inside "
                "get_company_profile is no longer guarded by "
                "is_demo_caller — silent Demo fallback re-introduced."
            )

    def test_submit_onboarding_create_data_no_is_default_true(self) -> None:
        src = self.COMPANY_PY.read_text(encoding="utf-8")
        match = re.search(
            r"async def submit_onboarding\(.*?\)\s*:\s*\n(.*?)(?=\n@router|\nasync def |\ndef )",
            src, flags=re.DOTALL,
        )
        assert match, "could not locate submit_onboarding body"
        body = match.group(1)
        assert '"is_default": True' not in body, (
            "Regression: submit_onboarding create_data sets "
            '"is_default": True — only the canonical Demo seed is '
            "allowed to own that flag (T-C)."
        )
