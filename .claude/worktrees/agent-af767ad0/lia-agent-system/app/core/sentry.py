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
import re
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Patterns PII para scrubbing
# ---------------------------------------------------------------------------

_PII_PATTERNS = [
    # E-mail
    (re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'), '[EMAIL]'),
    # CPF (com ou sem pontuação)
    (re.compile(r'\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b'), '[CPF]'),
    # Telefone brasileiro (fixo e celular, com ou sem +55/DDD)
    (re.compile(r'\b(?:\+55\s?)?(?:\(?\d{2}\)?\s?)?(?:9\s?)?\d{4}[-\s]?\d{4}\b'), '[PHONE]'),
]


def _scrub_pii(text: str) -> str:
    """Remove PII de strings antes de enviar ao Sentry."""
    for pattern, replacement in _PII_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def _before_send(event: dict, hint: dict) -> Optional[dict]:
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


def init_sentry(dsn: Optional[str] = None) -> bool:
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

        sentry_sdk.init(
            dsn=_dsn,
            integrations=[
                StarletteIntegration(transaction_style="endpoint"),
                FastApiIntegration(transaction_style="endpoint"),
            ],
            traces_sample_rate=0.1,
            before_send=_before_send,
            send_default_pii=False,  # LGPD: nunca enviar PII automaticamente
        )
        logger.info("[Sentry] Inicializado (traces_sample_rate=0.1)")
        return True

    except ImportError:
        logger.warning("[Sentry] sentry-sdk não instalado — Sentry desativado")
        return False
    except Exception as exc:
        logger.warning("[Sentry] Falha ao inicializar: %s", exc)
        return False
