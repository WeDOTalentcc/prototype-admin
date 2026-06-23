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
import os
import re
from contextvars import ContextVar
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


# P1 C (2026-05-23): UUID v4 guard pattern compartilhado por mask_pii e
# strip_pii_for_llm_prompt — single source of truth.
#
# Por que aqui (não junto da definição original lá embaixo)?
# `mask_pii` precisa de _UUID_V4_PATTERN definido ANTES dela. A definição
# original em strip_pii_for_llm_prompt fica DEPOIS de mask_pii (ordem do
# arquivo). Centralizamos a definição aqui e removemos a duplicata abaixo.
_UUID_V4_PATTERN: Pattern = re.compile(
    r'\b[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b',
    re.IGNORECASE,
)


def mask_pii(text: str) -> str:
    """Mask PII em log strings preservando UUID v4 (P1 C, ref: backlog 2026-05-23).

    Aplica mesmo guard-token pattern de `strip_pii_for_llm_prompt`: UUIDs v4
    viram placeholders opacos antes de aplicar PII regex e voltam depois.
    Garante invariante "UUID v4 nunca é PII" — protege tenant_id em logs
    `[LLM-AUDIT]` contra falso-positivo do `PHONE_BR_PATTERN`
    (`\\d{4}[-\\s]?\\d{4}\\b` casa segmentos internos de UUIDs).
    """
    if not text:
        return text

    # ── UUID v4 guard via reversible placeholder ──
    _uuid_map: dict[str, str] = {}

    def _shield(match: "re.Match") -> str:
        uid = match.group(0)
        # \x00 é seguro: nunca aparece em logs reais e é transparente para
        # todos os regexes de PII (que casam dígitos/pontuação ASCII).
        token = f"\x00UUID{len(_uuid_map)}\x00"
        _uuid_map[token] = uid
        return token

    masked = _UUID_V4_PATTERN.sub(_shield, text)

    for pattern, replacement in PII_PATTERNS:
        masked = pattern.sub(replacement, masked)

    # Restaura UUIDs
    for token, uid in _uuid_map.items():
        masked = masked.replace(token, uid)
    return masked


# Saida do chat do RECRUTADOR: por decisao de produto (Paulo 2026-06-06), o
# recrutador AUTENTICADO ve CPF/email/telefone (necessario pro recrutamento; o
# dado ja e visivel pra ele na plataforma; LGPD Art. 7 II legitimo interesse).
# Default = PRESERVAR. Masking opt-in (futuro: config per-user na tela de
# cadastro) via LIA_RECRUITER_CHAT_MASK_PII=true. LOGS continuam mascarados
# (PIIMaskingFilter / mask_pii em logs sao independentes desta funcao).
_RECRUITER_CHAT_MASK_PII = os.environ.get(
    "LIA_RECRUITER_CHAT_MASK_PII", "false"
).strip().lower() in ("1", "true", "yes", "on")

# Per-chat-turn flag: when True, mask identity docs (CPF/RG/CNPJ) in chat output
# for a user not allowed to see `cpf`. Set by the chat handler (B2), read by
# mask_pii_outbound. Leaves email/phone untouched (primary contacts stay visible
# per product decision Paulo 2026-06-07).
_chat_pii_mask_identity: ContextVar[bool] = ContextVar("_chat_pii_mask_identity", default=False)


# T3 audit 2026-06-22: skip input PII strip for recruiter chat.
# Recruiter is LGPD data controller (Art. 7 III legitimate interest).
# Output masking per RBAC (mask_pii_outbound) stays active.
_skip_llm_input_pii_strip: ContextVar[bool] = ContextVar("_skip_llm_input_pii_strip", default=False)


def set_skip_llm_input_pii_strip(value: bool):
    """Set per-request flag to skip input PII stripping (recruiter chat context)."""
    return _skip_llm_input_pii_strip.set(bool(value))


def reset_skip_llm_input_pii_strip(token) -> None:
    """Reset the ContextVar to its previous value."""
    try:
        _skip_llm_input_pii_strip.reset(token)
    except Exception:
        pass


def set_chat_pii_mask_identity(value: bool):
    """Set the per-turn identity-masking flag. Returns a token for reset()."""
    return _chat_pii_mask_identity.set(bool(value))


def reset_chat_pii_mask_identity(token) -> None:
    """Reset the ContextVar to its previous value using the token from set()."""
    try:
        _chat_pii_mask_identity.reset(token)
    except Exception:
        pass


