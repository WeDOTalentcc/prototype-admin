"""
T5a UX Transformação 5 — WhatsAppAgentPlugin canonical contract tests.

Pins:
- plugin_name == "whatsapp_custom_agent"
- on_message_received: emits canonical audit row (best-effort)
- generate_response: builds prompt + uses canonical llm_service
- on_message_sent: records canonical billing + audit completion row
- Best-effort: audit/billing failures NEVER block the response

Multi-tenancy: company_id is captured at plugin construction; plugin NEVER
trusts external input.
"""
from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.domains.agent_studio.whatsapp_agent_plugin import WhatsAppAgentPlugin


COMPANY_ID = "11111111-1111-1111-1111-111111111111"
AGENT_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"


def _make_plugin(
    *,
    company_id: str = COMPANY_ID,
    agent_id: str = AGENT_ID,
    system_prompt: str = "You are LIA, recruiting assistant.",
    allowed_tools: list[str] | None = None,
    description: str | None = "Recruiter screening agent",
) -> WhatsAppAgentPlugin:
    return WhatsAppAgentPlugin(
        agent_id=agent_id,
        agent_config={
            "system_prompt": system_prompt,
            "allowed_tools": allowed_tools or [],
            "description": description,
            "pricing_tier": "pro",
        },
        company_id=company_id,
    )


class TestPluginProtocol:
    def test_plugin_name_canonical(self):
        plugin = _make_plugin()
        assert plugin.plugin_name == "whatsapp_custom_agent"

    def test_company_id_captured_at_construction(self):
        plugin = _make_plugin(company_id="co-A")
        assert plugin.company_id == "co-A"

    def test_agent_id_stringified(self):
        from uuid import UUID

        uid = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
        plugin = WhatsAppAgentPlugin(
            agent_id=uid,
            agent_config={"system_prompt": "x"},
            company_id=COMPANY_ID,
        )
        assert isinstance(plugin.agent_id, str)
        assert plugin.agent_id == str(uid)


class TestOnMessageReceived:
    @pytest.mark.asyncio
    async def test_emits_canonical_audit_row(self):
        plugin = _make_plugin()
        with patch(
            "app.shared.compliance.audit_service.AuditService"
        ) as mock_audit_cls:
            instance = MagicMock()
            instance.log_decision = AsyncMock(return_value=None)
            mock_audit_cls.return_value = instance

            await plugin.on_message_received(
                user_message="Olá, gostaria de saber sobre a vaga.",
                sender_phone="+5511999999999",
                session_id="sess-1",
                db=None,
            )
            instance.log_decision.assert_called_once()
            kwargs = instance.log_decision.call_args.kwargs
            assert kwargs["company_id"] == COMPANY_ID
            assert kwargs["decision_type"] == "whatsapp_message_received"
            assert "whatsapp_agent_plugin" in kwargs["agent_name"]

    @pytest.mark.asyncio
    async def test_audit_failure_does_not_raise(self):
        """Best-effort: audit failure must NOT block message processing."""
        plugin = _make_plugin()
        with patch(
            "app.shared.compliance.audit_service.AuditService",
            side_effect=Exception("audit DB down"),
        ):
            # Must not raise
            await plugin.on_message_received(
                user_message="test",
                sender_phone="+5511999999999",
            )


