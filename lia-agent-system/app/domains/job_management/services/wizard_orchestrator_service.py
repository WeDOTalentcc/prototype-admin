"""
Wizard Orchestrator Service

Detecta intenções do usuário no wizard de criação de vaga e mapeia para tool calls.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum, StrEnum
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

MAX_CONTEXT_CHARS = 16000


class WizardIntent(StrEnum):
    PUBLISH_JOB = "publish_job"
    PAUSE_JOB = "pause_job"
    CLOSE_JOB = "close_job"
    SAVE_DRAFT = "save_draft"
    VALIDATE_FIELDS = "validate_fields"
    GET_SUGGESTIONS = "get_suggestions"
    SEARCH_SALARY = "search_salary"
    UPDATE_FIELD = "update_field"
    UNKNOWN = "unknown"


INTENT_TO_TOOL_MAPPING: dict[WizardIntent, dict] = {
    WizardIntent.PUBLISH_JOB:     {"tool_name": "publish_job",     "requires_confirmation": True,  "required_params": ["job_id"]},
    WizardIntent.PAUSE_JOB:       {"tool_name": "pause_job",       "requires_confirmation": True,  "required_params": ["job_id"]},
    WizardIntent.CLOSE_JOB:       {"tool_name": "close_job",       "requires_confirmation": True,  "required_params": ["job_id", "reason"]},
    WizardIntent.SAVE_DRAFT:      {"tool_name": "save_draft",      "requires_confirmation": False, "required_params": []},
    WizardIntent.VALIDATE_FIELDS: {"tool_name": "validate_fields", "requires_confirmation": False, "required_params": []},
    WizardIntent.GET_SUGGESTIONS: {"tool_name": "get_suggestions", "requires_confirmation": False, "required_params": []},
    WizardIntent.SEARCH_SALARY:   {"tool_name": "search_salary",   "requires_confirmation": False, "required_params": ["job_title"]},
    WizardIntent.UPDATE_FIELD:    {"tool_name": "update_field",    "requires_confirmation": False, "required_params": ["field_name", "value"]},
}


@dataclass
class SuggestedToolCall:
    tool_name: str
    parameters: dict[str, Any]
    requires_confirmation: bool
    confirmation_message: str | None = None


@dataclass
class IntentDetectionResult:
    intent: WizardIntent
    confidence: float
    entities: dict[str, Any] = field(default_factory=dict)
    suggested_tool_call: SuggestedToolCall | None = None


_INTENT_KEYWORDS: list[tuple] = [
    (WizardIntent.PUBLISH_JOB,     ["publicar", "publish", "ativar vaga", "postar"]),
    (WizardIntent.PAUSE_JOB,       ["pausar", "pause", "suspender", "ocultar"]),
    (WizardIntent.CLOSE_JOB,       ["encerrar", "fechar vaga", "close", "arquivar"]),
    (WizardIntent.SAVE_DRAFT,      ["salvar", "rascunho", "draft", "guardar"]),
    (WizardIntent.VALIDATE_FIELDS, ["validar", "verificar campos", "obrigatório"]),
    (WizardIntent.GET_SUGGESTIONS, ["sugestão", "sugerir", "suggest", "opção"]),
    (WizardIntent.SEARCH_SALARY,   ["salário", "salary", "faixa salarial", "benchmark"]),
    (WizardIntent.UPDATE_FIELD,    ["atualizar", "alterar", "mudar", "update", "editar"]),
]


class WizardOrchestratorService:
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    def _detect_intent(
        self,
        message: str,
        context: dict[str, Any] | None = None,
    ) -> IntentDetectionResult:
        """Detecta intenção por keyword matching."""
        msg_lower = message.lower()
        for intent, keywords in _INTENT_KEYWORDS:
            for kw in keywords:
                if kw in msg_lower:
                    mapping = INTENT_TO_TOOL_MAPPING.get(intent)
                    tool_call = SuggestedToolCall(
                        tool_name=mapping["tool_name"],
                        parameters=context or {},
                        requires_confirmation=mapping["requires_confirmation"],
                        confirmation_message=(
                            f"Confirmar: {intent.value}?"
                            if mapping["requires_confirmation"] else None
                        ),
                    ) if mapping else None
                    return IntentDetectionResult(
                        intent=intent,
                        confidence=0.85,
                        entities={"keyword": kw},
                        suggested_tool_call=tool_call,
                    )
        return IntentDetectionResult(intent=WizardIntent.UNKNOWN, confidence=0.5)

    def process_wizard_message(
        self,
        message: str,
        context: dict[str, Any] | None = None,
        include_response: bool = True,
    ) -> dict[str, Any]:
        """Processa mensagem do wizard e retorna intenção detectada com tool suggestion."""
        detection = self._detect_intent(message, context)
        response: dict[str, Any] = {
            "intent": detection.intent.value,
            "confidence": detection.confidence,
            "entities": detection.entities,
        }

        if detection.suggested_tool_call:
            response["suggested_tool_call"] = {
                "tool_name": detection.suggested_tool_call.tool_name,
                "parameters": detection.suggested_tool_call.parameters,
                "requires_confirmation": detection.suggested_tool_call.requires_confirmation,
                "confirmation_message": detection.suggested_tool_call.confirmation_message
            }

        if include_response:
            response["conversational_response"] = self._generate_response(detection)

        return response

    def _generate_response(self, detection: IntentDetectionResult) -> str:
        """Generate a conversational response based on detection."""
        intent = detection.intent

        responses = {
            WizardIntent.PUBLISH_JOB: "Entendi que você quer publicar a vaga. Posso prosseguir com a publicação?",
            WizardIntent.PAUSE_JOB: "Certo, vou pausar a vaga. Ela ficará invisível para novos candidatos.",
            WizardIntent.CLOSE_JOB: "Você quer encerrar esta vaga. Qual o motivo do encerramento?",
            WizardIntent.SAVE_DRAFT: "Salvando as alterações como rascunho.",
            WizardIntent.VALIDATE_FIELDS: "Vou verificar se todos os campos obrigatórios estão preenchidos.",
            WizardIntent.GET_SUGGESTIONS: "Posso sugerir algumas opções. Qual campo você gostaria de completar?",
            WizardIntent.SEARCH_SALARY: "Vou buscar dados de mercado para faixa salarial.",
            WizardIntent.UPDATE_FIELD: "Qual campo você gostaria de atualizar?",
            WizardIntent.UNKNOWN: "Como posso ajudar com a vaga?",
        }

        return responses.get(intent, "Como posso ajudar?")

    def get_available_intents(self) -> list[dict[str, Any]]:
        """Get list of available wizard intents and their tool mappings."""
        return [
            {
                "intent": intent.value,
                "tool_name": mapping["tool_name"],
                "requires_confirmation": mapping["requires_confirmation"],
                "required_params": mapping["required_params"],
                "description": self._get_intent_description(intent)
            }
            for intent, mapping in INTENT_TO_TOOL_MAPPING.items()
        ]

    def _get_intent_description(self, intent: WizardIntent) -> str:
        """Get human-readable description for an intent."""
        descriptions = {
            WizardIntent.PUBLISH_JOB: "Publicar a vaga para candidatos",
            WizardIntent.PAUSE_JOB: "Pausar temporariamente a vaga",
            WizardIntent.CLOSE_JOB: "Encerrar definitivamente a vaga",
            WizardIntent.SAVE_DRAFT: "Salvar como rascunho",
            WizardIntent.VALIDATE_FIELDS: "Validar campos obrigatórios",
            WizardIntent.GET_SUGGESTIONS: "Obter sugestões de IA",
            WizardIntent.SEARCH_SALARY: "Pesquisar benchmark salarial",
            WizardIntent.UPDATE_FIELD: "Atualizar um campo específico",
        }
        return descriptions.get(intent, "")

    def build_context_for_prompt(
        self,
        context_data: dict[str, Any],
        max_chars: int = MAX_CONTEXT_CHARS
    ) -> str:
        """
        Build a formatted context string for LLM prompt injection.

        Args:
            context_data: Context data from ConversationMemory.get_context_for_llm()
                - messages: List of messages in LLM format
                - summary: Latest conversation summary
                - context_type: Type of conversation
                - context_id: Related entity ID
                - metadata: Conversation metadata with preferences
            max_chars: Maximum characters for context (default ~16000, ≈4000 tokens)

        Returns:
            Formatted context string for system prompt injection
        """
        parts = []
        parts.append("## Contexto da Conversa")

        summary = context_data.get("summary")
        if summary:
            parts.append(f"Resumo: {summary}")
        else:
            parts.append("Resumo: Início da conversa")

        messages = context_data.get("messages", [])
        if messages:
            parts.append("\nÚltimas mensagens:")
            messages_text = []
            for msg in messages[-10:]:
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                if len(content) > 300:
                    content = content[:300] + "..."
                messages_text.append(f"- [{role}]: {content}")
            parts.extend(messages_text)

        metadata = context_data.get("metadata", {})
        preferences = metadata.get("preferences") if metadata else None
        if preferences:
            parts.append("\n## Preferências do Usuário")
            if isinstance(preferences, dict):
                for key, value in preferences.items():
                    parts.append(f"- {key}: {value}")
            elif isinstance(preferences, str):
                parts.append(preferences)

        context_type = context_data.get("context_type")
        context_id = context_data.get("context_id")
        if context_type or context_id:
            parts.append("\n## Contexto Atual")
            if context_type:
                parts.append(f"Tipo: {context_type}")
            if context_id:
                parts.append(f"ID: {context_id}")

        full_context = "\n".join(parts)

        if len(full_context) > max_chars:
            truncation_note = "\n[Contexto truncado por limite de tokens]"
            full_context = full_context[:max_chars - len(truncation_note)] + truncation_note
            self.logger.warning(f"Context truncated to {max_chars} characters")

        return full_context

    async def process_wizard_message_with_memory(
        self,
        db: AsyncSession,
        message: str,
        context: dict[str, Any] | None = None,
        conversation_id: str | None = None,
        user_id: str | None = None,
        include_response: bool = True
    ) -> dict[str, Any]:
        """
        Process a wizard message with conversation memory support.

        Args:
            db: Database session
            message: User message text
            context: Optional context with job/wizard data
            conversation_id: Optional conversation ID for memory
            user_id: Optional user ID for creating new conversations
            include_response: Whether to include a conversational response

        Returns:
            Response dict with intent detection, tool suggestion, and injected context
        """
        from app.domains.recruiter_assistant.services.conversation_memory import ConversationMemory

        conversation_context = None
        injected_context = None
        memory_service = ConversationMemory()

        if conversation_id:
            try:
                conversation_context = await memory_service.get_context_for_llm(
                    db=db,
                    conversation_id=conversation_id,
                    max_messages=10,
                    include_summary=True
                )

                if conversation_context and conversation_context.get("messages"):
                    injected_context = self.build_context_for_prompt(conversation_context)
                    self.logger.info(f"Injected {len(injected_context)} chars of context from conversation {conversation_id}")

            except Exception as e:
                self.logger.warning(f"Failed to get conversation context: {e}")

        result = self.process_wizard_message(
            message=message,
            context=context,
            include_response=include_response
        )

        result["injected_context"] = injected_context
        result["conversation_id"] = conversation_id

        if conversation_id:
            try:
                await memory_service.add_message(
                    db=db,
                    conversation_id=conversation_id,
                    role="user",
                    content=message,
                    intent=result.get("intent")
                )

                if result.get("conversational_response"):
                    await memory_service.add_message(
                        db=db,
                        conversation_id=conversation_id,
                        role="assistant",
                        content=result["conversational_response"],
                        intent=result.get("intent"),
                        tool_calls=[result.get("suggested_tool_call")] if result.get("suggested_tool_call") else None
                    )

                await db.commit()
                self.logger.debug(f"Saved messages to conversation {conversation_id}")

            except Exception as e:
                self.logger.warning(f"Failed to save messages to conversation: {e}")
                await db.rollback()

        return result



wizard_orchestrator_service = WizardOrchestratorService()

# ---------------------------------------------------------------------------
# Tombstone: get_wizard_step → HTTP 410 Gone (Task #857 N-02)
# Canonical path: WS /ws/agent-chat with domain=job_creation
# ---------------------------------------------------------------------------

_WIZARD_410_DETAIL = {
    "error": (
        "Endpoint deprecated. Use WS /ws/agent-chat with "
        "domain=job_creation."
    ),
}

import logging as _logging
_wizard_orch_logger = _logging.getLogger(__name__)


async def get_wizard_step(session_id: str, _company_id: str = "", **kwargs):
    """Tombstone — raises HTTPException 410 to enforce migration away from legacy wizard."""
    _wizard_orch_logger.info(
        "wizard.legacy.deprecated_call",
        extra={
            "tenant.company_id": _company_id,
            "caller": "WizardOrchestratorService.get_wizard_step",
            "path": "wizard_orchestrator_service",
        },
    )
    raise HTTPException(status_code=410, detail=_WIZARD_410_DETAIL)
