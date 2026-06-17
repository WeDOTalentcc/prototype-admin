"""
Wave 5 Sensor: offer domain FE invariants.

Harness-engineering classification:
  SENSOR (computacional) — guards that prevent regressions in the offer FE
  components, hooks, store, and proxy routes shipped in PR-B.

Guards:
  1. OfferReviewModal.tsx ≤250 lines (component size rule)
  2. OfferReviewModal sends user_confirmation: true (HITL never bypassed)
  3. OfferReviewModal does NOT auto-send without confirmState=confirming
  4. offersApi calls /api/backend-proxy (not direct BE, multi-tenant proxy required)
  5. useOfferReviewFlow.start() calls offersApi.createDraft
  6. useOfferDraftStore has reset() action
  7. OfferDataForm has aria-invalid on salary input
  8. OfferHITLBanner has role="alert" on error state
  9. All 5 offer proxy routes exist (POST, PATCH, DELETE, send, prepare-manual)
  10. offer-draft-store uses Zustand (not useState, not Redux)
"""
from pathlib import Path

import pytest

MONOREPO_ROOT = Path(__file__).parent.parent.parent.parent
FE = MONOREPO_ROOT / "plataforma-lia" / "src"
MODAL = FE / "components" / "offer-review-modal" / "OfferReviewModal.tsx"
HITL_BANNER = FE / "components" / "offer-review-modal" / "OfferHITLBanner.tsx"
DATA_FORM = FE / "components" / "offer-review-modal" / "OfferDataForm.tsx"
STORE = FE / "stores" / "offer-draft-store.ts"
REVIEW_FLOW = FE / "hooks" / "offers" / "useOfferReviewFlow.ts"
OFFERS_API = FE / "services" / "lia-api" / "offers-api.ts"

PROXY_ROUTES = [
    FE / "app" / "api" / "backend-proxy" / "offers" / "drafts" / "route.ts",
    FE / "app" / "api" / "backend-proxy" / "offers" / "drafts" / "[id]" / "route.ts",
    FE / "app" / "api" / "backend-proxy" / "offers" / "drafts" / "[id]" / "send" / "route.ts",
    FE / "app" / "api" / "backend-proxy" / "offers" / "drafts" / "[id]" / "prepare-manual" / "route.ts",
]


def _read(path: Path) -> str:
    assert path.exists(), f"File not found: {path}"
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Guard 1 — OfferReviewModal.tsx ≤ 250 lines
# ---------------------------------------------------------------------------

def test_offer_review_modal_size_under_limit():
    """OfferReviewModal.tsx must stay ≤250 lines (component size rule from CLAUDE.md)."""
    lines = len(_read(MODAL).splitlines())
    assert lines <= 250, (
        f"OfferReviewModal.tsx has {lines} lines — exceeds the 250-line limit. "
        "FIX: Extract logic into sub-components (e.g., OfferHITLBanner, OfferSendModeSelector)."
    )


# ---------------------------------------------------------------------------
# Guard 2 — user_confirmation: true is present in the send call
# ---------------------------------------------------------------------------

def test_offer_modal_sends_user_confirmation_true():
    """OfferReviewModal must pass user_confirmation: true to sendDraft (HITL gate)."""
    src = _read(MODAL)
    assert "user_confirmation: true" in src, (
        "OfferReviewModal.tsx missing `user_confirmation: true` in sendDraft call. "
        "FIX: Ensure offersApi.sendDraft() is called with { user_confirmation: true }."
    )


# ---------------------------------------------------------------------------
# Guard 3 — send only fires after confirmState transition
# ---------------------------------------------------------------------------

def test_offer_modal_requires_confirm_state():
    """Send must only execute after entering 'confirming' state — never auto-fires."""
    src = _read(MODAL)
    assert "confirmState" in src, (
        "OfferReviewModal.tsx missing confirmState guard. "
        "FIX: Add HITL two-step: idle → confirming → send."
    )
    # The confirm handler must call setConfirmState("confirming") or similar
    assert "confirming" in src, (
        "OfferReviewModal.tsx missing 'confirming' state transition. "
        "FIX: Add setConfirmState('confirming') in the request-confirm handler."
    )


# ---------------------------------------------------------------------------
# Guard 4 — offersApi calls /api/backend-proxy (not direct FastAPI)
# ---------------------------------------------------------------------------