def chat_should_mask_identity(user, role_defaults: dict | None = None) -> bool:
    """True when the user is NOT allowed to see `cpf` (-> mask identity docs in chat).

    Resolves cpf visibility via pii_field_resolver precedence:
    user override > role default > legacy bucket (can_view_sensitive_pii) > True.
    """
    from lia_pii.field_visibility import resolve_pii_field_visibility
    try:
        effective = resolve_pii_field_visibility(user, role_defaults or {})
        return not effective.get("cpf", True)
    except Exception:
        return False


# Strict RG pattern for chat output: requires explicit separators (dots/dash)
# to avoid false-positives on BR phone numbers (which share the loose digit count).
# _RG_PATTERN (used for logs) is broader — intentional for full coverage in logs.
_RG_PATTERN_STRICT = re.compile(r'\b\d{1,2}[\.\-]\d{3}[\.\-]\d{3}[\-][0-9Xx]\b')


def _mask_identity_docs(text: str) -> str:
    """Mask ONLY identity documents (CPF/RG/CNPJ). Leaves email/phone untouched.

    Uses _RG_PATTERN_STRICT (separators required) to avoid false-positive matches
    on BR phone numbers which share digit counts with the broader _RG_PATTERN.
    """
    out = CPF_PATTERN.sub("***CPF***", text)
    out = _RG_PATTERN_STRICT.sub("***RG***", out)
    out = _CNPJ_PATTERN.sub("***CNPJ***", out)
    return out


def mask_pii_outbound(text):
    """Masking de PII na SAIDA do chat do recrutador. Default: passthrough
    (preserva -- recrutador autorizado ve). Mascara so se opt-in
    (LIA_RECRUITER_CHAT_MASK_PII). Para LOGS, use mask_pii direto.
    Per-turn identity masking: when _chat_pii_mask_identity ContextVar is True,
    masks CPF/RG/CNPJ only (email/phone preserved -- primary contacts stay visible)."""
    if not text or not isinstance(text, str):
        return text
    if _chat_pii_mask_identity.get():
        return _mask_identity_docs(text)
    if not _RECRUITER_CHAT_MASK_PII:
        return text
    return mask_pii(text)


def mask_phone_preserve_tail(phone: str | None) -> str | None:
    """F-07 P0 LGPD Art. 11: mask phone keeping country code + DDD + last 4 digits.

    Use case: persistent storage (JSONB session state, audit metadata) where
    operators need partial visibility for debug/support but full number is
    LGPD-protected. Output example:
        "+5511999991234"  -> "+55 11 ****1234"
        "11999991234"      -> "11 ****1234"
        "+551134567890"    -> "+55 11 ****7890"
        "1234"              -> "****"
        ""                   -> ""
        None                  -> None

    NEVER use mask_pii (regex-based) on phones intended for storage — the
    full digits are replaced with literal "***PHONE***" sentinel which loses
    debug-friendly tail. This helper is the canonical for JSONB at-rest masking.
    """
    if phone is None:
        return None
    s = str(phone).strip()
    if not s:
        return s

    has_plus = s.startswith("+")
    digits = "".join(ch for ch in s if ch.isdigit())
    if len(digits) <= 4:
        return "*" * len(digits) if digits else s

    # Preserve last 4. Try to also expose country code (2-3 digits) and DDD (2 digits)
    # when the number is long enough. Brazilian format: +55 11 9XXXX-XXXX = 13 digits.
    if len(digits) >= 12:  # +55 + DDD + 9-digit mobile, or international with country+DDD
        country = digits[:2]
        ddd = digits[2:4]
        tail = digits[-4:]
        prefix = ("+" if has_plus else "") + country
        return f"{prefix} {ddd} ****{tail}"
    if len(digits) >= 10:  # DDD + 8/9-digit (no country code)
        ddd = digits[:2]
        tail = digits[-4:]
        return f"{ddd} ****{tail}"
    # 5-9 digits: just preserve last 4
    tail = digits[-4:]
    return f"****{tail}"


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


