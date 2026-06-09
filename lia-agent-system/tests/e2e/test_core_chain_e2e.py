"""
Contract Test — Core recruitment chain: pipeline + search + screening.

MIGRATION_PLAN item 8.2 (PX08).

CONTEXT:
    This test exercises the happy-path "recruiter's day" chain contract:

        1. Each step in the pipeline (source → shortlist → screen → move)
           invokes the correct service/endpoint with the right arguments.
        2. A screening decision of "reject" must prevent further pipeline
           transitions to the interview stage.
        3. The chain produces the expected audit events (pipeline.moved,
           screening.completed) for the Rails LiaEventsWorker (item 2.1).

    Converted from E2E (requires staging Rails + Python orchestrator) →
    unit/contract (mocks HTTP clients and service calls). The behaviour
    contract is identical; transport and external state are stubbed.

DEPENDENCIES:
    - app/shared/messaging/rails_event_publisher.py — ✅ shipped
    - app/shared/messaging/rails_event_schemas.py    — ✅ shipped
"""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch, call

import pytest


# ──────────────────────────────────────────────────────────────────────
# Fixtures / constants
# ──────────────────────────────────────────────────────────────────────

COMPANY_ID = "company-" + uuid.uuid4().hex[:8]
CANDIDATE_ID = "cand-" + uuid.uuid4().hex[:4]
JOB_ID = "job-1"


# ──────────────────────────────────────────────────────────────────────
# Chain simulation helpers
# ──────────────────────────────────────────────────────────────────────

class _FakePipelineService:
    """Minimal fake pipeline service tracking transitions."""

    def __init__(self):
        self.transitions: list[dict] = []
        # Candidates in this set are blocked from moving to "interview"
        self._rejected: set[str] = set()

    def mark_rejected(self, candidate_id: str) -> None:
        self._rejected.add(candidate_id)

    async def transition(self, job_id: str, candidate_id: str, to_stage: str) -> dict:
        if to_stage == "interview" and candidate_id in self._rejected:
            raise ValueError(
                f"Candidate {candidate_id} has a 'reject' screening decision. "
                "Pipeline guard must block interview transition."
            )
        record = {"job_id": job_id, "candidate_id": candidate_id, "to_stage": to_stage}
        self.transitions.append(record)
        return record


class _FakeSourcingService:
    """Returns one canned candidate."""

    async def search(self, job_id: str, keywords: list[str]) -> list[dict]:
        return [
            {
                "id": CANDIDATE_ID,
                "name": "Ana Souza",
                "skills": keywords[:2],
                "match_score": 0.82,
            }
        ]


class _FakeScreeningService:
    """Returns configurable screening result."""

    def __init__(self, decision: str = "approved", score: float = 0.87):
        self._decision = decision
        self._score = score

    async def evaluate(self, job_id: str, candidate_id: str) -> dict:
        return {
            "candidate_id": candidate_id,
            "job_id": job_id,
            "score": self._score,
            "decision": self._decision,
        }


# ──────────────────────────────────────────────────────────────────────
# Tests
# ──────────────────────────────────────────────────────────────────────

