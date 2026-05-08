"""
R-016 — Rails field mapping contract tests.

These tests pin the *required fields* that LIA's mapper functions extract from
Rails HTTP responses. If Rails renames or removes a field, these tests fail
before the gap reaches production.

Pattern: provide a canonical Rails payload → call the mapper → assert that the
output contains every expected key (or that a missing required field is
detectable as absent/None).

Mapper source: app/domains/integrations_hub/services/rails_adapter.py

Why these fields matter:
- Silent None-filter: each mapper uses ``{k: v for k, v in result.items() if v
  is not None}`` — so a renamed Rails field produces a missing key in the
  output dict (no KeyError at call time, silent regression instead).
- Contract tests make that silent failure loud.

Additive safety: Rails can ADD new fields without breaking these tests.
Only RENAMES or REMOVALS of listed fields will cause failures.
"""
from __future__ import annotations

import pytest

from app.domains.integrations_hub.services.rails_adapter import (
    rails_apply_to_fork,
    rails_candidate_to_fork,
    rails_job_to_fork,
    rails_message_to_fork,
    rails_selective_process_to_fork,
)


# ──────────────────────────────────────────────────────────────────
# Canonical Rails payload fixtures
# Fields are taken directly from the mapper's data.get("...") calls
# ──────────────────────────────────────────────────────────────────

CANONICAL_RAILS_CANDIDATE = {
    # IDs
    "id": 101,
    # Basic identity
    "name": "Ana",
    "surname": "Lima",
    "email": "ana@example.com",
    "secondary_email": "ana2@example.com",
    "phone": "+55 11 9999-0001",
    "mobile_phone": "+55 11 99999-0001",
    # Professional
    "role_name": "Engenheira de Software",
    "position_level": "senior",
    "current_company": "TechCorp",
    "self_introduction": "Apaixonada por Python.",
    "curriculum_text": "10 anos de experiência...",
    "curriculum_pdf_url": "https://cdn.example.com/cv.pdf",
    # Location
    "city": "São Paulo",
    "state": "SP",
    "country": "Brasil",
    # Salary
    "current_salary": 12000,
    "desired_salary": 15000,
    "currency": "BRL",
    # Preferences
    "remote_work": True,
    "mobility": False,
    # Source
    "source": "linkedin",
    # Rails-only
    "uid": "uid-abc123",
    "completed_register": True,
    "accept_terms": True,
}

CANONICAL_RAILS_JOB = {
    "id": 42,
    "title": "Engenheiro Python Sênior",
    "description": "Trabalhe em produtos de IA de RH.",
    "city": "São Paulo",
    "state": "SP",
    "is_remote": False,
    "workplace_type": "hibrido",
    "status": True,  # Rails boolean: True → "Ativa"
    # Visibility / auth
    "visibility": "internal",
    "is_confidential": False,
    "created_by": "recruiter@company.com",
    "recruiter_email": "recruiter@company.com",
    "access_list": ["recruiter@company.com"],
    # Rails-only
    "provider": "greenhouse",
    "provider_job_id": "gh-99",
    "application_deadline": "2026-06-30",
}

CANONICAL_RAILS_APPLY = {
    "id": 7,
    "candidate_id": 101,
    "job_id": 42,
    "selective_process_id": 5,
    "is_deleted": False,
}

CANONICAL_RAILS_SELECTIVE_PROCESS = {
    "id": 5,
    "name": "Triagem Inicial",
    "position": 1,
    "job_id": 42,
    "status": "active",
    "sub_status": ["aguardando_cv", "em_revisao"],
}

CANONICAL_RAILS_MESSAGE = {
    "id": 303,
    "content": "Olá, candidata! Parabéns pela aprovação.",
    "entity": "candidate",
    "status": "sent",
    "parent_message_id": None,
    "reference_type": "apply",
    "reference_id": 7,
    "metadata": {"source": "automated"},
    "account_id": "acct-456",
}


# ──────────────────────────────────────────────────────────────────
# rails_candidate_to_fork
# ──────────────────────────────────────────────────────────────────

