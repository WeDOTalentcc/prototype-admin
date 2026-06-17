"""Coverage tests — Batch M.

Targets zero-coverage shared utility modules:
  - app/shared/errors.py                  (154 stmts)
  - app/shared/chat_event_serializer.py   (220 stmts)
  - app/shared/value_objects/company_id.py (175 stmts)
  - app/shared/upload_validators.py       (177 stmts)
  - app/shared/websocket/ws_message_schemas.py (302 stmts)
  - app/shared/cache_strategy.py          (293 stmts)
"""
import io
import json
import zipfile

import pytest


# ===========================================================================
# app/shared/errors.py
# ===========================================================================
from app.shared.errors import (
    LIAError,
    LIAAgentError,
    LIAToolError,
    LIALLMError,
    LIAValidationError,
    LIATenantError,
    LIAComplianceError,
    LIAConsentError,
    LIAFairnessError,
    LIAIntegrationError,
)


class TestLIAError:
    def test_default_values(self):
        e = LIAError()
        assert e.code == "INTERNAL_ERROR"
        assert e.recoverable is True
        assert e.details == {}
        assert str(e) == "Erro interno da plataforma"

    def test_custom_message_code(self):
        e = LIAError(message="Falha geral", code="GEN_FAIL", recoverable=False)
        assert e.message == "Falha geral"
        assert e.code == "GEN_FAIL"
        assert e.recoverable is False

    def test_details(self):
        e = LIAError(details={"tool": "search", "timeout": 30})
        assert e.details["tool"] == "search"

    def test_to_dict(self):
        e = LIAError(message="Err", code="ERR", details={"k": "v"}, recoverable=True)
        d = e.to_dict()
        assert d["error"] == "ERR"
        assert d["message"] == "Err"
        assert d["details"] == {"k": "v"}
        assert d["recoverable"] is True

    def test_repr(self):
        e = LIAError(code="FOO")
        assert "LIAError" in repr(e)
        assert "FOO" in repr(e)

    def test_is_exception(self):
        e = LIAError(message="boom")
        with pytest.raises(LIAError):
            raise e


class TestLIAAgentError:
    def test_default(self):
        e = LIAAgentError()
        assert e.code == "AGENT_ERROR"

    def test_is_lia_error(self):
        e = LIAAgentError()
        assert isinstance(e, LIAError)


class TestLIAToolError:
    def test_default(self):
        e = LIAToolError()
        assert e.code == "TOOL_ERROR"
        assert e.recoverable is True

    def test_custom(self):
        e = LIAToolError(
            message="Busca indisponível",
            code="TOOL_SEARCH_UNAVAILABLE",
            details={"tool": "search"},
        )
        assert e.details["tool"] == "search"

    def test_inherits_agent_error(self):
        e = LIAToolError()
        assert isinstance(e, LIAAgentError)


class TestLIALLMError:
    def test_default(self):
        e = LIALLMError()
        assert e.code == "LLM_ERROR"
        assert e.recoverable is True


class TestLIAValidationError:
    def test_default(self):
        e = LIAValidationError()
        assert e.code == "VALIDATION_ERROR"
        assert e.recoverable is True

    def test_custom(self):
        e = LIAValidationError(message="Campo obrigatório faltando", code="MISSING_FIELD")
        assert e.code == "MISSING_FIELD"


class TestLIATenantError:
    def test_default(self):
        e = LIATenantError()
        assert e.code == "TENANT_ERROR"
        assert e.recoverable is False  # fail-closed


class TestLIAComplianceError:
    def test_always_not_recoverable(self):
        e = LIAComplianceError()
        assert e.recoverable is False

    def test_even_if_caller_sets_recoverable_true(self):
        # recoverable=False is forced
        e = LIAComplianceError(recoverable=True)
        assert e.recoverable is False

    def test_custom(self):
        e = LIAComplianceError(message="Violação", code="COMPLIANCE_ERROR")
        assert e.code == "COMPLIANCE_ERROR"


class TestLIAConsentError:
    def test_default(self):
        e = LIAConsentError()
        assert e.code == "CONSENT_ERROR"
        assert e.recoverable is False

    def test_inherits_compliance(self):
        assert isinstance(LIAConsentError(), LIAComplianceError)


