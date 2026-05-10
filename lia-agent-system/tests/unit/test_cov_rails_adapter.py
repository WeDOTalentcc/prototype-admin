"""Coverage tests for rails_adapter.py — pure mapping functions and static methods."""
import pytest

from app.domains.integrations_hub.services.rails_adapter import (
    CANDIDATE_FORK_TO_RAILS,
    CANDIDATE_RAILS_TO_FORK,
    JOB_FORK_TO_RAILS,
    APPLY_FORK_TO_RAILS,
    SELECTIVE_PROCESS_FORK_TO_RAILS,
    USER_FORK_TO_RAILS,
    MESSAGE_FORK_TO_RAILS,
    rails_candidate_to_fork,
    rails_job_to_fork,
    rails_apply_to_fork,
    rails_selective_process_to_fork,
    rails_message_to_fork,
    RailsAdapter,
)


# ─── Module-level constants ───────────────────────────────────────────────────

class TestConstants:
    def test_candidate_fork_to_rails_has_required_fields(self):
        assert "email" in CANDIDATE_FORK_TO_RAILS
        assert "id" in CANDIDATE_FORK_TO_RAILS
        assert "name" in CANDIDATE_FORK_TO_RAILS

    def test_candidate_rails_to_fork_is_inverse(self):
        # Built from {v: k for k, v in CANDIDATE_FORK_TO_RAILS.items() if isinstance(v, str)}
        assert isinstance(CANDIDATE_RAILS_TO_FORK, dict)
        # Spot-check one inversion
        assert CANDIDATE_RAILS_TO_FORK.get("email") == "email"

    def test_job_fork_to_rails_has_required_fields(self):
        assert "title" in JOB_FORK_TO_RAILS
        assert "status" in JOB_FORK_TO_RAILS

    def test_apply_fork_to_rails_has_fields(self):
        assert "id" in APPLY_FORK_TO_RAILS
        assert "candidate_id" in APPLY_FORK_TO_RAILS

    def test_selective_process_fork_to_rails_has_fields(self):
        assert "id" in SELECTIVE_PROCESS_FORK_TO_RAILS
        assert "name" in SELECTIVE_PROCESS_FORK_TO_RAILS

    def test_user_fork_to_rails_has_fields(self):
        assert "id" in USER_FORK_TO_RAILS
        assert "email" in USER_FORK_TO_RAILS

    def test_message_fork_to_rails_has_fields(self):
        assert "id" in MESSAGE_FORK_TO_RAILS
        assert "content" in MESSAGE_FORK_TO_RAILS


# ─── rails_candidate_to_fork ─────────────────────────────────────────────────

class TestRailsCandidateToFork:
    def test_empty_input_returns_empty(self):
        assert rails_candidate_to_fork({}) == {}

    def test_none_input_returns_empty(self):
        assert rails_candidate_to_fork(None) == {}  # type: ignore

    def test_basic_fields_mapped(self):
        result = rails_candidate_to_fork({"id": 42, "name": "João", "email": "j@ex.com"})
        assert result["id"] == "42"
        assert result["rails_id"] == 42
        assert result["name"] == "João"
        assert result["email"] == "j@ex.com"
        assert result["_source"] == "rails"

    def test_full_name_constructed(self):
        result = rails_candidate_to_fork({"id": 1, "name": "João", "surname": "Silva"})
        assert result["full_name"] == "João Silva"

    def test_full_name_no_surname(self):
        result = rails_candidate_to_fork({"id": 1, "name": "Maria"})
        assert result["full_name"] == "Maria"

    def test_id_none_becomes_empty_string(self):
        result = rails_candidate_to_fork({"id": None, "name": "Test"})
        assert result["id"] == ""

    def test_linkedin_field_mapping(self):
        result = rails_candidate_to_fork({"id": 1, "linkedin": "https://linkedin.com/in/joao"})
        assert result["linkedin_url"] == "https://linkedin.com/in/joao"

    def test_location_fields_mapped(self):
        result = rails_candidate_to_fork({
            "id": 1, "city": "São Paulo", "state": "SP", "country": "Brasil"
        })
        assert result["location_city"] == "São Paulo"
        assert result["location_state"] == "SP"
        assert result["location_country"] == "Brasil"

    def test_salary_fields_mapped(self):
        result = rails_candidate_to_fork({"id": 1, "desired_salary": 8000})
        assert result["desired_salary_min"] == 8000

    def test_resume_fields_mapped(self):
        result = rails_candidate_to_fork({
            "id": 1,
            "curriculum_text": "cv text",
            "curriculum_pdf_url": "http://s3/cv.pdf",
        })
        assert result["resume_text"] == "cv text"
        assert result["resume_url"] == "http://s3/cv.pdf"

    def test_currency_default_brl(self):
        result = rails_candidate_to_fork({"id": 1})
        assert result.get("salary_currency") == "BRL"

    def test_number_coerced_to_str(self):
        result = rails_candidate_to_fork({"id": 1, "number": 123})
        assert result["address_number"] == "123"

    def test_null_fields_excluded(self):
        result = rails_candidate_to_fork({"id": 1})
        assert "linkedin_url" not in result  # None values filtered out

    def test_rails_only_fields_preserved(self):
        result = rails_candidate_to_fork({"id": 1, "uid": "uid123", "comments": "note"})
        assert result.get("uid") == "uid123"
        assert result.get("comments") == "note"


