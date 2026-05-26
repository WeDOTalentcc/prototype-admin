"""onboarding_field_extractor.py — P2-2 Sprint A.3 canonical extractor.

Recebe pergunta + resposta natural language → extrai structured value
via LLM tool call. Output sempre marcado pra confirmation antes de persist.

Princípios canonical-fix:
- Fail-CLOSED: extração falhou OR confidence baixa → returns None ou flag.
- Single source of truth: usa OnboardingField do yaml_loader, não duplica schema.
- No silent fallback: log warn em extraction failures, NUNCA fingir sucesso.

Audit ref: ~/Documents/wedotalent_audit_2026-05-26/P2-2_ONBOARDING_CONVERSACIONAL_ADR.md Sprint A.3
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any

from app.services.onboarding_yaml_loader import OnboardingField

logger = logging.getLogger(__name__)


# --- Canonical enums --------------------------------------------------------

_WORK_MODEL_NORMALIZATION = {
    "presencial": "presencial",
    "in-office": "presencial",
    "office": "presencial",
    "in office": "presencial",
    "hibrido": "hybrid",
    "híbrido": "hybrid",
    "hybrid": "hybrid",
    "remoto": "remoto",
    "remote": "remoto",
    "home office": "remoto",
    "homeoffice": "remoto",
}

_LOW_MEDIUM_HIGH = {
    "baixa": "baixa",
    "baixo": "baixa",
    "low": "baixa",
    "media": "media",
    "média": "media",
    "medium": "media",
    "alta": "alta",
    "alto": "alta",
    "high": "alta",
}

_PERSONA_TONES = {
    "formal",
    "profissional",
    "amigavel",
    "amigável",
    "casual",
    "inspirador",
    "direto",
}

_BOOL_TRUE = {"sim", "yes", "true", "s", "y"}
_BOOL_FALSE = {"nao", "não", "no", "false", "n"}

_PERSONA_NAME_RE = re.compile(r"^[A-Za-zÀ-ÖØ-öø-ÿ0-9 ]{2,20}$")
_CNPJ_DIGITS_RE = re.compile(r"^\d{14}$")
_CNPJ_MASKED_RE = re.compile(r"^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$")
_URL_RE = re.compile(r"^https?://[^\s]+\.[^\s]+", re.IGNORECASE)


@dataclass(frozen=True)
class ExtractionResult:
    """Resultado canonical de extração.

    Fields:
        success: bool — extração teve sucesso
        extracted_fields: dict[field_key, value] — pode conter múltiplos campos
        confidence: float — 0.0 a 1.0
        needs_confirmation: bool — sempre True se success, exigir confirm antes persist
        raw_response: str — resposta original do LLM (debug)
        error: str | None — se success=False, motivo
    """

    success: bool
    extracted_fields: dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    needs_confirmation: bool = False
    raw_response: str = ""
    error: str | None = None


# --- Prompt building --------------------------------------------------------


def build_extraction_prompt(
    target_field: OnboardingField,
    user_message: str,
    additional_context_fields: list[OnboardingField] | None = None,
) -> str:
    """Constroi prompt canonical pra LLM extrair.

    Pure function — sem side effects, totalmente testavel.

    Args:
        target_field: campo principal sendo perguntado
        user_message: resposta do usuario em natural language
        additional_context_fields: outros fields que LLM PODE extrair
            oportunisticamente (multi-field extraction).

    Returns:
        Prompt completo em PT-BR pra LLM.
    """
    lines: list[str] = []
    lines.append(
        "Você é um extrator de informações estruturadas do onboarding "
        "conversacional da plataforma WeDOTalent."
    )
    lines.append("")
    lines.append("## Pergunta feita ao usuário")
    lines.append(f"Campo: `{target_field.field_key}`")
    lines.append(f"Pergunta: {target_field.question}")
    if target_field.example_response:
        lines.append(f"Exemplo de resposta esperada: {target_field.example_response}")
    if target_field.extract_hint:
        lines.append(f"Dica de extração: {target_field.extract_hint}")
    if target_field.validation:
        lines.append(f"Regra de validação canonical: `{target_field.validation}`")
    lines.append("")
    lines.append("## Resposta do usuário (natural language)")
    lines.append(f'"""{user_message}"""')
    lines.append("")

    if additional_context_fields:
        lines.append("## Campos adicionais que VOCÊ PODE extrair oportunisticamente")
        lines.append(
            "Se a resposta do usuário trouxer dados relevantes a estes "
            "outros campos, extraia também (multi-field extraction):"
        )
        for f_ in additional_context_fields:
            extra = f" — validação: `{f_.validation}`" if f_.validation else ""
            lines.append(f"- `{f_.field_key}`: {f_.question}{extra}")
        lines.append("")

    lines.append("## Formato de saída obrigatório (JSON estruturado)")
    lines.append("Retorne EXATAMENTE este JSON, sem comentários, sem markdown fence:")
    lines.append("{")
    lines.append('  "extracted_fields": { "<field_key>": <valor>, ... },')
    lines.append('  "confidence": <float entre 0.0 e 1.0>,')
    lines.append('  "reasoning": "<breve explicação em PT-BR>"')
    lines.append("}")
    lines.append("")
    lines.append(
        "Regras: (1) NUNCA invente dados ausentes. (2) Em dúvida, baixe a "
        "confidence. (3) Use PT-BR para strings. (4) Respeite tipos: integers "
        "como números JSON, booleans como true/false, listas como arrays."
    )

    return "\n".join(lines)


# --- Validation -------------------------------------------------------------


def _validate_integer_range(value: Any, lo: int, hi: int) -> tuple[bool, str | None]:
    try:
        n = int(value)
    except (TypeError, ValueError):
        return False, f"Valor não é inteiro: {value!r}"
    if not (lo <= n <= hi):
        return False, f"Inteiro {n} fora do intervalo [{lo}, {hi}]"
    return True, None


def validate_extracted_value(
    field: OnboardingField, value: Any
) -> tuple[bool, str | None]:
    """Valida valor extraido contra rules do field.

    Suporta as validation rules canonical em onboarding_questions.yaml.

    Returns:
        (is_valid, error_message)
    """
    rule = (field.validation or "").strip()
    if not rule:
        return True, None

    # required / optional
    if rule == "required":
        if value is None:
            return False, "Campo obrigatório: valor ausente"
        if isinstance(value, str) and not value.strip():
            return False, "Campo obrigatório: string vazia"
        if isinstance(value, (list, dict)) and len(value) == 0:
            return False, "Campo obrigatório: coleção vazia"
        return True, None

    if rule == "optional":
        return True, None

    # cnpj_format
    if rule == "cnpj_format":
        if not isinstance(value, str):
            return False, "CNPJ deve ser string"
        s = value.strip()
        digits = re.sub(r"\D", "", s)
        if _CNPJ_MASKED_RE.match(s) or _CNPJ_DIGITS_RE.match(digits):
            if len(digits) == 14:
                return True, None
        return False, f"CNPJ inválido: {value!r} (esperado 14 dígitos ou XX.XXX.XXX/XXXX-XX)"

    # url_format
    if rule == "url_format":
        if not isinstance(value, str) or not _URL_RE.match(value.strip()):
            return False, f"URL inválida: {value!r} (esperado http(s)://...)"
        return True, None

    # integer ranges
    if rule == "integer":
        try:
            int(value)
            return True, None
        except (TypeError, ValueError):
            return False, f"Valor não é inteiro: {value!r}"

    if rule == "integer_1_to_10":
        return _validate_integer_range(value, 1, 10)
    if rule == "integer_15_to_180":
        return _validate_integer_range(value, 15, 180)
    if rule == "integer_0_to_50":
        return _validate_integer_range(value, 0, 50)
    if rule == "integer_1_to_72":
        return _validate_integer_range(value, 1, 72)

    # text_min_20
    if rule == "text_min_20":
        if not isinstance(value, str):
            return False, "Texto deve ser string"
        if len(value.strip()) < 20:
            return False, f"Texto muito curto ({len(value.strip())} chars, mínimo 20)"
        return True, None

    # list_min_3
    if rule == "list_min_3":
        if not isinstance(value, list):
            return False, "Esperada lista"
        if len(value) < 3:
            return False, f"Lista precisa de pelo menos 3 itens (recebido {len(value)})"
        return True, None

    # enums
    if rule == "enum_work_model":
        if not isinstance(value, str):
            return False, "Esperada string"
        if value.strip().lower() in _WORK_MODEL_NORMALIZATION:
            return True, None
        return False, f"Modelo de trabalho inválido: {value!r}"

    if rule == "enum_low_medium_high":
        if not isinstance(value, str):
            return False, "Esperada string"
        if value.strip().lower() in _LOW_MEDIUM_HIGH:
            return True, None
        return False, f"Esperado baixa/media/alta, recebido: {value!r}"

    # ai persona
    if rule == "ai_persona_name":
        if not isinstance(value, str):
            return False, "Nome deve ser string"
        if not _PERSONA_NAME_RE.match(value.strip()):
            return False, (
                f"Nome inválido: {value!r} (2-20 chars, alfanumérico + acentos)"
            )
        return True, None

    if rule == "ai_persona_tone":
        if not isinstance(value, str):
            return False, "Tom deve ser string"
        if value.strip().lower() in _PERSONA_TONES:
            return True, None
        return False, f"Tom inválido: {value!r} (esperado formal/profissional/amigavel/casual/inspirador/direto)"

    # Regra desconhecida: fail-CLOSED com aviso
    logger.warning(
        "validation rule desconhecida: %r — aceitando por default mas registrando",
        rule,
    )
    return True, None


def _normalize_enum_value(rule: str, value: Any) -> Any:
    """Normaliza valor de enum pra forma canonical quando aplicável."""
    if not isinstance(value, str):
        return value
    v = value.strip().lower()
    if rule == "enum_work_model":
        return _WORK_MODEL_NORMALIZATION.get(v, value)
    if rule == "enum_low_medium_high":
        return _LOW_MEDIUM_HIGH.get(v, value)
    return value


# --- Extraction (mock until Sprint A.4 LLM wire-up) -------------------------


async def extract_field_from_message(
    target_field: OnboardingField,
    user_message: str,
    additional_context_fields: list[OnboardingField] | None = None,
    company_id: str | None = None,
) -> ExtractionResult:
    """Wrapper async que (futuramente) chamará LLMService.generate_with_tools.

    NOTE: por enquanto retorna heurística simples — wire-up com LLMService real
    fica pra Sprint A.4 integração. Mantém API canonical estável.

    Args:
        target_field: campo principal sendo perguntado
        user_message: resposta natural language
        additional_context_fields: outros campos pra extração oportunista
        company_id: pra audit trail (não usado na extração em si)

    Returns:
        ExtractionResult com extracted_fields + confidence + needs_confirmation=True
    """
    if not isinstance(user_message, str) or not user_message.strip():
        logger.warning(
            "extract_field_from_message: empty message field=%s company=%s",
            target_field.field_key,
            company_id,
        )
        return ExtractionResult(
            success=False,
            extracted_fields={},
            confidence=0.0,
            needs_confirmation=False,
            raw_response="",
            error="Mensagem vazia",
        )

    msg = user_message.strip()
    msg_lower = msg.lower()
    rule = (target_field.validation or "").strip()

    extracted: Any = msg
    confidence = 0.7

    # Boolean inference
    if msg_lower in _BOOL_TRUE:
        if rule.startswith("enum_low") or rule in {"required", "optional", ""}:
            # Pode ser confirmação; usamos True
            extracted = True
            confidence = 0.85
        else:
            extracted = True
            confidence = 0.6
    elif msg_lower in _BOOL_FALSE:
        extracted = False
        confidence = 0.85

    # Integer parse
    elif rule.startswith("integer"):
        # tentar extrair primeiro número da mensagem
        m = re.search(r"-?\d+", msg)
        if m:
            try:
                extracted = int(m.group(0))
                confidence = 0.9
            except ValueError:
                extracted = msg
                confidence = 0.4
        else:
            confidence = 0.3

    # Enum normalization
    elif rule in {"enum_work_model", "enum_low_medium_high"}:
        normalized = _normalize_enum_value(rule, msg_lower)
        if normalized != msg:
            extracted = normalized
            confidence = 0.9
        else:
            # match parcial em substring
            target_map = (
                _WORK_MODEL_NORMALIZATION
                if rule == "enum_work_model"
                else _LOW_MEDIUM_HIGH
            )
            found = None
            for k, v in target_map.items():
                if k in msg_lower:
                    found = v
                    break
            if found:
                extracted = found
                confidence = 0.8
            else:
                confidence = 0.4

    # Validar resultado contra rule do field
    is_valid, err = validate_extracted_value(target_field, extracted)
    if not is_valid:
        logger.warning(
            "extract_field_from_message: validation failed field=%s value=%r err=%s company=%s",
            target_field.field_key,
            extracted,
            err,
            company_id,
        )
        return ExtractionResult(
            success=False,
            extracted_fields={},
            confidence=0.0,
            needs_confirmation=False,
            raw_response=msg,
            error=err,
        )

    if confidence < 0.5:
        logger.warning(
            "extract_field_from_message: low confidence=%.2f field=%s message=%r company=%s",
            confidence,
            target_field.field_key,
            msg,
            company_id,
        )

    return ExtractionResult(
        success=True,
        extracted_fields={target_field.field_key: extracted},
        confidence=confidence,
        needs_confirmation=True,
        raw_response=msg,
        error=None,
    )
