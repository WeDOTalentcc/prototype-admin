"""
Coverage boost 2 — Additional unit tests for high-miss-count modules.
All unit tests: no real DB, no real Redis. Pure mocks.
"""
import pytest
import json
import hashlib
from unittest.mock import MagicMock, AsyncMock, patch, call
from typing import Optional, List
from pydantic import BaseModel


# ---------------------------------------------------------------------------
# GROUP F: structured_output service
# ---------------------------------------------------------------------------

@pytest.fixture
def so_module():
    try:
        from app.services import structured_output
        return structured_output
    except ImportError as exc:
        pytest.skip(f"structured_output not importable: {exc}")


class SimpleModel(BaseModel):
    name: str
    age: int
    score: Optional[float] = None


class NestedModel(BaseModel):
    title: str
    items: List[str]


def test_so_pydantic_to_json_schema_basic(so_module):
    schema = so_module.pydantic_to_json_schema(SimpleModel)
    assert "properties" in schema
    assert "name" in schema["properties"]
    assert "age" in schema["properties"]


def test_so_pydantic_to_json_schema_returns_dict(so_module):
    schema = so_module.pydantic_to_json_schema(SimpleModel)
    assert isinstance(schema, dict)


def test_so_pydantic_to_claude_tool_structure(so_module):
    tool = so_module.pydantic_to_claude_tool(SimpleModel)
    assert "name" in tool
    assert "input_schema" in tool
    assert tool["name"] == "respond"


def test_so_pydantic_to_claude_tool_custom_name(so_module):
    tool = so_module.pydantic_to_claude_tool(SimpleModel, tool_name="my_tool")
    assert tool["name"] == "my_tool"


def test_so_pydantic_to_claude_tool_schema_type(so_module):
    tool = so_module.pydantic_to_claude_tool(SimpleModel)
    assert tool["input_schema"]["type"] == "object"
    assert "properties" in tool["input_schema"]


def test_so_pydantic_to_gemini_schema(so_module):
    schema = so_module.pydantic_to_gemini_schema(SimpleModel)
    assert isinstance(schema, dict)


def test_so_get_json_type_str(so_module):
    result = so_module._get_json_type(str)
    assert result == "string"


def test_so_get_json_type_int(so_module):
    result = so_module._get_json_type(int)
    assert result == "integer"


def test_so_get_json_type_float(so_module):
    result = so_module._get_json_type(float)
    assert result == "number"


def test_so_get_json_type_bool(so_module):
    result = so_module._get_json_type(bool)
    assert result == "boolean"


def test_so_get_json_type_list(so_module):
    result = so_module._get_json_type(list)
    assert result == "array"


def test_so_get_json_type_dict(so_module):
    result = so_module._get_json_type(dict)
    assert result == "object"


def test_so_parse_claude_tool_response_with_tool_use(so_module):
    mock_block = MagicMock()
    mock_block.type = "tool_use"
    mock_block.name = "respond"
    mock_block.input = {"name": "Alice", "age": 30}

    mock_response = MagicMock()
    mock_response.content = [mock_block]

    result = so_module.parse_claude_tool_response(mock_response, SimpleModel)
    assert result.name == "Alice"
    assert result.age == 30


def test_so_parse_claude_tool_response_wrong_tool_name(so_module):
    """Tool with different name should not be parsed, falls to text extraction."""
    mock_block = MagicMock()
    mock_block.type = "tool_use"
    mock_block.name = "other_tool"
    mock_block.input = {"name": "Alice", "age": 30}

    text_block = MagicMock()
    text_block.type = "text"
    text_block.text = '{"name": "Bob", "age": 25}'

    mock_response = MagicMock()
    mock_response.content = [mock_block, text_block]

    result = so_module.parse_claude_tool_response(mock_response, SimpleModel)
    assert result.name == "Bob"


def test_so_parse_claude_tool_response_text_json(so_module):
    text_block = MagicMock()
    text_block.type = "text"
    text_block.text = '{"name": "Charlie", "age": 40}'

    mock_response = MagicMock()
    mock_response.content = [text_block]

    result = so_module.parse_claude_tool_response(mock_response, SimpleModel)
    assert result.name == "Charlie"
    assert result.age == 40


def test_so_parse_claude_tool_response_no_content_raises(so_module):
    mock_response = MagicMock()
    mock_response.content = []
    with pytest.raises(ValueError):
        so_module.parse_claude_tool_response(mock_response, SimpleModel)