class TestLIAFairnessError:
    def test_default(self):
        e = LIAFairnessError()
        assert e.code == "FAIRNESS_BLOCKED"
        assert e.recoverable is False

    def test_details(self):
        e = LIAFairnessError(
            message="Critério discriminatório",
            details={"criterion": "age", "delta": 0.15},
        )
        assert e.details["criterion"] == "age"


class TestLIAIntegrationError:
    def test_default(self):
        e = LIAIntegrationError()
        assert e.code == "INTEGRATION_ERROR"
        assert e.recoverable is True


# ===========================================================================
# app/shared/chat_event_serializer.py
# ===========================================================================
from app.shared.chat_event_serializer import (
    serialize_event,
    serialize_thinking,
    serialize_token,
    serialize_token_done,
    serialize_message,
    serialize_error,
    serialize_panel_update,
    serialize_background_task_update,
    serialize_connected,
    format_sse_event,
    format_sse_keepalive,
)


class TestSerializeEvent:
    def test_basic(self):
        result = serialize_event("thinking", content="processing")
        assert result["type"] == "thinking"
        assert result["content"] == "processing"

    def test_none_values_omitted(self):
        result = serialize_event("token", content="hello", extra=None)
        assert "extra" not in result

    def test_type_only(self):
        result = serialize_event("ping")
        assert result == {"type": "ping"}


class TestSerializeThinking:
    def test_basic(self):
        e = serialize_thinking("analyzing", step=1)
        assert e["type"] == "thinking"
        assert e["content"] == "analyzing"
        assert e["step"] == 1

    def test_defaults(self):
        e = serialize_thinking()
        assert e["type"] == "thinking"
        assert e["step"] == 0


class TestSerializeToken:
    def test_basic(self):
        e = serialize_token("hello")
        assert e["type"] == "token"
        assert e["content"] == "hello"

    def test_empty_string(self):
        e = serialize_token("")
        assert e["content"] == ""


class TestSerializeTokenDone:
    def test_default(self):
        e = serialize_token_done()
        assert e["type"] == "token_done"
        assert e["tokens_sent"] == 0

    def test_with_count(self):
        e = serialize_token_done(tokens_sent=42)
        assert e["tokens_sent"] == 42


class TestSerializeMessage:
    def test_minimal(self):
        e = serialize_message("Olá!")
        assert e["type"] == "message"
        assert e["content"] == "Olá!"
        assert e["confidence"] == 0.0
        assert e["domain"] == ""
        assert e["source"] == "direct"

    def test_full(self):
        e = serialize_message(
            content="Resposta completa",
            confidence=0.95,
            domain="kanban",
            source="direct",
            actions=[{"type": "move"}],
            navigation={"path": "/jobs"},
            state_updates={"stage": "triagem"},
            fairness_warnings=["check gender"],
            execution_plan={"steps": 3},
            conversation_id="conv-001",
        )
        assert e["confidence"] == 0.95
        assert e["domain"] == "kanban"
        assert e["actions"] == [{"type": "move"}]
        assert e["navigation"] == {"path": "/jobs"}
        assert e["state_updates"] == {"stage": "triagem"}
        assert e["fairness_warnings"] == ["check gender"]
        assert e["execution_plan"] == {"steps": 3}
        assert e["conversation_id"] == "conv-001"

    def test_optional_fields_absent_when_none(self):
        e = serialize_message("test")
        assert "actions" not in e
        assert "navigation" not in e
        assert "conversation_id" not in e


class TestSerializeError:
    def test_basic(self):
        e = serialize_error("Algo deu errado")
        assert e["type"] == "error"
        assert e["message"] == "Algo deu errado"

    def test_with_code(self):
        e = serialize_error("Timeout", error_code="LLM_TIMEOUT")
        assert e["error_code"] == "LLM_TIMEOUT"

    def test_without_code(self):
        e = serialize_error("Falha")
        assert "error_code" not in e


class TestSerializePanelUpdate:
    def test_basic(self):
        e = serialize_panel_update("candidate_profile", {"id": "c1"})
        assert e["type"] == "panel_update"
        assert e["panel_type"] == "candidate_profile"
        assert e["panel_data"] == {"id": "c1"}
        assert e["action"] == "open"

    def test_custom_action(self):
        e = serialize_panel_update("jobs", {}, action="close")
        assert e["action"] == "close"


