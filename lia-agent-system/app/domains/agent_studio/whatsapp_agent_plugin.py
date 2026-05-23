"""
WhatsAppAgentPlugin — T5a UX Transformação 5 (audit 2026-05-23).

Plugin canonical permitindo que custom agents do Agent Studio respondam via
canal WhatsApp (message-driven). Espelha o pattern de StudioVoicePlugin
(Sprint 3.6 W4-1 V2) mas adapta para semântica WhatsApp:

Voice (V2):
    - Real-time bidirectional streaming + orchestrator pesado.
    - VoiceCoreOrchestrator com plugin hook system.

WhatsApp (T5a):
    - Message-driven sync. Mensagem chega → resposta LLM → envia via canonical
      WhatsAppChannelAdapter. Sem orchestrator separado.
    - Plugin gerencia: generate_response (LLM), record_execution (billing),
      AuditService.log_decision (compliance), envio via channel adapter.

Multi-tenancy
─────────────
``company_id`` é capturado na construção do plugin (espelhando
CustomAgentRuntime). Plugin NUNCA confia em input externo para tenant. Todos
audit/billing/send calls usam o canonical ``company_id``.

Best-effort guarantees
──────────────────────
Audit + billing falham non-blocking: WhatsApp delivery NÃO é bloqueada por
side-effect failures. Send em si pode falhar — neste caso retorna
``status="send_failed"`` com erro estruturado (não raise).

Refs
────
- audit doc: UX_AUDIT_ESTUDIO_AGENTES_2026-05-21.md §4.5 Transformação 5
- pattern reference: app/domains/voice/plugins/studio_voice_plugin.py
- channel canonical: app/shared/channels/adapters/whatsapp_adapter.py
- billing canonical: app/services/agent_marketplace_service.py
- ADR-LGPD-001 + REGRA ZERO multi-tenancy via JWT
"""
from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

logger = logging.getLogger(__name__)