def strip_pii_for_llm_prompt(text: str, mask_names: bool = True) -> str:
    """Remove PII e quasi-identificadores de texto antes de enviar ao LLM.

    Aplica até 4 camadas:
      - Layer 0 (R1/T-F): UUID v4 guard — protege identificadores de tenant/job
        contra falso-positivo do PHONE_BR_PATTERN
      - Layer 1: Regex direto (CPF, email, telefone, RG, CNPJ)
      - Layer 3 basic: Quasi-identificadores (ano de formatura, idade explícita,
        referências de endereço)
      - Layer 4: NER via Microsoft Presidio para mascarar NOME (PERSON), LOCATION
        e demais entidades não capturadas por regex. Ligada por padrão
        (LLM_PROMPT_PRESIDIO_ENABLED, padrão: true) usando o modelo spaCy PT-BR
        pt_core_news_sm. Se o modelo não estiver disponível, a falha é logada em
        CRITICAL (nome vaza sem máscara) — não é um fallback silencioso.

    Controlado pela env LLM_PROMPT_PII_STRIPPING_ENABLED (padrão: true).

    LGPD Art. 12: minimização de dados pessoais processados por sistemas de IA.
    EU AI Act Art. 13: transparência sobre dados usados em sistemas de alto risco.

    Returns:
        Texto com PII removido ou o texto original se a feature estiver desabilitada.
    """
    if not _LLM_PROMPT_PII_STRIPPING_ENABLED or not text:
        return text
    if _skip_llm_input_pii_strip.get():
        return text

    # ── Layer 0 (R1/T-F): UUID guard via reversible placeholder ──
    # Coleta UUIDs e substitui por sentinelas opacas que NÃO casam nenhum
    # PII pattern. Restauramos no final para preservar fidelidade do prompt.
    _uuid_map: dict[str, str] = {}

    def _shield(match: re.Match) -> str:
        uid = match.group(0)
        # \x00 é seguro: nunca aparece em prompts reais e é "transparente"
        # para todos os regexes de PII (que casam dígitos/pontuação ASCII).
        token = f"\x00UUID{len(_uuid_map)}\x00"
        _uuid_map[token] = uid
        return token

    result = _UUID_V4_PATTERN.sub(_shield, text)

    # Layer 4 (NER): Presidio mascara NOME (PERSON)/LOCATION. mask_names=False
    # PULA esta camada (chat do recrutador: nome/titulo sao NECESSARIOS e
    # AUTORIZADOS; falso-positivo tratava 'Diretor Juridico' como PERSON).
    # CPF/email/telefone (Layer 1/3 regex) seguem mascarados.
    if mask_names:
        result = _presidio_layer4_strip(result)
    # Layer 1 + Layer 3: regex determinístico como backstop (CPF/email/telefone/
    # RG/CNPJ + quasi-identificadores) — captura o que o NER não pegou.
    for pattern, replacement in _LLM_PROMPT_PII_PATTERNS:
        result = pattern.sub(replacement, result)

    # ── Restaura UUIDs ──
    for token, uid in _uuid_map.items():
        result = result.replace(token, uid)
    return result


_PRESIDIO_ENABLED = _os.environ.get("LLM_PROMPT_PRESIDIO_ENABLED", "true").lower() == "true"

# Modelo spaCy NER usado pelo Presidio. PT-BR por padrão (currículos brasileiros).
# DEVE estar declarado em requirements.txt — sem ele o AnalyzerEngine default tenta
# baixar o modelo inglês em runtime, falha (ambiente externally-managed) e o nome
# do candidato NÃO é mascarado (vazamento silencioso para o LLM).
_PRESIDIO_LANG = _os.environ.get("LLM_PROMPT_PRESIDIO_LANG", "pt").lower()
_PRESIDIO_SPACY_MODEL = _os.environ.get(
    "LLM_PROMPT_PRESIDIO_SPACY_MODEL", "pt_core_news_sm"
)

_presidio_analyzer_instance = None  # lazy singleton
_presidio_load_failed = False  # evita re-tentar (e re-logar CRITICAL) a cada chamada
_presidio_runtime_fail_logged = False  # latch one-shot p/ falha de runtime do NER