def test_so_parse_gemini_json_response_text(so_module):
    mock_response = MagicMock()
    mock_response.text = '{"name": "Gemini", "age": 1}'

    result = so_module.parse_gemini_json_response(mock_response, SimpleModel)
    assert result.name == "Gemini"


def test_so_parse_gemini_json_response_markdown_block(so_module):
    mock_response = MagicMock()
    mock_response.text = '```json\n{"name": "Block", "age": 5}\n```'

    result = so_module.parse_gemini_json_response(mock_response, SimpleModel)
    assert result.name == "Block"


def test_so_parse_gemini_json_response_no_text_raises(so_module):
    mock_response = MagicMock(spec=[])  # no .text attribute
    mock_response.candidates = []
    with pytest.raises(ValueError):
        so_module.parse_gemini_json_response(mock_response, SimpleModel)


# ---------------------------------------------------------------------------
# GROUP G: EmailTrackingService (unit — mocked DB)
# ---------------------------------------------------------------------------

@pytest.fixture
def email_tracking_svc():
    try:
        from app.domains.communication.services.email_tracking_service import EmailTrackingService
        return EmailTrackingService()
    except ImportError as exc:
        pytest.skip(f"email_tracking_service not importable: {exc}")


@pytest.fixture
def email_tracking_module():
    try:
        from app.services import email_tracking_service
        return email_tracking_service
    except ImportError as exc:
        pytest.skip(f"email_tracking_service not importable: {exc}")


def test_email_tracking_generate_token_returns_string(email_tracking_svc):
    token = email_tracking_svc.generate_tracking_token("notif-1", "company-1")
    assert isinstance(token, str)
    assert len(token) > 0


def test_email_tracking_generate_token_unique(email_tracking_svc):
    t1 = email_tracking_svc.generate_tracking_token("notif-1", "company-1")
    t2 = email_tracking_svc.generate_tracking_token("notif-1", "company-1")
    assert t1 != t2


def test_email_tracking_hash_ip(email_tracking_module):
    result = email_tracking_module._hash_ip("192.168.1.1")
    expected = hashlib.sha256("192.168.1.1".encode()).hexdigest()
    assert result == expected


def test_email_tracking_hash_ip_none(email_tracking_module):
    result = email_tracking_module._hash_ip(None)
    assert result is None


def test_email_tracking_hash_email(email_tracking_module):
    result = email_tracking_module._hash_email("user@test.com")
    expected = hashlib.sha256("user@test.com".encode()).hexdigest()
    assert result == expected


def test_email_tracking_hash_email_none(email_tracking_module):
    result = email_tracking_module._hash_email(None)
    assert result is None


def test_email_tracking_sha256(email_tracking_module):
    result = email_tracking_module._sha256("hello")
    assert result == hashlib.sha256("hello".encode()).hexdigest()


@pytest.mark.asyncio
async def test_email_tracking_record_open_invalid_token(email_tracking_svc):
    """When token not found in DB, record_open returns False."""
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result

    result = await email_tracking_svc.record_open(mock_db, "invalid-token", ip="1.2.3.4")
    assert result is False


@pytest.mark.asyncio
async def test_email_tracking_record_open_valid_token(email_tracking_svc):
    """When token found, record_open creates open event and returns True."""
    mock_base_event = MagicMock()
    mock_base_event.notification_id = "notif-1"
    mock_base_event.company_id = "company-1"
    mock_base_event.recipient_hash = "abc123"

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_base_event

    mock_db = AsyncMock()
    mock_db.execute.return_value = mock_result
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()

    result = await email_tracking_svc.record_open(mock_db, "valid-token", ip="1.2.3.4")
    assert result is True
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_email_tracking_record_click_invalid_token(email_tracking_svc):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None

    mock_db = AsyncMock()
    mock_db.execute.return_value = mock_result

    result = await email_tracking_svc.record_click(mock_db, "bad-token", "https://example.com")
    assert result is None


@pytest.mark.asyncio
async def test_email_tracking_record_click_valid_token(email_tracking_svc):
    mock_base_event = MagicMock()
    mock_base_event.notification_id = "notif-1"
    mock_base_event.company_id = "company-1"
    mock_base_event.recipient_hash = "abc123"

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_base_event

    mock_db = AsyncMock()
    mock_db.execute.return_value = mock_result
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()

    result = await email_tracking_svc.record_click(mock_db, "valid-token", "https://example.com")
    assert result == "https://example.com"
    mock_db.add.assert_called_once()


