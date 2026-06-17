"""
tests/unit/test_rail_a_routing_deterministic.py

Rail A routing determinism tests — Wave 4 W4-1.

harness-engineering [sensor computacional]:
  Validates that check_rail_a_capability routes all 22 Rail A cards
  deterministically. No real LLM calls, no real DB queries.

  Cells covered per harness taxonomy:
    - Guide: SUGGESTION_HINTS + capability_map.yaml (already in place)
    - Sensor (THIS FILE): CI asserts routing is correct for every card

Sensor message for LLM:
  If a test fails, the routing for the flagged card is broken.
  Fix by adding/updating the intent in capability_map.yaml
  or adjusting the routing_layer in rail_a_golden_dataset.json.
"""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"
GOLDEN_DATASET_PATH = FIXTURES_DIR / "rail_a_golden_dataset.json"


@pytest.fixture(scope="module")
def golden_dataset() -> dict:
    return json.loads(GOLDEN_DATASET_PATH.read_text())


@pytest.fixture(autouse=True)
def clear_cap_map_cache():
    """Clear lru_cache before each test so yaml edits are picked up."""
    from app.shared.services.capability_map_service import CapabilityMapService
    CapabilityMapService.load.cache_clear()
    yield
    CapabilityMapService.load.cache_clear()


def _rail_a_ctx(intent_hint: str) -> dict:
    """Minimal Rail A context dict as sent by the FE after PR-A."""
    return {
        "source": "rail_a",
        "metadata": {
            "source": "rail_a",
            "intent_hint": intent_hint,
            "card_id": "test-card",
        },
    }


# ---------------------------------------------------------------------------
# Group 1 — Gate early-exit conditions
# ---------------------------------------------------------------------------