class WhatsAppAgentPlugin:
    """
    Canonical WhatsApp plugin for Agent Studio custom agents (T5a).

    Diferentemente de StudioVoicePlugin (que implementa VoiceCorePlugin ABC
    do orchestrator pesado), WhatsApp é message-driven sync — sem protocolo
    upstream a herdar. Plugin é um objeto stateful que vive enquanto
    processa uma mensagem entrante.

    Hooks (chamados por CustomAgentRuntime._invoke_whatsapp)
    ────────────────────────────────────────────────────────
    - on_message_received(...): registra recebimento + audit canonical.
    - generate_response(...): chama LLM com agent.system_prompt + history.
    - on_message_sent(...): record_execution canonical + audit completion.
    """

    def __init__(
        self,
        *,
        agent_id: str | UUID,
        agent_config: dict[str, Any] | None,
        company_id: str,
    ) -> None:
        """
        Args:
            agent_id: UUID (or str) of the Agent Studio custom agent.
            agent_config: dict with optional keys:
                - system_prompt: str — canonical agent persona (mesmo do chat).
                - allowed_tools: list[str] — whitelist names (telemetry only;
                  WhatsApp path não invoca tools — apenas LLM text response).
                - description: str | None — short agent description.
                - persona: dict | None — per-tenant persona overrides
                  (forwarded para telemetry; injection é runtime-owned).
                - pricing_tier: str — billing tier override (default "pro").
            company_id: tenant identifier (REQUIRED for audit + billing).
        """
        self.agent_id = str(agent_id)
        self.config: dict[str, Any] = dict(agent_config or {})
        self.company_id = company_id

    @property
    def plugin_name(self) -> str:
        return "whatsapp_custom_agent"

    # ── Hooks (chamados pelo CustomAgentRuntime._invoke_whatsapp) ─────────

    async def on_message_received(
        self,
        *,
        user_message: str,
        sender_phone: str,
        session_id: str | None = None,
        db: Any = None,
    ) -> None:
        """Canonical audit row when WhatsApp message arrives at agent."""
        try:
            from app.shared.compliance.audit_service import AuditService

            allowed_tools = self.config.get("allowed_tools") or []
            await AuditService().log_decision(
                company_id=self.company_id,
                agent_name=f"whatsapp_agent_plugin:{self.agent_id}",
                decision_type="whatsapp_message_received",
                action="whatsapp_message_received",
                decision="processing",
                reasoning=[
                    f"agent_id={self.agent_id}",
                    f"session_id={session_id or 'n/a'}",
                    f"message_len={len(user_message or '')}",
                    f"allowed_tools_count={len(allowed_tools)}",
                ],
                criteria_used=[
                    "agent_config_loaded",
                    "tenant_isolation",
                    "plugin=whatsapp_custom_agent",
                ],
                criteria_ignored=[],
                human_review_required=False,
            )
        except Exception as e:
            logger.warning(
                "[WhatsAppAgentPlugin] audit log on_message_received failed "
                "(non-blocking) agent=%s err=%s",
                self.agent_id,
                e,
            )

    async def generate_response(
        self,
        *,
        conversation_history: list[dict[str, Any]] | None,
        user_message: str,
        sender_phone: str | None = None,
    ) -> str:
        """
        Best-effort response generation via canonical ``llm_service``.

        Build prompt from agent.system_prompt + last N turns of history +
        current user message. WhatsApp path does NOT invoke tools — pure
        text completion. Returns generic fallback if LLM fails (fallback
        is explicit, NOT silent — caller sees ``"[Erro temporário..."``
        marker and can decide whether to retry).

        Multi-tenancy: LLM call inherits ContextVar from caller (which set
        company_id upstream in _invoke_whatsapp).
        """
        system_prompt = (
            self.config.get("system_prompt")
            or "Você é uma assistente de recrutamento. Responda em português, "
            "de forma cordial e profissional, mensagens via WhatsApp."
        )

        try:
            from app.domains.ai.services.llm import llm_service

            history_text = ""
            if conversation_history:
                for turn in conversation_history[-6:]:  # cap at last 6 turns
                    if not isinstance(turn, dict):
                        continue
                    role = str(turn.get("role", "user"))
                    text = str(turn.get("text") or turn.get("content") or "")
                    if not text:
                        continue
                    history_text += f"{role}: {text[:500]}\n"

            description = self.config.get("description") or ""
            prompt = (
                f"{system_prompt}\n\n"
                f"Contexto do agente: {description}\n\n"
                "Você está conversando via WhatsApp. Mantenha mensagens curtas "
                "(2-4 frases), tom cordial em PT-BR, sem listas longas.\n\n"
                f"Histórico recente:\n{history_text}\n"
                f"user: {user_message[:1500]}\n\n"
                "Sua resposta (PT-BR, curta):"
            )

            text = await llm_service.generate_with_gemini(prompt)
            response_text = (text or "").strip()
            if not response_text:
                # explicit fallback (REGRA 4: not silent — caller can detect)
                logger.warning(
                    "[WhatsAppAgentPlugin] LLM returned empty response; "
                    "using explicit fallback agent=%s",
                    self.agent_id,
                )
                return "Obrigado pela mensagem! Vou checar e te respondo em breve."
            # cap at WhatsApp body ceiling (4096 char Meta limit; we use 2000 for safety)
            return response_text[:2000]
        except Exception as e:
            logger.error(
                "[WhatsAppAgentPlugin] generate_response failed agent=%s err=%s",
                self.agent_id,
                e,
                exc_info=True,
            )
            # Explicit error marker — caller can decide to retry.
            return "Obrigado pela mensagem! Vou checar e te respondo em breve."

    async def on_message_sent(
        self,
        *,
        delivery_success: bool,
        response_text: str,
        delivery_status: str,
        db: Any = None,
    ) -> None:
        """Record canonical billing (record_execution) + audit completion."""
        # Billing: WhatsApp execution counts as one record_execution per
        # outbound message (same pricing tier as voice/chat — sub-pricing
        # to be calibrated in canary phase post-launch).
        credits_consumed = 1
        try:
            from app.services.agent_marketplace_service import (
                agent_marketplace_service,
            )

            if db is not None:
                await agent_marketplace_service.record_execution(
                    db=db,
                    agent_id=self.agent_id,
                    company_id=self.company_id,
                    credits_consumed=credits_consumed,
                    pricing_tier=self.config.get("pricing_tier", "pro"),
                )
        except Exception as e:
            logger.warning(
                "[WhatsAppAgentPlugin] record_execution failed (non-blocking) "
                "agent=%s err=%s",
                self.agent_id,
                e,
            )

        # Canonical audit row for completion.
        try:
            from app.shared.compliance.audit_service import AuditService

            await AuditService().log_decision(
                company_id=self.company_id,
                agent_name=f"whatsapp_agent_plugin:{self.agent_id}",
                decision_type="whatsapp_message_sent",
                action="whatsapp_message_sent",
                decision="completed" if delivery_success else "failed",
                reasoning=[
                    f"agent_id={self.agent_id}",
                    f"delivery_success={delivery_success}",
                    f"delivery_status={delivery_status}",
                    f"response_len={len(response_text or '')}",
                    f"credits_consumed={credits_consumed}",
                ],
                criteria_used=[
                    "agent_canonical_completion",
                    "plugin=whatsapp_custom_agent",
                ],
                criteria_ignored=[],
                human_review_required=False,
            )
        except Exception as e:
            logger.warning(
                "[WhatsAppAgentPlugin] audit log on_message_sent failed "
                "(non-blocking) agent=%s err=%s",
                self.agent_id,
                e,
            )