@pytest.mark.asyncio
async def test_email_tracking_create_tracking_token(email_tracking_svc):
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_db.flush = AsyncMock()

    token = await email_tracking_svc.create_tracking_token(mock_db, "notif-1", "company-1", "user@test.com")
    assert isinstance(token, str)
    assert len(token) > 0
    mock_db.add.assert_called_once()
    mock_db.flush.assert_called_once()


# ---------------------------------------------------------------------------
# GROUP H: TrainingDataService (unit — mocked DB + feedback)
# ---------------------------------------------------------------------------

@pytest.fixture
def training_module():
    try:
        from app.services import training_data_service
        return training_data_service
    except ImportError as exc:
        pytest.skip(f"training_data_service not importable: {exc}")


@pytest.fixture
def training_svc(training_module):
    db = AsyncMock()
    return training_module.TrainingDataService(db=db)


def test_training_svc_constants(training_module):
    assert hasattr(training_module, "SYSTEM_PROMPT_FOR_TRAINING")
    assert hasattr(training_module, "ERROR_PATTERNS")
    assert len(training_module.ERROR_PATTERNS) > 0


def test_training_svc_error_patterns_content(training_module):
    assert "erro" in training_module.ERROR_PATTERNS or "error" in training_module.ERROR_PATTERNS


def test_training_svc_is_quality_response_good(training_svc):
    feedback = MagicMock()
    feedback.lia_response = "A" * 100  # > MIN_RESPONSE_LENGTH
    feedback.thumbs = "up"
    feedback.rating = None
    feedback.confidence_score = None
    assert training_svc._is_quality_response(feedback) is True


def test_training_svc_is_quality_response_high_rating(training_svc):
    feedback = MagicMock()
    feedback.lia_response = "B" * 100
    feedback.thumbs = "down"
    feedback.rating = 5
    feedback.confidence_score = None
    assert training_svc._is_quality_response(feedback) is True


def test_training_svc_is_quality_response_too_short(training_svc):
    feedback = MagicMock()
    feedback.lia_response = "short"
    feedback.thumbs = "up"
    feedback.rating = 5
    feedback.confidence_score = None
    assert training_svc._is_quality_response(feedback) is False


def test_training_svc_is_quality_response_error_pattern(training_svc, training_module):
    feedback = MagicMock()
    feedback.lia_response = "A" * 100 + " erro ao processar"
    feedback.thumbs = "up"
    feedback.rating = 5
    feedback.confidence_score = None
    assert training_svc._is_quality_response(feedback) is False


def test_training_svc_is_quality_response_low_confidence(training_svc):
    feedback = MagicMock()
    feedback.lia_response = "C" * 100
    feedback.thumbs = "up"
    feedback.rating = 5
    feedback.confidence_score = 0.3  # < MIN_CONFIDENCE_SCORE
    assert training_svc._is_quality_response(feedback) is False


def test_training_svc_is_quality_response_no_response(training_svc):
    feedback = MagicMock()
    feedback.lia_response = None
    feedback.thumbs = "up"
    feedback.rating = 5
    feedback.confidence_score = None
    assert training_svc._is_quality_response(feedback) is False


def test_training_svc_is_quality_response_bad_thumbs_no_rating(training_svc):
    feedback = MagicMock()
    feedback.lia_response = "D" * 100
    feedback.thumbs = "down"
    feedback.rating = 2
    feedback.confidence_score = None
    assert training_svc._is_quality_response(feedback) is False


def test_training_svc_min_response_length(training_module):
    svc = training_module.TrainingDataService(db=AsyncMock())
    assert svc.MIN_RESPONSE_LENGTH == 50


def test_training_svc_min_confidence_score(training_module):
    svc = training_module.TrainingDataService(db=AsyncMock())
    assert svc.MIN_CONFIDENCE_SCORE == 0.7


# ---------------------------------------------------------------------------
# GROUP I: SuggestionInteractionService (unit — regex detection)
# ---------------------------------------------------------------------------

@pytest.fixture
def suggestion_module():
    try:
        from app.services import suggestion_interaction_service
        return suggestion_interaction_service
    except ImportError as exc:
        pytest.skip(f"suggestion_interaction_service not importable: {exc}")


@pytest.fixture
def suggestion_svc(suggestion_module):
    with patch("app.services.suggestion_interaction_service.skills_catalog_service"):
        svc = suggestion_module.SuggestionInteractionService()
    return svc


