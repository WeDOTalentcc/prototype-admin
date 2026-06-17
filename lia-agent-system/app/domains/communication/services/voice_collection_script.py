"""
Voice data-collection — funções PURAS (Fase 4 fundação).

Sem I/O, sem DB. O orquestrador de voz (sessão dedicada, real-time) consome estas
funções para:
- montar um roteiro falado ordenado a partir dos campos pendentes do DataRequest;
- normalizar/validar respostas faladas por DataFieldType;
- decidir quais campos exigem read-back de confirmação (sensíveis) e quais NÃO podem
  ser coletados por voz (arquivo → portal).

Limite honesto (decisão Paulo 2026-06-06): arquivo/foto não se coletam por voz —
seguem pro portal; voz coleta campos verbais. Sensível exige confirmação verbal.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

# Tipos não-coletáveis por voz (exigem upload → portal)
_FILE_TYPES = {"file", "photo"}

# Tipos intrinsecamente sensíveis → read-back de confirmação obrigatório
_SENSITIVE_TYPES = {"cpf", "cnpj", "currency", "number"}

# Pistas no NOME do campo que indicam dado sensível (banco/PIS/RG/salário)
_SENSITIVE_NAME_HINTS = (
    "bank", "banc", "pis", "pasep", "rg", "conta", "agencia", "agência",
    "iban", "cpf", "cnpj", "salar", "pix",
)

# Palavras-número PT → dígito (p/ CPF/telefone ditados verbalmente)
_PT_DIGITS = {
    "zero": "0", "um": "1", "uma": "1", "dois": "2", "duas": "2",
    "tres": "3", "três": "3", "quatro": "4", "cinco": "5", "seis": "6",
    "meia": "6", "sete": "7", "oito": "8", "nove": "9",
}


@dataclass(frozen=True)
class VoiceFieldPrompt:
    """Um campo a ser pedido por voz."""
    name: str
    label: str
    field_type: str
    required: bool
    voice_collectable: bool  # False → arquivo, redirecionar ao portal
    sensitive: bool          # True → read-back de confirmação obrigatório


@dataclass(frozen=True)
class NormalizedValue:
    value: str | None
    valid: bool
    error: str | None = None


def is_voice_collectable(field_type: str) -> bool:
    """Campos de arquivo/foto não se coletam por voz."""
    return (field_type or "").lower() not in _FILE_TYPES


def is_sensitive_field(name: str, field_type: str) -> bool:
    """Campo exige read-back de confirmação (por tipo OU por nome)."""
    ft = (field_type or "").lower()
    nm = (name or "").lower()
    if ft in _SENSITIVE_TYPES:
        return True
    return any(h in nm for h in _SENSITIVE_NAME_HINTS)


def _coerce_type(raw_type) -> str:
    """Aceita str ou enum (DataFieldType) e devolve o valor lowercase."""
    if raw_type is None:
        return "text"
    return (raw_type.value if hasattr(raw_type, "value") else str(raw_type)).lower()


def build_collection_script(
    fields_requested: list[dict] | None,
    completed_names: list[str] | set[str] | None = None,
) -> list[VoiceFieldPrompt]:
    """
    Ordena os campos PENDENTES (não-completados) em prompts de voz, preservando a ordem.

    fields_requested: lista de dicts com {name, label, field_type|type, is_required|required}.
    completed_names: nomes já coletados (pulados).
    """
    done = set(completed_names or [])
    out: list[VoiceFieldPrompt] = []
    for f in fields_requested or []:
        name = (f.get("name") or "").strip()
        if not name or name in done:
            continue
        ft = _coerce_type(f.get("field_type") or f.get("type"))
        label = f.get("label") or f.get("displayName") or name
        required = bool(f.get("is_required", f.get("required", True)))
        out.append(
            VoiceFieldPrompt(
                name=name,
                label=label,
                field_type=ft,
                required=required,
                voice_collectable=is_voice_collectable(ft),
                sensitive=is_sensitive_field(name, ft),
            )
        )
    return out


def portal_only_fields(script: list[VoiceFieldPrompt]) -> list[VoiceFieldPrompt]:
    """Campos que NÃO podem ser coletados por voz (devem ir ao portal)."""
    return [p for p in script if not p.voice_collectable]


def _digits_from_speech(raw: str) -> str:
    """Extrai dígitos diretos + converte palavras-número PT em dígitos."""
    tokens = re.split(r"[\s,.\-]+", (raw or "").lower())
    chars: list[str] = []
    for t in tokens:
        if t.isdigit():
            chars.append(t)
        elif t in _PT_DIGITS:
            chars.append(_PT_DIGITS[t])
    return "".join(chars)


def normalize_field_value(field_type: str, raw: str) -> NormalizedValue:
    """Normaliza/valida uma resposta falada conforme o tipo do campo."""
    ft = _coerce_type(field_type)
    raw = (raw or "").strip()
    if not raw:
        return NormalizedValue(None, False, "empty")

    if ft == "cpf":
        # dígitos literais (com pontuação) têm precedência; senão, número ditado por extenso
        d = re.sub(r"\D", "", raw) or _digits_from_speech(raw)
        return NormalizedValue(d, len(d) == 11, None if len(d) == 11 else "cpf_invalid_length")
    if ft == "cnpj":
        d = re.sub(r"\D", "", raw) or _digits_from_speech(raw)
        return NormalizedValue(d, len(d) == 14, None if len(d) == 14 else "cnpj_invalid_length")
    if ft == "phone":
        d = re.sub(r"\D", "", raw) or _digits_from_speech(raw)
        return NormalizedValue(d, 10 <= len(d) <= 13, None if 10 <= len(d) <= 13 else "phone_invalid_length")
    if ft == "number":
        d = re.sub(r"\D", "", raw)
        return NormalizedValue(d, bool(d), None if d else "number_invalid")
    if ft == "email":
        v = raw.lower().replace(" arroba ", "@").replace(" ponto ", ".").replace(" ", "")
        ok = bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", v))
        return NormalizedValue(v, ok, None if ok else "email_invalid")
    if ft == "date":
        # parsing de data falada fica na camada de orquestração (LLM); aqui passa cru
        return NormalizedValue(raw, True, None)
    # text / textarea / address / select / currency-as-text → texto livre
    return NormalizedValue(raw, True, None)
