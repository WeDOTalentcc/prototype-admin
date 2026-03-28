"""
Extended unit tests for short_lists API helpers and schema validation.

Covers: _encode_meta / _decode_meta edge cases, _is_shortlist,
_to_short_list_response, schema validation, round-trip encoding,
router structure verification.
"""
import pytest

pytestmark = pytest.mark.medium

from datetime import datetime
from unittest.mock import MagicMock


# ---------------------------------------------------------------------------
# _encode_meta / _decode_meta — edge cases
# ---------------------------------------------------------------------------

class TestEncodeDecodeEdgeCases:
    def test_encode_with_empty_description(self):
        from app.api.v1.short_lists import _encode_meta
        result = _encode_meta("job-999", "")
        # empty description treated as falsy → no pipe appended
        assert result == "shortlist:job-999"

    def test_encode_with_whitespace_only_description(self):
        from app.api.v1.short_lists import _encode_meta
        # "   ".strip() truthy test: "   " is truthy in Python so it gets appended
        result = _encode_meta("job-001", "   ")
        assert "job-001" in result

    def test_decode_empty_string_returns_empties(self):
        from app.api.v1.short_lists import _decode_meta
        job_id, desc = _decode_meta("")
        assert job_id == ""
        assert desc == ""

    def test_decode_prefix_only(self):
        from app.api.v1.short_lists import _decode_meta
        job_id, desc = _decode_meta("shortlist:")
        assert job_id == ""
        assert desc == ""

    def test_decode_preserves_multi_word_description(self):
        from app.api.v1.short_lists import _decode_meta
        job_id, desc = _decode_meta("shortlist:job-42|Candidatos finalistas para Dev Sênior")
        assert job_id == "job-42"
        assert desc == "Candidatos finalistas para Dev Sênior"

    def test_encode_with_uuid_job_id(self):
        from app.api.v1.short_lists import _encode_meta, _decode_meta
        uuid_job = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        encoded = _encode_meta(uuid_job, "UUID job")
        decoded_job, decoded_desc = _decode_meta(encoded)
        assert decoded_job == uuid_job
        assert decoded_desc == "UUID job"

    def test_encode_decode_special_chars_in_job_id(self):
        from app.api.v1.short_lists import _encode_meta, _decode_meta
        # job_id with hyphens and numbers
        job_id = "job-2026-03-08"
        encoded = _encode_meta(job_id)
        decoded_job, decoded_desc = _decode_meta(encoded)
        assert decoded_job == job_id

    def test_decode_multiple_pipes_splits_on_first(self):
        from app.api.v1.short_lists import _decode_meta
        # "shortlist:job-1|desc|with|pipes"
        job_id, desc = _decode_meta("shortlist:job-1|desc|with|pipes")
        assert job_id == "job-1"
        # only first pipe splits job_id from desc
        assert "desc" in desc


# ---------------------------------------------------------------------------
# _is_shortlist
# ---------------------------------------------------------------------------

class TestIsShortlistExtended:
    def test_is_shortlist_with_full_description(self):
        from app.api.v1.short_lists import _is_shortlist
        record = MagicMock()
        record.description = "shortlist:job-123|Finalistas"
        assert _is_shortlist(record) is True

    def test_is_shortlist_with_prefix_only(self):
        from app.api.v1.short_lists import _is_shortlist
        record = MagicMock()
        record.description = "shortlist:job-456"
        assert _is_shortlist(record) is True

    def test_not_shortlist_with_random_text(self):
        from app.api.v1.short_lists import _is_shortlist
        record = MagicMock()
        record.description = "Lista genérica de candidatos"
        assert _is_shortlist(record) is False

    def test_not_shortlist_with_similar_prefix(self):
        from app.api.v1.short_lists import _is_shortlist
        record = MagicMock()
        record.description = "shortlisted:job-1"  # wrong prefix
        assert _is_shortlist(record) is False

    def test_not_shortlist_empty_description(self):
        from app.api.v1.short_lists import _is_shortlist
        record = MagicMock()
        record.description = ""
        assert _is_shortlist(record) is False


# ---------------------------------------------------------------------------
# _to_short_list_response — various scenarios
# ---------------------------------------------------------------------------