def test_offers_api_uses_backend_proxy():
    """offersApi must call /api/backend-proxy, not the FastAPI server directly."""
    src = _read(OFFERS_API)
    assert "/api/backend-proxy/offers" in src, (
        "offers-api.ts must route through /api/backend-proxy/offers, not direct FastAPI URL. "
        "FIX: Change all API calls to use /api/backend-proxy/offers/drafts/* path."
    )
    # Must not contain direct FastAPI port or hardcoded URL
    assert "8001" not in src and "localhost" not in src, (
        "offers-api.ts contains hardcoded localhost or port 8001 — bypasses Next.js proxy. "
        "FIX: Use relative /api/backend-proxy/ path."
    )


# ---------------------------------------------------------------------------
# Guard 5 — useOfferReviewFlow calls offersApi.createDraft
# ---------------------------------------------------------------------------

def test_offer_review_flow_calls_create_draft():
    """useOfferReviewFlow.start() must call offersApi.createDraft."""
    src = _read(REVIEW_FLOW)
    assert "offersApi.createDraft" in src or "createDraft" in src, (
        "useOfferReviewFlow.ts must call offersApi.createDraft in start(). "
        "FIX: Add `const draft = await offersApi.createDraft({ candidate_id, job_id })` in start()."
    )
    assert "setDraft" in src, (
        "useOfferReviewFlow.ts must call setDraft() after creating the draft. "
        "FIX: Call store.setDraft(draft) after createDraft."
    )
    assert "setOpen" in src, (
        "useOfferReviewFlow.ts must call setOpen(true) after creating the draft. "
        "FIX: Call store.setOpen(true) to display the modal."
    )


# ---------------------------------------------------------------------------
# Guard 6 — useOfferDraftStore has reset()
# ---------------------------------------------------------------------------

def test_offer_draft_store_has_reset():
    """useOfferDraftStore must have a reset() action."""
    src = _read(STORE)
    assert "reset" in src, (
        "offer-draft-store.ts missing reset() action. "
        "FIX: Add reset: () => set(initialState) to the store."
    )
    assert "initialState" in src, (
        "offer-draft-store.ts must define initialState for reset(). "
        "FIX: Add const initialState = { activeDraft: null, isOpen: false, ... }."
    )


# ---------------------------------------------------------------------------
# Guard 7 — OfferDataForm has aria-invalid on salary
# ---------------------------------------------------------------------------

def test_offer_data_form_has_aria_invalid():
    """OfferDataForm.tsx salary input must have aria-invalid for screen-reader feedback."""
    src = _read(DATA_FORM)
    assert "aria-invalid" in src, (
        "OfferDataForm.tsx salary input missing aria-invalid attribute. "
        "FIX: Add aria-invalid={salaryOverBudget} to the salary Input component."
    )


# ---------------------------------------------------------------------------
# Guard 8 — OfferHITLBanner error state has role="alert"
# ---------------------------------------------------------------------------

def test_offer_hitl_banner_has_role_alert():
    """OfferHITLBanner.tsx must have role='alert' on the error state container."""
    src = _read(HITL_BANNER)
    # role="alert" triggers screen-reader announcement on error
    has_alert = 'role="alert"' in src or "role={'alert'}" in src
    assert has_alert, (
        "OfferHITLBanner.tsx missing role='alert' on error state container. "
        "FIX: Add role='alert' to the error state div for WCAG 2.1 AA compliance."
    )


# ---------------------------------------------------------------------------
# Guard 9 — all 5 proxy route files exist
# ---------------------------------------------------------------------------

def test_offer_proxy_routes_all_exist():
    """All 4 offer proxy route files must exist (covers all 5 HTTP operations)."""
    for route_path in PROXY_ROUTES:
        assert route_path.exists(), (
            f"Offer proxy route not found at {route_path}. "
            "FIX: Create the Next.js route handler that proxies to FastAPI /api/v1/offers/*."
        )


# ---------------------------------------------------------------------------
# Guard 10 — store uses Zustand (not useState/useReducer)
# ---------------------------------------------------------------------------

def test_offer_draft_store_uses_zustand():
    """offer-draft-store.ts must use Zustand (create from 'zustand')."""
    src = _read(STORE)
    assert 'from "zustand"' in src or "from 'zustand'" in src, (
        "offer-draft-store.ts must use Zustand for state management. "
        "FIX: Import { create } from 'zustand' and define the store with create()."
    )
    assert "devtools" in src, (
        "offer-draft-store.ts should use Zustand devtools middleware for debugging. "
        "FIX: Import { devtools } from 'zustand/middleware' and wrap the store."
    )