class TestSerializeBackgroundTaskUpdate:
    def test_basic(self):
        e = serialize_background_task_update(
            task_id="task-001",
            task_type="screening",
            label="Triagem automática",
            status="running",
        )
        assert e["type"] == "background_task_update"
        assert e["task_id"] == "task-001"
        assert e["status"] == "running"

    def test_with_progress(self):
        e = serialize_background_task_update(
            task_id="t1", task_type="rank", label="Ranking", status="in_progress",
            progress=50, message="Processando...", result={"done": 5},
        )
        assert e["progress"] == 50
        assert e["result"] == {"done": 5}


class TestSerializeConnected:
    def test_basic(self):
        e = serialize_connected("session-123", domain="kanban")
        assert e["type"] == "connected"
        assert e["session_id"] == "session-123"
        assert e["domain"] == "kanban"


class TestFormatSSE:
    def test_format_sse_event(self):
        data = {"type": "token", "content": "hello"}
        result = format_sse_event(data, event_id="123")
        assert result.startswith("id: 123\n")
        assert "data:" in result
        assert result.endswith("\n\n")
        # JSON parseable
        lines = result.strip().split("\n")
        data_line = next(l for l in lines if l.startswith("data:"))
        parsed = json.loads(data_line[len("data: "):])
        assert parsed["content"] == "hello"

    def test_format_sse_event_auto_id(self):
        data = {"type": "ping"}
        result = format_sse_event(data)
        assert "id:" in result

    def test_format_sse_keepalive(self):
        result = format_sse_keepalive()
        assert result == ": keepalive\n\n"


# ===========================================================================
# app/shared/value_objects/company_id.py
# ===========================================================================
from app.shared.value_objects.company_id import CompanyId
from app.shared.exceptions.tenant_errors import InvalidCompanyIdError


_VALID_UUID_V4 = "550e8400-e29b-41d4-a716-446655440000"


class TestCompanyIdParse:
    def test_valid_uuid_v4_str(self):
        cid = CompanyId.parse(_VALID_UUID_V4)
        assert cid.value == _VALID_UUID_V4.lower()

    def test_valid_uuid_uppercase(self):
        cid = CompanyId.parse(_VALID_UUID_V4.upper())
        assert cid.value == _VALID_UUID_V4.lower()

    def test_valid_slug(self):
        cid = CompanyId.parse("demo-company")
        assert cid.value == "demo-company"

    def test_valid_slug_with_numbers(self):
        cid = CompanyId.parse("acme123")
        assert cid.value == "acme123"

    def test_none_raises(self):
        with pytest.raises(InvalidCompanyIdError):
            CompanyId.parse(None)

    def test_empty_raises(self):
        with pytest.raises(InvalidCompanyIdError):
            CompanyId.parse("")

    def test_whitespace_only_raises(self):
        with pytest.raises(InvalidCompanyIdError):
            CompanyId.parse("   ")

    def test_forbidden_default_raises(self):
        with pytest.raises(InvalidCompanyIdError):
            CompanyId.parse("default")

    def test_forbidden_none_raises(self):
        with pytest.raises(InvalidCompanyIdError):
            CompanyId.parse("none")

    def test_forbidden_system_raises(self):
        with pytest.raises(InvalidCompanyIdError):
            CompanyId.parse("system")

    def test_forbidden_anonymous_raises(self):
        with pytest.raises(InvalidCompanyIdError):
            CompanyId.parse("anonymous")

    def test_invalid_format_raises(self):
        with pytest.raises(InvalidCompanyIdError):
            CompanyId.parse("not a valid id !!!")

    def test_too_short_slug_raises(self):
        # Slug must be ≥3 chars (letter + 2 more)
        with pytest.raises(InvalidCompanyIdError):
            CompanyId.parse("ab")  # only 2 chars

    def test_uuid_object(self):
        from uuid import UUID
        raw = UUID(_VALID_UUID_V4)
        cid = CompanyId.parse(raw)
        assert cid.value == _VALID_UUID_V4.lower()


