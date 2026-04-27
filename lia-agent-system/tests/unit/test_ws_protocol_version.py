"""
PM-03 (Audit Rev 4) — versionamento explícito do contrato WS.

Garante:
  * `LIA_WS_PROTOCOL_VERSION` é exportado e segue semver MAJOR.MINOR.
  * `WSConnectedMessage` carrega `protocol_version` por default.
  * `WSHelloMessage` aceita versão custom e default.
  * `is_protocol_compatible()` valida regra de MAJOR.
"""
import re

import pytest

pytestmark = pytest.mark.easy

from app.shared.websocket.ws_message_schemas import (
    LIA_WS_PROTOCOL_VERSION,
    WSConnectedMessage,
    WSHelloMessage,
    is_protocol_compatible,
)


_SEMVER_RE = re.compile(r"^\d+\.\d+(\.\d+)?$")


class TestProtocolVersionConstant:

    def test_constant_is_semver(self):
        assert _SEMVER_RE.match(LIA_WS_PROTOCOL_VERSION), (
            f"LIA_WS_PROTOCOL_VERSION must be MAJOR.MINOR semver, got "
            f"{LIA_WS_PROTOCOL_VERSION!r}"
        )

    def test_constant_starts_at_1(self):
        # Production-grade: contract starts at 1.0 (não pode regredir)
        major = int(LIA_WS_PROTOCOL_VERSION.split(".", 1)[0])
        assert major >= 1


class TestWSConnectedMessage:

    def test_default_includes_protocol_version(self):
        msg = WSConnectedMessage(session_id="s1", domain="wizard")
        assert msg.protocol_version == LIA_WS_PROTOCOL_VERSION

    def test_protocol_version_serializable(self):
        msg = WSConnectedMessage(session_id="s1", domain="wizard")
        payload = msg.model_dump()
        assert "protocol_version" in payload
        assert payload["protocol_version"] == LIA_WS_PROTOCOL_VERSION


class TestWSHelloMessage:

    def test_default_protocol_version(self):
        msg = WSHelloMessage()
        assert msg.type == "hello"
        assert msg.protocol_version == LIA_WS_PROTOCOL_VERSION
        assert msg.client == ""

    def test_client_custom_version(self):
        msg = WSHelloMessage(protocol_version="1.4", client="web@1.4.2")
        assert msg.protocol_version == "1.4"
        assert msg.client == "web@1.4.2"


class TestIsProtocolCompatible:

    def test_none_is_compatible(self):
        assert is_protocol_compatible(None) is True

    def test_empty_is_compatible(self):
        assert is_protocol_compatible("") is True

    def test_same_major_is_compatible(self):
        # Cliente mais novo no MINOR → compatível.
        assert is_protocol_compatible("1.99") is True

    def test_different_major_is_incompatible(self):
        assert is_protocol_compatible("2.0") is False
        assert is_protocol_compatible("0.9") is False

    def test_invalid_returns_false(self):
        # String que não tem `.` retorna o próprio MAJOR — só compatível
        # se for igual ao MAJOR atual (`"1"` casa, `"abc"` não casa).
        assert is_protocol_compatible("abc") is False
