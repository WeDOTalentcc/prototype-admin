"""
E2.2 contract sensor — service canonical para persona AI per-tenant.

Garante:
1. ``get_ai_persona`` retorna defaults (LIA / profissional) quando policy
   inexistente ou ``ai_persona`` ausente.
2. ``get_ai_persona`` retorna valores customizados quando policy tem
   ``communication_rules.ai_persona`` populado.
3. ``update_ai_persona`` rejeita inválido SEM persistir (fail-closed).
4. ``update_ai_persona`` aceita update parcial (só nome OR só tom).
5. Quando tone é atualizado, ``lia_tone`` legacy fica sincronizado
   (um controle de UI = duas escritas backend coerentes).
6. Audit log canonical é emitido com prev/next.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.domains.persona.services import ai_persona_service
from app.domains.persona.services.ai_persona_validator import (
    DEFAULT_AI_NAME, DEFAULT_AI_TONE,
)


def _make_policy(communication_rules: dict | None) -> MagicMock:
    policy = MagicMock()
    policy.communication_rules = communication_rules
    return policy


def _make_repo(policy: MagicMock | None) -> MagicMock:
    repo = MagicMock()
    repo.get_by_company = AsyncMock(return_value=policy)
    repo.create_if_missing = AsyncMock(return_value=policy or _make_policy({}))
    repo.flush = AsyncMock()
    return repo


def _install_repo_mock(repo: MagicMock) -> None:
    """Patch HiringPolicyRepository at the binding the service holds.

    The service module imports the class at top-level. Patching the source
    module after import has no effect — Python keeps the cached reference.
    Patch where the service uses it.
    """
    import app.domains.persona.services.ai_persona_service as svc_mod
    svc_mod.HiringPolicyRepository = MagicMock(return_value=repo)


# --- get_ai_persona --------------------------------------------------------

@pytest.mark.asyncio
async def test_get_ai_persona_returns_defaults_when_policy_missing():
    _install_repo_mock(_make_repo(policy=None))
    result = await ai_persona_service.get_ai_persona("co-1", db=MagicMock())
    assert result == {"name": DEFAULT_AI_NAME, "tone": DEFAULT_AI_TONE}


@pytest.mark.asyncio
async def test_get_ai_persona_returns_defaults_when_ai_persona_absent():
    """Policy existe mas communication_rules.ai_persona não tem nada — usa
    defaults pra cada campo independente."""
    _install_repo_mock(_make_repo(_make_policy({"lia_tone": "formal"})))
    result = await ai_persona_service.get_ai_persona("co-1", db=MagicMock())
    assert result == {"name": DEFAULT_AI_NAME, "tone": DEFAULT_AI_TONE}


@pytest.mark.asyncio
async def test_get_ai_persona_returns_stored_values():
    _install_repo_mock(_make_repo(_make_policy({
        "ai_persona": {"name": "Sofia", "tone": "amigavel"},
    })))
    result = await ai_persona_service.get_ai_persona("co-1", db=MagicMock())
    assert result == {"name": "Sofia", "tone": "amigavel"}


# --- update_ai_persona -----------------------------------------------------

@pytest.mark.asyncio
async def test_update_ai_persona_rejects_invalid_name_without_persisting():
    repo = _make_repo(_make_policy({}))
    _install_repo_mock(repo)
    with pytest.raises(ValueError) as exc_info:
        await ai_persona_service.update_ai_persona(
            "co-1", MagicMock(), name="Claude", tone=None,
        )
    # ValueError carrega lista de erros (caller traduz pra 422)
    assert exc_info.value.args, "ValueError sem args — erro não estruturado"
    # E nenhum flush deve ter ocorrido (fail-closed)
    repo.flush.assert_not_called()


@pytest.mark.asyncio
async def test_update_ai_persona_rejects_invalid_tone_without_persisting():
    repo = _make_repo(_make_policy({}))
    _install_repo_mock(repo)
    with pytest.raises(ValueError):
        await ai_persona_service.update_ai_persona(
            "co-1", MagicMock(), name=None, tone="rude",
        )
    repo.flush.assert_not_called()


@pytest.mark.asyncio
async def test_update_ai_persona_persists_name_only():
    """Update parcial: só name. Tone preservado se já existia."""
    policy = _make_policy({
        "ai_persona": {"name": "OldName", "tone": "formal"},
        "lia_tone": "formal",
    })
    repo = _make_repo(policy)
    _install_repo_mock(repo)
    result = await ai_persona_service.update_ai_persona(
        "co-1", MagicMock(), name="Sofia", tone=None,
        actor_user_id="user-1",
    )
    assert result["name"] == "Sofia"
    assert result["tone"] == "formal"
    # lia_tone legacy NÃO foi alterado porque tone não foi enviado
    assert policy.communication_rules["lia_tone"] == "formal"
    repo.flush.assert_called_once()


@pytest.mark.asyncio
async def test_update_ai_persona_persists_tone_only_and_syncs_lia_tone():
    """Quando tone é enviado, lia_tone legacy é mantido sincronizado.
    Pin: um controle de UI = duas escritas backend coerentes.

    F3.1 audit 2026-05-24: ai_persona.tone permanece PT-BR canonical;
    lia_tone legacy fica em EN (translator at the boundary). Mapping
    em ai_persona_validator.TONE_PT_TO_EN_LEGACY.
    """
    policy = _make_policy({
        "ai_persona": {"name": "Sofia", "tone": "formal"},
        "lia_tone": "formal",
    })
    repo = _make_repo(policy)
    _install_repo_mock(repo)
    result = await ai_persona_service.update_ai_persona(
        "co-1", MagicMock(), name=None, tone="amigavel",
        actor_user_id="user-1",
    )
    assert result["name"] == "Sofia"
    # ai_persona.tone permanece PT-BR canonical
    assert result["tone"] == "amigavel"
    # lia_tone legacy é traduzido pra EN reconhecido pelo dispatcher
    assert policy.communication_rules["lia_tone"] == "friendly"


@pytest.mark.asyncio
async def test_update_ai_persona_strips_whitespace_on_name():
    """Trim canonical: usuário digita ' Sofia ', persiste 'Sofia'."""
    policy = _make_policy({})
    repo = _make_repo(policy)
    _install_repo_mock(repo)
    result = await ai_persona_service.update_ai_persona(
        "co-1", MagicMock(), name="  Sofia  ", tone=None,
    )
    assert result["name"] == "Sofia"


@pytest.mark.asyncio
async def test_update_ai_persona_emits_audit_log():
    """Audit canonical com prev/next. Trail SOX/LGPD-equivalente."""
    policy = _make_policy({
        "ai_persona": {"name": "OldName", "tone": "formal"},
    })
    repo = _make_repo(policy)
    _install_repo_mock(repo)

    # Mock AuditService.log_decision to capture call
    import app.domains.persona.services.ai_persona_service as svc_mod
    audit_mock = MagicMock()
    audit_mock.log_decision = AsyncMock()
    svc_mod.AuditService = MagicMock(return_value=audit_mock)

    await ai_persona_service.update_ai_persona(
        "co-1", MagicMock(), name="Sofia", tone="amigavel",
        actor_user_id="user-1",
    )
    audit_mock.log_decision.assert_called_once()
    call_kwargs = audit_mock.log_decision.call_args.kwargs
    assert call_kwargs["action"] == "ai_persona_update"
    assert call_kwargs["decision_type"] == "admin_config_change"
    assert call_kwargs["company_id"] == "co-1"
    assert call_kwargs["actor_user_id"] == "user-1"
    # reasoning deve conter prev/next
    reasoning = " ".join(call_kwargs["reasoning"])
    assert "OldName" in reasoning
    assert "Sofia" in reasoning


@pytest.mark.asyncio
async def test_update_ai_persona_rejects_no_change():
    """name=None E tone=None deve falhar (caller bug)."""
    repo = _make_repo(_make_policy({}))
    _install_repo_mock(repo)
    with pytest.raises(ValueError):
        await ai_persona_service.update_ai_persona(
            "co-1", MagicMock(), name=None, tone=None,
        )
    repo.flush.assert_not_called()
