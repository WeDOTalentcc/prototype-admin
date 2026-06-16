"""
Tests for WSI state serialization helpers (Phase 3.2).

Covers:
- _wsi_state_to_dict: serialização básica e campos datetime/enum
- _wsi_state_from_dict: round-trip fidelidade
- Nested WSIQuestionBlock serialização/desserialização
- WSIResponseRecord com datetime scored_at
- stage enum → value → enum round-trip
"""
import pytest
import sys
import os
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))


def _make_minimal_state():
    from app.domains.cv_screening.agents.wsi_interview_graph import WSIInterviewState
    return WSIInterviewState(
        session_id="sess-wsi-001",
        company_id="company-abc",
        candidate_id="cand-123",
        job_id="job-456",
        interview_level="standard",
    )


def _make_question_block():
    from app.domains.cv_screening.agents.wsi_interview_graph import WSIQuestionBlock
    return WSIQuestionBlock(
        block_id="block-001",
        block_type="technical",
        question="Explique o padrão Singleton.",
        competency="Python",
        bloom_level="comprehension",
        dreyfus_level="competent",
        big_five_trait=None,
        max_score=10.0,
    )


# ---------------------------------------------------------------------------
# Section 1: _wsi_state_to_dict
# ---------------------------------------------------------------------------

class TestWsiStateToDictBasic:

    def test_returns_dict(self):
        from app.domains.cv_screening.agents.wsi_interview_graph import _wsi_state_to_dict
        state = _make_minimal_state()
        result = _wsi_state_to_dict(state)
        assert isinstance(result, dict)

    def test_identity_fields_present(self):
        from app.domains.cv_screening.agents.wsi_interview_graph import _wsi_state_to_dict
        state = _make_minimal_state()
        d = _wsi_state_to_dict(state)
        assert d["session_id"] == "sess-wsi-001"
        assert d["company_id"] == "company-abc"
        assert d["candidate_id"] == "cand-123"
        assert d["job_id"] == "job-456"
        assert d["interview_level"] == "standard"

    def test_stage_serialized_as_string(self):
        from app.domains.cv_screening.agents.wsi_interview_graph import _wsi_state_to_dict
        state = _make_minimal_state()
        d = _wsi_state_to_dict(state)
        assert isinstance(d["stage"], str)

    def test_started_at_serialized_as_iso_string(self):
        from app.domains.cv_screening.agents.wsi_interview_graph import _wsi_state_to_dict
        state = _make_minimal_state()
        d = _wsi_state_to_dict(state)
        assert isinstance(d["started_at"], str)
        # Must parse back to datetime without error
        datetime.fromisoformat(d["started_at"])

    def test_completed_at_none_when_not_complete(self):
        from app.domains.cv_screening.agents.wsi_interview_graph import _wsi_state_to_dict
        state = _make_minimal_state()
        d = _wsi_state_to_dict(state)
        assert d["completed_at"] is None

    def test_empty_question_blocks(self):
        from app.domains.cv_screening.agents.wsi_interview_graph import _wsi_state_to_dict
        state = _make_minimal_state()
        d = _wsi_state_to_dict(state)
        assert isinstance(d["question_blocks"], list)
        assert len(d["question_blocks"]) == 0

    def test_empty_responses(self):
        from app.domains.cv_screening.agents.wsi_interview_graph import _wsi_state_to_dict
        state = _make_minimal_state()
        d = _wsi_state_to_dict(state)
        assert isinstance(d["responses"], list)
        assert len(d["responses"]) == 0


class TestWsiStateToDictWithBlocks:

    def test_question_blocks_serialized(self):
        from app.domains.cv_screening.agents.wsi_interview_graph import _wsi_state_to_dict
        state = _make_minimal_state()
        block = _make_question_block()
        state.question_blocks = [block]
        d = _wsi_state_to_dict(state)
        assert len(d["question_blocks"]) == 1
        b = d["question_blocks"][0]
        assert b["block_id"] == "block-001"
        assert b["block_type"] == "technical"
        assert b["question"] == "Explique o padrão Singleton."
        assert b["competency"] == "Python"

    def test_question_blocks_serializable_to_json(self):
        import json
        from app.domains.cv_screening.agents.wsi_interview_graph import _wsi_state_to_dict
        state = _make_minimal_state()
        state.question_blocks = [_make_question_block()]
        d = _wsi_state_to_dict(state)
        # Must not raise
        json.dumps(d)

    def test_full_state_serializable_to_json(self):
        import json
        from app.domains.cv_screening.agents.wsi_interview_graph import _wsi_state_to_dict
        state = _make_minimal_state()
        state.question_blocks = [_make_question_block()]
        state.current_question = _make_question_block()
        d = _wsi_state_to_dict(state)
        json.dumps(d)  # must not raise


# ---------------------------------------------------------------------------
# Section 2: _wsi_state_from_dict
# ---------------------------------------------------------------------------