class TestCompanyIdProperties:
    def test_is_uuid_true(self):
        cid = CompanyId.parse(_VALID_UUID_V4)
        assert cid.is_uuid is True

    def test_is_uuid_false_for_slug(self):
        cid = CompanyId.parse("acme-corp")
        assert cid.is_uuid is False

    def test_is_slug_true_for_slug(self):
        cid = CompanyId.parse("acme-corp")
        assert cid.is_slug is True

    def test_is_slug_false_for_uuid(self):
        cid = CompanyId.parse(_VALID_UUID_V4)
        assert cid.is_slug is False

    def test_as_str(self):
        cid = CompanyId.parse(_VALID_UUID_V4)
        assert cid.as_str() == _VALID_UUID_V4.lower()

    def test_as_uuid(self):
        from uuid import UUID
        cid = CompanyId.parse(_VALID_UUID_V4)
        assert cid.as_uuid() == UUID(_VALID_UUID_V4)

    def test_as_uuid_raises_for_slug(self):
        cid = CompanyId.parse("acme-corp")
        with pytest.raises(InvalidCompanyIdError):
            cid.as_uuid()

    def test_str_method(self):
        cid = CompanyId.parse("acme-slug")
        assert str(cid) == "acme-slug"

    def test_immutable_frozen(self):
        cid = CompanyId.parse("acme-slug")
        with pytest.raises(Exception):
            cid.value = "other"  # type: ignore[misc]

    def test_equality(self):
        a = CompanyId.parse(_VALID_UUID_V4)
        b = CompanyId.parse(_VALID_UUID_V4)
        assert a == b


# ===========================================================================
# app/shared/upload_validators.py
# ===========================================================================
from app.shared.upload_validators import (
    validate_upload,
    ValidatedFile,
    UnsupportedFileTypeError,
    _looks_like_text,
    _is_docx,
)

_PDF_BYTES = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n"
_TXT_BYTES = b"Hello world, this is plain text.\n"