def test_suggestion_svc_detect_empty_message(suggestion_svc):
    result = suggestion_svc.detect_interactions("", [])
    assert result == []


def test_suggestion_svc_detect_whitespace(suggestion_svc):
    result = suggestion_svc.detect_interactions("   ", [])
    assert result == []


def test_suggestion_svc_detect_accept_pattern(suggestion_svc, suggestion_module):
    msg = "aceito a sugestão de Python"
    result = suggestion_svc._detect_via_regex(msg)
    types = [i.interaction_type for i in result]
    assert suggestion_module.SuggestionInteractionType.ACCEPT in types


def test_suggestion_svc_detect_reject_pattern(suggestion_svc, suggestion_module):
    msg = "não preciso de JavaScript"
    result = suggestion_svc._detect_via_regex(msg)
    types = [i.interaction_type for i in result]
    assert suggestion_module.SuggestionInteractionType.REJECT in types


def test_suggestion_svc_detect_clean_message_returns_list(suggestion_svc):
    msg = "Quais são as competências necessárias?"
    result = suggestion_svc._detect_via_regex(msg)
    assert isinstance(result, list)


def test_suggestion_svc_patterns_exist(suggestion_module):
    assert hasattr(suggestion_module, "ACCEPT_PATTERN")
    assert hasattr(suggestion_module, "REJECT_PATTERN")
    assert hasattr(suggestion_module, "REPLACE_PATTERN")
    assert hasattr(suggestion_module, "ADJUST_LEVEL_PATTERN")
    assert hasattr(suggestion_module, "CLARIFY_PATTERN")


def test_suggestion_svc_level_mapping_exists(suggestion_module):
    assert hasattr(suggestion_module, "LEVEL_MAPPING")
    assert "obrigatório" in suggestion_module.LEVEL_MAPPING or "obrigatorio" in suggestion_module.LEVEL_MAPPING


def test_suggestion_svc_parse_level_obrigatorio(suggestion_svc, suggestion_module):
    from app.schemas.job_description import RequirementLevel
    level = suggestion_svc._parse_level("obrigatorio")
    assert level == RequirementLevel.REQUIRED


def test_suggestion_svc_parse_level_diferencial(suggestion_svc, suggestion_module):
    from app.schemas.job_description import RequirementLevel
    level = suggestion_svc._parse_level("diferencial")
    assert level == RequirementLevel.NICE_TO_HAVE


def test_suggestion_svc_parse_level_unknown(suggestion_svc):
    level = suggestion_svc._parse_level("desconhecido")
    assert level is None


def test_suggestion_svc_fuzzy_threshold(suggestion_svc):
    assert suggestion_svc.FUZZY_MATCH_THRESHOLD == 0.7


# ---------------------------------------------------------------------------
# GROUP J: LGPD Cleanup Service (unit — mocked AsyncSessionLocal)
# ---------------------------------------------------------------------------

@pytest.fixture
def lgpd_module():
    try:
        from app.services import lgpd_cleanup_service
        return lgpd_cleanup_service
    except ImportError as exc:
        pytest.skip(f"lgpd_cleanup_service not importable: {exc}")


def test_lgpd_retention_days_exists(lgpd_module):
    assert hasattr(lgpd_module, "RETENTION_DAYS")
    rd = lgpd_module.RETENTION_DAYS
    assert isinstance(rd, dict)


def test_lgpd_retention_days_rejected(lgpd_module):
    assert lgpd_module.RETENTION_DAYS["rejected"] == 90


def test_lgpd_retention_days_withdrawn(lgpd_module):
    assert lgpd_module.RETENTION_DAYS["withdrawn"] == 90


def test_lgpd_retention_days_screening_logs(lgpd_module):
    assert lgpd_module.RETENTION_DAYS["screening_logs"] == 365


def test_lgpd_retention_days_ai_logs(lgpd_module):
    assert "ai_logs" in lgpd_module.RETENTION_DAYS


def test_lgpd_schedule_deletion_returns_datetime(lgpd_module):
    """schedule_deletion_for_candidate returns a datetime object."""
    import asyncio
    from datetime import datetime

    mock_candidate = MagicMock()
    mock_candidate.scheduled_deletion_at = None

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_candidate

    mock_db = AsyncMock()
    mock_db.execute.return_value = mock_result
    mock_db.commit = AsyncMock()

    candidate_id = "00000000-0000-0000-0000-000000000001"

    result = asyncio.run(
        lgpd_module.schedule_deletion_for_candidate(mock_db, candidate_id, "rejected")
    )
    assert isinstance(result, datetime)