# ─── rails_job_to_fork ────────────────────────────────────────────────────────

class TestRailsJobToFork:
    def test_empty_input_returns_empty(self):
        assert rails_job_to_fork({}) == {}

    def test_none_input_returns_empty(self):
        assert rails_job_to_fork(None) == {}  # type: ignore

    def test_basic_fields_mapped(self):
        result = rails_job_to_fork({"id": 10, "title": "Backend Dev"})
        assert result["id"] == "10"
        assert result["rails_id"] == 10
        assert result["title"] == "Backend Dev"
        assert result["_source"] == "rails"

    def test_status_active(self):
        result = rails_job_to_fork({"id": 1, "status": True})
        assert result["status"] == "Ativa"

    def test_status_draft(self):
        result = rails_job_to_fork({"id": 1, "status": False})
        assert result["status"] == "Rascunho"

    def test_location_constructed(self):
        result = rails_job_to_fork({"id": 1, "city": "SP", "state": "SP"})
        assert "SP" in result["location"]

    def test_work_model_remote(self):
        result = rails_job_to_fork({"id": 1, "is_remote": True})
        assert result["work_model"] == "remoto"

    def test_work_model_from_workplace_type(self):
        result = rails_job_to_fork({"id": 1, "workplace_type": "hibrido"})
        assert result["work_model"] == "hibrido"

    def test_visibility_defaults_public(self):
        result = rails_job_to_fork({"id": 1})
        assert result["visibility"] == "public"

    def test_access_list_defaults_empty(self):
        result = rails_job_to_fork({"id": 1})
        assert result["access_list"] == []

    def test_id_none_becomes_empty_string(self):
        result = rails_job_to_fork({"id": None})
        assert result["id"] == ""


# ─── rails_apply_to_fork ─────────────────────────────────────────────────────

class TestRailsApplyToFork:
    def test_empty_input_returns_empty(self):
        assert rails_apply_to_fork({}) == {}

    def test_basic_mapping(self):
        result = rails_apply_to_fork({
            "id": 5, "candidate_id": 10, "job_id": 20,
            "selective_process_id": 30, "is_deleted": False,
        })
        assert result["id"] == "5"
        assert result["rails_id"] == 5
        assert result["candidate_id"] == 10
        assert result["job_id"] == 20
        assert result["stage_id"] == 30
        assert result["is_active"] is True

    def test_is_deleted_inverts_is_active(self):
        result = rails_apply_to_fork({"id": 5, "is_deleted": True})
        assert result["is_active"] is False


# ─── rails_selective_process_to_fork ─────────────────────────────────────────

class TestRailsSelectiveProcessToFork:
    def test_empty_input_returns_empty(self):
        assert rails_selective_process_to_fork({}) == {}

    def test_basic_mapping(self):
        result = rails_selective_process_to_fork({
            "id": 7, "name": "Stage 1", "position": 1,
            "job_id": 100, "status": 0, "sub_status": {"a": 1},
        })
        assert result["id"] == "7"
        assert result["name"] == "Stage 1"
        assert result["position"] == 1
        assert result["sub_stages"] == {"a": 1}


# ─── rails_message_to_fork ───────────────────────────────────────────────────

class TestRailsMessageToFork:
    def test_empty_input_returns_empty(self):
        assert rails_message_to_fork({}) == {}

    def test_basic_mapping(self):
        result = rails_message_to_fork({
            "id": 99, "content": "Hello", "entity": "recruiter",
            "account_id": "abc",
        })
        assert result["id"] == "99"
        assert result["content"] == "Hello"
        assert result["entity"] == "recruiter"


# ─── RailsAdapter static methods ─────────────────────────────────────────────

class TestRailsAdapterStatics:
    def test_to_rails_id_valid(self):
        assert RailsAdapter._to_rails_id("42") == 42

    def test_to_rails_id_not_digit(self):
        assert RailsAdapter._to_rails_id("abc") is None

    def test_to_rails_id_empty(self):
        assert RailsAdapter._to_rails_id("") is None

    def test_to_rails_id_none(self):
        assert RailsAdapter._to_rails_id(None) is None  # type: ignore

    def test_looks_like_uuid_valid(self):
        uuid = "550e8400-e29b-41d4-a716-446655440000"
        assert RailsAdapter._looks_like_uuid(uuid) is True

    def test_looks_like_uuid_short(self):
        assert RailsAdapter._looks_like_uuid("12345") is False

    def test_looks_like_uuid_wrong_dashes(self):
        assert RailsAdapter._looks_like_uuid("550e8400xe29bx41d4xa716x446655440000") is False

    def test_looks_like_uuid_empty(self):
        assert RailsAdapter._looks_like_uuid("") is False

    def test_looks_like_uuid_none(self):
        assert RailsAdapter._looks_like_uuid(None) is False  # type: ignore
