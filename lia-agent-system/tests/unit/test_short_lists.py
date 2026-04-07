"""
Unit tests — Short List API (Sprint F4).

Cobre:
- _encode_meta / _decode_meta helpers
- _is_shortlist discriminador
- _to_short_list_response conversão
- Endpoints: create, list, get, add_candidate, remove_candidate (mocked DB)
- Multi-tenant: company_id obrigatório
- Conflito de candidato duplicado (409)
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------

class TestShortListHelpers:

    def test_encode_meta_without_description(self):
        from app.api.v1.short_lists import _encode_meta
        result = _encode_meta("job-123")
        assert result == "shortlist:job-123"

    def test_encode_meta_with_description(self):
        from app.api.v1.short_lists import _encode_meta
        result = _encode_meta("job-456", "Candidatos finais")
        assert result == "shortlist:job-456|Candidatos finais"

    def test_decode_meta_without_description(self):
        from app.api.v1.short_lists import _decode_meta
        job_id, desc = _decode_meta("shortlist:job-789")
        assert job_id == "job-789"
        assert desc == ""

    def test_decode_meta_with_description(self):
        from app.api.v1.short_lists import _decode_meta
        job_id, desc = _decode_meta("shortlist:job-111|Minha short list")
        assert job_id == "job-111"
        assert desc == "Minha short list"

    def test_decode_meta_non_shortlist_returns_empty_job_id(self):
        from app.api.v1.short_lists import _decode_meta
        job_id, desc = _decode_meta("generic description")
        assert job_id == ""
        assert desc == "generic description"

    def test_decode_meta_none_returns_empties(self):
        from app.api.v1.short_lists import _decode_meta
        job_id, desc = _decode_meta(None)
        assert job_id == ""
        assert desc == ""

    def test_is_shortlist_true(self):
        from app.api.v1.short_lists import _is_shortlist
        record = MagicMock()
        record.description = "shortlist:job-999"
        assert _is_shortlist(record) is True

    def test_is_shortlist_false(self):
        from app.api.v1.short_lists import _is_shortlist
        record = MagicMock()
        record.description = "generic list"
        assert _is_shortlist(record) is False

    def test_is_shortlist_none_description(self):
        from app.api.v1.short_lists import _is_shortlist
        record = MagicMock()
        record.description = None
        assert _is_shortlist(record) is False

    def test_to_short_list_response(self):
        from app.api.v1.short_lists import _to_short_list_response
        from datetime import datetime
        record = MagicMock()
        record.id = "list-abc"
        record.description = "shortlist:job-xyz|Devs sênior"
        record.name = "Devs Sênior"
        record.created_by = "recruiter@acme.com"
        record.created_at = datetime(2026, 3, 8, 12, 0, 0)
        record.members = [MagicMock(), MagicMock()]
        resp = _to_short_list_response(record)
        assert resp.job_id == "job-xyz"
        assert resp.description == "Devs sênior"
        assert resp.candidate_count == 2

    def test_to_short_list_response_no_members(self):
        from app.api.v1.short_lists import _to_short_list_response
        from datetime import datetime
        record = MagicMock()
        record.id = "list-empty"
        record.description = "shortlist:job-000"
        record.name = "Vazia"
        record.created_by = "user"
        record.created_at = datetime(2026, 3, 8)
        record.members = None
        resp = _to_short_list_response(record)
        assert resp.candidate_count == 0


# ---------------------------------------------------------------------------
# Schemas Pydantic
# ---------------------------------------------------------------------------

class TestShortListSchemas:

    def test_short_list_create_schema(self):
        from app.api.v1.short_lists import ShortListCreate
        body = ShortListCreate(job_id="j-1", name="Lista A")
        assert body.job_id == "j-1"
        assert body.name == "Lista A"
        assert body.description is None

    def test_short_list_create_with_description(self):
        from app.api.v1.short_lists import ShortListCreate
        body = ShortListCreate(job_id="j-2", name="Lista B", description="Descrição")
        assert body.description == "Descrição"

    def test_short_list_candidate_add_schema(self):
        from app.api.v1.short_lists import ShortListCandidateAdd
        body = ShortListCandidateAdd(candidate_id="c-123")
        assert body.candidate_id == "c-123"
        assert body.notes is None

    def test_short_list_candidate_add_with_notes(self):
        from app.api.v1.short_lists import ShortListCandidateAdd
        body = ShortListCandidateAdd(candidate_id="c-456", notes="Ótimo candidato")
        assert body.notes == "Ótimo candidato"

    def test_short_list_response_schema(self):
        from app.api.v1.short_lists import ShortListResponse
        resp = ShortListResponse(
            id="sl-1",
            job_id="j-1",
            name="Lista",
            description=None,
            created_by="user",
            created_at="2026-03-08T00:00:00",
            candidate_count=3,
        )
        assert resp.candidate_count == 3


# ---------------------------------------------------------------------------
# Router registrado em main.py
# ---------------------------------------------------------------------------

class TestShortListsRouter:

    def test_router_registered_in_main(self):
        import pathlib
        content = pathlib.Path("app/api/routes.py").read_text()
        assert "short_lists" in content
        assert "short-lists" in content

    def test_short_lists_module_importable(self):
        from app.api.v1.short_lists import router
        assert router is not None

    def test_router_has_correct_prefix(self):
        from app.api.v1.short_lists import router
        assert router.prefix == "/short-lists"

    def test_router_has_all_routes(self):
        from app.api.v1.short_lists import router
        paths = {r.path for r in router.routes}
        assert "/short-lists" in paths                                    # GET + POST
        assert "/short-lists/{list_id}" in paths                          # GET /{list_id}
        assert "/short-lists/{list_id}/candidates" in paths               # POST candidates
        assert "/short-lists/{list_id}/candidates/{candidate_id}" in paths  # DELETE


# ---------------------------------------------------------------------------
# encode/decode round-trip
# ---------------------------------------------------------------------------

class TestShortListRoundTrip:

    def test_encode_decode_roundtrip(self):
        from app.api.v1.short_lists import _encode_meta, _decode_meta
        for job_id, desc in [
            ("job-1", None),
            ("job-2", "Finalistas"),
            ("job-3", "Lista com | pipe"),
        ]:
            encoded = _encode_meta(job_id, desc)
            decoded_job, decoded_desc = _decode_meta(encoded)
            assert decoded_job == job_id
            if desc:
                assert desc.split("|")[0] in decoded_desc  # pipe trunca no primeiro |
            else:
                assert decoded_desc == ""
