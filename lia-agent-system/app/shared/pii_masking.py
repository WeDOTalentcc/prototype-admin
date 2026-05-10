"""
PII Masking for log outputs -- UC-P3-12 (app/shared/pii_masking.py).

PURPOSE (when to use THIS filter vs ats_pii_filter):
  Use pii_masking when you need to:
  - Sanitize log messages / exception text before they reach log sinks (LGPD accountability)
  - Strip PII from arbitrary strings before sending them to the LLM (strip_pii_for_llm_prompt)
  - Install a global Python logging filter that auto-redacts all log records

  Use ats_pii_filter (app/domains/ats_integration/services/ats_clients/ats_pii_filter.py) when:
  - Filtering outbound API payloads sent to external ATS systems (Gupy, Pandape)
  - Checking per-candidate consent before sharing fields
  - Sanitizing inbound text fields received from ATS webhooks

FIELDS COVERED:
  - Direct identifiers: CPF, email, phone (BR), RG, CNPJ
  - Quasi-identifiers (LLM prompt layer): graduation year, explicit age, address references
  - Optional NER layer via Presidio (opt-in: LLM_PROMPT_PRESIDIO_ENABLED=true)

OPERATION MODE:
  - Inline (synchronous): all functions operate on strings in-place
  - Via Python logging middleware: PIIMaskingFilter / install_global_pii_masking()
    intercepts log records across the process without changing call-sites

LGPD Art. 12 (anonimizacao/minimizacao) + EU AI Act Art. 13 (transparencia).

Usage:
    logger = get_masked_logger(__name__)
    # pii-logs ok: email/phone mascarado em runtime via PIIMaskingFilter (LGPD Art.46 + ADR-006 defesa em profundidade)
    logger.info(f"Processing candidate {email}")  # email will be redacted
    
    # Or use the filter directly:
    handler.addFilter(PIIMaskingFilter())
"""
import logging
import re
from re import Pattern

CPF_PATTERN = re.compile(r'\b\d{3}[.\-]?\d{3}[.\-]?\d{3}[.\-/]?\d{2}\b')
EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
PHONE_BR_PATTERN = re.compile(r'(?:\+55\s?)?(?:\(?\d{2}\)?\s?)?(?:9\s?)?\d{4}[\-\s]?\d{4}\b')
NAME_IN_LOG_PATTERN = re.compile(r'(?:name|nome|candidato|recruiter|user)\s*[=:]\s*["\']([^"\']+)["\']', re.IGNORECASE)
# Matches file names with common document extensions that may contain personal names
FILE_NAME_PATTERN = re.compile(
    r'\b[\w\s\-\.]{2,60}\.(?:pdf|doc|docx|txt|odt|rtf)\b',
    re.IGNORECASE,
)

