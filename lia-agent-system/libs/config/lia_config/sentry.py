"""
Sentry integration — FastAPI + Celery com scrubbing de PII (André P8).

SENTRY_DSN env var controla se Sentry está ativo (vazio = desativado).
PII scrubbed: email, cpf, nome, telefone em before_send hook.

Uso em main.py:
    from app.core.sentry import init_sentry
    init_sentry()

O módulo é gracefully degradável:
- Sem DSN → log INFO + retorna False (sem exceção)
- Sem sentry-sdk instalado → log WARNING + retorna False
- Qualquer outra falha → log WARNING + retorna False
"""
import logging
import re

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# W3-013 (2026-05-23): Patterns PII para scrubbing — REUSA canonical de
# `app.shared.pii_masking._LLM_PROMPT_PII_PATTERNS` (8 patterns: CPF, email,
# phone, RG, CNPJ, graduation year, age, address) + ADICIONA 4 patterns de
# segurança (password/api_key/bearer_token/credit_card).
#
# Antes: 3 patterns (email, CPF, phone BR).
# Depois: 8 canonical + 4 security = 12 patterns.
# ---------------------------------------------------------------------------

_SECURITY_PII_PATTERNS = [
    # password=xxx, password: xxx (case-insensitive)
    (re.compile(r'(?i)(password|passwd|pwd|senha)\s*[:=]\s*[^\s"\\\',;]+'), r'\1=[REDACTED]'),
    # api_key=xxx, api-key: xxx, apikey: xxx
    (re.compile(r'(?i)(api[-_]?key|apikey|x-api-key)\s*[:=]\s*[^\s"\\\',;]+'), r'\1=[REDACTED]'),
    # Bearer / Authorization tokens (truncated)
    (re.compile(r'(?i)(bearer|authorization:\s*bearer)\s+[A-Za-z0-9._\-]+'), r'\1 [TOKEN]'),
    # Credit card numbers (12-19 digits, optional dashes/spaces)
    (re.compile(r'\b(?:\d[ -]*?){12,19}\d\b'), '[CARD]'),
]


def _get_pii_patterns():
    """Lazy-load canonical patterns (avoid circular imports + import-time cost)."""
    try:
        from lia_pii.masking import _LLM_PROMPT_PII_PATTERNS
        return list(_LLM_PROMPT_PII_PATTERNS) + _SECURITY_PII_PATTERNS
    except ImportError:
        # Fallback: 3 BR-specific patterns + 4 security (minimum viable scrubbing)
        return [
            (re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'), '[EMAIL]'),
            (re.compile(r'\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b'), '[CPF]'),
            (re.compile(r'\b(?:\+55\s?)?(?:\(?\d{2}\)?\s?)?(?:9\s?)?\d{4}[-\s]?\d{4}\b'), '[PHONE]'),
        ] + _SECURITY_PII_PATTERNS


_PII_PATTERNS = _get_pii_patterns()


def _scrub_pii(text: str) -> str:
    """Remove PII de strings antes de enviar ao Sentry."""
    for pattern, replacement in _PII_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def _before_send(event: dict, hint: dict) -> dict | None:
    """
    Hook Sentry before_send: remove PII de exception messages e breadcrumbs.

    Sempre retorna o evento (nunca descarta), apenas sanitiza.
    """
    if event is None:
        return event

    # Scrub exception messages
    if 'exception' in event:
        for exc in event['exception'].get('values', []):
            if exc.get('value'):
                exc['value'] = _scrub_pii(str(exc['value']))

    # Scrub breadcrumbs
    for crumb in event.get('breadcrumbs', {}).get('values', []):
        if crumb.get('message'):
            crumb['message'] = _scrub_pii(str(crumb['message']))

    return event


def init_sentry(dsn: str | None = None) -> bool:
    """
    Inicializa Sentry se DSN disponível.

    Ordem de resolução do DSN:
    1. Parâmetro dsn passado explicitamente
    2. settings.SENTRY_DSN (via lia_config)
    3. Env var SENTRY_DSN diretamente (fallback)

    Retorna True se Sentry inicializado com sucesso, False caso contrário.
    Nunca lança exceção.
    """
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.starlette import StarletteIntegration

        _dsn = dsn

        if not _dsn:
            try:
                from lia_config.config import settings
                _dsn = getattr(settings, 'SENTRY_DSN', '') or ''
            except Exception:
                import os
                _dsn = os.getenv('SENTRY_DSN', '')

        if not _dsn:
            logger.info("[Sentry] DSN não configurado — Sentry desativado")
            return False

        import os
        # UC-P1-05: env-aware sample rate (30% prod / 100% staging/test)
        _env = os.getenv('APP_ENV', os.getenv('ENVIRONMENT', 'development'))
        _default_rate = '1.0' if _env in ('staging', 'test') else '0.3'
        _traces_rate = float(os.getenv('SENTRY_TRACES_SAMPLE_RATE', _default_rate))
        # lia_config is NOT consulted for traces_sample_rate — env var is the source of truth
        # (UC-P1-05: env-aware rate must not be overridden by lia_config default)

        sentry_sdk.init(
            dsn=_dsn,
            integrations=[
                StarletteIntegration(transaction_style="endpoint"),
                FastApiIntegration(transaction_style="endpoint"),
            ],
            traces_sample_rate=_traces_rate,
            profiles_sample_rate=float(os.getenv("SENTRY_PROFILES_SAMPLE_RATE", "0.1")),
            before_send=_before_send,
            send_default_pii=False,
            environment=os.getenv('APP_ENV', 'development'),
            release=os.getenv('APP_VERSION', '0.1.0'),
        )
        logger.info("[Sentry] Inicializado (traces_sample_rate=%s)", _traces_rate)
        return True

    except ImportError:
        logger.warning("[Sentry] sentry-sdk não instalado — Sentry desativado")
        return False
    except Exception as exc:
        logger.warning("[Sentry] Falha ao inicializar: %s", exc)
        return False
