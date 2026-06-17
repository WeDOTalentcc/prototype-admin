"""
Unit tests for WSI Interview Graph state handling.

Covers: WSIInterviewState dataclass, WSIQuestionBlock, WSIResponseRecord,
serialization/deserialization, stage transitions, progress calculation,
log_step, properties (is_complete, questions_remaining, progress_pct).
"""
import pytest

pytestmark = pytest.mark.hard

from datetime import datetime
from uuid import uuid4

from app.domains.cv_screening.agents.wsi_interview_graph import (
    WSIInterviewStage,
    WSIQuestionBlock,
    WSIResponseRecord,
    WSIInterviewState,
    _wsi_state_to_dict,
    _wsi_state_from_dict,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def make_block(block_id="b-1", block_type="behavioral", question="Descreva um desafio?",
               competency="resolução de problemas", bloom_level=3, dreyfus_level=2):
    return WSIQuestionBlock(
        block_id=block_id,
        block_type=block_type,
        question=question,
        competency=competency,
        bloom_level=bloom_level,
        dreyfus_level=dreyfus_level,
    )


def make_state(**kwargs):
    defaults = dict(
        session_id=str(uuid4()),
        company_id="company-1",
        candidate_id="cand-1",
        job_id="job-1",
    )
    defaults.update(kwargs)
    return WSIInterviewState(**defaults)


# ---------------------------------------------------------------------------
# WSIInterviewStage enum
# ---------------------------------------------------------------------------

class TestWSIInterviewStage:
    def test_all_stages_present(self):
        stages = {s.value for s in WSIInterviewStage}
        expected = {
            "init", "load_context", "generate_question", "await_response",
            "validate_response", "score_response", "advance",
            "generate_feedback", "complete", "error"
        }
        assert expected.issubset(stages)

    def test_stage_is_string_enum(self):
        assert isinstance(WSIInterviewStage.INIT, str)
        assert WSIInterviewStage.INIT == "init"

    def test_complete_stage_value(self):
        assert WSIInterviewStage.COMPLETE.value == "complete"

    def test_error_stage_value(self):
        assert WSIInterviewStage.ERROR.value == "error"


# ---------------------------------------------------------------------------
# WSIQuestionBlock
# ---------------------------------------------------------------------------

class TestWSIQuestionBlock:
    def test_default_max_score_is_10(self):
        block = make_block()
        assert block.max_score == 10.0

    def test_custom_max_score(self):
        block = WSIQuestionBlock(
            block_id="b-x", block_type="technical",
            question="Q?", competency="C",
            bloom_level=4, dreyfus_level=3, max_score=20.0
        )
        assert block.max_score == 20.0

    def test_big_five_trait_default_none(self):
        block = make_block()
        assert block.big_five_trait is None

    def test_big_five_trait_can_be_set(self):
        block = make_block()
        block.big_five_trait = "conscientiousness"
        assert block.big_five_trait == "conscientiousness"

    def test_block_type_eligibility(self):
        block = WSIQuestionBlock(
            block_id="e-1", block_type="eligibility",
            question="Você tem CNH?", competency="requisito",
            bloom_level=1, dreyfus_level=1,
        )
        assert block.block_type == "eligibility"


# ---------------------------------------------------------------------------
# WSIResponseRecord
# ---------------------------------------------------------------------------

class TestWSIResponseRecord:
    def test_default_score_is_zero(self):
        block = make_block()
        record = WSIResponseRecord(question_block=block, candidate_response="Resposta do candidato")
        assert record.score == 0.0

    def test_default_bloom_dreyfus_zero(self):
        block = make_block()
        record = WSIResponseRecord(question_block=block, candidate_response="R")
        assert record.bloom_achieved == 0
        assert record.dreyfus_achieved == 0

    def test_scored_at_default_none(self):
        block = make_block()
        record = WSIResponseRecord(question_block=block, candidate_response="R")
        assert record.scored_at is None

    def test_reasoning_default_empty(self):
        block = make_block()
        record = WSIResponseRecord(question_block=block, candidate_response="R")
        assert record.reasoning == ""

    def test_can_set_score(self):
        block = make_block()
        record = WSIResponseRecord(question_block=block, candidate_response="R", score=8.5)
        assert record.score == 8.5


# ---------------------------------------------------------------------------
# WSIInterviewState — properties
# ---------------------------------------------------------------------------

class TestWSIInterviewStateProperties:
    def test_is_complete_false_in_init(self):
        state = make_state()
        assert state.is_complete is False

    def test_is_complete_true_in_complete_stage(self):
        state = make_state()
        state.stage = WSIInterviewStage.COMPLETE
        assert state.is_complete is True

    def test_is_complete_true_in_error_stage(self):
        state = make_state()
        state.stage = WSIInterviewStage.ERROR
        assert state.is_complete is True

    def test_questions_remaining_no_blocks(self):
        state = make_state()
        assert state.questions_remaining == 0

    def test_questions_remaining_full_set(self):
        state = make_state()
        state.question_blocks = [make_block(block_id=f"b-{i}") for i in range(5)]
        state.current_question_index = 0
        assert state.questions_remaining == 5

    def test_questions_remaining_after_advance(self):
        state = make_state()
        state.question_blocks = [make_block(block_id=f"b-{i}") for i in range(5)]
        state.current_question_index = 3
        assert state.questions_remaining == 2

    def test_progress_pct_zero_when_no_blocks(self):
        state = make_state()
        assert state.progress_pct == 0.0

    def test_progress_pct_zero_at_start(self):
        state = make_state()
        state.question_blocks = [make_block(block_id=f"b-{i}") for i in range(4)]
        state.current_question_index = 0
        assert state.progress_pct == 0.0

    def test_progress_pct_50_percent(self):
        state = make_state()
        state.question_blocks = [make_block(block_id=f"b-{i}") for i in range(4)]
        state.current_question_index = 2
        assert state.progress_pct == 50.0

    def test_progress_pct_100_percent(self):
        state = make_state()
        state.question_blocks = [make_block(block_id=f"b-{i}") for i in range(4)]
        state.current_question_index = 4
        assert state.progress_pct == 100.0


# ---------------------------------------------------------------------------
# WSIInterviewState — log_step
# ---------------------------------------------------------------------------

class TestLogStep:
    def test_log_step_appends_to_execution_log(self):
        state = make_state()
        assert len(state.execution_log) == 0
        state.log_step("generate_question", {"question_id": "q-1"})
        assert len(state.execution_log) == 1

    def test_log_step_contains_node(self):
        state = make_state()
        state.log_step("score_response", {"score": 7.5})
        entry = state.execution_log[0]
        assert entry["node"] == "score_response"

    def test_log_step_contains_timestamp(self):
        state = make_state()
        state.log_step("advance", {})
        entry = state.execution_log[0]
        assert "timestamp" in entry

    def test_log_step_contains_question_index(self):
        state = make_state()
        state.current_question_index = 3
        state.log_step("validate_response", {})
        entry = state.execution_log[0]
        assert entry["question_index"] == 3

    def test_log_step_merges_extra_details(self):
        state = make_state()
        state.log_step("score_response", {"score": 8.0, "reasoning": "Good answer"})
        entry = state.execution_log[0]
        assert entry["score"] == 8.0
        assert entry["reasoning"] == "Good answer"

    def test_multiple_log_steps(self):
        state = make_state()
        state.log_step("step_a", {"data": 1})
        state.log_step("step_b", {"data": 2})
        state.log_step("step_c", {"data": 3})
        assert len(state.execution_log) == 3
        assert state.execution_log[2]["node"] == "step_c"


# ---------------------------------------------------------------------------
# Serialization: _wsi_state_to_dict / _wsi_state_from_dict
# ---------------------------------------------------------------------------

class TestWSISerialization:
    def test_to_dict_contains_required_fields(self):
        state = make_state()
        d = _wsi_state_to_dict(state)
        required = {
            "session_id", "company_id", "candidate_id", "job_id",
            "stage", "question_blocks", "responses", "current_question_index",
            "technical_score", "behavioral_score", "situational_score",
            "eligibility_score", "wsi_final_score", "recommendation",
            "execution_log", "started_at", "completed_at", "error",
        }
        assert required.issubset(set(d.keys()))

    def test_to_dict_stage_is_string(self):
        state = make_state()
        d = _wsi_state_to_dict(state)
        assert isinstance(d["stage"], str)
        assert d["stage"] == "init"

    def test_to_dict_empty_blocks(self):
        state = make_state()
        d = _wsi_state_to_dict(state)
        assert d["question_blocks"] == []

    def test_to_dict_with_blocks(self):
        state = make_state()
        state.question_blocks = [make_block(block_id="b-1"), make_block(block_id="b-2")]
        d = _wsi_state_to_dict(state)
        assert len(d["question_blocks"]) == 2
        assert d["question_blocks"][0]["block_id"] == "b-1"

    def test_roundtrip_basic_state(self):
        state = make_state(
            session_id="sess-rt",
            company_id="corp-rt",
            candidate_id="cand-rt",
            job_id="job-rt",
        )
        d = _wsi_state_to_dict(state)
        restored = _wsi_state_from_dict(d)
        assert restored.session_id == "sess-rt"
        assert restored.company_id == "corp-rt"
        assert restored.candidate_id == "cand-rt"
        assert restored.job_id == "job-rt"
        assert restored.stage == WSIInterviewStage.INIT

    def test_roundtrip_with_blocks(self):
        state = make_state()
        block = make_block(block_id="b-rt", competency="leadership")
        state.question_blocks = [block]
        d = _wsi_state_to_dict(state)
        restored = _wsi_state_from_dict(d)
        assert len(restored.question_blocks) == 1
        assert restored.question_blocks[0].block_id == "b-rt"
        assert restored.question_blocks[0].competency == "leadership"

    def test_roundtrip_complete_stage(self):
        state = make_state()
        state.stage = WSIInterviewStage.COMPLETE
        state.wsi_final_score = 8.2
        state.recommendation = "aprovado"
        d = _wsi_state_to_dict(state)
        restored = _wsi_state_from_dict(d)
        assert restored.stage == WSIInterviewStage.COMPLETE
        assert restored.wsi_final_score == 8.2
        assert restored.recommendation == "aprovado"

    def test_roundtrip_with_scores(self):
        state = make_state()
        state.technical_score = 7.5
        state.behavioral_score = 8.0
        state.situational_score = 6.5
        state.eligibility_score = 10.0
        d = _wsi_state_to_dict(state)
        restored = _wsi_state_from_dict(d)
        assert restored.technical_score == 7.5
        assert restored.behavioral_score == 8.0
        assert restored.situational_score == 6.5
        assert restored.eligibility_score == 10.0

    def test_roundtrip_completed_at(self):
        state = make_state()
        state.completed_at = datetime(2026, 3, 8, 15, 30, 0)
        d = _wsi_state_to_dict(state)
        assert d["completed_at"] is not None
        restored = _wsi_state_from_dict(d)
        assert restored.completed_at is not None

    def test_roundtrip_null_completed_at(self):
        state = make_state()
        state.completed_at = None
        d = _wsi_state_to_dict(state)
        assert d["completed_at"] is None
        restored = _wsi_state_from_dict(d)
        assert restored.completed_at is None

    def test_roundtrip_error_field(self):
        state = make_state()
        state.error = "LLM timeout after 30s"
        state.stage = WSIInterviewStage.ERROR
        d = _wsi_state_to_dict(state)
        restored = _wsi_state_from_dict(d)
        assert restored.error == "LLM timeout after 30s"

    def test_from_dict_missing_optional_fields_uses_defaults(self):
        minimal = {
            "session_id": "s-1", "company_id": "c-1",
            "candidate_id": "cd-1", "job_id": "j-1",
        }
        restored = _wsi_state_from_dict(minimal)
        assert restored.interview_level == "standard"
        assert restored.question_blocks == []
        assert restored.responses == []
        assert restored.current_question_index == 0
        assert restored.stage == WSIInterviewStage.INIT