class TestGenerateResponse:
    @pytest.mark.asyncio
    async def test_calls_canonical_llm_service(self):
        plugin = _make_plugin()
        with patch(
            "app.domains.ai.services.llm.llm_service"
        ) as mock_llm:
            mock_llm.generate_with_gemini = AsyncMock(
                return_value="Olá! Sobre a vaga: ..."
            )
            response = await plugin.generate_response(
                conversation_history=[],
                user_message="Oi, sobre a vaga?",
            )
            assert "Olá" in response
            mock_llm.generate_with_gemini.assert_called_once()

    @pytest.mark.asyncio
    async def test_caps_response_at_2000_chars(self):
        plugin = _make_plugin()
        with patch(
            "app.domains.ai.services.llm.llm_service"
        ) as mock_llm:
            mock_llm.generate_with_gemini = AsyncMock(return_value="x" * 5000)
            response = await plugin.generate_response(
                conversation_history=None,
                user_message="test",
            )
            assert len(response) <= 2000

    @pytest.mark.asyncio
    async def test_uses_explicit_fallback_when_llm_empty(self):
        """REGRA 4 canonical: fallback EXPLICIT (not silent), caller sees marker."""
        plugin = _make_plugin()
        with patch(
            "app.domains.ai.services.llm.llm_service"
        ) as mock_llm:
            mock_llm.generate_with_gemini = AsyncMock(return_value="")
            response = await plugin.generate_response(
                conversation_history=[],
                user_message="oi",
            )
            # Fallback é uma string clara, não silencioso retornar None
            assert response
            assert isinstance(response, str)

    @pytest.mark.asyncio
    async def test_handles_llm_exception_with_fallback(self):
        plugin = _make_plugin()
        with patch(
            "app.domains.ai.services.llm.llm_service"
        ) as mock_llm:
            mock_llm.generate_with_gemini = AsyncMock(
                side_effect=Exception("LLM unavailable")
            )
            response = await plugin.generate_response(
                conversation_history=[],
                user_message="oi",
            )
            assert response
            assert isinstance(response, str)

    @pytest.mark.asyncio
    async def test_history_capped_at_last_6_turns(self):
        plugin = _make_plugin()
        history: list[dict[str, Any]] = [
            {"role": "user", "text": f"msg {i}"} for i in range(20)
        ]
        captured_prompt = {}

        async def _capture(prompt, model=None):
            captured_prompt["text"] = prompt
            return "response"

        with patch(
            "app.domains.ai.services.llm.llm_service"
        ) as mock_llm:
            mock_llm.generate_with_gemini = AsyncMock(side_effect=_capture)
            await plugin.generate_response(
                conversation_history=history,
                user_message="now",
            )
        # Only the last 6 turns should appear (msg 14..19)
        assert "msg 19" in captured_prompt["text"]
        assert "msg 14" in captured_prompt["text"]
        assert "msg 13" not in captured_prompt["text"]


class TestOnMessageSent:
    @pytest.mark.asyncio
    async def test_records_canonical_billing(self):
        plugin = _make_plugin()
        with patch(
            "app.services.agent_marketplace_service.agent_marketplace_service"
        ) as mock_marketplace, patch(
            "app.shared.compliance.audit_service.AuditService"
        ) as mock_audit_cls:
            mock_marketplace.record_execution = AsyncMock(return_value=None)
            instance = MagicMock()
            instance.log_decision = AsyncMock(return_value=None)
            mock_audit_cls.return_value = instance

            fake_db = MagicMock()
            await plugin.on_message_sent(
                delivery_success=True,
                response_text="ok",
                delivery_status="sent",
                db=fake_db,
            )
            mock_marketplace.record_execution.assert_called_once()
            kwargs = mock_marketplace.record_execution.call_args.kwargs
            assert kwargs["company_id"] == COMPANY_ID
            assert kwargs["agent_id"] == AGENT_ID

    @pytest.mark.asyncio
    async def test_emits_audit_completion(self):
        plugin = _make_plugin()
        with patch(
            "app.shared.compliance.audit_service.AuditService"
        ) as mock_audit_cls, patch(
            "app.services.agent_marketplace_service.agent_marketplace_service"
        ) as mock_mp:
            instance = MagicMock()
            instance.log_decision = AsyncMock(return_value=None)
            mock_audit_cls.return_value = instance
            mock_mp.record_execution = AsyncMock(return_value=None)

            await plugin.on_message_sent(
                delivery_success=True,
                response_text="ok",
                delivery_status="sent",
                db=MagicMock(),
            )
            instance.log_decision.assert_called_once()
            kwargs = instance.log_decision.call_args.kwargs
            assert kwargs["decision_type"] == "whatsapp_message_sent"
            assert kwargs["decision"] == "completed"

    @pytest.mark.asyncio
    async def test_billing_failure_does_not_raise(self):
        plugin = _make_plugin()
        with patch(
            "app.services.agent_marketplace_service.agent_marketplace_service"
        ) as mock_mp, patch(
            "app.shared.compliance.audit_service.AuditService"
        ):
            mock_mp.record_execution = AsyncMock(side_effect=Exception("billing DB down"))
            # Must not raise
            await plugin.on_message_sent(
                delivery_success=True,
                response_text="ok",
                delivery_status="sent",
                db=MagicMock(),
            )

    @pytest.mark.asyncio
    async def test_db_none_skips_billing(self):
        """Multi-tenancy safety: no db session → no DB writes."""
        plugin = _make_plugin()
        with patch(
            "app.services.agent_marketplace_service.agent_marketplace_service"
        ) as mock_mp, patch(
            "app.shared.compliance.audit_service.AuditService"
        ):
            mock_mp.record_execution = AsyncMock()
            await plugin.on_message_sent(
                delivery_success=True,
                response_text="ok",
                delivery_status="sent",
                db=None,
            )
            mock_mp.record_execution.assert_not_called()