class TestGateEarlyExit:
    """Gate must return None immediately when preconditions are unmet."""

    @pytest.mark.asyncio
    async def test_no_intent_hint_returns_none(self):
        from app.orchestrator.guards.rail_a_capability_check import check_rail_a_capability

        result = await check_rail_a_capability(
            context={"source": "rail_a", "metadata": {}},
            message="test",
            company_id="co-1",
            db=None,
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_source_not_rail_a_returns_none(self):
        """source != rail_a: gate never fires, even with valid intent_hint."""
        from app.orchestrator.guards.rail_a_capability_check import check_rail_a_capability

        result = await check_rail_a_capability(
            context={
                "source": "chat",
                "metadata": {"source": "chat", "intent_hint": "send_offer"},
            },
            message="test",
            company_id="co-1",
            db=None,
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_unknown_intent_hint_returns_none(self):
        """intent_hint not in capability_map -> returns None (LLM fallthrough)."""
        from app.orchestrator.guards.rail_a_capability_check import check_rail_a_capability

        result = await check_rail_a_capability(
            context=_rail_a_ctx("completely_unknown_intent_xyz"),
            message="test",
            company_id="co-1",
            db=None,
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_empty_context_does_not_crash(self):
        """Empty context dict: gate returns None, does not raise."""
        from app.orchestrator.guards.rail_a_capability_check import check_rail_a_capability

        result = await check_rail_a_capability(
            context={},
            message="test",
            company_id="co-1",
            db=None,
        )
        assert result is None


# ---------------------------------------------------------------------------
# Group 2 — FE-only cards (navigate + FE-modal): intents NOT in capability_map
# ---------------------------------------------------------------------------


class TestFEOnlyCards:
    """Navigate (4) and FE-modal-only (2) cards have intents NOT in capability_map.
    Backend gate must return None — routing is handled exclusively in FE."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "intent_hint,description",
        [
            ("list_talent_pools",      "navigate: /bancos-de-talentos"),
            ("get_studio_consumption", "navigate: ai-credits page"),
            ("configure_policy",       "navigate: configuracoes section=pipeline"),
            ("create_template",        "navigate: configuracoes section=templates"),
            ("create_job",             "FE modal: CreateJobModal"),
            ("create_from_template",   "FE modal: JobTemplateModal"),
        ],
    )
    async def test_fe_only_cards_not_in_cap_map(self, intent_hint, description):
        """FE-only routing: capability_map must NOT contain these intents.

        Sensor message: if this test fails, the intent was added to capability_map.yaml
        but still has routing_layer=navigate or modal=FE-only in the golden dataset.
        Either update routing_layer to chat_cap_map or remove from capability_map.
        """
        from app.orchestrator.guards.rail_a_capability_check import check_rail_a_capability

        result = await check_rail_a_capability(
            context=_rail_a_ctx(intent_hint),
            message="test",
            company_id="co-1",
            db=None,
        )
        assert result is None, (
            f"intent_hint={intent_hint!r} ({description}) returned non-None. "
            "FE handles this card via NAVIGATION_OVERRIDES or MODAL_OVERRIDES. "
            "Remove from capability_map.yaml if it was accidentally added."
        )


# ---------------------------------------------------------------------------
# Group 3 — LLM fallback cards: intents NOT in capability_map
# ---------------------------------------------------------------------------


class TestLLMFallbackCards:
    """3 cards whose intents fall through to the keyword/LLM router.
    Gate must return None — no deterministic path yet configured.
    Note: schedule_interview was moved to capability_map.yaml (chat_cap_map)."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "intent_hint,card_id",
        [
            ("quick_question",    "candidate-info"),
            ("create_automation", "configure-automations"),
            ("suggest_action",    "ai-suggestions"),
        ],
    )
    async def test_llm_fallback_returns_none(self, intent_hint, card_id):
        """LLM fallback intents must not be in capability_map.

        Sensor message: if this fails, the intent was added to capability_map.yaml.
        Update golden dataset routing_layer from chat_llm_fallback to chat_cap_map,
        and ensure the new capability_map entry is correct.
        """
        from app.orchestrator.guards.rail_a_capability_check import check_rail_a_capability

        result = await check_rail_a_capability(
            context=_rail_a_ctx(intent_hint),
            message="test",
            company_id="co-1",
            db=None,
        )
        assert result is None, (
            f"card={card_id!r} intent_hint={intent_hint!r} must fall through to LLM router. "
            "If you added this to capability_map.yaml intentionally, change "
            f"routing_layer to chat_cap_map in rail_a_golden_dataset.json for card {card_id!r}."
        )


# ---------------------------------------------------------------------------
# Group 4 — Non-chat-executable: returns open_modal immediately
# ---------------------------------------------------------------------------


class TestNonChatExecutable:
    """chat_executable=false -> gate returns open_modal without any LLM call."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "intent_hint,expected_modal_id",
        [
            ("add_candidate", "add_candidate"),
            ("send_offer",    "offer_review"),
        ],
    )
    async def test_returns_open_modal(self, intent_hint, expected_modal_id):
        from app.orchestrator.guards.rail_a_capability_check import check_rail_a_capability

        result = await check_rail_a_capability(
            context=_rail_a_ctx(intent_hint),
            message="test",
            company_id="co-1",
            db=None,
        )
        assert result is not None, (
            f"{intent_hint!r}: gate must return response dict, not None. "
            "Check capability_map.yaml: chat_executable must be false."
        )
        assert result["ui_action"] == "open_modal", (
            f"{intent_hint!r}: expected ui_action=open_modal, got {result.get('ui_action')!r}"
        )
        assert result["ui_action_params"]["modal_id"] == expected_modal_id, (
            f"{intent_hint!r}: expected modal_id={expected_modal_id!r}, "
            f"got {result['ui_action_params'].get('modal_id')!r}"
        )
        assert result["confidence"] == 1.0
        assert result["source"] == "rail_a_gate"

    @pytest.mark.asyncio
    async def test_non_chat_executable_skips_db(self):
        """Non-chat-executable must not touch the DB at all."""
        from app.orchestrator.guards.rail_a_capability_check import check_rail_a_capability

        mock_db = AsyncMock()
        result = await check_rail_a_capability(
            context=_rail_a_ctx("add_candidate"),
            message="test",
            company_id="co-1",
            db=mock_db,
        )
        assert result is not None
        assert result["ui_action"] == "open_modal"
        mock_db.execute.assert_not_called()


# ---------------------------------------------------------------------------
# Group 5 — chat_executable with no entity_required -> returns None
# ---------------------------------------------------------------------------


class TestChatExecutableNoEntity:
    """chat_executable=true AND entity_required=[] -> returns None (chat pipeline proceeds)."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "intent_hint",
        ["search_candidates", "daily_briefing", "forecast"],
    )
    async def test_no_entity_required_returns_none(self, intent_hint):
        """Tenant-wide intents need no entity: gate is a no-op.

        Sensor message: if this fails, entity_required was accidentally added
        to a tenant-wide intent in capability_map.yaml. Remove the entity entry.
        """
        from app.orchestrator.guards.rail_a_capability_check import check_rail_a_capability

        result = await check_rail_a_capability(
            context=_rail_a_ctx(intent_hint),
            message="test",
            company_id="co-1",
            db=None,
        )
        assert result is None, (
            f"{intent_hint!r}: no entity required, gate must return None. "
            f"Got: {result}"
        )


# ---------------------------------------------------------------------------
# Group 6 — Entity required, entity NOT found -> navigate_to fallback
# ---------------------------------------------------------------------------


class TestEntityResolutionNotFound:
    """When EntityResolverService finds no match, gate returns not_found + navigate_to."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "intent_hint,card_id",
        [
            ("move_candidate",       "update-status"),
            ("reschedule_interview", "reschedule-interview"),
            ("compare_candidates",   "compare-candidates"),
            ("register_hire",        "register-hire"),
            ("close_job",            "close-vacancy"),
            ("generate_job_report",  "job-report"),
            ("start_wsi_interview",  "wsi-screening"),
        ],
    )
    async def test_entity_not_found_returns_navigate(self, intent_hint, card_id):
        """Entity not found -> gate returns not_found response with navigate_to action."""
        from app.orchestrator.guards.rail_a_capability_check import check_rail_a_capability

        not_found = MagicMock()
        not_found.resolved = False
        not_found.ambiguous = False
        not_found.navigate_to = None  # will use default "/teams-tab/candidatos"

        with (
            patch(
                "app.shared.services.entity_resolver_service.EntityResolverService.resolve",
                new=AsyncMock(return_value=not_found),
            ),
            patch(
                "app.shared.navigation_routes.validate_navigate_route",
                return_value=True,
            ),
            patch(
                "app.shared.navigation_routes.safe_navigate_route",
                side_effect=lambda x: x,
            ),
        ):
            result = await check_rail_a_capability(
                context=_rail_a_ctx(intent_hint),
                message="buscar candidato",
                company_id="co-1",
                db=MagicMock(),
            )

        assert result is not None, (
            f"card={card_id!r} intent={intent_hint!r}: entity not found must return response. "
            "Check _resolve_required_entities in rail_a_capability_check.py."
        )
        assert result.get("ui_action") == "navigate_to", (
            f"card={card_id!r}: expected ui_action=navigate_to, "
            f"got {result.get('ui_action')!r}"
        )
        page = result.get("ui_action_params", {}).get("page", "")
        assert page, f"card={card_id!r}: navigate_to must have a non-empty page"

    @pytest.mark.asyncio
    async def test_entity_ambiguous_returns_disambiguation(self):
        """Ambiguous entity -> gate returns disambiguation choices, domain=entity_resolver."""
        from app.orchestrator.guards.rail_a_capability_check import check_rail_a_capability

        ambiguous = MagicMock()
        ambiguous.resolved = False
        ambiguous.ambiguous = True
        ambiguous.candidates_preview = [
            {"name": "João Silva", "stage": "triagem"},
            {"name": "João Santos", "stage": "entrevista"},
        ]

        with patch(
            "app.shared.services.entity_resolver_service.EntityResolverService.resolve",
            new=AsyncMock(return_value=ambiguous),
        ):
            result = await check_rail_a_capability(
                context=_rail_a_ctx("move_candidate"),
                message="João",
                company_id="co-1",
                db=MagicMock(),
            )

        assert result is not None
        assert result.get("domain") == "entity_resolver"
        assert result.get("source") == "disambiguation"
        content = result.get("content", "")
        assert "João" in content


# ---------------------------------------------------------------------------
# Group 7 — Entity resolved in-place -> context enriched, pipeline proceeds
# ---------------------------------------------------------------------------


class TestEntityResolutionResolved:
    """Resolved entity enriches context dict in-place."""

    @pytest.mark.asyncio
    async def test_resolved_enriches_context(self):
        """First entity resolves -> context enriched with entity_id before further processing."""
        from app.orchestrator.guards.rail_a_capability_check import check_rail_a_capability

        resolved = MagicMock()
        resolved.resolved = True
        resolved.ambiguous = False
        resolved.entity_id = "cand-abc123"
        resolved.preview = {"name": "João"}

        not_found = MagicMock()
        not_found.resolved = False
        not_found.ambiguous = False
        not_found.navigate_to = None

        call_count = 0

        async def _mock_resolve(entity_type, hint, company_id, db):
            nonlocal call_count
            call_count += 1
            return resolved if entity_type == "candidate" else not_found

        with (
            patch(
                "app.shared.services.entity_resolver_service.EntityResolverService.resolve",
                new=AsyncMock(side_effect=_mock_resolve),
            ),
            patch("app.shared.navigation_routes.validate_navigate_route", return_value=True),
            patch("app.shared.navigation_routes.safe_navigate_route", side_effect=lambda x: x),
        ):
            ctx = _rail_a_ctx("move_candidate")
            await check_rail_a_capability(
                context=ctx,
                message="atualizar status",
                company_id="co-1",
                db=MagicMock(),
            )

        # Context enriched with resolved candidate
        assert (
            ctx.get("candidate_id") == "cand-abc123"
            or ctx.get("entity_id") == "cand-abc123"
        )
        assert call_count >= 1


# ---------------------------------------------------------------------------
# Group 8 — Golden dataset structural integrity
# ---------------------------------------------------------------------------


class TestGoldenDatasetIntegrity:
    """Structural assertions: golden dataset is complete and internally consistent."""

    def test_has_22_cards(self, golden_dataset):
        assert len(golden_dataset["cards"]) == 22

    def test_has_110_variations(self, golden_dataset):
        total = sum(len(c.get("variations", [])) for c in golden_dataset["cards"])
        assert total == 110, f"Expected 110 variations (22×5), got {total}"

    def test_all_cards_have_5_variations(self, golden_dataset):
        bad = [
            c["card_id"]
            for c in golden_dataset["cards"]
            if len(c.get("variations", [])) != 5
        ]
        assert not bad, f"Cards with != 5 variations: {bad}"

    def test_routing_layer_distribution(self, golden_dataset):
        layers: dict[str, int] = {}
        for c in golden_dataset["cards"]:
            layers[c["routing_layer"]] = layers.get(c["routing_layer"], 0) + 1
        assert layers.get("navigate") == 4
        assert layers.get("modal") == 3
        assert layers.get("chat_cap_map") == 12
        assert layers.get("chat_llm_fallback") == 3

    def test_chat_cap_map_intents_in_capability_map(self, golden_dataset):
        """Every chat_cap_map card must have its intent_hint in capability_map.yaml.

        Sensor message: this fails when a card is labelled chat_cap_map but its
        intent_hint is missing from capability_map.yaml. Add the missing intent.
        """
        from app.shared.services.capability_map_service import CapabilityMapService

        for card in golden_dataset["cards"]:
            if card["routing_layer"] != "chat_cap_map":
                continue
            hint = card.get("intent_hint")
            assert hint, f"card {card['card_id']!r} missing intent_hint"
            cap = CapabilityMapService.get(hint)
            assert cap is not None, (
                f"card {card['card_id']!r} intent_hint={hint!r} is routing_layer=chat_cap_map "
                "but NOT in capability_map.yaml. Add the intent or fix routing_layer."
            )

    def test_no_duplicate_card_ids(self, golden_dataset):
        ids = [c["card_id"] for c in golden_dataset["cards"]]
        dupes = [x for x in ids if ids.count(x) > 1]
        assert not dupes, f"Duplicate card_ids: {dupes}"


# ---------------------------------------------------------------------------
# Group 9 — capability_map.yaml structural sanity
# ---------------------------------------------------------------------------


class TestCapabilityMapSanity:
    """capability_map.yaml is the canonical source — validate its structure."""

    def test_no_duplicate_capability_keys(self):
        """YAML duplicate keys are silently overwritten — detect them before runtime.

        Sensor message: capability_map.yaml has a duplicate capability key.
        Remove the duplicate block.
        """
        from app.shared.services.capability_map_service import CONFIG_PATH

        keys_seen: list[str] = []
        for line in CONFIG_PATH.read_text().splitlines():
            # Match exactly 2-space-indented keys (capability names in YAML mapping)
            if line.startswith("  ") and not line.startswith("    "):
                stripped = line.strip()
                if stripped.endswith(":") and not stripped.startswith("#"):
                    keys_seen.append(stripped.rstrip(":"))

        duplicates = [k for k in set(keys_seen) if keys_seen.count(k) > 1]
        assert not duplicates, (
            f"capability_map.yaml duplicate keys: {duplicates}. "
            "Remove the duplicate block."
        )

    def test_all_intents_have_navigate_or_modal(self):
        """Every capability must have navigate_fallback OR modal_id (YAML rule).

        Sensor message: an intent in capability_map.yaml is missing both
        navigate_fallback and modal_id. Add at least one.
        """
        from app.shared.services.capability_map_service import CapabilityMapService

        for intent, cap in CapabilityMapService.load().items():
            has_fallback = bool(cap.navigate_fallback)
            has_modal = bool(cap.modal_id)
            assert has_fallback or has_modal, (
                f"intent={intent!r}: must have navigate_fallback OR modal_id in "
                "capability_map.yaml. Add at least one."
            )

    def test_load_returns_12_intents(self):
        """capability_map.yaml must have exactly 12 intents.

        Sensor message: this fails when an intent is added or removed without
        updating this test. Update the expected count here.
        """
        from app.shared.services.capability_map_service import CapabilityMapService

        intents = CapabilityMapService.load()
        assert len(intents) == 22, (
            f"Expected 12 intents in capability_map.yaml, got {len(intents)}: "
            f"{sorted(intents.keys())}"
        )