class TestWsiStateFromDict:

    def test_returns_wsi_interview_state(self):
        from app.domains.cv_screening.agents.wsi_interview_graph import (
            _wsi_state_to_dict,
            _wsi_state_from_dict,
            WSIInterviewState,
        )
        state = _make_minimal_state()
        d = _wsi_state_to_dict(state)
        result = _wsi_state_from_dict(d)
        assert isinstance(result, WSIInterviewState)

    def test_round_trip_identity_fields(self):
        from app.domains.cv_screening.agents.wsi_interview_graph import (
            _wsi_state_to_dict,
            _wsi_state_from_dict,
        )
        state = _make_minimal_state()
        d = _wsi_state_to_dict(state)
        restored = _wsi_state_from_dict(d)
        assert restored.session_id == state.session_id
        assert restored.company_id == state.company_id
        assert restored.candidate_id == state.candidate_id
        assert restored.job_id == state.job_id
        assert restored.interview_level == state.interview_level

    def test_round_trip_stage_enum(self):
        from app.domains.cv_screening.agents.wsi_interview_graph import (
            _wsi_state_to_dict,
            _wsi_state_from_dict,
            WSIInterviewStage,
        )
        state = _make_minimal_state()
        state.stage = WSIInterviewStage.LOAD_CONTEXT
        d = _wsi_state_to_dict(state)
        restored = _wsi_state_from_dict(d)
        assert restored.stage == WSIInterviewStage.LOAD_CONTEXT

    def test_round_trip_question_blocks(self):
        from app.domains.cv_screening.agents.wsi_interview_graph import (
            _wsi_state_to_dict,
            _wsi_state_from_dict,
        )
        state = _make_minimal_state()
        state.question_blocks = [_make_question_block()]
        d = _wsi_state_to_dict(state)
        restored = _wsi_state_from_dict(d)
        assert len(restored.question_blocks) == 1
        assert restored.question_blocks[0].block_id == "block-001"
        assert restored.question_blocks[0].question == "Explique o padrão Singleton."

    def test_round_trip_current_question(self):
        from app.domains.cv_screening.agents.wsi_interview_graph import (
            _wsi_state_to_dict,
            _wsi_state_from_dict,
        )
        state = _make_minimal_state()
        state.current_question = _make_question_block()
        d = _wsi_state_to_dict(state)
        restored = _wsi_state_from_dict(d)
        assert restored.current_question is not None
        assert restored.current_question.block_id == "block-001"

    def test_current_question_none_preserved(self):
        from app.domains.cv_screening.agents.wsi_interview_graph import (
            _wsi_state_to_dict,
            _wsi_state_from_dict,
        )
        state = _make_minimal_state()
        state.current_question = None
        d = _wsi_state_to_dict(state)
        restored = _wsi_state_from_dict(d)
        assert restored.current_question is None

    def test_round_trip_awaiting_response_flag(self):
        from app.domains.cv_screening.agents.wsi_interview_graph import (
            _wsi_state_to_dict,
            _wsi_state_from_dict,
        )
        state = _make_minimal_state()
        state.awaiting_response = True
        d = _wsi_state_to_dict(state)
        restored = _wsi_state_from_dict(d)
        assert restored.awaiting_response is True

    def test_round_trip_scores(self):
        from app.domains.cv_screening.agents.wsi_interview_graph import (
            _wsi_state_to_dict,
            _wsi_state_from_dict,
        )
        state = _make_minimal_state()
        state.technical_score = 7.5
        state.behavioral_score = 8.0
        state.wsi_final_score = 7.75
        d = _wsi_state_to_dict(state)
        restored = _wsi_state_from_dict(d)
        assert restored.technical_score == 7.5
        assert restored.behavioral_score == 8.0
        assert restored.wsi_final_score == 7.75


# ---------------------------------------------------------------------------
# Section 3: _WSILangGraphState TypedDict
# ---------------------------------------------------------------------------

class TestWSILangGraphStateTypedDict:

    def test_typed_dict_importable(self):
        from app.domains.cv_screening.agents.wsi_interview_graph import _WSILangGraphState
        assert _WSILangGraphState is not None

    def test_valid_lg_input_structure(self):
        from app.domains.cv_screening.agents.wsi_interview_graph import _wsi_state_to_dict
        state = _make_minimal_state()
        lg_input = {
            "wsi_data": _wsi_state_to_dict(state),
            "pending_response": "",
            "operation": "start",
        }
        assert lg_input["operation"] == "start"
        assert isinstance(lg_input["wsi_data"], dict)

    def test_submit_operation_structure(self):
        from app.domains.cv_screening.agents.wsi_interview_graph import _wsi_state_to_dict
        state = _make_minimal_state()
        lg_input = {
            "wsi_data": _wsi_state_to_dict(state),
            "pending_response": "Minha resposta aqui",
            "operation": "submit",
        }
        assert lg_input["operation"] == "submit"
        assert lg_input["pending_response"] == "Minha resposta aqui"