class TestToShortListResponse:
    def test_created_at_as_string(self):
        from app.api.v1.short_lists import _to_short_list_response
        record = MagicMock()
        record.id = "sl-str"
        record.description = "shortlist:j-1|Desc"
        record.name = "Test List"
        record.created_by = "user@test.com"
        record.created_at = datetime(2026, 1, 15, 9, 30, 0)
        record.members = []
        resp = _to_short_list_response(record)
        assert isinstance(resp.created_at, str)
        assert "2026" in resp.created_at

    def test_candidate_count_exact(self):
        from app.api.v1.short_lists import _to_short_list_response
        record = MagicMock()
        record.id = "sl-count"
        record.description = "shortlist:j-2"
        record.name = "Devs"
        record.created_by = "hr"
        record.created_at = datetime(2026, 3, 8)
        record.members = [MagicMock() for _ in range(7)]
        resp = _to_short_list_response(record)
        assert resp.candidate_count == 7

    def test_job_id_extracted_correctly(self):
        from app.api.v1.short_lists import _to_short_list_response
        record = MagicMock()
        record.id = "sl-jid"
        record.description = "shortlist:job-unique-42"
        record.name = "Lista"
        record.created_by = "u"
        record.created_at = datetime(2026, 3, 8)
        record.members = []
        resp = _to_short_list_response(record)
        assert resp.job_id == "job-unique-42"

    def test_description_extracted_correctly(self):
        from app.api.v1.short_lists import _to_short_list_response
        record = MagicMock()
        record.id = "sl-desc"
        record.description = "shortlist:job-777|Minha descrição especial"
        record.name = "Lista Desc"
        record.created_by = "u"
        record.created_at = datetime(2026, 3, 8)
        record.members = []
        resp = _to_short_list_response(record)
        assert resp.description == "Minha descrição especial"

    def test_response_id_matches_record_id(self):
        from app.api.v1.short_lists import _to_short_list_response
        record = MagicMock()
        record.id = "unique-id-xyz"
        record.description = "shortlist:job-1"
        record.name = "Lista"
        record.created_by = "u"
        record.created_at = datetime(2026, 3, 8)
        record.members = []
        resp = _to_short_list_response(record)
        assert resp.id == "unique-id-xyz"


# ---------------------------------------------------------------------------
# ShortListCreate schema — validation
# ---------------------------------------------------------------------------

class TestShortListCreateValidation:
    def test_job_id_required(self):
        from pydantic import ValidationError
        from app.api.v1.short_lists import ShortListCreate
        with pytest.raises((ValidationError, TypeError)):
            ShortListCreate(name="Lista sem job_id")

    def test_name_required(self):
        from pydantic import ValidationError
        from app.api.v1.short_lists import ShortListCreate
        with pytest.raises((ValidationError, TypeError)):
            ShortListCreate(job_id="j-1")

    def test_description_optional_none_by_default(self):
        from app.api.v1.short_lists import ShortListCreate
        body = ShortListCreate(job_id="j-1", name="Lista")
        assert body.description is None

    def test_all_fields_set(self):
        from app.api.v1.short_lists import ShortListCreate
        body = ShortListCreate(job_id="j-1", name="Lista", description="Desc")
        assert body.job_id == "j-1"
        assert body.name == "Lista"
        assert body.description == "Desc"


# ---------------------------------------------------------------------------
# ShortListCandidateAdd schema
# ---------------------------------------------------------------------------

class TestShortListCandidateAddValidation:
    def test_candidate_id_required(self):
        from pydantic import ValidationError
        from app.api.v1.short_lists import ShortListCandidateAdd
        with pytest.raises((ValidationError, TypeError)):
            ShortListCandidateAdd()

    def test_notes_optional(self):
        from app.api.v1.short_lists import ShortListCandidateAdd
        body = ShortListCandidateAdd(candidate_id="c-1")
        assert body.notes is None

    def test_notes_set(self):
        from app.api.v1.short_lists import ShortListCandidateAdd
        body = ShortListCandidateAdd(candidate_id="c-2", notes="Excelente experiência")
        assert body.notes == "Excelente experiência"


# ---------------------------------------------------------------------------
# ShortListResponse schema
# ---------------------------------------------------------------------------

class TestShortListResponseSchema:
    def test_candidate_count_zero(self):
        from app.api.v1.short_lists import ShortListResponse
        resp = ShortListResponse(
            id="s-1", job_id="j-1", name="Lista", description=None,
            created_by="u", created_at="2026-01-01T00:00:00", candidate_count=0
        )
        assert resp.candidate_count == 0

    def test_description_can_be_none(self):
        from app.api.v1.short_lists import ShortListResponse
        resp = ShortListResponse(
            id="s-1", job_id="j-1", name="Lista", description=None,
            created_by="u", created_at="2026-01-01T00:00:00", candidate_count=1
        )
        assert resp.description is None

    def test_all_fields_accessible(self):
        from app.api.v1.short_lists import ShortListResponse
        resp = ShortListResponse(
            id="s-2", job_id="j-2", name="Lista Final",
            description="Desc", created_by="recruiter@co.com",
            created_at="2026-03-08T10:00:00", candidate_count=5
        )
        assert resp.id == "s-2"
        assert resp.created_by == "recruiter@co.com"