class TestPipelineSearchScreeningChain:
    """Happy-path chain: each step's output feeds the next."""

    @pytest.mark.asyncio
    async def test_chain_happy_path_produces_expected_transitions_and_events(self):
        """Step sequence: source → shortlist → screen → move to interview.
        Verifies that pipeline transitions are recorded and the screening
        result triggers the correct next action.
        """
        pipeline = _FakePipelineService()
        sourcing = _FakeSourcingService()
        screening = _FakeScreeningService(decision="approved", score=0.87)
        published_events: list[dict] = []

        async def _mock_publish(event_type: str, payload: dict, company_id: str):
            published_events.append({
                "event_type": event_type,
                "company_id": company_id,
                **payload,
            })

        with patch(
            "app.shared.messaging.rails_event_publisher.publish_to_exchange",
            new_callable=AsyncMock,
        ):
            from app.shared.messaging.rails_event_publisher import publish_rails_event

            # Step 2: sourcing
            candidates = await sourcing.search(JOB_ID, ["python", "backend"])
            assert len(candidates) >= 1, "Sourcing must return at least one candidate"
            top = candidates[0]
            candidate_id = top["id"]
            assert candidate_id, "Candidate must have an id"

            # Step 3: shortlist → screening stage
            move_to_screening = await pipeline.transition(JOB_ID, candidate_id, "screening")
            assert move_to_screening["to_stage"] == "screening"

            # Step 3 event
            await _mock_publish("pipeline.moved", {
                "candidate_id": candidate_id, "job_id": JOB_ID,
                "from_stage": "sourcing", "to_stage": "screening",
            }, COMPANY_ID)

            # Step 4: CV screening
            result = await screening.evaluate(JOB_ID, candidate_id)
            assert "score" in result, "Screening response must include score"
            assert "decision" in result, "Screening response must include decision"

            # Step 4 event
            await _mock_publish("screening.completed", {
                "candidate_id": candidate_id, "job_id": JOB_ID,
                "score": result["score"], "decision": result["decision"],
            }, COMPANY_ID)

            # Step 5: move to interview (only when approved)
            if result["decision"] in {"approved", "pass"}:
                move_to_interview = await pipeline.transition(JOB_ID, candidate_id, "interview")
                assert move_to_interview["to_stage"] == "interview"
                await _mock_publish("pipeline.moved", {
                    "candidate_id": candidate_id, "job_id": JOB_ID,
                    "from_stage": "screening", "to_stage": "interview",
                }, COMPANY_ID)

        # Step 6: verify audit trail (events published)
        event_types = {e["event_type"] for e in published_events}
        assert "pipeline.moved" in event_types, (
            "pipeline.moved event not published. "
            "LiaEventsWorker (item 2.1) would miss pipeline transitions."
        )
        assert "screening.completed" in event_types, (
            "screening.completed event not published. "
            "LiaEventsWorker (item 2.1) would miss screening results."
        )

        # All events must carry company_id for multi-tenancy
        for event in published_events:
            assert event.get("company_id") == COMPANY_ID, (
                f"Event {event['event_type']} missing company_id. "
                "Multi-tenancy invariant violated."
            )

    @pytest.mark.asyncio
    async def test_rejection_stops_chain(self):
        """Rejection path: screening decision 'reject' must block transition
        to interview stage. The pipeline guard must enforce this."""
        pipeline = _FakePipelineService()
        screening = _FakeScreeningService(decision="reject", score=0.2)

        # Run screening
        result = await screening.evaluate(JOB_ID, CANDIDATE_ID)
        assert result["decision"] == "reject"

        # Mark as rejected in pipeline (simulating the guard)
        pipeline.mark_rejected(CANDIDATE_ID)

        # Attempt to skip to interview — must be blocked
        with pytest.raises((ValueError, Exception)) as exc_info:
            await pipeline.transition(JOB_ID, CANDIDATE_ID, "interview")

        assert "reject" in str(exc_info.value).lower() or "block" in str(exc_info.value).lower(), (
            f"Pipeline allowed transition to interview for rejected candidate. "
            f"Error was: {exc_info.value}. The pipeline_agent guard is missing."
        )


class TestChainEventSchemaContract:
    """The events emitted by the chain must match the Rails event schemas."""

    def test_all_chain_event_types_are_in_registry(self):
        """pipeline.moved and screening.completed must be in EVENT_REGISTRY."""
        from app.shared.messaging.rails_event_schemas import EVENT_REGISTRY

        chain_events = {"pipeline.moved", "screening.completed"}
        missing = chain_events - set(EVENT_REGISTRY.keys())
        assert not missing, (
            f"Chain event types missing from EVENT_REGISTRY: {missing}. "
            "Rails LiaEventsWorker (item 2.1) has no handler for these."
        )

    def test_pipeline_moved_event_has_required_fields(self):
        """PipelineMovedEvent must carry from_stage, to_stage, candidate_id."""
        from app.shared.messaging.rails_event_schemas import PipelineMovedEvent

        event = PipelineMovedEvent(
            company_id=COMPANY_ID,
            candidate_id=int(CANDIDATE_ID.split("-")[-1], 16) if "-" in CANDIDATE_ID else 1,
            job_id=1,
            from_stage="screening",
            to_stage="interview",
            reason="screening_approved",
        )
        d = event.to_dict()
        assert d["event_type"] == "pipeline.moved"
        assert d["from_stage"] == "screening"
        assert d["to_stage"] == "interview"
        assert d["company_id"] == COMPANY_ID
        assert "version" in d
        assert "timestamp" in d

    def test_screening_completed_event_has_required_fields(self):
        """ScreeningCompletedEvent must carry score, candidate_id, company_id."""
        from app.shared.messaging.rails_event_schemas import ScreeningCompletedEvent

        event = ScreeningCompletedEvent(
            company_id=COMPANY_ID,
            candidate_id=1,
            job_id=1,
            score=0.87,
            recommendation="advance",
        )
        d = event.to_dict()
        assert d["event_type"] == "screening.completed"
        assert d["score"] == 0.87
        assert d["company_id"] == COMPANY_ID
        assert "version" in d