class TestCandidateMapper:
    """Contract tests for rails_candidate_to_fork()."""

    def test_id_is_string(self):
        result = rails_candidate_to_fork(CANONICAL_RAILS_CANDIDATE)
        assert result["id"] == "101"

    def test_rails_id_is_int(self):
        result = rails_candidate_to_fork(CANONICAL_RAILS_CANDIDATE)
        assert result["rails_id"] == 101

    def test_source_marker_is_rails(self):
        result = rails_candidate_to_fork(CANONICAL_RAILS_CANDIDATE)
        assert result["_source"] == "rails"

    def test_required_identity_fields_present(self):
        result = rails_candidate_to_fork(CANONICAL_RAILS_CANDIDATE)
        for field in ("name", "surname", "email"):
            assert field in result, f"Required field '{field}' missing from candidate output"

    def test_full_name_is_concatenated(self):
        result = rails_candidate_to_fork(CANONICAL_RAILS_CANDIDATE)
        assert result["full_name"] == "Ana Lima"

    def test_professional_fields_mapped(self):
        result = rails_candidate_to_fork(CANONICAL_RAILS_CANDIDATE)
        # Rails "role_name" → LIA "current_title"
        assert result["current_title"] == "Engenheira de Software"
        # Rails "position_level" → LIA "seniority_level"
        assert result["seniority_level"] == "senior"
        # Rails "curriculum_text" → LIA "resume_text"
        assert result["resume_text"] == "10 anos de experiência..."
        # Rails "curriculum_pdf_url" → LIA "resume_url"
        assert result["resume_url"] == "https://cdn.example.com/cv.pdf"

    def test_location_fields_mapped(self):
        result = rails_candidate_to_fork(CANONICAL_RAILS_CANDIDATE)
        assert result["location_city"] == "São Paulo"
        assert result["location_state"] == "SP"
        assert result["location_country"] == "Brasil"

    def test_salary_fields_mapped(self):
        result = rails_candidate_to_fork(CANONICAL_RAILS_CANDIDATE)
        assert result["current_salary"] == 12000
        # Rails "desired_salary" → LIA "desired_salary_min"
        assert result["desired_salary_min"] == 15000
        assert result["salary_currency"] == "BRL"

    def test_empty_payload_returns_empty_dict(self):
        assert rails_candidate_to_fork({}) == {}
        assert rails_candidate_to_fork(None) == {}  # type: ignore[arg-type]

    def test_missing_email_is_detectable(self):
        """If Rails renames 'email', it silently disappears from output."""
        payload = {**CANONICAL_RAILS_CANDIDATE}
        del payload["email"]
        result = rails_candidate_to_fork(payload)
        # email defaults to "" (empty string) so it's filtered out by the None-filter
        # An empty string is NOT None, so it stays — but if Rails renames it
        # we would get "" not the real value. Assert it's not the real email.
        assert result.get("email") != "ana@example.com"

    def test_missing_name_is_detectable(self):
        """If Rails renames 'name', full_name will be broken."""
        payload = {**CANONICAL_RAILS_CANDIDATE}
        del payload["name"]
        result = rails_candidate_to_fork(payload)
        # full_name will be just the surname
        assert result.get("full_name") == "Lima"

    def test_renamed_role_name_breaks_current_title(self):
        """Simulates Rails renaming 'role_name' → 'job_title'."""
        payload = {**CANONICAL_RAILS_CANDIDATE}
        del payload["role_name"]
        result = rails_candidate_to_fork(payload)
        # current_title maps from "role_name" — if renamed, it goes None → filtered
        assert "current_title" not in result

    def test_renamed_curriculum_text_breaks_resume_text(self):
        """Simulates Rails renaming 'curriculum_text' → 'resume'."""
        payload = {**CANONICAL_RAILS_CANDIDATE}
        del payload["curriculum_text"]
        result = rails_candidate_to_fork(payload)
        assert "resume_text" not in result

    def test_source_field_preserved(self):
        result = rails_candidate_to_fork(CANONICAL_RAILS_CANDIDATE)
        assert result["source"] == "linkedin"


