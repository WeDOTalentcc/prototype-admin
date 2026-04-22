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
import logging
import os as _os
import re
from re import Pattern

CPF_PATTERN = re.compile(r'\b\d{3}[.\-]?\d{3}[.\-]?\d{3}[.\-/]?\d{2}\b')
EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
PHONE_BR_PATTERN = re.compile(r'(?<!\d)(?:\+55\s?)?(?:\(?\d{2}\)?\s?)?(?:9\s?)?\d{4}[\-\s]?\d{4}(?!\d)')
NAME_IN_LOG_PATTERN = re.compile(r'(?:name|nome|candidato|recruiter|user)\s*[=:]\s*["\']([^"\']+)["\']', re.IGNORECASE)

PII_PATTERNS: list[tuple[Pattern, str]] = [
    (CPF_PATTERN, "***CPF***"),
    (EMAIL_PATTERN, "***EMAIL***"),
    (PHONE_BR_PATTERN, "***PHONE***"),
    (NAME_IN_LOG_PATTERN, r"***NAME***"),
]

# ────────────────────────────────────────────────────────────────────────────
# Onda 2.1 G5 light (2026-04-21) — Response-boundary PII redaction with audit.
#
# Existing PII_PATTERNS are log-focused (mask_pii + PIIMaskingFilter) —
# they mutate in place without telling the caller WHAT was redacted.
# Response-boundary use case needs audit trail per LGPD Art. 12 + 13:
# who saw what, when, under which control.
#
# Adds:
#   - CNPJ pattern (PT-BR company tax id, missing from PII_PATTERNS)
#   - Full-name heuristic (capitalized 2+ word runs — HIGH false-positive
#     rate, opt-in via redact_response_with_audit strict_mode=True)
#   - redact_response_with_audit(text) → (redacted, audit_log)
# ────────────────────────────────────────────────────────────────────────────

CNPJ_PATTERN = re.compile(r'\b\d{2}[.\-]?\d{3}[.\-]?\d{3}/?\d{4}[\-]?\d{2}\b')

# Heuristic: PT-BR full name with accents (opt-in via strict_mode)
# Matches 2+ capitalized words in sequence where each starts uppercase
# and has accented-lowercase continuation.
FULL_NAME_HEURISTIC = re.compile(
    r'\b[A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]{2,}(?:\s+[A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]{2,}){1,}\b'
)

# Response-boundary patterns: higher signal than log-level (adds CNPJ + name heuristic).
_RESPONSE_PATTERNS: list[tuple[Pattern, str, str]] = [
    # (pattern, replacement, pii_type_label_for_audit)
    (CPF_PATTERN, "[CPF REDACTED]", "cpf"),
    (CNPJ_PATTERN, "[CNPJ REDACTED]", "cnpj"),
    (EMAIL_PATTERN, "[EMAIL REDACTED]", "email"),
    (PHONE_BR_PATTERN, "[PHONE REDACTED]", "phone"),
]

_RESPONSE_REDACTION_ENABLED = _os.environ.get(
    "LIA_RESPONSE_PII_REDACTION_ENABLED", "true"
).lower() == "true"


def redact_response_with_audit(
    text: str,
    *,
    strict_mode: bool = False,
) -> tuple[str, list[dict]]:
    """G5 light: redact response text + return per-match audit trail.

    Args:
        text: Raw response content from LLM.
        strict_mode: When True, also applies FULL_NAME_HEURISTIC (higher
            false-positive rate on names like \"Product Manager\" caps). Off by
            default to avoid over-redacting headings.

    Returns:
        (redacted_text, audit_log). audit_log is a list of dicts:
        [{"type": "cpf", "span": (start, end), "snippet": "123.456.789-00"},
         {"type": "email", ...}]

    Feature flag: env LIA_RESPONSE_PII_REDACTION_ENABLED (default "true").
    When disabled, returns (text, []) — caller can still log but no mutation.
    """
    if not text or not _RESPONSE_REDACTION_ENABLED:
        return text, []

    audit_log: list[dict] = []
    redacted = text

    # Apply structured patterns (high precision)
    for pattern, replacement, pii_type in _RESPONSE_PATTERNS:
        for match in list(pattern.finditer(redacted)):
            audit_log.append({
                "type": pii_type,
                "span": (match.start(), match.end()),
                "snippet": match.group()[:40],  # truncated for audit log
            })
        redacted = pattern.sub(replacement, redacted)

    # Strict mode only: full name heuristic (higher false-positive)
    if strict_mode:
        for match in list(FULL_NAME_HEURISTIC.finditer(redacted)):
            audit_log.append({
                "type": "full_name_heuristic",
                "span": (match.start(), match.end()),
                "snippet": match.group()[:40],
            })
        redacted = FULL_NAME_HEURISTIC.sub("[NAME REDACTED]", redacted)

    return redacted, audit_log





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
        logger.addFilter(PIIMaskingFilter())
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

    logging.getLogger(__name__).info("[PII-MASKING] Global PII masking installed (logger + %d handler(s))", len(root_logger.handlers))



_LLM_PROMPT_PII_STRIPPING_ENABLED = _os.environ.get("LLM_PROMPT_PII_STRIPPING_ENABLED", "true").lower() == "true"

# Quasi-identifier patterns — Layer 3 basic (no NER required)
# Captura variações com profissão/curso entre o verbo de formatura e o ano,
# por exemplo: "Formada em Engenharia em 2012", "Bacharelado em Administração
# concluído em 2009", "Concluí o MBA em 2021", "Formou-se em 2017".
_GRADUATION_YEAR_PATTERN = re.compile(
    r'\b(?:'
    r'formad[oa]s?|formou[\-\s]se|formaram[\-\s]se|formei[\-\s]me|'
    r'graduad[oa]s?|graduou[\-\s]se|graduaram[\-\s]se|graduei[\-\s]me|gradua[çc][ãa]o|'
    r'formatura|'
    r'conclu[ií](?:do|da|u|í|ído|ída)?|conclus[ãa]o|'
    r'bacharelad[oa]|licenciad[oa]|'
    r'mestrad[oa]|mestrando|'
    r'doutorad[oa]|doutorando|'
    r'p[óo]s[\-\s]?graduad[oa]|p[óo]s[\-\s]?gradua[çc][ãa]o|'
    r'mba'
    r')\b[^.\n]{0,80}?\b\d{4}\b',
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
    # Marker padronizado: usa "REMOVIDO" para alinhar com os demais
    # ([CPF REMOVIDO], [EMAIL REMOVIDO], [ANO_FORMATURA REMOVIDO] …) — assim
    # consumidores e testes podem assumir um único token grammar-agnostic.
    (_AGE_EXPLICIT_PATTERN, "[IDADE REMOVIDO]"),
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