def test_lgpd_schedule_deletion_uses_default_days(lgpd_module):
    """When no retention_days given, uses RETENTION_DAYS[reason]."""
    import asyncio
    from datetime import datetime, timedelta

    mock_candidate = MagicMock()

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_candidate

    mock_db = AsyncMock()
    mock_db.execute.return_value = mock_result
    mock_db.commit = AsyncMock()

    candidate_id = "00000000-0000-0000-0000-000000000002"
    before = datetime.utcnow()
    result = asyncio.run(
        lgpd_module.schedule_deletion_for_candidate(mock_db, candidate_id, "rejected")
    )
    expected_min = before + timedelta(days=89)
    expected_max = before + timedelta(days=91)
    assert expected_min <= result <= expected_max


def test_lgpd_schedule_deletion_custom_days(lgpd_module):
    import asyncio
    from datetime import datetime, timedelta

    mock_candidate = MagicMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_candidate

    mock_db = AsyncMock()
    mock_db.execute.return_value = mock_result
    mock_db.commit = AsyncMock()

    candidate_id = "00000000-0000-0000-0000-000000000003"
    before = datetime.utcnow()
    result = asyncio.run(
        lgpd_module.schedule_deletion_for_candidate(mock_db, candidate_id, "rejected", retention_days=30)
    )
    expected_min = before + timedelta(days=29)
    expected_max = before + timedelta(days=31)
    assert expected_min <= result <= expected_max


def test_lgpd_schedule_deletion_no_candidate_found(lgpd_module):
    """When candidate not found, still returns datetime but no commit."""
    import asyncio
    from datetime import datetime

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None

    mock_db = AsyncMock()
    mock_db.execute.return_value = mock_result
    mock_db.commit = AsyncMock()

    candidate_id = "00000000-0000-0000-0000-000000000004"
    result = asyncio.run(
        lgpd_module.schedule_deletion_for_candidate(mock_db, candidate_id, "rejected")
    )
    assert isinstance(result, datetime)
    mock_db.commit.assert_not_called()


@pytest.mark.asyncio
async def test_lgpd_run_cleanup_dry_run_returns_summary(lgpd_module):
    """run_cleanup(dry_run=True) returns summary dict with expected keys."""
    mock_session = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    # Return empty result sets for all 3 selects
    mock_result = MagicMock()
    mock_result.all.return_value = []
    mock_session.execute.return_value = mock_result

    with patch("app.domains.lgpd.services.lgpd_cleanup_service.AsyncSessionLocal", return_value=mock_session):
        summary = await lgpd_module.run_cleanup(dry_run=True)

    assert "dry_run" in summary
    assert summary["dry_run"] is True
    assert "candidates_deleted" in summary
    assert "vacancy_candidates_deleted" in summary
    assert "errors" in summary


@pytest.mark.asyncio
async def test_lgpd_run_cleanup_summary_keys(lgpd_module):
    mock_session = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    mock_result = MagicMock()
    mock_result.all.return_value = []
    mock_session.execute.return_value = mock_result

    with patch("app.domains.lgpd.services.lgpd_cleanup_service.AsyncSessionLocal", return_value=mock_session):
        summary = await lgpd_module.run_cleanup(dry_run=True)

    expected_keys = {"dry_run", "ran_at", "candidates_deleted", "vacancy_candidates_deleted", "errors"}
    for key in expected_keys:
        assert key in summary, f"Missing summary key: {key}"


@pytest.mark.asyncio
async def test_lgpd_run_cleanup_no_deletions_when_dry_run(lgpd_module):
    mock_session = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    mock_result = MagicMock()
    # Simulate 2 candidates to delete
    mock_row = MagicMock()
    from datetime import datetime
    mock_row.id = "id-1"
    mock_row.company_id = "company-1"
    mock_row.scheduled_deletion_at = datetime.utcnow()
    mock_result.all.return_value = [mock_row, mock_row]
    mock_session.execute.return_value = mock_result

    with patch("app.domains.lgpd.services.lgpd_cleanup_service.AsyncSessionLocal", return_value=mock_session):
        summary = await lgpd_module.run_cleanup(dry_run=True)

    # In dry_run mode: candidates_deleted counts them but no actual delete
    assert summary["candidates_deleted"] == 2
    # commit should NOT have been called for actual deletion
    mock_session.commit.assert_not_called()