# ──────────────────────────────────────────────────────────────────
# rails_job_to_fork
# ──────────────────────────────────────────────────────────────────

class TestJobMapper:
    """Contract tests for rails_job_to_fork()."""

    def test_id_is_string(self):
        result = rails_job_to_fork(CANONICAL_RAILS_JOB)
        assert result["id"] == "42"

    def test_rails_id_is_int(self):
        result = rails_job_to_fork(CANONICAL_RAILS_JOB)
        assert result["rails_id"] == 42

    def test_required_fields_present(self):
        result = rails_job_to_fork(CANONICAL_RAILS_JOB)
        for field in ("title", "description", "status", "_source"):
            assert field in result, f"Required field '{field}' missing from job output"

    def test_status_active_when_rails_boolean_true(self):
        result = rails_job_to_fork(CANONICAL_RAILS_JOB)
        assert result["status"] == "Ativa"

    def test_status_draft_when_rails_boolean_false(self):
        payload = {**CANONICAL_RAILS_JOB, "status": False}
        result = rails_job_to_fork(payload)
        assert result["status"] == "Rascunho"

    def test_work_model_remoto_when_is_remote_true(self):
        payload = {**CANONICAL_RAILS_JOB, "is_remote": True}
        result = rails_job_to_fork(payload)
        assert result["work_model"] == "remoto"

    def test_work_model_falls_back_to_workplace_type(self):
        result = rails_job_to_fork(CANONICAL_RAILS_JOB)
        assert result["work_model"] == "hibrido"

    def test_location_concatenated(self):
        result = rails_job_to_fork(CANONICAL_RAILS_JOB)
        assert "São Paulo" in result["location"]
        assert "SP" in result["location"]

    def test_visibility_and_auth_fields_present(self):
        """Confidentiality defense-in-depth requires these fields."""
        result = rails_job_to_fork(CANONICAL_RAILS_JOB)
        assert result["visibility"] == "internal"
        assert result["is_confidential"] is False
        assert result["created_by"] == "recruiter@company.com"
        assert result["recruiter_email"] == "recruiter@company.com"
        assert "access_list" in result

    def test_visibility_defaults_to_public_when_missing(self):
        payload = {**CANONICAL_RAILS_JOB}
        del payload["visibility"]
        result = rails_job_to_fork(payload)
        assert result["visibility"] == "public"

    def test_access_list_defaults_to_empty_list_when_missing(self):
        payload = {**CANONICAL_RAILS_JOB}
        del payload["access_list"]
        result = rails_job_to_fork(payload)
        assert result["access_list"] == []

    def test_empty_payload_returns_empty_dict(self):
        assert rails_job_to_fork({}) == {}
        assert rails_job_to_fork(None) == {}  # type: ignore[arg-type]

    def test_renamed_title_breaks_title(self):
        """Simulates Rails renaming 'title' → 'job_title'."""
        payload = {**CANONICAL_RAILS_JOB}
        del payload["title"]
        result = rails_job_to_fork(payload)
        # title defaults to "" — still present but empty
        assert result["title"] == ""

    def test_renamed_city_breaks_location(self):
        """Simulates Rails renaming 'city' → 'municipality'."""
        payload = {**CANONICAL_RAILS_JOB}
        del payload["city"]
        result = rails_job_to_fork(payload)
        # location is f-string; city will be empty
        assert "São Paulo" not in result.get("location", "")


# ──────────────────────────────────────────────────────────────────
# rails_apply_to_fork
# ──────────────────────────────────────────────────────────────────

