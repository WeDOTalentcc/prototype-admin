"""
PII Masking for log outputs.

Redacts personally identifiable information (CPF, email, phone, names)
from log messages to comply with LGPD and prevent data leaks.

Usage:
    logger = get_masked_logger(__name__)
    logger.info(f"Processing candidate {email}")  # email will be redacted
    
    # Or use the filter directly:
    handler.addFilter(PIIMaskingFilter())
"""
import re
import logging
from typing import List, Tuple, Pattern

CPF_PATTERN = re.compile(r'\b\d{3}[.\-]?\d{3}[.\-]?\d{3}[.\-/]?\d{2}\b')
EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
PHONE_BR_PATTERN = re.compile(r'(?:\+55\s?)?(?:\(?\d{2}\)?\s?)?(?:9\s?)?\d{4}[\-\s]?\d{4}\b')
NAME_IN_LOG_PATTERN = re.compile(r'(?:name|nome|candidato|recruiter|user)\s*[=:]\s*["\']([^"\']+)["\']', re.IGNORECASE)

PII_PATTERNS: List[Tuple[Pattern, str]] = [
    (CPF_PATTERN, "***CPF***"),
    (EMAIL_PATTERN, "***EMAIL***"),
    (PHONE_BR_PATTERN, "***PHONE***"),
    (NAME_IN_LOG_PATTERN, r"***NAME***"),
]


def mask_pii(text: str) -> str:
    if not text:
        return text
    masked = text
    for pattern, replacement in PII_PATTERNS:
        masked = pattern.sub(replacement, masked)
    return masked


class PIIMaskingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = mask_pii(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {k: mask_pii(str(v)) if isinstance(v, str) else v for k, v in record.args.items()}
            elif isinstance(record.args, tuple):
                record.args = tuple(mask_pii(str(a)) if isinstance(a, str) else a for a in record.args)
        return True


def get_masked_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not any(isinstance(f, PIIMaskingFilter) for f in logger.filters):
        logger.addFilter(PIIMaskingFilter())
    return logger


def install_global_pii_masking() -> None:
    root_logger = logging.getLogger()
    if not any(isinstance(f, PIIMaskingFilter) for f in root_logger.filters):
        root_logger.addFilter(PIIMaskingFilter())
        logging.getLogger(__name__).info("[PII-MASKING] Global PII masking filter installed")


import os as _os

_LLM_PROMPT_PII_STRIPPING_ENABLED = _os.environ.get("LLM_PROMPT_PII_STRIPPING_ENABLED", "true").lower() == "true"

# Quasi-identifier patterns — Layer 3 basic (no NER required)
_GRADUATION_YEAR_PATTERN = re.compile(
    r'\b(?:formad[oa]|graduad[oa]|formatura|conclu[ií][u]|bacharelad[oa]|pós[\-\s]graduad[oa])'
    r'(?:\s+em)?\s+(?:em\s+)?\d{4}\b',
    re.IGNORECASE,
)
_AGE_EXPLICIT_PATTERN = re.compile(
    r'\b(\d{2})\s*anos?\b',
    re.IGNORECASE,
)
_ADDRESS_BAIRRO_PATTERN = re.compile(
    r'\b(?:moro|resido|residente|moradora?|endere[çc]o|bairro|cep|rua|avenida|av\.|r\.)\b[^.]{0,60}',
    re.IGNORECASE,
)
_RG_PATTERN = re.compile(r'\b\d{1,2}[\.\-]?\d{3}[\.\-]?\d{3}[\-]?[0-9Xx]\b')
_CNPJ_PATTERN = re.compile(r'\b\d{2}[\.\-]?\d{3}[\.\-]?\d{3}[/\\]?\d{4}[\-]?\d{2}\b')

_LLM_PROMPT_PII_PATTERNS: List[Tuple[Pattern, str]] = [
    # Direct identifiers
    (CPF_PATTERN, "[CPF REMOVIDO]"),
    (EMAIL_PATTERN, "[EMAIL REMOVIDO]"),
    (PHONE_BR_PATTERN, "[TELEFONE REMOVIDO]"),
    (_RG_PATTERN, "[RG REMOVIDO]"),
    (_CNPJ_PATTERN, "[CNPJ REMOVIDO]"),
    # Quasi-identifiers
    (_GRADUATION_YEAR_PATTERN, "[ANO_FORMATURA REMOVIDO]"),
    (_AGE_EXPLICIT_PATTERN, "[IDADE REMOVIDA]"),
    (_ADDRESS_BAIRRO_PATTERN, "[ENDEREÇO REMOVIDO]"),
]


def strip_pii_for_llm_prompt(text: str) -> str:
    """Remove PII e quasi-identificadores de texto antes de enviar ao LLM.

    Aplica 2 camadas:
      - Layer 1: Regex direto (CPF, email, telefone, RG, CNPJ)
      - Layer 3 basic: Quasi-identificadores (ano de formatura, idade explícita,
        referências de endereço)

    Controlado pela env LLM_PROMPT_PII_STRIPPING_ENABLED (padrão: true).

    LGPD Art. 12: minimização de dados pessoais processados por sistemas de IA.
    EU AI Act Art. 13: transparência sobre dados usados em sistemas de alto risco.

    Returns:
        Texto com PII removido ou o texto original se a feature estiver desabilitada.
    """
    if not _LLM_PROMPT_PII_STRIPPING_ENABLED or not text:
        return text
    result = text
    for pattern, replacement in _LLM_PROMPT_PII_PATTERNS:
        result = pattern.sub(replacement, result)
    return result
