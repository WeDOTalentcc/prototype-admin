"""
Schemas para interações com sugestões no wizard de vagas.

Modelos para detecção e resposta a comandos de aceitação, rejeição,
substituição, ajuste de nível e clarificação de sugestões durante
a criação de Job Descriptions.
"""
from enum import Enum, StrEnum

from pydantic import BaseModel, Field

from .job_description import RequirementLevel
from app.shared.types import WeDoBaseModel


class SuggestionInteractionType(StrEnum):
    """Tipos de interações possíveis com sugestões"""
    ACCEPT = "accept"
    REJECT = "reject"
    REPLACE = "replace"
    ADJUST_LEVEL = "adjust_level"
    CLARIFY = "clarify"


class SuggestionInteractionRequest(WeDoBaseModel):
    """Request para processar interação com sugestões"""
    message: str = Field(
        ...,
        description="Mensagem original do recrutador"
    )
    job_id: str | None = Field(
        None,
        description="ID da vaga em processamento"
    )
    conversation_id: str | None = Field(
        None,
        description="ID da conversa/sessão"
    )
    current_suggestions: list[str] = Field(
        default_factory=list,
        description="Lista de sugestões ativas no momento"
    )


class DetectedInteraction(BaseModel):
    """Interação detectada na mensagem do recrutador"""
    interaction_type: SuggestionInteractionType = Field(
        ...,
        description="Tipo de interação detectada"
    )
    target_skill: str = Field(
        ...,
        description="Skill/competência alvo da ação"
    )
    replacement_skill: str | None = Field(
        None,
        description="Skill de substituição (para interações REPLACE)"
    )
    new_level: RequirementLevel | None = Field(
        None,
        description="Novo nível de requirement (para interações ADJUST_LEVEL)"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confiança na detecção (0-1)"
    )
    original_text: str = Field(
        ...,
        description="Trecho de texto que originou a detecção"
    )


class SuggestionInteractionResponse(BaseModel):
    """Response após processar interação com sugestões"""
    success: bool = Field(
        ...,
        description="Indica se a interação foi processada com sucesso"
    )
    interactions: list[DetectedInteraction] = Field(
        default_factory=list,
        description="Lista de interações detectadas"
    )
    updated_suggestions: list[str] = Field(
        default_factory=list,
        description="Lista atualizada de sugestões após as interações"
    )
    lia_response: str = Field(
        ...,
        description="Mensagem de confirmação/resposta da LIA ao recrutador"
    )
    feedback_logged: bool = Field(
        False,
        description="Indica se o feedback foi registrado no sistema"
    )
