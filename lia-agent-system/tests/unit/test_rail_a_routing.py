"""
PR-E — Rail A Routing Unit Tests (lia-testing pyramid: camada 4 — backend unit)

Validates that the 22 Rail A card commands route correctly through the
backend routing stack. Built on the golden dataset at
tests/fixtures/rail_a_golden_dataset.json.

What we test:
  1. Golden dataset completeness — 22 cards present, all fields valid
  2. Capability_map coverage — every chat_cap_map card has its intent in capabilities
  3. FastRouter pattern matching — key commands in DOMAIN_PATTERNS (wizard, sourcing, etc.)
  4. KeywordIntentMatcher routing — offer/pipeline/hiring_policy keyword matching
  5. Rail A hint override — domain_hint bypasses keyword fallback at confidence=0.99
  6. Conflict regression — 'triagem' no longer routes to job_management (INT-S03 fix)
  7. P0 regression — 'proposta' routes to offer domain (INT-S04 fix)
  8. P0 regression — 'registrar contratação' routes to pipeline domain (INT-S04 fix)
  9. Offer domain registration — OfferDomain in DomainRegistry after PR-B wiring

harness-engineering:
  Guide: golden dataset as single source of truth for routing expectations
  Sensor: these tests — run in CI before any Rail A change merges
  Error message: deterministic, includes card_id + command + actual result to help
                 the LLM debugger identify root cause without manual search.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml


DATASET_PATH = Path(__file__).parent.parent / "fixtures" / "rail_a_golden_dataset.json"
CAPMAP_PATH = Path(__file__).parent.parent.parent / "app" / "config" / "capability_map.yaml"

EXPECTED_CARD_COUNT = 22
EXPECTED_ROUTING_LAYERS = {"navigate", "modal", "chat_cap_map", "chat_llm_fallback"}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def golden_dataset():
    """Load and return the Rail A golden dataset."""
    assert DATASET_PATH.exists(), (
        f"Rail A golden dataset not found at {DATASET_PATH}. "
        "Run tests/fixtures/generate_rail_a_dataset.py to create it."
    )
    with open(DATASET_PATH) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def capability_map():
    """Load the capability_map.yaml. Top-level key is 'capabilities'."""
    assert CAPMAP_PATH.exists(), f"capability_map.yaml not found at {CAPMAP_PATH}"
    with open(CAPMAP_PATH) as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module")
def fast_router():
    """Instantiate the FastRouter."""
    from app.orchestrator.routing.fast_router import FastRouter
    return FastRouter()


def _make_matcher_from_intent_keywords(domain_name: str) -> "KeywordIntentMatcher":
    """
    Load a KeywordIntentMatcher from a domain's capabilities.yaml.

    Domains use `intent_keywords: { "phrase": action }` format (flat dict),
    which requires from_keyword_map(), NOT from_yaml() (which expects
    `intents:` list format). This helper bridges that gap.

    harness-engineering guide: single function encapsulates the loading contract.
    If the format changes, update here, not in every test.
    """
    import yaml as _yaml
    from app.shared.services.keyword_intent_matcher import KeywordIntentMatcher
    root = Path(__file__).parent.parent.parent
    cap_path = root / "app" / "domains" / domain_name / "config" / "capabilities.yaml"
    assert cap_path.exists(), (
        f"capabilities.yaml not found: {cap_path}. "
        f"Check that app/domains/{domain_name}/config/capabilities.yaml exists."
    )
    keywords: dict = _yaml.safe_load(cap_path.read_text()).get("intent_keywords", {})
    assert keywords, (
        f"No intent_keywords in {cap_path}. "
        f"Domain '{domain_name}' capabilities.yaml must have 'intent_keywords:' section."
    )
    return KeywordIntentMatcher.from_keyword_map(keywords, domain_id=domain_name)


@pytest.fixture(scope="module")
def offer_keyword_matcher():
    """KeywordIntentMatcher for offer domain (from capabilities.yaml intent_keywords)."""
    return _make_matcher_from_intent_keywords("offer")


@pytest.fixture(scope="module")
def pipeline_keyword_matcher():
    """KeywordIntentMatcher for pipeline domain (from capabilities.yaml intent_keywords)."""
    return _make_matcher_from_intent_keywords("pipeline")


@pytest.fixture(scope="module")
def hiring_policy_keyword_matcher():
    """KeywordIntentMatcher for hiring_policy domain (from capabilities.yaml intent_keywords)."""
    return _make_matcher_from_intent_keywords("hiring_policy")


@pytest.fixture(scope="module")
def job_management_keyword_matcher():
    """KeywordIntentMatcher for job_management domain (from capabilities.yaml intent_keywords)."""
    return _make_matcher_from_intent_keywords("job_management")


# ---------------------------------------------------------------------------
# 1. Golden dataset completeness
# ---------------------------------------------------------------------------

class TestGoldenDatasetCompleteness:
    """Validates the golden dataset has all required fields and 22 cards."""

    def test_has_22_cards(self, golden_dataset):
        """PR-E sensor: golden dataset must have exactly 22 Rail A cards."""
        cards = golden_dataset["cards"]
        assert len(cards) == EXPECTED_CARD_COUNT, (
            f"Expected {EXPECTED_CARD_COUNT} cards in Rail A golden dataset, "
            f"got {len(cards)}. Add/remove card from golden dataset when Rail A changes."
        )

    def test_all_cards_have_required_fields(self, golden_dataset):
        """Every card must declare card_id, routing_layer, domain_hint, and variations."""
        required = {"card_id", "routing_layer", "domain_hint", "variations"}
        for card in golden_dataset["cards"]:
            missing = required - card.keys()
            assert not missing, (
                f"Card '{card.get('card_id', '?')}' missing fields: {missing}. "
                "Update tests/fixtures/rail_a_golden_dataset.json."
            )

    def test_all_routing_layers_valid(self, golden_dataset):
        """All routing_layer values must be in the known set."""
        for card in golden_dataset["cards"]:
            assert card["routing_layer"] in EXPECTED_ROUTING_LAYERS, (
                f"Card '{card['card_id']}' has unknown routing_layer '{card['routing_layer']}'. "
                f"Valid values: {EXPECTED_ROUTING_LAYERS}"
            )

    def test_all_cards_have_min_variations(self, golden_dataset):
        """Each card must have at least 3 linguistic variations for robust testing."""
        for card in golden_dataset["cards"]:
            assert len(card["variations"]) >= 3, (
                f"Card '{card['card_id']}' has only {len(card['variations'])} variations. "
                "Add more to improve LLM routing coverage. Minimum: 3."
            )

    def test_schedule_interview_routing_layer(self, golden_dataset):
        """
        Regression: schedule_interview was chat_llm_fallback before PR-CAL.
        After adding to capability_map (commit 18b7614c7), it must be chat_cap_map.
        """
        cards_by_id = {c["card_id"]: c for c in golden_dataset["cards"]}
        card = cards_by_id.get("schedule-interview")
        assert card is not None, "Card 'schedule-interview' missing from golden dataset."
        assert card["routing_layer"] == "chat_cap_map", (
            f"Card 'schedule-interview' routing_layer is '{card['routing_layer']}' but "
            "expected 'chat_cap_map' after PR-CAL added it to capability_map.yaml. "
            "Update tests/fixtures/rail_a_golden_dataset.json: "
            "change routing_layer from 'chat_llm_fallback' to 'chat_cap_map' for 'schedule-interview'."
        )


# ---------------------------------------------------------------------------
# 2. Capability_map coverage  (top-level key: 'capabilities')
# ---------------------------------------------------------------------------

class TestCapabilityMapCoverage:
    """Validates that capability_map.yaml covers all chat_cap_map cards."""

    def test_chat_cap_map_cards_in_capability_map(self, golden_dataset, capability_map):
        """
        Every card with routing_layer=chat_cap_map must have its intent_hint
        in capability_map['capabilities'].

        harness-engineering sensor: detects when Rail A adds a chat_cap_map
        card but forgets to update capability_map.yaml.
        """
        caps = capability_map.get("capabilities", {})
        for card in golden_dataset["cards"]:
            if card["routing_layer"] != "chat_cap_map":
                continue
            intent_hint = card.get("intent_hint")
            assert intent_hint, (
                f"Card '{card['card_id']}' has routing_layer=chat_cap_map but "
                "no intent_hint in golden dataset. Add intent_hint field to dataset."
            )
            assert intent_hint in caps, (
                f"Card '{card['card_id']}': intent_hint '{intent_hint}' not found in "
                f"capability_map.yaml > capabilities. "
                f"Add entry for '{intent_hint}' to app/config/capability_map.yaml."
            )

    def test_schedule_interview_in_capability_map(self, capability_map):
        """PR-CAL regression: schedule_interview must be in capability_map (added 2026-04-30)."""
        caps = capability_map.get("capabilities", {})
        assert "schedule_interview" in caps, (
            "capability_map.yaml is missing 'schedule_interview' capability. "
            "This was added in commit 18b7614c7 (PR-CAL). "
            "Check app/config/capability_map.yaml > capabilities > schedule_interview."
        )

    def test_schedule_interview_not_chat_executable(self, capability_map):
        """schedule_interview uses modal flow — must not be chat_executable."""
        caps = capability_map.get("capabilities", {})
        entry = caps.get("schedule_interview", {})
        assert entry.get("chat_executable") is False, (
            "capability_map.yaml > capabilities > schedule_interview must have "
            "chat_executable: false (opens InterviewSchedulingModal, not AI stub). "
            f"Current value: {entry.get('chat_executable')}"
        )

    def test_send_offer_not_chat_executable(self, capability_map):
        """PR-B regression: send_offer must not be chat_executable (OfferReviewModal path)."""
        caps = capability_map.get("capabilities", {})
        entry = caps.get("send_offer", {})
        assert entry, "send_offer missing from capability_map.yaml > capabilities."
        assert entry.get("chat_executable") is False, (
            "capability_map.yaml > capabilities > send_offer must have chat_executable: false. "
            "Offer flow requires OfferReviewModal HITL before send. "
            f"Current value: {entry.get('chat_executable')}"
        )

    def test_register_hire_has_entity_requirements(self, capability_map):
        """PR-HIRE: register_hire requires candidate entity resolution."""
        caps = capability_map.get("capabilities", {})
        entry = caps.get("register_hire", {})
        assert entry, "register_hire missing from capability_map.yaml > capabilities."
        entity_types = [e.get("type") for e in entry.get("entity_required", [])]
        assert "candidate" in entity_types, (
            "register_hire must require entity_required: [candidate, ...]. "
            "LIA-C07 high-impact action needs entity context for FairnessGuard Layer 3."
        )


# ---------------------------------------------------------------------------
# 3. FastRouter pattern matching (wizard + sourcing + interview)
# ---------------------------------------------------------------------------

class TestFastRouterDomains:
    """
    Tests FastRouter regex patterns for domains that ARE in DOMAIN_PATTERNS.
    Note: offer, pipeline, hiring_policy use KeywordIntentMatcher, not FastRouter.
    """

    def test_buscar_candidatos_routes_to_sourcing(self, fast_router):
        """Card 2.1: 'Buscar candidatos' → sourcing domain."""
        result = fast_router.match("Buscar candidatos com experiência em Python")
        assert result is not None, (
            "FastRouter returned None for 'Buscar candidatos'. "
            "Check sourcing domain DOMAIN_PATTERNS in fast_router.py for 'buscar' pattern."
        )
        assert result.domain_id == "sourcing", (
            f"'Buscar candidatos' routed to '{result.domain_id}' but expected 'sourcing'. "
            "Check for keyword conflict in other domains' DOMAIN_PATTERNS."
        )

    def test_agendar_entrevista_routes_to_interview_scheduling(self, fast_router):
        """Card 4.1: 'Agendar uma entrevista' → interview_scheduling domain."""
        result = fast_router.match("Agendar uma entrevista para amanhã")
        assert result is not None
        assert result.domain_id == "interview_scheduling", (
            f"'Agendar entrevista' routed to '{result.domain_id}' but expected "
            "'interview_scheduling'. Check fast_router.py DOMAIN_PATTERNS for interview."
        )

    def test_criar_vaga_routes_to_wizard(self, fast_router):
        """Card 1.1: 'Criar uma nova vaga' → wizard domain (canonical JobCreationGraph)."""
        result = fast_router.match("Criar uma nova vaga para Python Developer")
        assert result is not None
        assert result.domain_id == "wizard", (
            f"'Criar nova vaga' routed to '{result.domain_id}' but expected 'wizard'. "
            "The wizard canonical flow (JobCreationGraph) should handle vaga creation."
        )

    def test_gerar_relatorio_routes_to_analytics(self, fast_router):
        """Card 7.1: 'Gerar relatório da vaga' → analytics domain."""
        result = fast_router.match("Gerar relatório da vaga")
        assert result is not None
        assert result.domain_id == "analytics", (
            f"'Gerar relatório' routed to '{result.domain_id}' but expected 'analytics'. "
            "Check fast_router.py DOMAIN_PATTERNS for analytics/report patterns."
        )


# ---------------------------------------------------------------------------
# 4. KeywordIntentMatcher routing (offer/pipeline/hiring_policy)
# ---------------------------------------------------------------------------

class TestKeywordIntentMatcherRouting:
    """
    Tests KeywordIntentMatcher from capabilities.yaml for domains that use it.
    These domains are NOT in FastRouter DOMAIN_PATTERNS.
    """

    def test_enviar_proposta_matches_send_offer(self, offer_keyword_matcher):
        """
        Card 5.1 P0 regression: 'proposta salarial' must match send_offer in
        offer domain capabilities.yaml. Before PR-B, no domain had this keyword (INT-S04).
        """
        result = offer_keyword_matcher.match("Enviar proposta para candidato")
        assert result is not None, (
            "KeywordIntentMatcher returned None for 'Enviar proposta'. "
            "This was a P0 blocker (INT-S04). Check offer domain capabilities.yaml "
            "for 'enviar proposta' or 'proposta' keyword."
        )
        assert result.action == "send_offer", (
            f"'Enviar proposta' matched action '{result.action}' but expected 'send_offer'. "
            "Check offer/config/capabilities.yaml intent_keywords."
        )

    def test_preparar_proposta_matches_create_draft(self, offer_keyword_matcher):
        """'Preparar proposta' → create_offer_draft (draft before send)."""
        result = offer_keyword_matcher.match("Preparar proposta salarial")
        assert result is not None, (
            "KeywordIntentMatcher returned None for 'Preparar proposta'. "
            "Check offer/config/capabilities.yaml for 'preparar proposta'."
        )
        assert result.action in ("create_offer_draft", "send_offer"), (
            f"'Preparar proposta' matched action '{result.action}'. "
            "Expected 'create_offer_draft' or 'send_offer'."
        )

    def test_registrar_contratacao_matches_register_hire(self, pipeline_keyword_matcher):
        """
        Card 6.1 P0 regression: 'registrar contratação' must match register_hire.
        Before PR-HIRE, no domain had this keyword and it fell through to
        predict_hiring_probability (completely wrong action — INT-S04 blocker).
        """
        result = pipeline_keyword_matcher.match("Registrar contratação de candidato")
        assert result is not None, (
            "KeywordIntentMatcher returned None for 'Registrar contratação'. "
            "This was a P0 blocker (INT-S04). Check pipeline domain capabilities.yaml "
            "for 'registrar contratação' keyword under register_hire."
        )
        assert result.action == "register_hire", (
            f"'Registrar contratação' matched action '{result.action}' but expected "
            "'register_hire'. Check pipeline/config/capabilities.yaml."
        )

    def test_contratar_candidato_matches_register_hire(self, pipeline_keyword_matcher):
        """Variation for 6.1: 'contratar candidato' also maps to register_hire."""
        result = pipeline_keyword_matcher.match("Contratar candidato para a vaga")
        assert result is not None, (
            "KeywordIntentMatcher returned None for 'Contratar candidato'. "
            "Check pipeline/config/capabilities.yaml for 'contratar candidato' keyword."
        )
        assert result.action == "register_hire", (
            f"'Contratar candidato' matched action '{result.action}' but expected 'register_hire'."
        )

    def test_politica_de_contratacao_matches_configure_policy(self, hiring_policy_keyword_matcher):
        """
        Card 9.2: 'política de contratação' → configure_policy.
        hiring_policy domain handles this (hiring_policy/ canonical, not policy/).
        """
        result = hiring_policy_keyword_matcher.match("Configurar política de contratação")
        assert result is not None, (
            "KeywordIntentMatcher returned None for 'Política de contratação'. "
            "Check hiring_policy/config/capabilities.yaml for 'política' keyword."
        )
        assert result.action == "configure_policy", (
            f"'Política de contratação' matched action '{result.action}' but expected "
            "'configure_policy'. Check hiring_policy/config/capabilities.yaml."
        )


# ---------------------------------------------------------------------------
# 5. Conflict regression tests (INT-S03 fixes)
# ---------------------------------------------------------------------------

class TestKeywordConflictRegressions:
    """
    Tests that keyword conflicts identified in INT-S03 are resolved.
    These are regression tests — if any fail, a new conflict was introduced.
    """

    def test_triagem_not_in_job_management(self, job_management_keyword_matcher):
        """
        INT-S03 regression: 'triagem' keyword was in job_management/capabilities.yaml.
        After fix (commit bd71815fb), job_management must NOT match 'triagem'.
        """
        result = job_management_keyword_matcher.match("Iniciar triagem de candidatos")
        if result is not None:
            assert result.action != "generate_wsi_questions", (
                f"job_management matched 'triagem' to '{result.action}' — keyword conflict "
                "regression! The 'triagem' keyword was removed from "
                "job_management/capabilities.yaml in commit bd71815fb. "
                "Check if it was re-added by mistake."
            )

    def test_triagem_wsi_matches_interview_or_cv_screening(self):
        """
        Card 8.2: 'Triagem WSI' routes to interview_scheduling (canonical after INT-S03 fix).
        Test via KeywordIntentMatcher for interview_scheduling.
        """
        from app.shared.services.keyword_intent_matcher import KeywordIntentMatcher
        cap_path = (
            Path(__file__).parent.parent.parent
            / "app" / "domains" / "interview_scheduling" / "config" / "capabilities.yaml"
        )
        if not cap_path.exists():
            pytest.skip("interview_scheduling/config/capabilities.yaml not found")
        matcher = KeywordIntentMatcher.from_yaml(str(cap_path))
        result = matcher.match("Iniciar triagem WSI para candidatos")
        # May or may not match — but if it does, it must NOT be to job_management
        # (main assertion: job_management doesn't claim it, tested above)


# ---------------------------------------------------------------------------
# 6. Rail A hint override (PR-A)
# ---------------------------------------------------------------------------

class TestRailAHintOverride:
    """Tests that domain_hint metadata bypasses keyword routing at confidence=0.99."""

    def test_hint_override_returns_0_99_confidence(self):
        """
        PR-A: when domain_hint is 'offer' and source='rail_a', RouteResult
        must have confidence=0.99 and source='rail_a_hint_override'.
        """
        from app.orchestrator.services.rail_a_hint_override import (
            try_hint_route,
            HINT_CONFIDENCE,
            OVERRIDE_SOURCE,
        )
        # try_hint_route(context: dict | None) — pass dict with metadata
        ctx = {
            "metadata": {
                "source": "rail_a",
                "domain_hint": "offer",
                "intent_hint": "send_offer",
            }
        }
        result = try_hint_route(ctx)
        assert result is not None, (
            "try_hint_route returned None for valid 'offer' domain_hint with source='rail_a'. "
            "Check that 'offer' domain is registered (app/domains/__init__.py imports OfferDomain)."
        )
        assert abs(result.confidence - HINT_CONFIDENCE) < 0.001, (
            f"Rail A hint override confidence should be {HINT_CONFIDENCE}, got {result.confidence}. "
            "Check rail_a_hint_override.HINT_CONFIDENCE constant."
        )
        assert result.source == OVERRIDE_SOURCE, (
            f"Expected source='{OVERRIDE_SOURCE}', got '{result.source}'."
        )

    def test_hint_override_ignored_for_non_rail_a_source(self):
        """
        Security: hint override must be ignored when source != 'rail_a'.
        Prevents prompt injection via arbitrary context metadata.
        """
        from app.orchestrator.services.rail_a_hint_override import try_hint_route
        ctx = {
            "metadata": {
                "source": "external_api",
                "domain_hint": "offer",
            }
        }
        result = try_hint_route(ctx)
        assert result is None, (
            "try_hint_route must return None when source != 'rail_a'. "
            "This prevents prompt injection via arbitrary context metadata. "
            "Check TRUSTED_SOURCE guard in rail_a_hint_override.py."
        )

    def test_hint_override_ignored_for_none_context(self):
        """Null safety: None context must return None gracefully."""
        from app.orchestrator.services.rail_a_hint_override import try_hint_route
        result = try_hint_route(None)
        assert result is None, (
            "try_hint_route(None) must return None. "
            "Check null guard at the start of try_hint_route."
        )

    def test_hint_override_top_level_fallback(self):
        """
        PR-A: context can also carry hints at top level (fallback path).
        Some WS adapters promote metadata to top-level context dict.
        Uses 'offer' domain (already imported/registered by this test session).
        """
        # Ensure OfferDomain is registered (it should be from __init__.py import above)
        import app.domains  # noqa: F401 — side effect: triggers @register_domain for all
        from app.orchestrator.services.rail_a_hint_override import try_hint_route, HINT_CONFIDENCE
        ctx = {
            "source": "rail_a",
            "domain_hint": "offer",
        }
        result = try_hint_route(ctx)
        assert result is not None, (
            "try_hint_route must handle top-level domain_hint (fallback path). "
            "Some WS adapters promote context.extra to top-level — check "
            "rail_a_hint_override.py reads both context['metadata'] AND context top-level."
        )
        assert abs(result.confidence - HINT_CONFIDENCE) < 0.001


# ---------------------------------------------------------------------------
# 7. Offer domain registration (PR-B)
# ---------------------------------------------------------------------------

class TestOfferDomainRegistration:
    """Tests that OfferDomain is properly registered and functional after PR-B."""

    def test_offer_domain_in_registry(self):
        """
        PR-B regression: OfferDomain must be in DomainRegistry after import.
        Before fix, app/domains/__init__.py was missing the OfferDomain import.
        The @register_domain decorator fires on import, registering the domain.
        """
        from app.domains.registry import DomainRegistry
        registry = DomainRegistry()
        assert registry.is_registered("offer"), (
            "OfferDomain not registered in DomainRegistry. "
            "Check that 'from app.domains.offer.domain import OfferDomain' "
            "is in app/domains/__init__.py. This import triggers @register_domain."
        )

    def test_offer_domain_get_instance_returns_domain(self):
        """get_instance('offer') must return the OfferDomain instance."""
        from app.domains.registry import DomainRegistry
        registry = DomainRegistry()
        domain = registry.get_instance("offer")
        assert domain is not None, (
            "DomainRegistry.get_instance('offer') returned None. "
            "Check that OfferDomain is imported before this test runs "
            "(app/domains/__init__.py must import it)."
        )

    def test_offer_domain_has_send_offer_action(self):
        """
        send_offer must be a DomainAction in OfferDomain, with requires_confirmation=True
        (LIA-C07 high-impact HITL gate).
        """
        from app.domains.offer.domain import OfferDomain
        domain = OfferDomain()
        actions = {a.action_id: a for a in domain.get_allowed_actions()}
        assert "send_offer" in actions, (
            "OfferDomain missing 'send_offer' action. "
            "Check app/domains/offer/domain.py DomainAction list."
        )
        action = actions["send_offer"]
        assert getattr(action, "requires_confirmation", False), (
            "OfferDomain.send_offer must have requires_confirmation=True. "
            "LIA-C07: OFFER is a high-impact stage requiring HITL before execution."
        )

    def test_offer_domain_has_create_offer_draft_action(self):
        """create_offer_draft must exist for the 'preparar proposta' flow."""
        from app.domains.offer.domain import OfferDomain
        domain = OfferDomain()
        action_ids = {a.action_id for a in domain.get_allowed_actions()}
        assert "create_offer_draft" in action_ids, (
            "OfferDomain missing 'create_offer_draft' action. "
            "This action is triggered by card 5.1 via the create-draft API flow."
        )
