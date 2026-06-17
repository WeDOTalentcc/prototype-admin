"""
Microsoft Teams Bot Service using Bot Framework.

Provides proactive notifications for key recruitment events:
- Triagem completed
- Scheduling confirmed
- Candidate timeout alerts
"""
import logging
from datetime import datetime
from typing import Any

import httpx
from botbuilder.core import (
    BotFrameworkAdapter,
    BotFrameworkAdapterSettings,
    MessageFactory,
    TurnContext,
)
from botbuilder.schema import Activity, ActivityTypes, ConversationReference

from app.core.config import settings

logger = logging.getLogger(__name__)


class TeamsBot:
    """
    Microsoft Teams Bot using Bot Framework SDK.
    Lazy-initialised: adapter is only created when credentials are configured.
    """

    def __init__(self):
        self._adapter: BotFrameworkAdapter | None = None
        self._initialised = False

    def _ensure_adapter(self) -> bool:
        if self._initialised:
            return self._adapter is not None
        self._initialised = True
        app_id = getattr(settings, "MICROSOFT_APP_ID", None)
        app_password = getattr(settings, "MICROSOFT_APP_PASSWORD", None)
        if not app_id or not app_password:
            logger.info("[TeamsBot] MICROSOFT_APP_ID/PASSWORD not configured — Teams notifications disabled")
            return False
        try:
            adapter_settings = BotFrameworkAdapterSettings(
                app_id=app_id,
                app_password=app_password,
            )
            self._adapter = BotFrameworkAdapter(adapter_settings)

            async def on_error(context: TurnContext, error: Exception):
                logger.error(f"Teams bot error: {error}", exc_info=True)
                await context.send_activity("Desculpe, ocorreu um erro. Tente novamente.")

            self._adapter.on_turn_error = on_error
            logger.info("[TeamsBot] Adapter initialised successfully")
            return True
        except Exception as exc:
            logger.error("[TeamsBot] Failed to initialise adapter: %s", exc)
            return False

    @property
    def adapter(self) -> BotFrameworkAdapter | None:
        self._ensure_adapter()
        return self._adapter

    @property
    def is_available(self) -> bool:
        return self._ensure_adapter()

    async def process_activity(self, activity: dict[str, Any], auth_header: str) -> dict[str, Any]:
        if not self._ensure_adapter():
            return {"status": "disabled", "reason": "Teams not configured"}
        activity_obj = Activity().deserialize(activity)

        async def bot_logic(turn_context: TurnContext):
            if turn_context.activity.type == ActivityTypes.message:
                await self._handle_message(turn_context)
            elif turn_context.activity.type == ActivityTypes.conversation_update:
                await self._handle_conversation_update(turn_context)
            elif turn_context.activity.type == ActivityTypes.invoke:
                await self._handle_invoke(turn_context)

        await self._adapter.process_activity(activity_obj, auth_header, bot_logic)
        return {"status": "ok"}

    async def _handle_message(self, turn_context: TurnContext):
        user_message = turn_context.activity.text
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"Received message from {turn_context.activity.from_property.name}: {user_message}")
        TurnContext.get_conversation_reference(turn_context.activity)
        await turn_context.send_activity(
            f"Recebi sua mensagem: '{user_message}'. Em breve responderei com inteligência!"
        )

    async def _handle_conversation_update(self, turn_context: TurnContext):
        if turn_context.activity.members_added:
            for member in turn_context.activity.members_added:
                if member.id != turn_context.activity.recipient.id:
                    await turn_context.send_activity(
                        f"Olá {member.name}!\n\n"
                        "Sou a **LIA**, assistente de recrutamento da WedoTalent.\n\n"
                        "Posso te ajudar a:\n"
                        "- Criar vagas\n"
                        "- Buscar candidatos\n"
                        "- Agendar entrevistas\n"
                        "- Organizar sua agenda de recrutamento\n\n"
                        "Como posso te ajudar hoje?"
                    )

    async def _handle_invoke(self, turn_context: TurnContext):
        action_data = turn_context.activity.value
        logger.info(f"Received invoke action: {action_data}")
        await turn_context.send_activity("Ação recebida! Processando...")

    async def _send_via_webhook(self, card_payload: dict[str, Any]) -> bool:
        """Send an Adaptive Card via incoming webhook URL (no conversation reference needed)."""
        webhook_url = getattr(settings, "TEAMS_WEBHOOK_URL", None)
        if not webhook_url:
            logger.debug("[TeamsBot] TEAMS_WEBHOOK_URL not configured — webhook fallback skipped")
            return False
        try:
            payload = {
                "type": "message",
                "attachments": [
                    {
                        "contentType": "application/vnd.microsoft.card.adaptive",
                        "content": card_payload,
                    }
                ],
            }
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(webhook_url, json=payload)
                resp.raise_for_status()
            logger.info("[TeamsBot] Notification sent via webhook")
            return True
        except Exception as exc:
            logger.warning("[TeamsBot] Webhook send failed: %s", exc)
            return False

    async def _deliver_card(
        self,
        card_payload: dict[str, Any],
        conversation_reference: ConversationReference | None = None,
    ) -> bool:
        """
        Deliver an Adaptive Card via proactive message (if conversation_reference
        is provided and adapter available) or via incoming webhook fallback.
        """
        if conversation_reference and self._ensure_adapter():
            try:
                async def callback(turn_context: TurnContext):
                    await turn_context.send_activity(
                        MessageFactory.attachment({
                            "contentType": "application/vnd.microsoft.card.adaptive",
                            "content": card_payload,
                        })
                    )

                await self._adapter.continue_conversation(
                    conversation_reference,
                    callback,
                    getattr(settings, "MICROSOFT_APP_ID", ""),
                )
                logger.info("[TeamsBot] Proactive message sent via adapter")
                return True
            except Exception as exc:
                logger.warning("[TeamsBot] Proactive send failed, trying webhook: %s", exc)

        return await self._send_via_webhook(card_payload)

    async def send_proactive_message(
        self,
        conversation_reference: ConversationReference,
        message: str,
        card_payload: dict[str, Any] | None = None
    ) -> bool:
        if card_payload:
            return await self._deliver_card(card_payload, conversation_reference)
        if not self._ensure_adapter():
            logger.warning("[TeamsBot] Cannot send proactive message — adapter not available")
            return False
        try:
            async def callback(turn_context: TurnContext):
                await turn_context.send_activity(message)

            await self._adapter.continue_conversation(
                conversation_reference,
                callback,
                getattr(settings, "MICROSOFT_APP_ID", ""),
            )
            logger.info("Proactive message sent successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to send proactive message: {e}", exc_info=True)
            return False

    async def send_notification(
        self,
        notification_type: str,
        data: dict[str, Any],
        conversation_reference: ConversationReference | None = None,
    ) -> bool:
        card = self._create_adaptive_card(notification_type, data)
        return await self._deliver_card(card, conversation_reference)

    async def notify_triagem_completed(
        self,
        candidate_name: str,
        job_title: str,
        score: float | None = None,
        classification: str | None = None,
        details_url: str | None = None,
        conversation_reference: ConversationReference | None = None,
    ) -> bool:
        """
        Notify recruiter that a candidate has completed triagem.
        Uses incoming webhook if no conversation_reference is provided.
        """
        data = {
            "candidate_name": candidate_name,
            "job_title": job_title,
            "completed_at": datetime.utcnow().strftime("%d/%m/%Y %H:%M UTC"),
        }
        if score is not None:
            data["score"] = f"{score:.1f}"
        if classification:
            data["classification"] = classification
        if details_url:
            data["details_url"] = details_url

        card = self._card_triagem_completed(data)
        return await self._deliver_card(card, conversation_reference)

    async def notify_scheduling_confirmed(
        self,
        candidate_name: str,
        job_title: str,
        scheduled_time: str,
        interview_type: str = "Entrevista",
        details_url: str | None = None,
        conversation_reference: ConversationReference | None = None,
    ) -> bool:
        """
        Notify recruiter that an interview scheduling has been confirmed.
        Uses incoming webhook if no conversation_reference is provided.
        """
        data = {
            "candidate_name": candidate_name,
            "job_title": job_title,
            "scheduled_time": scheduled_time,
            "interview_type": interview_type,
        }
        if details_url:
            data["details_url"] = details_url

        card = self._card_scheduling_confirmed(data)
        return await self._deliver_card(card, conversation_reference)

    async def notify_candidate_timeout(
        self,
        candidate_name: str,
        job_title: str,
        timeout_type: str = "triagem",
        hours_elapsed: float | None = None,
        details_url: str | None = None,
        conversation_reference: ConversationReference | None = None,
    ) -> bool:
        """
        Notify recruiter that a candidate has timed out.
        Uses incoming webhook if no conversation_reference is provided.
        """
        data = {
            "candidate_name": candidate_name,
            "job_title": job_title,
            "timeout_type": timeout_type,
        }
        if hours_elapsed is not None:
            data["hours_elapsed"] = str(hours_elapsed)
        if details_url:
            data["details_url"] = details_url

        card = self._card_candidate_timeout(data)
        return await self._deliver_card(card, conversation_reference)

    def _card_triagem_completed(self, data: dict[str, Any]) -> dict[str, Any]:
        facts = [
            {"title": "Candidato:", "value": data.get("candidate_name", "")},
            {"title": "Vaga:", "value": data.get("job_title", "")},
            {"title": "Concluída em:", "value": data.get("completed_at", "")},
        ]
        if data.get("score"):
            facts.append({"title": "Score WSI:", "value": data["score"]})
        if data.get("classification"):
            facts.append({"title": "Classificação:", "value": data["classification"]})

        card: dict[str, Any] = {
            "type": "AdaptiveCard",
            "version": "1.4",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "Triagem Concluída",
                    "weight": "Bolder",
                    "size": "Large",
                    "color": "Good",
                },
                {
                    "type": "FactSet",
                    "facts": facts,
                },
            ],
        }
        if data.get("details_url"):
            card["actions"] = [
                {"type": "Action.OpenUrl", "title": "Ver Detalhes", "url": data["details_url"]}
            ]
        return card

    def _card_scheduling_confirmed(self, data: dict[str, Any]) -> dict[str, Any]:
        card: dict[str, Any] = {
            "type": "AdaptiveCard",
            "version": "1.4",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "Agendamento Confirmado",
                    "weight": "Bolder",
                    "size": "Large",
                    "color": "Accent",
                },
                {
                    "type": "FactSet",
                    "facts": [
                        {"title": "Candidato:", "value": data.get("candidate_name", "")},
                        {"title": "Vaga:", "value": data.get("job_title", "")},
                        {"title": "Tipo:", "value": data.get("interview_type", "Entrevista")},
                        {"title": "Data/Hora:", "value": data.get("scheduled_time", "")},
                    ],
                },
            ],
        }
        if data.get("details_url"):
            card["actions"] = [
                {"type": "Action.OpenUrl", "title": "Ver Detalhes", "url": data["details_url"]}
            ]
        return card

    def _card_candidate_timeout(self, data: dict[str, Any]) -> dict[str, Any]:
        facts = [
            {"title": "Candidato:", "value": data.get("candidate_name", "")},
            {"title": "Vaga:", "value": data.get("job_title", "")},
            {"title": "Tipo:", "value": data.get("timeout_type", "triagem")},
        ]
        if data.get("hours_elapsed"):
            facts.append({"title": "Horas sem resposta:", "value": data["hours_elapsed"]})

        card: dict[str, Any] = {
            "type": "AdaptiveCard",
            "version": "1.4",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "Alerta de Timeout",
                    "weight": "Bolder",
                    "size": "Large",
                    "color": "Warning",
                },
                {
                    "type": "TextBlock",
                    "text": f"{data.get('candidate_name', 'Candidato')} não respondeu dentro do prazo.",
                    "wrap": True,
                },
                {
                    "type": "FactSet",
                    "facts": facts,
                },
            ],
        }
        if data.get("details_url"):
            card["actions"] = [
                {"type": "Action.OpenUrl", "title": "Ver Detalhes", "url": data["details_url"]}
            ]
        return card

    async def notify_high_match(
        self,
        candidate_name: str,
        job_title: str,
        match_score: float,
        key_matches: list[str] | None = None,
        candidate_profile_url: str | None = None,
        conversation_reference: ConversationReference | None = None,
    ) -> bool:
        """Notify recruiter about a high-match candidate via Teams Adaptive Card."""
        data = {
            "candidate_name": candidate_name,
            "job_title": job_title,
            "match_score": f"{match_score:.0f}%",
            "detected_at": datetime.utcnow().strftime("%d/%m/%Y %H:%M UTC"),
        }
        if key_matches:
            data["key_matches"] = key_matches[:5]
        if candidate_profile_url:
            data["candidate_profile_url"] = candidate_profile_url

        card = self._card_high_match(data)
        return await self._deliver_card(card, conversation_reference)

    async def notify_sla_violated(
        self,
        job_title: str,
        sla_type: str,
        expected_time: str,
        actual_time: str,
        candidates_affected: int,
        action_url: str | None = None,
        conversation_reference: ConversationReference | None = None,
    ) -> bool:
        """Notify manager about SLA violation via Teams Adaptive Card."""
        data = {
            "job_title": job_title,
            "sla_type": sla_type,
            "expected_time": expected_time,
            "actual_time": actual_time,
            "candidates_affected": str(candidates_affected),
            "detected_at": datetime.utcnow().strftime("%d/%m/%Y %H:%M UTC"),
        }
        if action_url:
            data["action_url"] = action_url

        card = self._card_sla_violated(data)
        return await self._deliver_card(card, conversation_reference)

    async def notify_goal_at_risk(
        self,
        recruiter_name: str,
        goal_name: str,
        current_progress: float,
        target: float,
        deadline: str,
        suggestions: list[str] | None = None,
        action_url: str | None = None,
        conversation_reference: ConversationReference | None = None,
    ) -> bool:
        """Notify recruiter about goal at risk via Teams Adaptive Card."""
        data = {
            "recruiter_name": recruiter_name,
            "goal_name": goal_name,
            "current_progress": f"{current_progress:.0f}%",
            "target": f"{target:.0f}%",
            "deadline": deadline,
        }
        if suggestions:
            data["suggestions"] = suggestions[:4]
        if action_url:
            data["action_url"] = action_url

        card = self._card_goal_at_risk(data)
        return await self._deliver_card(card, conversation_reference)

    def _card_high_match(self, data: dict[str, Any]) -> dict[str, Any]:
        facts = [
            {"title": "Candidato:", "value": data.get("candidate_name", "")},
            {"title": "Vaga:", "value": data.get("job_title", "")},
            {"title": "Match:", "value": data.get("match_score", "")},
            {"title": "Detectado em:", "value": data.get("detected_at", "")},
        ]
        body: list[dict[str, Any]] = [
            {
                "type": "TextBlock",
                "text": "🎯 Match Alto Detectado",
                "weight": "Bolder",
                "size": "Large",
                "color": "Good",
            },
            {"type": "FactSet", "facts": facts},
        ]
        key_matches = data.get("key_matches", [])
        if key_matches:
            body.append({
                "type": "TextBlock",
                "text": "**Principais compatibilidades:**",
                "weight": "Bolder",
                "spacing": "Medium",
            })
            for match in key_matches:
                body.append({
                    "type": "TextBlock",
                    "text": f"• {match}",
                    "wrap": True,
                    "spacing": "None",
                })

        card: dict[str, Any] = {
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "type": "AdaptiveCard",
            "version": "1.4",
            "body": body,
        }
        actions = []
        if data.get("candidate_profile_url"):
            actions.append({
                "type": "Action.OpenUrl",
                "title": "Ver Perfil Completo",
                "url": data["candidate_profile_url"],
            })
        actions.extend([
            {
                "type": "Action.Submit",
                "title": "✅ Avançar Candidato",
                "style": "positive",
                "data": {
                    "action": "advance_candidate",
                    "candidate_name": data.get("candidate_name"),
                    "job_title": data.get("job_title"),
                },
            },
            {
                "type": "Action.Submit",
                "title": "📅 Agendar Entrevista",
                "data": {
                    "action": "schedule_interview",
                    "candidate_name": data.get("candidate_name"),
                    "job_title": data.get("job_title"),
                },
            },
        ])
        card["actions"] = actions
        return card

    def _card_sla_violated(self, data: dict[str, Any]) -> dict[str, Any]:
        facts = [
            {"title": "Vaga:", "value": data.get("job_title", "")},
            {"title": "Tipo de SLA:", "value": data.get("sla_type", "")},
            {"title": "Tempo esperado:", "value": data.get("expected_time", "")},
            {"title": "Tempo atual:", "value": data.get("actual_time", "")},
            {"title": "Candidatos afetados:", "value": data.get("candidates_affected", "0")},
            {"title": "Detectado em:", "value": data.get("detected_at", "")},
        ]
        card: dict[str, Any] = {
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "type": "AdaptiveCard",
            "version": "1.4",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "⚠️ SLA Violado",
                    "weight": "Bolder",
                    "size": "Large",
                    "color": "Warning",
                },
                {
                    "type": "TextBlock",
                    "text": f"O processo seletivo para **{data.get('job_title', '')}** ultrapassou o SLA definido.",
                    "wrap": True,
                    "spacing": "Small",
                },
                {"type": "FactSet", "facts": facts, "spacing": "Medium"},
            ],
        }
        actions = []
        if data.get("action_url"):
            actions.append({
                "type": "Action.OpenUrl",
                "title": "Ver Processo",
                "url": data["action_url"],
            })
        actions.append({
            "type": "Action.Submit",
            "title": "📋 Ver Candidatos Afetados",
            "data": {"action": "view_sla_affected", "job_title": data.get("job_title")},
        })
        card["actions"] = actions
        return card

    def _card_goal_at_risk(self, data: dict[str, Any]) -> dict[str, Any]:
        facts = [
            {"title": "Meta:", "value": data.get("goal_name", "")},
            {"title": "Progresso atual:", "value": data.get("current_progress", "")},
            {"title": "Objetivo:", "value": data.get("target", "")},
            {"title": "Prazo:", "value": data.get("deadline", "")},
        ]
        body: list[dict[str, Any]] = [
            {
                "type": "TextBlock",
                "text": "⚠️ Meta em Risco",
                "weight": "Bolder",
                "size": "Large",
                "color": "Warning",
            },
            {
                "type": "TextBlock",
                "text": f"Olá **{data.get('recruiter_name', '')}**, uma das suas metas está em risco.",
                "wrap": True,
                "spacing": "Small",
            },
            {"type": "FactSet", "facts": facts, "spacing": "Medium"},
        ]
        suggestions = data.get("suggestions", [])
        if suggestions:
            body.append({
                "type": "TextBlock",
                "text": "**Sugestões para recuperação:**",
                "weight": "Bolder",
                "spacing": "Medium",
            })
            for s in suggestions:
                body.append({
                    "type": "TextBlock",
                    "text": f"• {s}",
                    "wrap": True,
                    "spacing": "None",
                })

        card: dict[str, Any] = {
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "type": "AdaptiveCard",
            "version": "1.4",
            "body": body,
        }
        actions = []
        if data.get("action_url"):
            actions.append({
                "type": "Action.OpenUrl",
                "title": "Ver Detalhes da Meta",
                "url": data["action_url"],
            })
        actions.append({
            "type": "Action.Submit",
            "title": "📊 Analisar Situação",
            "data": {"action": "analyze_goal", "goal_name": data.get("goal_name")},
        })
        card["actions"] = actions
        return card

    def _create_adaptive_card(self, notification_type: str, data: dict[str, Any]) -> dict[str, Any]:
        if notification_type == "triagem_completed":
            return self._card_triagem_completed(data)
        if notification_type == "scheduling_confirmed":
            return self._card_scheduling_confirmed(data)
        if notification_type == "candidate_timeout":
            return self._card_candidate_timeout(data)
        if notification_type == "approval_needed":
            return {
                "type": "AdaptiveCard",
                "version": "1.4",
                "body": [
                    {"type": "TextBlock", "text": "Aprovação Necessária", "weight": "Bolder", "size": "Large"},
                    {"type": "TextBlock", "text": data.get("message", ""), "wrap": True},
                ],
                "actions": [
                    {"type": "Action.Submit", "title": "Aprovar", "data": {"action": "approve", "item_id": data.get("item_id")}},
                    {"type": "Action.Submit", "title": "Rejeitar", "data": {"action": "reject", "item_id": data.get("item_id")}},
                ],
            }
        if notification_type == "interview_scheduled":
            return self._card_scheduling_confirmed(data)

        return {
            "type": "AdaptiveCard",
            "version": "1.4",
            "body": [
                {"type": "TextBlock", "text": data.get("title", "Notificação"), "weight": "Bolder", "size": "Medium"},
                {"type": "TextBlock", "text": data.get("message", ""), "wrap": True},
            ],
        }


teams_bot = TeamsBot()
