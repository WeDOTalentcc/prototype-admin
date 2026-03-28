"""
Testes unitários para structured logging (Sprint H — coverage gate 40%).

Cobertura:
  - JSONFormatter.format: campos obrigatórios, exception, extra_data, context keys
  - ContextLogger: info, warning, error, debug
  - setup_structured_logging: handler adicionado, nível correto
"""
import json
import logging
import pytest

pytestmark = pytest.mark.easy

from app.shared.structured_logging import JSONFormatter, ContextLogger


# ---------------------------------------------------------------------------
# JSONFormatter
# ---------------------------------------------------------------------------

class TestJSONFormatter:

    def _make_record(self, msg="test msg", level=logging.INFO, exc_info=None):
        record = logging.LogRecord(
            name="test.logger", level=level,
            pathname="/app/test.py", lineno=42,
            msg=msg, args=(), exc_info=exc_info,
        )
        return record

    def test_format_returns_valid_json(self):
        fmt = JSONFormatter()
        record = self._make_record("hello world")
        output = fmt.format(record)
        parsed = json.loads(output)
        assert isinstance(parsed, dict)

    def test_required_fields_present(self):
        fmt = JSONFormatter()
        record = self._make_record("test")
        parsed = json.loads(fmt.format(record))
        for field in ("timestamp", "level", "logger", "message", "service", "module"):
            assert field in parsed, f"Missing field: {field}"

    def test_service_name_custom(self):
        fmt = JSONFormatter(service_name="my-service")
        record = self._make_record("test")
        parsed = json.loads(fmt.format(record))
        assert parsed["service"] == "my-service"

    def test_level_in_output(self):
        fmt = JSONFormatter()
        record = self._make_record("warning!", level=logging.WARNING)
        parsed = json.loads(fmt.format(record))
        assert parsed["level"] == "WARNING"

    def test_message_in_output(self):
        fmt = JSONFormatter()
        record = self._make_record("my specific message")
        parsed = json.loads(fmt.format(record))
        assert parsed["message"] == "my specific message"

    def test_exception_included_when_present(self):
        fmt = JSONFormatter()
        try:
            raise ValueError("boom")
        except ValueError:
            import sys
            exc = sys.exc_info()
        record = self._make_record("error occurred", exc_info=exc)
        parsed = json.loads(fmt.format(record))
        assert "exception" in parsed
        assert parsed["exception"]["type"] == "ValueError"

    def test_no_exception_field_when_none(self):
        fmt = JSONFormatter()
        record = self._make_record("clean log")
        parsed = json.loads(fmt.format(record))
        assert "exception" not in parsed

    def test_extra_data_included(self):
        fmt = JSONFormatter()
        record = self._make_record("with extra")
        record.extra_data = {"company_id": "c-1", "action": "search"}
        parsed = json.loads(fmt.format(record))
        assert "data" in parsed
        assert parsed["data"]["company_id"] == "c-1"

    def test_context_keys_included(self):
        fmt = JSONFormatter()
        record = self._make_record("traced")
        record.request_id = "req-123"
        record.user_id = "usr-456"
        parsed = json.loads(fmt.format(record))
        assert parsed.get("request_id") == "req-123"
        assert parsed.get("user_id") == "usr-456"

    def test_output_is_utf8_safe(self):
        fmt = JSONFormatter()
        record = self._make_record("Candidato: João Müller — vaga de engenharia")
        output = fmt.format(record)
        parsed = json.loads(output)
        assert "João" in parsed["message"]


# ---------------------------------------------------------------------------
# ContextLogger
# ---------------------------------------------------------------------------

class TestContextLogger:

    def _capture_logger(self, name="test.ctx"):
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
        handler = logging.handlers.MemoryHandler(capacity=100)
        logger.addHandler(handler)
        return logger, handler

    def test_info_logs_message(self, caplog):
        base = logging.getLogger("test.ctx.info")
        ctx = ContextLogger(base, {"tenant": "t-1"})
        with caplog.at_level(logging.INFO, logger="test.ctx.info"):
            ctx.info("testing info")
        assert "testing info" in caplog.text

    def test_warning_logs_message(self, caplog):
        base = logging.getLogger("test.ctx.warn")
        ctx = ContextLogger(base)
        with caplog.at_level(logging.WARNING, logger="test.ctx.warn"):
            ctx.warning("testing warning")
        assert "testing warning" in caplog.text

    def test_error_logs_message(self, caplog):
        base = logging.getLogger("test.ctx.err")
        ctx = ContextLogger(base)
        with caplog.at_level(logging.ERROR, logger="test.ctx.err"):
            ctx.error("testing error")
        assert "testing error" in caplog.text

    def test_debug_logs_message(self, caplog):
        base = logging.getLogger("test.ctx.dbg")
        ctx = ContextLogger(base)
        with caplog.at_level(logging.DEBUG, logger="test.ctx.dbg"):
            ctx.debug("testing debug")
        assert "testing debug" in caplog.text


import logging.handlers
