"""Gate de intenção de Configurações (fix 2026-06-01): uma ação explícita de
settings NÃO deve ser sequestrada por um wizard de vaga ativo/recente.

Contexto (bug "não salvo via chat" reportado por Paulo 2026-06-01):
  O chat lateral compartilha a session_id do chat flutuante. Após abrir um
  wizard de vaga, `is_wizard_session_active` fica True por 2h (TTL). Quando o
  usuário vai em Configurações e pede pra LIA preencher (CNPJ etc.), a mensagem
  `[ACTION:prefill_section]...` (e os turnos seguintes com domain_hint=
  "company_settings") eram pinados no agente `wizard`, que NÃO tem as tools
  `save_company_field`/`save_company_section`. Resultado: LIA conversa, pede
  confirmação, mas nunca persiste.

  Princípio canônico (mesma regra já aplicada ao `domain` hard no transport):
  intenção explícita do FE para um domínio NÃO-wizard vence o pin implícito.
"""
import pytest

from app.shared.sessions import thread_id as tid
from app.shared.sessions import should_pin_to_wizard


@pytest.mark.medium
@pytest.mark.asyncio
async def test_settings_action_tag_not_pinned_even_when_wizard_active(monkeypatch):
    """Turno 1: deeplink [ACTION:prefill_section] nao pina no wizard."""
    async def _active(c, s):
        return True
    monkeypatch.setattr(tid, "is_wizard_session_active", _active)
    msg = (
        "[ACTION:prefill_section]\n[target_section:basic]\n\n"
        "Quero preencher a secao Dados Basicos da minha empresa."
    )
    assert await should_pin_to_wizard("comp-1", "sess-1", msg) is False


@pytest.mark.medium
@pytest.mark.asyncio
async def test_configure_action_tag_not_pinned(monkeypatch):
    async def _active(c, s):
        return True
    monkeypatch.setattr(tid, "is_wizard_session_active", _active)
    assert await should_pin_to_wizard(
        "comp-1", "sess-1", "[ACTION:configure_benefits] preencher beneficios"
    ) is False


@pytest.mark.medium
@pytest.mark.asyncio
async def test_non_wizard_domain_hint_not_pinned(monkeypatch):
    """Turnos seguintes (texto puro): domain_hint=company_settings vence o pin."""
    async def _active(c, s):
        return True
    monkeypatch.setattr(tid, "is_wizard_session_active", _active)
    assert await should_pin_to_wizard(
        "comp-1", "sess-1", "12.345.678/0001-90", domain_hint="company_settings"
    ) is False


@pytest.mark.medium
@pytest.mark.asyncio
async def test_wizard_domain_hint_still_pins(monkeypatch):
    """domain_hint=wizard NAO deve escapar do pin (regressao guard)."""
    async def _active(c, s):
        return True
    monkeypatch.setattr(tid, "is_wizard_session_active", _active)
    assert await should_pin_to_wizard(
        "comp-1", "sess-1", "qual competencia?", domain_hint="wizard"
    ) is True


@pytest.mark.medium
@pytest.mark.asyncio
async def test_plain_continuation_without_hint_still_pins(monkeypatch):
    """Sem tag e sem hint, continuacao normal do wizard ainda pina (status quo)."""
    async def _active(c, s):
        return True
    monkeypatch.setattr(tid, "is_wizard_session_active", _active)
    assert await should_pin_to_wizard("comp-1", "sess-1", "muda a pergunta 3") is True
