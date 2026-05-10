"""Coverage tests for app/schemas/technical_tests.py — enums and Pydantic models."""
import pytest
from app.schemas.technical_tests import (
    TestCategoryEnum,
    TestSubcategoryEnum,
    TestDifficultyEnum,
    TechnicalTestCreate,
    TechnicalTestUpdate,
    TechnicalTestResponse,
    TechnicalTestListResponse,
    ClientTestConfigCreate,
)


class TestCategoryEnumValues:
    def test_has_values(self):
        assert TestCategoryEnum is not None
        values = list(TestCategoryEnum)
        assert len(values) > 0

    def test_coding(self):
        assert TestCategoryEnum.CODING == "coding"

    def test_logic(self):
        assert TestCategoryEnum.LOGIC == "logic"

    def test_domain_specific(self):
        assert TestCategoryEnum.DOMAIN_SPECIFIC == "domain_specific"

    def test_personality(self):
        assert TestCategoryEnum.PERSONALITY == "personality"


class TestDifficultyEnumValues:
    def test_has_multiple_levels(self):
        values = list(TestDifficultyEnum)
        assert len(values) >= 2

    def test_medium_exists(self):
        assert TestDifficultyEnum.MEDIUM is not None


class TestTechnicalTestCreate:
    def test_basic(self):
        m = TechnicalTestCreate(
            name="Python Basics",
            category=TestCategoryEnum.CODING,
        )
        assert m.name == "Python Basics"
        assert m.duration_minutes == 30  # default
        assert m.passing_score == pytest.approx(70.0)  # default
        assert m.max_attempts == 3  # default

    def test_custom_fields(self):
        m = TechnicalTestCreate(
            name="Advanced SQL",
            category=TestCategoryEnum.DOMAIN_SPECIFIC,
            duration_minutes=60,
            difficulty=TestDifficultyEnum.HARD,
            passing_score=80.0,
            max_attempts=2,
            instructions="Complete all queries",
        )
        assert m.duration_minutes == 60
        assert m.difficulty == TestDifficultyEnum.HARD
        assert m.passing_score == pytest.approx(80.0)
        assert m.max_attempts == 2

    def test_is_global_default(self):
        m = TechnicalTestCreate(
            name="Test",
            category=TestCategoryEnum.CODING,
        )
        assert m.is_global is True

    def test_with_questions_config(self):
        config = {"type": "multiple_choice", "count": 20}
        m = TechnicalTestCreate(
            name="Mixed Test",
            category=TestCategoryEnum.CODING,
            questions_config=config,
        )
        assert m.questions_config == config


class TestTechnicalTestUpdate:
    def test_all_optional(self):
        m = TechnicalTestUpdate()
        assert m.name is None
        assert m.duration_minutes is None
        assert m.is_active is None

    def test_update_duration(self):
        m = TechnicalTestUpdate(duration_minutes=90, difficulty=TestDifficultyEnum.EASY)
        assert m.duration_minutes == 90

    def test_update_is_active(self):
        m = TechnicalTestUpdate(is_active=False)
        assert m.is_active is False


class TestTechnicalTestResponse:
    def test_basic(self):
        m = TechnicalTestResponse(
            id="test-001",
            name="Python Test",
            category="programming",
            duration_minutes=30,
            difficulty="medium",
            passing_score=70.0,
            max_attempts=3,
            is_global=True,
            is_active=True,
        )
        assert m.id == "test-001"
        assert m.name == "Python Test"
        assert m.is_active is True

    def test_optional_fields_default_none(self):
        m = TechnicalTestResponse(
            id="t2",
            name="SQL Test",
            category="database",
            duration_minutes=45,
            difficulty="hard",
            passing_score=75.0,
            max_attempts=2,
            is_global=False,
            is_active=True,
        )
        assert m.subcategory is None
        assert m.description is None
        assert m.created_at is None


class TestTechnicalTestListResponse:
    def test_empty_list(self):
        m = TechnicalTestListResponse(tests=[], total=0, limit=20, offset=0)
        assert m.tests == []
        assert m.total == 0

    def test_with_pagination(self):
        m = TechnicalTestListResponse(
            tests=[],
            total=100,
            limit=20,
            offset=40,
        )
        assert m.total == 100
        assert m.offset == 40


class TestClientTestConfigCreate:
    def test_defaults(self):
        m = ClientTestConfigCreate()
        assert m.is_enabled is True
        assert m.custom_time_limit is None
        assert m.priority == 0

    def test_custom_config(self):
        m = ClientTestConfigCreate(
            is_enabled=True,
            custom_time_limit=45,
            custom_passing_score=85.0,
            custom_max_attempts=1,
            priority=10,
            required_for_roles=["backend_developer", "data_engineer"],
        )
        assert m.custom_time_limit == 45
        assert m.custom_passing_score == pytest.approx(85.0)
        assert m.required_for_roles == ["backend_developer", "data_engineer"]

    def test_disabled(self):
        m = ClientTestConfigCreate(is_enabled=False)
        assert m.is_enabled is False