PII_PATTERNS: list[tuple[Pattern, str]] = [
    (CPF_PATTERN, "***CPF***"),
    (EMAIL_PATTERN, "***EMAIL***"),
    (PHONE_BR_PATTERN, "***PHONE***"),
    (NAME_IN_LOG_PATTERN, r"***NAME***"),
    (FILE_NAME_PATTERN, "***FILENAME***"),
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
        # Mask PII in exception messages (stack traces podem expor email/CPF)
        if record.exc_info and record.exc_info[1] is not None:
            exc = record.exc_info[1]
            masked_msg = mask_pii(str(exc))
            if masked_msg != str(exc):
                # Substituir args da exceção para mascarar sem recriar o traceback
                exc.args = (masked_msg,) + exc.args[1:]
        return True


def get_masked_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not any(isinstance(f, PIIMaskingFilter) for f in logger.filters):
        logger.addFilter(PIIMaskingFilter())  # R-052: each caller gets a logger with PII masking; use lia.pii.* namespace for PII-specific loggers
    return logger


def install_global_pii_masking() -> None:
    """Instala PIIMaskingFilter no root logger e em todos os seus handlers.

    Por que handlers também?
    Child loggers (logging.getLogger(__name__)) propagam records para os
    handlers do root logger diretamente, bypassando os *filtros* do root logger.
    Adicionar o filtro nos handlers garante cobertura de todos os records
    propagados — não apenas de logs feitos diretamente no root logger.
    """
    pii_filter = PIIMaskingFilter()
    root_logger = logging.getLogger()

    # Filtro no root logger (cobre logging.debug/info direto no root)
    if not any(isinstance(f, PIIMaskingFilter) for f in root_logger.filters):
        root_logger.addFilter(pii_filter)

    # Filtro em todos os handlers existentes (cobre propagação de child loggers)
    for handler in root_logger.handlers:
        if not any(isinstance(f, PIIMaskingFilter) for f in handler.filters):
            handler.addFilter(pii_filter)

    logging.getLogger("lia.pii").info("[PII-MASKING] Global PII masking installed (logger + %d handler(s))", len(root_logger.handlers))  # R-052: PII filter uses isolated lia.pii logger


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

_LLM_PROMPT_PII_PATTERNS: list[tuple[Pattern, str]] = [
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

    Aplica até 4 camadas:
      - Layer 1: Regex direto (CPF, email, telefone, RG, CNPJ)
      - Layer 3 basic: Quasi-identificadores (ano de formatura, idade explícita,
        referências de endereço)
      - Layer 4: NER via Microsoft Presidio (opt-in, requer LLM_PROMPT_PRESIDIO_ENABLED=true
        e pacote presidio-analyzer instalado)

    Controlado pela env LLM_PROMPT_PII_STRIPPING_ENABLED (padrão: true).

    LGPD Art. 12: minimização de dados pessoais processados por sistemas de IA.
    EU AI Act Art. 13: transparência sobre dados usados em sistemas de alto risco.

    Returns:
        Texto com PII removido ou o texto original se a feature estiver desabilitada.
    """
    if not _LLM_PROMPT_PII_STRIPPING_ENABLED or not text:
        return text
    result = text
    # Layer 1 + Layer 3: regex patterns
    for pattern, replacement in _LLM_PROMPT_PII_PATTERNS:
        result = pattern.sub(replacement, result)
    # Layer 4: Presidio NER (opt-in)
    result = _presidio_layer4_strip(result)
    return result


_PRESIDIO_ENABLED = _os.environ.get("LLM_PROMPT_PRESIDIO_ENABLED", "false").lower() == "true"

_presidio_analyzer_instance = None  # lazy singleton


def _get_presidio_analyzer():
    """Retorna AnalyzerEngine do Presidio (lazy, fail-safe)."""
    global _presidio_analyzer_instance
    if _presidio_analyzer_instance is not None:
        return _presidio_analyzer_instance
    try:
        from presidio_analyzer import AnalyzerEngine
        _presidio_analyzer_instance = AnalyzerEngine()
        logging.getLogger(__name__).info("[PII-L4] Presidio AnalyzerEngine carregado")
    except ImportError:
        logging.getLogger(__name__).debug(
            "[PII-L4] presidio_analyzer não instalado — Layer 4 desabilitada. "
            "Instale com: pip install presidio-analyzer"
        )
        _presidio_analyzer_instance = None
    except Exception as exc:
        logging.getLogger(__name__).debug("[PII-L4] Presidio init falhou: %s", exc)
        _presidio_analyzer_instance = None
    return _presidio_analyzer_instance


# Entidades Presidio a remover (subconjunto relevante para currículos BR)
_PRESIDIO_ENTITIES = [
    "PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "LOCATION",
    "DATE_TIME", "NRP",  # NRP = nationality/religion/political group
]


def _presidio_layer4_strip(text: str) -> str:
    """Aplica NER Presidio para remover entidades PII não capturadas por regex.

    Fail-safe: retorna texto original em qualquer erro ou se Presidio não disponível.
    """
    if not _PRESIDIO_ENABLED or not text:
        return text
    try:
        analyzer = _get_presidio_analyzer()
        if analyzer is None:
            return text
        results = analyzer.analyze(
            text=text,
            entities=_PRESIDIO_ENTITIES,
            language="pt",
        )
        if not results:
            # Tentar fallback em inglês (currículos em inglês)
            results = analyzer.analyze(
                text=text,
                entities=_PRESIDIO_ENTITIES,
                language="en",
            )
        if not results:
            return text
        # Substituir de trás para frente para preservar índices
        redacted = list(text)
        for r in sorted(results, key=lambda x: x.start, reverse=True):
            placeholder = f"[{r.entity_type} REMOVIDO]"
            redacted[r.start:r.end] = list(placeholder)
        return "".join(redacted)
    except Exception as exc:
        logging.getLogger(__name__).debug("[PII-L4] Presidio strip falhou (fail-safe): %s", exc)
        return text
