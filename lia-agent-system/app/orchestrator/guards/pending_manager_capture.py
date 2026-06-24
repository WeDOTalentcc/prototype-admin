"""B8 Peça 1 — Captura determinística de gestor no chat geral.

Reutiliza extractors canônicos de manager_identity.py e wizard_session_service.py.
Grava em conversation_metadata["pending_manager"] para carry até wizard.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def extract_pending_manager(raw_message: str) -> dict[str, Any] | None:
    """Extrai nome+email do gestor do texto cru. Retorna dict ou None.

    Usa as mesmas funções determinísticas do wizard (T4b):
    - _extract_manager_email (wizard_session_service.py)
    - extract_manager_name_from_text (manager_identity.py)

    Retorna None se nenhum sinal de gestor detectado.
    """
    if not raw_message or len(raw_message) < 5:
        return None

    from app.domains.job_creation.services.wizard_session_service import (
        _extract_manager_email,
    )
    from app.domains.job_creation.helpers.manager_identity import (
        extract_manager_name_from_text,
        _MANAGER_CONTEXT_RE,
    )
    has_manager_context = bool(_MANAGER_CONTEXT_RE.search(raw_message))
    if not has_manager_context:
        return None

    name = extract_manager_name_from_text(raw_message, manager_context_hint=False)
    email = _extract_manager_email(raw_message)

    if not name and not email:
        return None

    return {"name": name, "email": email}


async def persist_pending_manager(
    conv: Any,
    pending: dict[str, Any],
    db: Any,
) -> None:
    """Grava pending_manager em conversation_metadata. Commit do caller."""
    if conv is None:
        return
    from sqlalchemy.orm.attributes import flag_modified
    md = dict(conv.conversation_metadata or {})
    md["pending_manager"] = pending
    conv.conversation_metadata = md
    flag_modified(conv, "conversation_metadata")


MANAGER_PROMPT_HINT = (
    "\n\n### REGRA OBRIGATÓRIA — Gestor da vaga (anotação pendente)\n"
    "O usuário mencionou um gestor/manager. Você ANOTOU o nome/email "
    "mas o gestor SÓ será de fato registrado quando a vaga for criada.\n"
    "RESPONDA EXATAMENTE assim:\n"
    '"Anotei [nome] como gestor. Vou registrar na vaga quando criarmos."\n'
    "PROIBIDO usar as palavras: registrado, cadastrado, salvo, gravado.\n"
    "Use APENAS: anotei, anotado, registro (futuro).\n"
)

MANAGER_PROMPT_HINT_NO_CAPTURE = (
    "\n\n### Menção a gestor sem dados identificáveis\n"
    "O usuário mencionou gestor/manager mas não foi possível "
    "extrair nome ou email. Peça: \"Pode me passar o nome completo "
    "e email do gestor?\". NUNCA afirme \"registrado\" sem ter os dados.\n"
)
