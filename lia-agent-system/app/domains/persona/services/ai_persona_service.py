"""
Service canonical para nome + tom da IA per-tenant (tab "Personalidade da
IA" em Minha Empresa, audit 2026-05-21 E2.2).

## Responsabilidades

- **Read:** retorna ``{name, tone}`` consolidado, com defaults canonical
  quando policy/tenant ainda não customizou.
- **Update:** valida via :mod:`ai_persona_validator`, persiste em
  ``CompanyHiringPolicy.communication_rules.ai_persona``, mantém
  ``communication_rules.lia_tone`` sincronizado (mesmo valor canonical
  pra outbound + chat), emite audit log canonical.

## Multi-tenancy

O ``company_id`` é argumento — caller é responsável por garantir vem
do JWT autenticado. Service confia no input (mesmo posture que outros
services-de-domínio).

## Por que sincronizar lia_tone legacy

UI tem 1 controle de tom (cards de seleção). Backend tem 2 campos:
``ai_persona.tone`` (consumido pelo SystemPromptBuilder — chat) e
``lia_tone`` (consumido pelo communication_dispatcher — outbound).
Sincronizar evita "tela mostra amigável mas e-mail sai formal".

Histórico: ``lia_tone`` é legacy do communication_dispatcher; ``ai_persona``
é o canonical novo do SystemPromptBuilder. Sprint futura pode unificar
totalmente.

## Audit canonical

Todo update emite ``audit_logs`` row com ``action='ai_persona_update'``,
``prev`` e ``next`` em ``reasoning``. Trail rastreável para LGPD/SOX-equiv.
"""
from __future__ import annotations

import logging
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.hiring_policy.repositories.hiring_policy_repository import (
    HiringPolicyRepository,
)
from app.domains.persona.services.ai_persona_validator import (
    DEFAULT_AI_NAME,
    DEFAULT_AI_TONE,
    validate_persona,
)
from app.shared.compliance.audit_service import AuditService

logger = logging.getLogger(__name__)


async def get_ai_persona(
    company_id: str,
    db: AsyncSession,
) -> dict[str, str]:
    """Read ``{name, tone}`` for ``company_id``, with canonical defaults.

    Never raises. Returns defaults when the policy row does not exist yet
    (cold-start tenant) — opt-in semantics: tenant has not customized,
    apply the platform default (LIA + profissional).
    """
    repo = HiringPolicyRepository(db)
    policy = await repo.get_by_company(company_id)
    if not policy or not policy.communication_rules:
        return {"name": DEFAULT_AI_NAME, "tone": DEFAULT_AI_TONE}
    stored = policy.communication_rules.get("ai_persona") or {}
    return {
        "name": stored.get("name", DEFAULT_AI_NAME),
        "tone": stored.get("tone", DEFAULT_AI_TONE),
    }


async def update_ai_persona(
    company_id: str,
    db: AsyncSession,
    *,
    name: str | None = None,
    tone: str | None = None,
    actor_user_id: str | None = None,
) -> dict[str, str]:
    """Validate + persist + audit. Returns the new persona dict.

    Partial updates are explicit — pass ``name=None`` to leave name unchanged,
    same for ``tone``. If both are ``None`` the validator rejects (caller bug).

    Raises:
        ValueError: with a list of structured errors as args[0] when the
            validator refuses. Endpoint layer translates to HTTP 422 with
            ``detail.errors`` for the admin UI to render inline.

    Side effects on success:
        - Writes ``policy.communication_rules.ai_persona = {name, tone}``.
        - When ``tone`` is provided, also writes ``policy.communication_rules.lia_tone``
          for outbound-message dispatcher sync (single UI control = 2 backend
          writes coherent).
        - Calls ``HiringPolicyRepository.flush()`` — caller is responsible
          for ``db.commit()``.
        - Audit log row via ``AuditService.log_decision`` with prev/next diff.
    """
    validation = validate_persona(name=name, tone=tone)
    if not validation.is_valid:
        # Fail-closed: nada é persistido. Caller pega args[0] = errors list
        # e traduz em HTTP 422.
        raise ValueError(validation.errors)

    repo = HiringPolicyRepository(db)
    policy = await repo.create_if_missing(company_id, actor_user_id)
    rules = dict(policy.communication_rules or {})
    prev = dict(rules.get("ai_persona") or {})

    next_persona = dict(prev)
    if name is not None:
        next_persona["name"] = name.strip()
    if tone is not None:
        next_persona["tone"] = tone
        # Sync legacy lia_tone field used by communication_dispatcher
        rules["lia_tone"] = tone
    # Preserve defaults for any missing key after merge — ensures the dict
    # returned to the caller is always fully populated, never partial.
    next_persona.setdefault("name", DEFAULT_AI_NAME)
    next_persona.setdefault("tone", DEFAULT_AI_TONE)

    rules["ai_persona"] = next_persona
    policy.communication_rules = rules
    policy.updated_at = datetime.utcnow()
    await repo.flush()

    # Audit canonical (não-bloqueante — falha de audit não derruba a write).
    try:
        await AuditService().log_decision(
            company_id=company_id,
            agent_name="ai_persona_service",
            decision_type="admin_config_change",
            action="ai_persona_update",
            decision="success",
            reasoning=[
                f"prev_name={prev.get('name', DEFAULT_AI_NAME)}",
                f"prev_tone={prev.get('tone', DEFAULT_AI_TONE)}",
                f"next_name={next_persona['name']}",
                f"next_tone={next_persona['tone']}",
            ],
            criteria_used=["ai_persona_validator"],
            actor_user_id=actor_user_id,
            human_review_required=False,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "[ai_persona_service] audit log failed (non-blocking): %s",
            str(exc)[:120],
        )

    return next_persona


__all__ = ["get_ai_persona", "update_ai_persona"]