def _get_presidio_analyzer():
    """Retorna AnalyzerEngine do Presidio configurado com o modelo NER PT.

    Fail-safe quanto a NÃO derrubar a aplicação, mas fail-LOUD quanto a
    observabilidade: se o Presidio estiver habilitado e a carga falhar, loga
    CRITICAL — porque nesse estado o nome do candidato vaza sem máscara para o
    LLM, e isso precisa ser detectável (não pode passar como debug silencioso).
    """
    global _presidio_analyzer_instance, _presidio_load_failed
    if _presidio_analyzer_instance is not None or _presidio_load_failed:
        return _presidio_analyzer_instance
    log = logging.getLogger(__name__)
    try:
        from presidio_analyzer import AnalyzerEngine
        from presidio_analyzer.nlp_engine import NlpEngineProvider

        nlp_engine = NlpEngineProvider(
            nlp_configuration={
                "nlp_engine_name": "spacy",
                "models": [
                    {"lang_code": _PRESIDIO_LANG, "model_name": _PRESIDIO_SPACY_MODEL}
                ],
            }
        ).create_engine()
        _presidio_analyzer_instance = AnalyzerEngine(
            nlp_engine=nlp_engine,
            supported_languages=[_PRESIDIO_LANG],
        )
        log.info(
            "[PII-L4] Presidio AnalyzerEngine carregado (lang=%s, model=%s)",
            _PRESIDIO_LANG,
            _PRESIDIO_SPACY_MODEL,
        )
    except ImportError as exc:
        _presidio_load_failed = True
        log.critical(
            "[PII-L4] presidio_analyzer indisponível (%s) — Layer 4 (mascaramento "
            "de NOME via NER) DESLIGADA enquanto LLM_PROMPT_PRESIDIO_ENABLED=true. "
            "Nomes de candidatos NÃO serão mascarados antes do LLM. Declare "
            "presidio-analyzer + %s em requirements.txt.",
            exc,
            _PRESIDIO_SPACY_MODEL,
        )
        _presidio_analyzer_instance = None
    except Exception as exc:
        _presidio_load_failed = True
        log.critical(
            "[PII-L4] Falha ao inicializar Presidio (%s) — mascaramento de NOME "
            "DESLIGADO apesar de LLM_PROMPT_PRESIDIO_ENABLED=true. Verifique se o "
            "modelo spaCy '%s' está instalado.",
            exc,
            _PRESIDIO_SPACY_MODEL,
        )
        _presidio_analyzer_instance = None
    return _presidio_analyzer_instance


# Entidades Presidio a remover (configurável via LLM_PROMPT_PRESIDIO_ENTITIES).
# O default foca nos identificadores diretos de privacidade — NOME (PERSON) é o
# gap real do D-10; EMAIL/PHONE são redundantes com o regex mas inofensivos; NRP
# = nationality/religion/political group (proxy de classe protegida).
# LOCATION e DATE_TIME ficam FORA do default de propósito: o modelo PT pequeno
# (pt_core_news_sm) rotula erroneamente skills/tecnologias como LOCATION
# (ex.: "React" → LOCATION), o que removeria informação útil da triagem.
# Modo privacidade máxima (mascara cidade/datas também):
#   LLM_PROMPT_PRESIDIO_ENTITIES="PERSON,EMAIL_ADDRESS,PHONE_NUMBER,NRP,LOCATION,DATE_TIME"
_DEFAULT_PRESIDIO_ENTITIES = ["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "NRP"]
_PRESIDIO_ENTITIES = [
    e.strip()
    for e in _os.environ.get(
        "LLM_PROMPT_PRESIDIO_ENTITIES", ",".join(_DEFAULT_PRESIDIO_ENTITIES)
    ).split(",")
    if e.strip()
]


def _presidio_layer4_strip(text: str) -> str:
    """Aplica NER Presidio para remover entidades PII não capturadas por regex.

    Resiliente (não derruba o request) mas NÃO silencioso: se o Presidio estiver
    habilitado e a máscara falhar em runtime, o NOME pode vazar sem máscara para
    o LLM — então a primeira falha loga CRITICAL (depois ERROR), não DEBUG.
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
            language=_PRESIDIO_LANG,
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
        global _presidio_runtime_fail_logged
        log = logging.getLogger(__name__)
        if not _presidio_runtime_fail_logged:
            _presidio_runtime_fail_logged = True
            log.critical(
                "[PII-L4] Presidio falhou em RUNTIME (%s) — NOME do candidato pode "
                "vazar sem máscara para o LLM enquanto LLM_PROMPT_PRESIDIO_ENABLED=true. "
                "Investigue o NER (log único; falhas seguintes logam ERROR).",
                exc,
            )
        else:
            log.error("[PII-L4] Presidio strip falhou novamente em runtime: %s", exc)
        return text


async def strip_pii_for_llm_prompt_async(text: str, mask_names: bool = True) -> str:
    """Async wrapper — runs Presidio+regex CPU work in thread pool.

    Prevents blocking the asyncio event loop when Presidio NER is enabled
    (LLM_PROMPT_PRESIDIO_ENABLED=true defaults to true). Use in all async
    LLM call paths (generate_with_tools, generate, generate_structured, etc.)
    to avoid 50-200ms event loop stalls per call under spaCy pt_core_news_sm.

    Harness: BUG-5 fix 2026-06-18 — canonical producer is this wrapper,
    consumers are llm.py async methods. DO NOT call sync version in async paths.
    """
    import asyncio
    if not _LLM_PROMPT_PII_STRIPPING_ENABLED or not text:
        return text
    if _skip_llm_input_pii_strip.get():
        return text
    return await asyncio.to_thread(strip_pii_for_llm_prompt, text, mask_names)
