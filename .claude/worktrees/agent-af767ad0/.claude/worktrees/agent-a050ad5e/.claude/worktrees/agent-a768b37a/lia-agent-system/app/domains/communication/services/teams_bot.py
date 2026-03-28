"""
Microsoft Teams Bot Service using Bot Framework.
"""
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
import httpx
from botbuilder.core import (
    BotFrameworkAdapter,
    BotFrameworkAdapterSettings,
    TurnContext,
    ConversationReference,
    MessageFactory
)
from botbuilder.schema import Activity, ActivityTypes, ChannelAccount

from app.core.config import settings

logger = logging.getLogger(__name__)


class TeamsBot:
    """
    Microsoft Teams Bot using Bot Framework SDK.
    """
    
    def __init__(self):
        """Initialize Teams Bot."""
        # Bot Framework adapter settings
        adapter_settings = BotFrameworkAdapterSettings(
            app_id=settings.MICROSOFT_APP_ID,
            app_password=settings.MICROSOFT_APP_PASSWORD
        )
        
        self.adapter = BotFrameworkAdapter(adapter_settings)
        
        # Error handler
        async def on_error(context: TurnContext, error: Exception):
            logger.error(f"Teams bot error: {error}", exc_info=True)
            await context.send_activity("Desculpe, ocorreu um erro. Tente novamente.")
        
        self.adapter.on_turn_error = on_error
    
    async def process_activity(self, activity: Dict[str, Any], auth_header: str) -> Dict[str, Any]:
        """
        Process incoming activity from Teams.
        
        Args:
            activity: Activity payload from Teams
            auth_header: Authorization header for validation
            
        Returns:
            Response to send back to Teams
        """
        # Create Activity object
        activity_obj = Activity().deserialize(activity)
        
        # Process through adapter
        async def bot_logic(turn_context: TurnContext):
            """Handle the activity."""
            if turn_context.activity.type == ActivityTypes.message:
                # User sent a message
                await self._handle_message(turn_context)
            
            elif turn_context.activity.type == ActivityTypes.conversation_update:
                # Bot added/removed or members added/removed
                await self._handle_conversation_update(turn_context)
            
            elif turn_context.activity.type == ActivityTypes.invoke:
                # Adaptive card action
                await self._handle_invoke(turn_context)
        
        # Process activity
        await self.adapter.process_activity(activity_obj, auth_header, bot_logic)
        
        return {"status": "ok"}
    
    async def _handle_message(self, turn_context: TurnContext):
        """Handle incoming message."""
        user_message = turn_context.activity.text
        
        logger.info(f"Received message from {turn_context.activity.from_property.name}: {user_message}")
        
        # Store conversation reference for proactive messaging
        conversation_ref = TurnContext.get_conversation_reference(turn_context.activity)
        
        # TODO: Integrate with LIA conversation agent
        # For now, send acknowledgment
        await turn_context.send_activity(
            f"Recebi sua mensagem: '{user_message}'. Em breve responderei com inteligência!"
        )
    
    async def _handle_conversation_update(self, turn_context: TurnContext):
        """Handle conversation update (bot added, members added, etc)."""
        if turn_context.activity.members_added:
            for member in turn_context.activity.members_added:
                if member.id != turn_context.activity.recipient.id:
                    # New member added (not the bot itself)
                    await turn_context.send_activity(
                        f"Olá {member.name}! 👋\n\n"
                        "Sou a **LIA**, assistente de recrutamento da WedoTalent.\n\n"
                        "Posso te ajudar a:\n"
                        "- Criar vagas\n"
                        "- Buscar candidatos\n"
                        "- Agendar entrevistas\n"
                        "- Organizar sua agenda de recrutamento\n\n"
                        "Como posso te ajudar hoje?"
                    )
    
    async def _handle_invoke(self, turn_context: TurnContext):
        """Handle adaptive card action."""
        # Extract action data
        action_data = turn_context.activity.value
        
        logger.info(f"Received invoke action: {action_data}")
        
        # TODO: Handle different action types
        await turn_context.send_activity("Ação recebida! Processando...")
    
    async def send_proactive_message(
        self,
        conversation_reference: ConversationReference,
        message: str,
        card_payload: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send proactive message to user.
        
        Args:
            conversation_reference: Stored conversation reference
            message: Text message to send
            card_payload: Optional adaptive card payload
            
        Returns:
            True if sent successfully
        """
        try:
            async def callback(turn_context: TurnContext):
                """Send the message."""
                if card_payload:
                    # Send adaptive card
                    await turn_context.send_activity(
                        MessageFactory.attachment({
                            "contentType": "application/vnd.microsoft.card.adaptive",
                            "content": card_payload
                        })
                    )
                else:
                    # Send text message
                    await turn_context.send_activity(message)
            
            # Continue conversation
            await self.adapter.continue_conversation(
                conversation_reference,
                callback,
                settings.MICROSOFT_APP_ID
            )
            
            logger.info(f"Proactive message sent successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send proactive message: {e}", exc_info=True)
            return False
    
    async def send_notification(
        self,
        conversation_reference: ConversationReference,
        notification_type: str,
        data: Dict[str, Any]
    ) -> bool:
        """
        Send notification with adaptive card.
        
        Args:
            conversation_reference: Stored conversation reference
            notification_type: Type of notification (approval_needed, interview_scheduled, etc)
            data: Notification data
            
        Returns:
            True if sent successfully
        """
        # Generate adaptive card based on notification type
        card = self._create_adaptive_card(notification_type, data)
        
        return await self.send_proactive_message(
            conversation_reference,
            message=data.get("message", ""),
            card_payload=card
        )
    
    def _create_adaptive_card(self, notification_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create adaptive card for notification.
        
        Args:
            notification_type: Type of notification
            data: Notification data
            
        Returns:
            Adaptive card JSON
        """
        if notification_type == "approval_needed":
            return {
                "type": "AdaptiveCard",
                "version": "1.4",
                "body": [
                    {
                        "type": "TextBlock",
                        "text": "✅ Aprovação Necessária",
                        "weight": "Bolder",
                        "size": "Large"
                    },
                    {
                        "type": "TextBlock",
                        "text": data.get("message", ""),
                        "wrap": True
                    }
                ],
                "actions": [
                    {
                        "type": "Action.Submit",
                        "title": "Aprovar",
                        "data": {
                            "action": "approve",
                            "item_id": data.get("item_id")
                        }
                    },
                    {
                        "type": "Action.Submit",
                        "title": "Rejeitar",
                        "data": {
                            "action": "reject",
                            "item_id": data.get("item_id")
                        }
                    }
                ]
            }
        
        elif notification_type == "interview_scheduled":
            return {
                "type": "AdaptiveCard",
                "version": "1.4",
                "body": [
                    {
                        "type": "TextBlock",
                        "text": "📅 Entrevista Agendada",
                        "weight": "Bolder",
                        "size": "Large"
                    },
                    {
                        "type": "FactSet",
                        "facts": [
                            {
                                "title": "Candidato:",
                                "value": data.get("candidate_name", "")
                            },
                            {
                                "title": "Vaga:",
                                "value": data.get("job_title", "")
                            },
                            {
                                "title": "Data/Hora:",
                                "value": data.get("scheduled_time", "")
                            }
                        ]
                    }
                ],
                "actions": [
                    {
                        "type": "Action.OpenUrl",
                        "title": "Ver Detalhes",
                        "url": data.get("details_url", "")
                    }
                ]
            }
        
        # Default card
        return {
            "type": "AdaptiveCard",
            "version": "1.4",
            "body": [
                {
                    "type": "TextBlock",
                    "text": data.get("title", "Notificação"),
                    "weight": "Bolder",
                    "size": "Medium"
                },
                {
                    "type": "TextBlock",
                    "text": data.get("message", ""),
                    "wrap": True
                }
            ]
        }


# Global Teams bot instance
teams_bot = TeamsBot()