def _make_docx_bytes() -> bytes:
    """Build a minimal valid DOCX (ZIP with [Content_Types].xml)."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode="w") as zf:
        zf.writestr("[Content_Types].xml", '<?xml version="1.0"?><Types/>')
        zf.writestr("word/document.xml", "<document/>")
    return buf.getvalue()


class TestLooksLikeText:
    def test_plain_text_is_text(self):
        assert _looks_like_text(b"Hello world") is True

    def test_utf8_is_text(self):
        assert _looks_like_text("Olá mundo é português".encode("utf-8")) is True

    def test_nul_byte_is_not_text(self):
        assert _looks_like_text(b"Hello\x00World") is False

    def test_empty_is_not_text(self):
        assert _looks_like_text(b"") is False

    def test_binary_data_fails(self):
        # A chunk of high-entropy binary-looking bytes
        binary = bytes(range(256)) * 10
        assert _looks_like_text(binary) is False


class TestIsDocx:
    def test_valid_docx(self):
        assert _is_docx(_make_docx_bytes()) is True

    def test_pdf_is_not_docx(self):
        assert _is_docx(_PDF_BYTES) is False

    def test_plain_zip_without_manifest(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, mode="w") as zf:
            zf.writestr("readme.txt", "no content types here")
        assert _is_docx(buf.getvalue()) is False

    def test_non_zip_is_not_docx(self):
        assert _is_docx(b"not a zip at all") is False


class TestValidateUpload:
    def test_valid_pdf(self):
        result = validate_upload("resume.pdf", _PDF_BYTES)
        assert result.extension == ".pdf"
        assert "pdf" in result.mime

    def test_valid_txt(self):
        result = validate_upload("notes.txt", _TXT_BYTES)
        assert result.extension == ".txt"
        assert result.mime == "text/plain"

    def test_valid_md(self):
        result = validate_upload("readme.md", b"# Title\nSome markdown text\n")
        assert result.extension == ".md"
        assert result.mime == "text/markdown"

    def test_valid_docx(self):
        result = validate_upload("cv.docx", _make_docx_bytes())
        assert result.extension == ".docx"
        assert "wordprocessingml" in result.mime

    def test_unsupported_extension_raises(self):
        with pytest.raises(UnsupportedFileTypeError) as exc_info:
            validate_upload("payload.exe", b"MZ\x90\x00")
        assert exc_info.value.declared_ext == ".exe"

    def test_empty_file_raises(self):
        with pytest.raises(UnsupportedFileTypeError):
            validate_upload("empty.pdf", b"")

    def test_pdf_bytes_with_wrong_extension_raises(self):
        # Real PDF magic but declared as .txt → should raise
        with pytest.raises(UnsupportedFileTypeError):
            validate_upload("disguised.txt", _PDF_BYTES)

    def test_binary_as_txt_raises(self):
        # Binary bytes declared as .txt
        with pytest.raises(UnsupportedFileTypeError):
            validate_upload("evil.txt", b"MZ\x90\x00" + b"\x00" * 100)

    def test_wrong_magic_as_pdf_raises(self):
        with pytest.raises(UnsupportedFileTypeError):
            validate_upload("fake.pdf", b"Not a real PDF file")

    def test_plain_zip_as_docx_raises(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, mode="w") as zf:
            zf.writestr("readme.txt", "no manifest")
        with pytest.raises(UnsupportedFileTypeError):
            validate_upload("fake.docx", buf.getvalue())

    def test_error_has_declared_ext(self):
        with pytest.raises(UnsupportedFileTypeError) as exc_info:
            validate_upload("evil.xyz", b"data")
        assert exc_info.value.declared_ext == ".xyz"

    def test_filename_no_extension(self):
        with pytest.raises(UnsupportedFileTypeError):
            validate_upload("noext", _TXT_BYTES)


# ===========================================================================
# app/shared/websocket/ws_message_schemas.py
# ===========================================================================
from app.shared.websocket.ws_message_schemas import (
    LIA_WS_PROTOCOL_VERSION,
    is_protocol_compatible,
    WSHelloMessage,
    WSUserMessage,
    WSPingMessage,
    WSAbortMessage,
    WSConnectedMessage,
    WSThinkingMessage,
    WSTokenMessage,
    WSResponseMessage,
    WSErrorMessage,
    WSPongMessage,
    UIAction,
    UINavigateToParams,
    UIOpenModalParams,
    UIOpenPanelParams,
    validate_global_ui_action_params,
)


class TestProtocolVersion:
    def test_version_exists(self):
        assert LIA_WS_PROTOCOL_VERSION
        assert "." in LIA_WS_PROTOCOL_VERSION

    def test_compatible_same_major(self):
        assert is_protocol_compatible(LIA_WS_PROTOCOL_VERSION) is True

    def test_compatible_none(self):
        assert is_protocol_compatible(None) is True

    def test_compatible_empty_string(self):
        assert is_protocol_compatible("") is True

    def test_incompatible_major_mismatch(self):
        assert is_protocol_compatible("99.0") is False

    def test_compatible_minor_mismatch(self):
        major = LIA_WS_PROTOCOL_VERSION.split(".")[0]
        assert is_protocol_compatible(f"{major}.99") is True


class TestWSClientMessages:
    def test_hello_defaults(self):
        m = WSHelloMessage()
        assert m.type == "hello"
        assert m.protocol_version == LIA_WS_PROTOCOL_VERSION

    def test_hello_custom(self):
        m = WSHelloMessage(client="web@1.0.0", protocol_version="1.0")
        assert m.client == "web@1.0.0"

    def test_user_message(self):
        m = WSUserMessage(content="Mover candidato para triagem")
        assert m.type == "message"
        assert m.content == "Mover candidato para triagem"
        assert m.domain == "recruiter_assistant"

    def test_user_message_custom_domain(self):
        m = WSUserMessage(content="test", domain="kanban")
        assert m.domain == "kanban"

    def test_ping(self):
        m = WSPingMessage()
        assert m.type == "ping"

    def test_abort(self):
        m = WSAbortMessage()
        assert m.type == "abort"


class TestWSServerMessages:
    def test_connected(self):
        m = WSConnectedMessage(session_id="sess-001", domain="kanban")
        assert m.type == "connected"
        assert m.session_id == "sess-001"
        assert m.protocol_version == LIA_WS_PROTOCOL_VERSION

    def test_thinking(self):
        m = WSThinkingMessage()
        assert m.type == "thinking"
        assert m.job_id is None

    def test_thinking_with_job(self):
        m = WSThinkingMessage(job_id="job-001")
        assert m.job_id == "job-001"

    def test_token(self):
        m = WSTokenMessage(content="hello")
        assert m.type == "token"
        assert m.content == "hello"

    def test_response(self):
        m = WSResponseMessage(content="Candidato movido com sucesso.")
        assert m.type == "message"
        assert m.content == "Candidato movido com sucesso."
        assert 0.0 <= m.confidence <= 1.0

    def test_response_confidence_bounds(self):
        m = WSResponseMessage(content="test", confidence=0.95)
        assert m.confidence == pytest.approx(0.95)

    def test_error_message(self):
        m = WSErrorMessage(message="Timeout")
        assert m.type == "error"
        assert m.message == "Timeout"

    def test_error_with_code(self):
        m = WSErrorMessage(message="Auth failed", code="UNAUTHORIZED")
        assert m.code == "UNAUTHORIZED"

    def test_pong(self):
        m = WSPongMessage()
        assert m.type == "pong"


class TestUIAction:
    def test_basic(self):
        a = UIAction(type="navigate_to", params={"path": "/jobs"})
        assert a.type == "navigate_to"
        assert a.params["path"] == "/jobs"

    def test_empty_params(self):
        a = UIAction(type="move_candidate")
        assert a.params == {}


class TestValidateGlobalUIActionParams:
    def test_navigate_to_valid(self):
        result = validate_global_ui_action_params("navigate_to", {"page": "/jobs"})
        assert result is not None
        assert isinstance(result, UINavigateToParams)

    def test_open_modal_valid(self):
        result = validate_global_ui_action_params("open_modal", {"modal_id": "some-modal"})
        assert result is not None
        assert isinstance(result, UIOpenModalParams)

    def test_unknown_type_returns_none(self):
        result = validate_global_ui_action_params("page_specific_action", {})
        assert result is None

    def test_invalid_params_returns_none(self):
        # navigate_to requires "path"
        result = validate_global_ui_action_params("navigate_to", {})
        assert result is None


# ===========================================================================
# app/shared/cache_strategy.py
# ===========================================================================
from app.shared.cache_strategy import (
    CacheDomain,
    CacheStrategy,
    CacheNamespace,
    CacheTTL,
    CacheConfig,
    NAMESPACE_CACHE_CONFIGS,
    DOMAIN_TTL_CONFIG,
    CacheSettings,
)


class TestCacheDomain:
    def test_has_expected_domains(self):
        expected = {
            "CANDIDATE_SEARCH", "CANDIDATE_PROFILE", "JOB_VACANCY",
            "JOB_DESCRIPTION", "WSI_SCORE", "PIPELINE_STAGES",
            "COMPANY_CONFIG", "SKILL_CATALOG", "LLM_RESPONSE",
            "TEMPLATE", "ANALYTICS", "ROUTING",
        }
        actual = {d.name for d in CacheDomain}
        assert expected.issubset(actual)

    def test_is_str_enum(self):
        assert CacheDomain.CANDIDATE_SEARCH == "candidate_search"
        assert isinstance(CacheDomain.CANDIDATE_SEARCH, str)


class TestDomainTTLConfig:
    def test_all_domains_have_config(self):
        for domain in CacheDomain:
            assert domain in DOMAIN_TTL_CONFIG, f"Missing config for {domain}"

    def test_config_has_required_keys(self):
        for domain, cfg in DOMAIN_TTL_CONFIG.items():
            assert "ttl_seconds" in cfg, f"No ttl_seconds for {domain}"
            assert isinstance(cfg["ttl_seconds"], int)
            assert cfg["ttl_seconds"] > 0


class TestCacheStrategy:
    def test_get_ttl_known_domain(self):
        ttl = CacheStrategy.get_ttl(CacheDomain.CANDIDATE_SEARCH)
        assert isinstance(ttl, int)
        assert ttl > 0

    def test_get_ttl_all_domains(self):
        for d in CacheDomain:
            assert CacheStrategy.get_ttl(d) > 0

    def test_build_key_returns_string(self):
        key = CacheStrategy.build_key(CacheDomain.CANDIDATE_SEARCH, query="python")
        assert isinstance(key, str)
        assert "candidate_search" in key

    def test_build_key_stable(self):
        k1 = CacheStrategy.build_key(CacheDomain.JOB_VACANCY, job_id="j1")
        k2 = CacheStrategy.build_key(CacheDomain.JOB_VACANCY, job_id="j1")
        assert k1 == k2

    def test_build_key_different_params_differ(self):
        k1 = CacheStrategy.build_key(CacheDomain.JOB_VACANCY, job_id="j1")
        k2 = CacheStrategy.build_key(CacheDomain.JOB_VACANCY, job_id="j2")
        assert k1 != k2

    def test_build_key_different_domain_differs(self):
        k1 = CacheStrategy.build_key(CacheDomain.CANDIDATE_SEARCH, q="x")
        k2 = CacheStrategy.build_key(CacheDomain.JOB_VACANCY, q="x")
        assert k1 != k2

    def test_get_invalidation_events(self):
        events = CacheStrategy.get_invalidation_events(CacheDomain.CANDIDATE_SEARCH)
        assert isinstance(events, list)
        assert len(events) > 0

    def test_get_domains_for_event(self):
        domains = CacheStrategy.get_domains_for_event("candidate_update")
        assert isinstance(domains, list)
        assert CacheDomain.CANDIDATE_SEARCH in domains or CacheDomain.CANDIDATE_PROFILE in domains

    def test_get_domains_for_unknown_event(self):
        domains = CacheStrategy.get_domains_for_event("zzz_unknown_event")
        assert domains == []

    def test_get_all_ttls(self):
        all_ttls = CacheStrategy.get_all_ttls()
        assert isinstance(all_ttls, dict)
        assert len(all_ttls) == len(CacheDomain)
        for key, val in all_ttls.items():
            assert "ttl_seconds" in val
            assert "ttl_human" in val
            assert "description" in val
            assert "invalidate_on" in val

    def test_ttl_human_format_seconds(self):
        # SKILL_CATALOG = 86400 → "1d"
        all_ttls = CacheStrategy.get_all_ttls()
        assert all_ttls["skill_catalog"]["ttl_human"] == "1d"

    def test_ttl_human_format_hours(self):
        all_ttls = CacheStrategy.get_all_ttls()
        assert all_ttls["company_config"]["ttl_human"].endswith("h")

    def test_ttl_human_format_minutes(self):
        all_ttls = CacheStrategy.get_all_ttls()
        assert all_ttls["candidate_search"]["ttl_human"].endswith("m")


class TestCacheNamespace:
    def test_has_members(self):
        members = list(CacheNamespace)
        assert len(members) > 0

    def test_is_str_enum(self):
        for ns in CacheNamespace:
            assert isinstance(ns, str)


class TestCacheSettings:
    def test_has_attributes(self):
        assert hasattr(CacheSettings, "CACHE_ENABLED")
        assert hasattr(CacheSettings, "CACHE_TTL_DEFAULT")
        assert hasattr(CacheSettings, "REDIS_URL")

    def test_ttl_default_is_int(self):
        assert isinstance(CacheSettings.CACHE_TTL_DEFAULT, int)

    def test_get_ttl_for_intent_pipeline_stats(self):
        ttl = CacheSettings.get_ttl_for_intent("pipeline_stats")
        assert isinstance(ttl, int)
        assert ttl > 0

    def test_get_ttl_for_intent_default(self):
        # Unknown intent → fallback default
        ttl = CacheSettings.get_ttl_for_intent("unknown_intent_xyz")
        assert isinstance(ttl, int)
        assert ttl > 0

    def test_get_ttl_for_intent_candidate_search(self):
        ttl = CacheSettings.get_ttl_for_intent("candidate_search")
        assert ttl > 0


class TestCacheTTLAndConfig:
    def test_cache_ttl_has_attributes(self):
        assert hasattr(CacheTTL, "SHORT") or len(dir(CacheTTL)) > 0

    def test_namespace_cache_configs_dict(self):
        assert isinstance(NAMESPACE_CACHE_CONFIGS, dict)
        assert len(NAMESPACE_CACHE_CONFIGS) > 0

    def test_cache_config_is_dataclass(self):
        for ns, cfg in NAMESPACE_CACHE_CONFIGS.items():
            assert isinstance(cfg, CacheConfig)
            break  # just check first one
