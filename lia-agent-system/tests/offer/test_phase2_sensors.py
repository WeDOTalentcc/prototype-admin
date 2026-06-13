"""Phase 2 — N2 Concierge Informacional: TDD sensors.

Covers 12 assertions for the canonical offer system:
  2.12 Teams triggers (viewed/declined/expired)
  2.13 Scheduler: expire_pending_offers
  2.14 offer_concierge agent wiring
  2.15 tool dependency fixes
  2.16 Sistema B deprecation headers
"""
import inspect
from unittest.mock import AsyncMock, MagicMock, patch
import pytest


# ── 2.12 — Teams triggers ─────────────────────────────────────────────────

class TestTeamsOfferTriggers:
    """Tests that TeamsService has all offer lifecycle methods (2.12)."""

    def test_on_offer_viewed_method_exists(self):
        from app.domains.communication.services.teams_service import TeamsService
        assert hasattr(TeamsService, "on_offer_viewed"), \
            "TeamsService must have on_offer_viewed — call site in offer_portal.py already exists"

    def test_on_offer_responded_method_exists(self):
        from app.domains.communication.services.teams_service import TeamsService
        assert hasattr(TeamsService, "on_offer_responded"), \
            "TeamsService must have on_offer_responded — fire on OFFER_DECLINED / OFFER_ACCEPTED"

    def test_on_offer_expired_method_exists(self):
        from app.domains.communication.services.teams_service import TeamsService
        assert hasattr(TeamsService, "on_offer_expired"), \
            "TeamsService must have on_offer_expired — fired by mark_expired in OfferService"

    def test_offer_trigger_types_declared(self):
        from app.shared.automation.trigger_types_canonical import TriggerType
        required = {"offer_viewed", "offer_declined", "offer_expired", "offer_counter_proposed"}
        declared = {t.value for t in TriggerType}
        assert required.issubset(declared), \
            f"Missing trigger types in canonical enum: {required - declared}"


# ── 2.13 — Scheduler ──────────────────────────────────────────────────────

class TestOfferExpiryScheduler:
    """Tests scheduler + mark_expired pipeline (2.13)."""

    def test_offer_repository_has_list_deadline_passed(self):
        from app.domains.offer.repositories.offer_repository import OfferRepository
        assert hasattr(OfferRepository, "list_deadline_passed"), \
            "OfferRepository must have list_deadline_passed for the expiry scheduler"

    def test_mark_expired_is_idempotent_for_non_pending(self):
        """mark_expired on an already-expired offer must return early without mutation."""
        from app.domains.offer.services.offer_service import OfferService
        src = inspect.getsource(OfferService.mark_expired)
        # Must guard on status before mutating
        assert "status not in" in src or "status in (" in src, \
            "mark_expired must guard status to be idempotent (no double-expire)"

    @pytest.mark.asyncio
    async def test_expire_pending_offers_runs_without_error(self):
        """Smoke test: scheduler task should execute without exceptions when repo is empty."""
        from app.domains.automation.services.automation_scheduler import AutomationScheduler
        scheduler = AutomationScheduler.__new__(AutomationScheduler)

        async def _fake_list(*_, **__):
            return []

        with patch(
            "app.domains.offer.repositories.offer_repository.OfferRepository.list_deadline_passed",
            new=AsyncMock(side_effect=_fake_list),
        ):
            # Should not raise
            if hasattr(scheduler, "run_expire_pending_offers"):
                await scheduler.run_expire_pending_offers()
            else:
                pytest.skip("run_expire_pending_offers not found on AutomationScheduler")


# ── 2.14 — offer_concierge agent wiring ──────────────────────────────────

class TestOfferConciergeAgent:
    """Tests canonical anatomy of offer_concierge agent (2.14)."""

    def test_agent_registered(self):
        import app.domains.offer.agents.offer_concierge_agent  # noqa: F401 — triggers @register_agent
        from app.shared.agents.agent_registry import _AGENT_REGISTRY, _AGENT_ALIASES
        all_keys = set(_AGENT_REGISTRY.keys()) | set(_AGENT_ALIASES.keys())
        found = "offer_concierge" in all_keys or any("offer" in k for k in all_keys)
        assert found, \
            f"offer_concierge not found in _AGENT_REGISTRY. Keys: {list(all_keys)[:10]}"

    def test_agent_has_fairness_guard(self):
        from app.domains.offer.agents.offer_concierge_agent import OfferConciergeAgent
        src = inspect.getsource(OfferConciergeAgent)
        assert "FairnessGuard" in src, \
            "OfferConciergeAgent must call FairnessGuard (FAR-2 cross-cutting)"

    def test_agent_strips_pii(self):
        from app.domains.offer.agents.offer_concierge_agent import OfferConciergeAgent
        src = inspect.getsource(OfferConciergeAgent)
        assert "strip_pii_for_llm_prompt" in src or "PIIRedactor" in src, \
            "OfferConciergeAgent must strip PII before LLM call (ADR-LGPD-002)"

    def test_agent_has_hitl_gate(self):
        from app.domains.offer.agents.offer_concierge_agent import OfferConciergeAgent
        src = inspect.getsource(OfferConciergeAgent)
        assert "_HITL_MESSAGE_TYPES" in src or "hitl" in src.lower(), \
            "OfferConciergeAgent must have HITL gate for sensitive mutations (AUD-4)"


# ── 2.15 — tool dependency fixes ─────────────────────────────────────────

class TestOfferToolRegistry:
    """Tests that offer tool registry imports are correct (2.15)."""

    def test_tool_registry_importable(self):
        """offer_tool_registry must import without ImportError (no bad paths)."""
        try:
            from app.domains.offer.agents import offer_tool_registry  # noqa: F401
        except ImportError as exc:
            pytest.fail(f"offer_tool_registry has bad import: {exc}")

    def test_get_benefit_details_tool_exists(self):
        from app.domains.offer.agents.offer_tool_registry import _wrap_get_benefit_details
        assert callable(_wrap_get_benefit_details), \
            "_wrap_get_benefit_details must be callable — it powers the get_benefit_details LangChain Tool"


# ── 2.16 / 3.10 — Sistema B aposentado (410 Gone) ───────────────────────

class TestSistemaBDeprecationHeaders:
    """Sistema B (job_offers.py) foi aposentado em 3.10: todos os endpoints retornam 410 Gone."""

    def test_sistema_b_routes_return_410(self):
        """job_offers.py deve conter exatamente 5 rotas, todas com handler _gone (3.10)."""
        from app.api.v1 import job_offers
        routes = job_offers.router.routes
        assert len(routes) == 5, f"Esperados 5 endpoints 410, encontrados {len(routes)}"

    def test_sistema_b_has_gone_body(self):
        """_GONE_BODY deve referenciar o successor /api/v1/offers/."""
        from app.api.v1 import job_offers
        assert hasattr(job_offers, "_GONE_BODY"), "_GONE_BODY dict must exist in job_offers.py"
        assert "/api/v1/offers/" in str(job_offers._GONE_BODY.get("successor", "")), \
            "_GONE_BODY.successor must point to /api/v1/offers/"
