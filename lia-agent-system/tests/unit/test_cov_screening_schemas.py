"""Coverage tests for app/schemas/screening.py — Pydantic models."""
import pytest
from app.schemas.screening import (
    BigFiveProfile,
    RegenerateQuestionsRequest,
    ScreeningQuestion,
    ScreeningQuestionRequest,
    ScreeningQuestionResponse,
    UnifiedScreeningQuestion,
    WSIBlockSummary,
    WSIScreeningPipelineRequest,
    WSIScreeningPipelineResponse,
)


class TestBigFiveProfile:
    def test_empty(self):
        m = BigFiveProfile()
        assert m is not None

    def test_with_scores(self):
        m = BigFiveProfile(
            openness=80,
            conscientiousness=70,
            extraversion=60,
            agreeableness=75,
            stability=30,
        )
        assert m.openness == 80
        assert m.conscientiousness == 70

    def test_partial_scores(self):
        m = BigFiveProfile(openness=90)
        assert m.openness == 90


class TestRegenerateQuestionsRequest:
    def test_basic(self):
        ctx = ScreeningQuestionRequest(title="Senior Python developer role")
        m = RegenerateQuestionsRequest(context=ctx)
        assert m.context.title == "Senior Python developer role"

    def test_with_category(self):
        ctx = ScreeningQuestionRequest(title="Backend developer")
        m = RegenerateQuestionsRequest(context=ctx, category="technical")
        assert m.category == "technical"
        assert m.exclude_ids == []


class TestScreeningQuestion:
    def test_basic(self):
        m = ScreeningQuestion(
            id="q-001",
            text="Tell me about your experience with Python.",
            category="technical",
        )
        assert m.id == "q-001"
        assert m.text == "Tell me about your experience with Python."
        assert m.category == "technical"

    def test_behavioral(self):
        m = ScreeningQuestion(
            id="q-002",
            text="Describe a challenge you overcame.",
            category="behavioral",
        )
        assert m.category == "behavioral"

    def test_optional_fields(self):
        m = ScreeningQuestion(
            id="q-003",
            text="What is your greatest strength?",
            category="behavioral",
        )
        # Optional fields should be accessible
        assert m.id == "q-003"


class TestScreeningQuestionRequest:
    def test_basic(self):
        m = ScreeningQuestionRequest(title="Senior Backend Engineer")
        assert m.title == "Senior Backend Engineer"

    def test_with_options(self):
        m = ScreeningQuestionRequest(
            title="Data Scientist",
            num_questions=5,
            seniority="senior",
        )
        assert m.title == "Data Scientist"


class TestScreeningQuestionResponse:
    def test_empty(self):
        m = ScreeningQuestionResponse()
        assert m is not None

    def test_with_questions(self):
        q = ScreeningQuestion(id="q-1", text="Question 1", category="technical")
        m = ScreeningQuestionResponse(questions=[q], total_count=1)
        assert m.total_count == 1
        assert len(m.questions) == 1


class TestUnifiedScreeningQuestion:
    def test_basic(self):
        m = UnifiedScreeningQuestion(
            id="uq-001",
            text="How do you handle tight deadlines?",
            category="behavioral",
            block_id=1,
        )
        assert m.id == "uq-001"
        assert m.block_id == 1
        assert m.category == "behavioral"


class TestWSIBlockSummary:
    def test_basic(self):
        q1 = UnifiedScreeningQuestion(
            id="q1", text="Q1", category="technical", block_id=1
        )
        m = WSIBlockSummary(
            block_id=1,
            block_name="Technical Skills",
            question_count=1,
            questions=[q1],
        )
        assert m.block_id == 1
        assert m.question_count == 1
        assert len(m.questions) == 1

    def test_multiple_questions(self):
        questions = [
            UnifiedScreeningQuestion(id=f"q{i}", text=f"Q{i}", category="behavioral", block_id=2)
            for i in range(3)
        ]
        m = WSIBlockSummary(
            block_id=2,
            block_name="Behavioral",
            question_count=3,
            questions=questions,
        )
        assert m.question_count == 3


class TestWSIScreeningPipelineRequest:
    def test_basic(self):
        m = WSIScreeningPipelineRequest(job_title="Product Manager")
        assert m.job_title == "Product Manager"

    def test_with_context(self):
        m = WSIScreeningPipelineRequest(
            job_title="Senior Engineer",
        )
        assert m.job_title == "Senior Engineer"


class TestWSIScreeningPipelineResponse:
    def test_basic(self):
        m = WSIScreeningPipelineResponse(success=True)
        assert m.success is True
        assert m.questions == []
        assert m.blocks == []
        assert m.total_count == 0

    def test_with_blocks(self):
        block = WSIBlockSummary(
            block_id=1,
            block_name="Technical",
            question_count=2,
            questions=[
                UnifiedScreeningQuestion(id="q1", text="Q1", category="technical", block_id=1),
                UnifiedScreeningQuestion(id="q2", text="Q2", category="technical", block_id=1),
            ],
        )
        m = WSIScreeningPipelineResponse(success=True, blocks=[block], total_count=2)
        assert m.total_count == 2
        assert len(m.blocks) == 1
