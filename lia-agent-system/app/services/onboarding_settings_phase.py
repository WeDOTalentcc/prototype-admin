"""onboarding_settings_phase.py — P2-2 Sprint A.2 state machine handler.

Orquestra fase SETTINGS_EXTRACTION do onboarding conversacional:
1. Determina próxima pergunta (via yaml_loader.get_next_question)
2. Renderiza pergunta canonical pro usuário (formato chat-friendly)
3. Recebe resposta → registra em state
4. Quando bloco completo, congratula + transita

Este módulo é PURE state machine — não toca DB, não chama LLM, não envia
mensagens. Recebe estado, retorna acao. Caller (onboarding_orchestrator)
faz I/O.

Princípios canonical-fix:
- Single source of truth: yaml_loader.OnboardingConfig
- Fail-CLOSED: estado inválido raises explicitly
- Pure functions: testable sem mocks pesados

Audit ref: ~/Documents/wedotalent_audit_2026-05-26/P2-2_ONBOARDING_CONVERSACIONAL_ADR.md Sprint A.2
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from app.services.onboarding_yaml_loader import (
    OnboardingBlock,
    OnboardingConfig,
    OnboardingField,
    calculate_progress,
    get_next_question,
    is_complete,
    load_config,
)

logger = logging.getLogger(__name__)


# === Phrase detector canonical lists (PT-BR) ===
# Mantidas em module-level pra fácil ratchet + audit.
_SKIP_PHRASES: tuple[str, ...] = (
    "pular",
    "pulei",
    "skip",
    "depois",
    "não sei",
    "nao sei",
    "passar",
)

_STOP_PHRASES: tuple[str, ...] = (
    "parar",
    "chega",
    "depois faço",
    "depois faco",
    "finalizar",
    "tchau",
    "dispensar",
    "chega por hoje",
)

_YES_PHRASES: tuple[str, ...] = (
    "sim",
    "isso",
    "correto",
    "certo",
    "ta certo",
    "tá certo",
    "ok",
    "pode salvar",
    "pode",
    "afirmativo",
    "perfeito",
)

_NO_PHRASES: tuple[str, ...] = (
    "nao",
    "não",
    "errado",
    "corrigir",
    "incorreto",
    "deixa eu corrigir",
    "negativo",
)


class SettingsExtractionState(str, Enum):
    """Estados internos da fase SETTINGS_EXTRACTION."""

    INTRO = "intro"  # Primeira mensagem (greeting)
    ASKING = "asking"  # Aguardando resposta de pergunta
    CONFIRMING = "confirming"  # Mostrou extração, aguardando sim/não
    PERSISTING = "persisting"  # Salvando (estado transitório)
    COMPLETE = "complete"  # Atingiu threshold ou usuário pediu parar


class ActionType(str, Enum):
    """Tipos de ação que o handler retorna pro orchestrator executar."""

    SEND_MESSAGE = "send_message"
    EXTRACT_FIELDS = "extract_fields"
    CONFIRM_EXTRACTION = "confirm_extraction"
    PERSIST_FIELDS = "persist_fields"
    TRANSITION_BLOCK = "transition_block"
    FINALIZE = "finalize"


@dataclass
class SettingsExtractionStatus:
    """Snapshot mutável do estado da extração — caller persiste isto."""

    state: SettingsExtractionState = SettingsExtractionState.INTRO
    current_block_id: str | None = None
    answered_fields: dict[str, Any] = field(default_factory=dict)
    pending_extraction: dict[str, Any] = field(default_factory=dict)
    skipped_fields: set[str] = field(default_factory=set)
    last_asked_field: str | None = None

    @property
    def answered_field_keys(self) -> set[str]:
        return set(self.answered_fields.keys())


@dataclass(frozen=True)
class HandlerAction:
    """Ação retornada pelo handler pro orchestrator executar.

    Pure data — caller decide como executar (LLM call, DB write, etc.)
    """

    action_type: ActionType
    message: str = ""
    target_field: OnboardingField | None = None
    additional_context: list[OnboardingField] | None = None
    pending_extraction: dict[str, Any] | None = None
    progress_percent: int = 0
    next_block_id: str | None = None


# === Phrase detectors ===

def _normalize(message: str) -> str:
    return (message or "").strip().lower()


def is_skip_phrase(message: str) -> bool:
    """Detecta se usuário quer pular esta pergunta."""
    norm = _normalize(message)
    if not norm:
        return False
    # exact-ish: trata como skip se a msg É curta E bate phrase
    for phrase in _SKIP_PHRASES:
        if norm == phrase or norm.startswith(phrase + " ") or norm.endswith(" " + phrase):
            return True
    return False


def is_stop_phrase(message: str) -> bool:
    """Detecta se usuário quer terminar o onboarding agora."""
    norm = _normalize(message)
    if not norm:
        return False
    for phrase in _STOP_PHRASES:
        if phrase in norm:
            return True
    return False


def is_confirmation_yes(message: str) -> bool:
    """Detecta confirmação positiva. PT-BR informal."""
    norm = _normalize(message)
    if not norm:
        return False
    # Curto-circuito: se contém "não"/"nao" como palavra independente, NÃO é yes
    tokens = norm.replace(",", " ").replace(".", " ").replace("!", " ").split()
    if "nao" in tokens or "não" in tokens:
        return False
    for phrase in _YES_PHRASES:
        if norm == phrase:
            return True
        if phrase in tokens:
            return True
        # multi-word phrase
        if " " in phrase and phrase in norm:
            return True
    return False


def is_confirmation_no(message: str) -> bool:
    """Detecta negação / correção."""
    norm = _normalize(message)
    if not norm:
        return False
    tokens = norm.replace(",", " ").replace(".", " ").replace("!", " ").split()
    for phrase in _NO_PHRASES:
        if norm == phrase:
            return True
        if phrase in tokens:
            return True
        if " " in phrase and phrase in norm:
            return True
    return False


# === Renderers ===

def render_question_message(
    block: OnboardingBlock,
    target_field: OnboardingField,
    progress: int,
    config: OnboardingConfig | None = None,
) -> str:
    """Formata pergunta pra chat-friendly.

    Pattern:
    [Bloco X de N — Title]
    {question}
    {follow_up if any}
    Ex: {example} if any
    """
    cfg = config or load_config()
    # Block index for context
    block_idx = 0
    total_blocks = len(cfg.blocks)
    for i, b in enumerate(cfg.blocks, start=1):
        if b.id == block.id:
            block_idx = i
            break

    lines: list[str] = []
    header = f"**Bloco {block_idx} de {total_blocks} — {block.title}** ({progress}%)"
    lines.append(header)
    lines.append("")
    lines.append(target_field.question.strip())
    if target_field.follow_up:
        lines.append("")
        lines.append(target_field.follow_up.strip())
    if target_field.example_response:
        lines.append("")
        lines.append(f"_Ex: {target_field.example_response.strip()}_")
    return "\n".join(lines)


def render_confirmation_message(
    extracted_fields: dict[str, Any],
    config: OnboardingConfig | None = None,
) -> str:
    """Formata confirmação canonical via config.confirmation_template.

    Substitui {extracted_fields_summary} pelo formato:
    - field_key: value
    """
    cfg = config or load_config()
    lines: list[str] = []
    for key, value in extracted_fields.items():
        # value can be str, list, dict — render via repr-friendly
        if isinstance(value, list):
            value_str = ", ".join(str(v) for v in value)
        elif isinstance(value, dict):
            value_str = ", ".join(f"{k}={v}" for k, v in value.items())
        else:
            value_str = str(value)
        lines.append(f"- **{key}**: {value_str}")
    summary = "\n".join(lines) if lines else "(nada extraído)"
    return cfg.confirmation_template.replace("{extracted_fields_summary}", summary)


# === State machine handlers ===

def start_settings_extraction(
    config: OnboardingConfig | None = None,
) -> tuple[SettingsExtractionStatus, HandlerAction]:
    """Inicia fase. Retorna estado inicial + primeira ação (greeting)."""
    cfg = config or load_config()
    status = SettingsExtractionStatus(state=SettingsExtractionState.INTRO)
    action = HandlerAction(
        action_type=ActionType.SEND_MESSAGE,
        message=cfg.persona_greeting,
        progress_percent=0,
    )
    return status, action


def _next_question_action(
    status: SettingsExtractionStatus,
    config: OnboardingConfig,
) -> HandlerAction:
    """Helper: monta action pra próxima pergunta OR FINALIZE se completo."""
    answered = status.answered_field_keys | status.skipped_fields
    nxt = get_next_question(answered, status.current_block_id)
    progress = calculate_progress(status.answered_field_keys)
    if nxt is None or is_complete(status.answered_field_keys):
        status.state = SettingsExtractionState.COMPLETE
        return HandlerAction(
            action_type=ActionType.FINALIZE,
            message=config.persona_closing,
            progress_percent=progress,
        )
    block, target_field = nxt
    status.state = SettingsExtractionState.ASKING
    status.current_block_id = block.id
    status.last_asked_field = target_field.field_key
    msg = render_question_message(block, target_field, progress, config)
    return HandlerAction(
        action_type=ActionType.SEND_MESSAGE,
        message=msg,
        target_field=target_field,
        progress_percent=progress,
        next_block_id=block.id,
    )


def handle_user_response(
    status: SettingsExtractionStatus,
    user_message: str,
    config: OnboardingConfig | None = None,
) -> tuple[SettingsExtractionStatus, HandlerAction]:
    """Processa resposta do usuário e retorna próxima ação."""
    cfg = config or load_config()

    # Stop overrides everything
    if is_stop_phrase(user_message):
        status.state = SettingsExtractionState.COMPLETE
        progress = calculate_progress(status.answered_field_keys)
        return status, HandlerAction(
            action_type=ActionType.FINALIZE,
            message=cfg.persona_closing,
            progress_percent=progress,
        )

    if status.state == SettingsExtractionState.INTRO:
        action = _next_question_action(status, cfg)
        return status, action

    if status.state == SettingsExtractionState.ASKING:
        # Skip phrase: marca skipped, próxima pergunta
        if is_skip_phrase(user_message) and status.last_asked_field:
            status.skipped_fields.add(status.last_asked_field)
            action = _next_question_action(status, cfg)
            return status, action
        # Normal response: pede extract
        target_field: OnboardingField | None = None
        if status.last_asked_field:
            target_field = cfg.get_field(status.last_asked_field)
        return status, HandlerAction(
            action_type=ActionType.EXTRACT_FIELDS,
            message=user_message,
            target_field=target_field,
            progress_percent=calculate_progress(status.answered_field_keys),
        )

    if status.state == SettingsExtractionState.CONFIRMING:
        if is_confirmation_yes(user_message):
            return status, HandlerAction(
                action_type=ActionType.PERSIST_FIELDS,
                pending_extraction=dict(status.pending_extraction),
                progress_percent=calculate_progress(status.answered_field_keys),
            )
        if is_confirmation_no(user_message):
            # Re-ask current field — limpa pending, volta pra ASKING
            status.pending_extraction = {}
            status.state = SettingsExtractionState.ASKING
            if status.last_asked_field and status.current_block_id:
                block = cfg.get_block(status.current_block_id)
                target_field = cfg.get_field(status.last_asked_field)
                if block and target_field:
                    progress = calculate_progress(status.answered_field_keys)
                    msg = render_question_message(block, target_field, progress, cfg)
                    return status, HandlerAction(
                        action_type=ActionType.SEND_MESSAGE,
                        message=msg,
                        target_field=target_field,
                        progress_percent=progress,
                    )
            # Fallback: próxima pergunta
            return status, _next_question_action(status, cfg)
        # Ambíguo: pede confirmação de novo
        return status, HandlerAction(
            action_type=ActionType.SEND_MESSAGE,
            message="Não entendi — pode confirmar? Posso salvar (sim/não)?",
            progress_percent=calculate_progress(status.answered_field_keys),
        )

    # Estados terminais ou PERSISTING — não deveria receber input
    logger.warning(
        "handle_user_response called in unexpected state: %s", status.state
    )
    return status, HandlerAction(
        action_type=ActionType.SEND_MESSAGE,
        message=cfg.persona_closing,
        progress_percent=calculate_progress(status.answered_field_keys),
    )


def handle_extraction_result(
    status: SettingsExtractionStatus,
    extracted_fields: dict[str, Any],
    confidence: float,
    config: OnboardingConfig | None = None,
) -> tuple[SettingsExtractionStatus, HandlerAction]:
    """Após LLM extrair, monta confirmation message e transita CONFIRMING."""
    cfg = config or load_config()
    status.pending_extraction = dict(extracted_fields)
    status.state = SettingsExtractionState.CONFIRMING
    msg = render_confirmation_message(extracted_fields, cfg)
    return status, HandlerAction(
        action_type=ActionType.CONFIRM_EXTRACTION,
        message=msg,
        pending_extraction=dict(extracted_fields),
        progress_percent=calculate_progress(status.answered_field_keys),
    )


def handle_persist_success(
    status: SettingsExtractionStatus,
    persisted_fields: dict[str, Any],
    config: OnboardingConfig | None = None,
) -> tuple[SettingsExtractionStatus, HandlerAction]:
    """Após persist OK: copia pending pra answered, decide próxima ação."""
    cfg = config or load_config()
    # Merge persisted into answered_fields
    for key, value in persisted_fields.items():
        status.answered_fields[key] = value
    status.pending_extraction = {}
    # Decide next
    action = _next_question_action(status, cfg)
    return status, action