class TestApplyMapper:
    """Contract tests for rails_apply_to_fork()."""

    def test_id_is_string(self):
        result = rails_apply_to_fork(CANONICAL_RAILS_APPLY)
        assert result["id"] == "7"

    def test_rails_id_is_int(self):
        result = rails_apply_to_fork(CANONICAL_RAILS_APPLY)
        assert result["rails_id"] == 7

    def test_required_fields_present(self):
        result = rails_apply_to_fork(CANONICAL_RAILS_APPLY)
        for field in ("candidate_id", "job_id", "stage_id", "is_active"):
            assert field in result, f"Required field '{field}' missing from apply output"

    def test_candidate_id_mapped(self):
        result = rails_apply_to_fork(CANONICAL_RAILS_APPLY)
        assert result["candidate_id"] == 101

    def test_job_id_mapped(self):
        result = rails_apply_to_fork(CANONICAL_RAILS_APPLY)
        assert result["job_id"] == 42

    def test_stage_id_from_selective_process_id(self):
        """Rails 'selective_process_id' → LIA 'stage_id'."""
        result = rails_apply_to_fork(CANONICAL_RAILS_APPLY)
        assert result["stage_id"] == 5

    def test_is_active_inverts_is_deleted(self):
        result = rails_apply_to_fork(CANONICAL_RAILS_APPLY)
        assert result["is_active"] is True

    def test_is_active_false_when_deleted(self):
        payload = {**CANONICAL_RAILS_APPLY, "is_deleted": True}
        result = rails_apply_to_fork(payload)
        assert result["is_active"] is False

    def test_renamed_selective_process_id_breaks_stage_id(self):
        """Simulates Rails renaming 'selective_process_id' → 'stage_id'.

        NOTE: rails_apply_to_fork does NOT use the None-filter pattern (it
        returns a plain dict literal). So when 'selective_process_id' is absent
        the key 'stage_id' is still present in the output, but its value is
        None — which means downstream code silently gets None instead of an
        integer. The contract pins this as the detectable failure mode.
        """
        payload = {**CANONICAL_RAILS_APPLY}
        del payload["selective_process_id"]
        result = rails_apply_to_fork(payload)
        # stage_id maps from selective_process_id; if renamed → value is None
        assert result.get("stage_id") is None

    def test_empty_payload_returns_empty_dict(self):
        assert rails_apply_to_fork({}) == {}
        assert rails_apply_to_fork(None) == {}  # type: ignore[arg-type]


# ──────────────────────────────────────────────────────────────────
# rails_selective_process_to_fork
# ──────────────────────────────────────────────────────────────────

class TestSelectiveProcessMapper:
    """Contract tests for rails_selective_process_to_fork()."""

    def test_id_is_string(self):
        result = rails_selective_process_to_fork(CANONICAL_RAILS_SELECTIVE_PROCESS)
        assert result["id"] == "5"

    def test_rails_id_is_int(self):
        result = rails_selective_process_to_fork(CANONICAL_RAILS_SELECTIVE_PROCESS)
        assert result["rails_id"] == 5

    def test_required_fields_present(self):
        result = rails_selective_process_to_fork(CANONICAL_RAILS_SELECTIVE_PROCESS)
        for field in ("name", "job_id", "status"):
            assert field in result, f"Required field '{field}' missing from selective_process output"

    def test_name_mapped(self):
        result = rails_selective_process_to_fork(CANONICAL_RAILS_SELECTIVE_PROCESS)
        assert result["name"] == "Triagem Inicial"

    def test_position_mapped(self):
        result = rails_selective_process_to_fork(CANONICAL_RAILS_SELECTIVE_PROCESS)
        assert result["position"] == 1

    def test_job_id_mapped(self):
        result = rails_selective_process_to_fork(CANONICAL_RAILS_SELECTIVE_PROCESS)
        assert result["job_id"] == 42

    def test_status_mapped(self):
        result = rails_selective_process_to_fork(CANONICAL_RAILS_SELECTIVE_PROCESS)
        assert result["status"] == "active"

    def test_sub_stages_from_sub_status(self):
        """Rails 'sub_status' → LIA 'sub_stages'."""
        result = rails_selective_process_to_fork(CANONICAL_RAILS_SELECTIVE_PROCESS)
        assert result["sub_stages"] == ["aguardando_cv", "em_revisao"]

    def test_renamed_sub_status_breaks_sub_stages(self):
        """Simulates Rails renaming 'sub_status' → 'sub_stage_list'.

        NOTE: rails_selective_process_to_fork does NOT use the None-filter
        pattern. When 'sub_status' is absent the key 'sub_stages' is still
        present but its value is None — detectable silent failure.
        """
        payload = {**CANONICAL_RAILS_SELECTIVE_PROCESS}
        del payload["sub_status"]
        result = rails_selective_process_to_fork(payload)
        # key is present but value is None — downstream code sees None list
        assert result.get("sub_stages") is None

    def test_empty_payload_returns_empty_dict(self):
        assert rails_selective_process_to_fork({}) == {}
        assert rails_selective_process_to_fork(None) == {}  # type: ignore[arg-type]


