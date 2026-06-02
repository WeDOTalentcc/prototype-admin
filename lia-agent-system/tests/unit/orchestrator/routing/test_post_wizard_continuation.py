"""TDD (Task #1211) — post-wizard continuation store/offer logic.

Uses a hermetic in-memory fake store (no DB) to validate the park → offer →
confirm lifecycle. INVIOLABLE: this module never creates a job.

Run: pytest tests/unit/orchestrator/routing/test_post_wizard_continuation.py -v
"""
import pytest


class FakeStore:
    def __init__(self):
        self._d = {}

    def get(self, cid):
        return self._d.get(cid)

    def save(self, cid, state):
        self._d[cid] = state

    def remove(self, cid):
        self._d.pop(cid, None)


@pytest.fixture
def store():
    return FakeStore()


def _detect(msg):
    from app.orchestrator.routing.job_creation_disambiguator import detect_job_creation
    return detect_job_creation(msg)


class TestParkAndOffer:
    def test_simple_creation_parks_nothing(self, store):
        from app.orchestrator.routing.post_wizard_continuation import store_continuation
        det = _detect("criar uma vaga de dev")
        result = store_continuation("conv1", "c1", det, "criar uma vaga de dev", store=store)
        assert result is None
        assert store.get("conv1") is None

    def test_composite_parks_continuation_not_offered_yet(self, store):
        from app.orchestrator.routing.post_wizard_continuation import (
            CONTINUATION_INTENT,
            get_continuation,
            store_continuation,
        )
        det = _detect("criar a vaga e publicar no ATS")
        state = store_continuation("conv1", "c1", det, "criar a vaga e publicar no ATS", store=store)
        assert state is not None
        assert state.intent == CONTINUATION_INTENT
        assert state.awaiting_confirmation is False  # parked, not yet offered
        assert state.collected_params["continuation_kind"] == "publish_job"
        assert state.collected_params["continuation_connected"] is True
        assert get_continuation("conv1", store=store) is state

    def test_mark_offered_binds_job_and_flips_flag(self, store):
        from app.orchestrator.routing.post_wizard_continuation import (
            mark_offered,
            store_continuation,
        )
        det = _detect("criar a vaga e publicar")
        store_continuation("conv1", "c1", det, "criar a vaga e publicar", store=store)
        offered = mark_offered("conv1", "job-123", store=store)
        assert offered is not None
        assert offered.awaiting_confirmation is True
        assert offered.collected_params["job_id"] == "job-123"

    def test_offer_message_connected_mentions_action(self, store):
        from app.orchestrator.routing.post_wizard_continuation import (
            build_offer_message,
            mark_offered,
            store_continuation,
        )
        det = _detect("criar a vaga e publicar no ATS")
        store_continuation("conv1", "c1", det, "criar a vaga e publicar no ATS", store=store)
        offered = mark_offered("conv1", "job-1", store=store)
        msg = build_offer_message(offered)
        assert "criada" in msg.lower()
        assert "?" in msg  # it asks

    def test_offer_message_unconnected_is_explicit_not_faked(self, store):
        from app.orchestrator.routing.post_wizard_continuation import (
            build_offer_message,
            mark_offered,
            store_continuation,
        )
        det = _detect("criar a vaga e buscar candidatos no LinkedIn")
        state = store_continuation("conv1", "c1", det, "criar a vaga e buscar candidatos no LinkedIn", store=store)
        assert state.collected_params["continuation_connected"] is False
        offered = mark_offered("conv1", "job-1", store=store)
        msg = build_offer_message(offered)
        # Must NOT claim the step ran; must signal it is not connected.
        assert "não está conectada" in msg or "nao esta conectada" in msg

    def test_clear_removes(self, store):
        from app.orchestrator.routing.post_wizard_continuation import (
            clear_continuation,
            get_continuation,
            store_continuation,
        )
        det = _detect("criar a vaga e publicar")
        store_continuation("conv1", "c1", det, "criar a vaga e publicar", store=store)
        clear_continuation("conv1", store=store)
        assert get_continuation("conv1", store=store) is None


class TestNeverCreatesJob:
    def test_dispatch_targets_are_never_creation_actions(self):
        from app.orchestrator.routing.post_wizard_continuation import _CONTINUATION_DISPATCH
        from app.shared.execution.plan_detector import JOB_CREATION_ACTION_IDS

        for kind, (domain, action, _label) in _CONTINUATION_DISPATCH.items():
            assert action not in JOB_CREATION_ACTION_IDS, (
                f"continuation '{kind}' must never create a job (action={action})"
            )