# ──────────────────────────────────────────────────────────────────
# rails_message_to_fork
# ──────────────────────────────────────────────────────────────────

class TestMessageMapper:
    """Contract tests for rails_message_to_fork()."""

    def test_id_is_string(self):
        result = rails_message_to_fork(CANONICAL_RAILS_MESSAGE)
        assert result["id"] == "303"

    def test_rails_id_is_int(self):
        result = rails_message_to_fork(CANONICAL_RAILS_MESSAGE)
        assert result["rails_id"] == 303

    def test_required_fields_present(self):
        result = rails_message_to_fork(CANONICAL_RAILS_MESSAGE)
        for field in ("content", "entity", "status"):
            assert field in result, f"Required field '{field}' missing from message output"

    def test_content_mapped(self):
        result = rails_message_to_fork(CANONICAL_RAILS_MESSAGE)
        assert result["content"] == "Olá, candidata! Parabéns pela aprovação."

    def test_entity_mapped(self):
        result = rails_message_to_fork(CANONICAL_RAILS_MESSAGE)
        assert result["entity"] == "candidate"

    def test_status_mapped(self):
        result = rails_message_to_fork(CANONICAL_RAILS_MESSAGE)
        assert result["status"] == "sent"

    def test_reference_fields_mapped(self):
        result = rails_message_to_fork(CANONICAL_RAILS_MESSAGE)
        assert result["reference_type"] == "apply"
        assert result["reference_id"] == 7

    def test_metadata_mapped(self):
        result = rails_message_to_fork(CANONICAL_RAILS_MESSAGE)
        assert result["metadata"] == {"source": "automated"}

    def test_account_id_mapped(self):
        result = rails_message_to_fork(CANONICAL_RAILS_MESSAGE)
        assert result["account_id"] == "acct-456"

    def test_parent_message_id_none_is_preserved(self):
        """rails_message_to_fork does NOT use the None-filter pattern.

        None values (like parent_message_id=None for top-level messages) are
        kept in the output dict. This means callers must handle None explicitly.
        This test pins that behaviour — if someone adds a None-filter later,
        this test will catch the behaviour change.
        """
        result = rails_message_to_fork(CANONICAL_RAILS_MESSAGE)
        # parent_message_id=None is preserved (no None-filter in this mapper)
        assert "parent_message_id" in result
        assert result["parent_message_id"] is None

    def test_renamed_content_breaks_content(self):
        """Simulates Rails renaming 'content' → 'body'."""
        payload = {**CANONICAL_RAILS_MESSAGE}
        del payload["content"]
        result = rails_message_to_fork(payload)
        # content defaults to "" — not None, so stays present but empty
        assert result["content"] == ""

    def test_renamed_entity_breaks_entity(self):
        """Simulates Rails renaming 'entity' → 'entity_type'.

        NOTE: rails_message_to_fork does NOT use the None-filter pattern, so
        when 'entity' is absent the key is still present with value None.
        Downstream code silently receives None instead of a string.
        """
        payload = {**CANONICAL_RAILS_MESSAGE}
        del payload["entity"]
        result = rails_message_to_fork(payload)
        # key exists but value is None — the detectable silent failure
        assert result.get("entity") is None

    def test_empty_payload_returns_empty_dict(self):
        assert rails_message_to_fork({}) == {}
        assert rails_message_to_fork(None) == {}  # type: ignore[arg-type]
