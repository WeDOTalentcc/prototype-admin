"""Gate de intenção (fix 2026-05-31): saudação pura não resume o wizard.

Complementa o TTL: mesmo um wizard ATIVO e recente não deve ser sequestrado por
um "oi". Só saudações/smalltalk PUROS são bloqueados; mensagens com conteúdo e
continuações ("sim", "muda a pergunta 3", "criar vaga") passam normalmente.
"""
import pytest

from app.shared.sessions import thread_id as tid
from app.shared.sessions import is_greeting_only, should_pin_to_wizard


@pytest.mark.medium
@pytest.mark.parametrize("msg", [
    "oi", "Oi", "OI!", "olá", "ola", "opa", "e aí", "eai", "hey", "hello",
    "bom dia", "Boa tarde", "boa noite", "tudo bem?", "tudo certo", "beleza",
    "oi 👋", "olá!!!", "  oi  ", "menu", "começar",
])
def test_greetings_are_detected(msg):
    assert is_greeting_only(msg) is True


@pytest.mark.medium
@pytest.mark.parametrize("msg", [
    "oi, quero criar uma vaga de analista",
    "criar vaga",
    "sim",
    "ok",
    "muda a pergunta 3",
    "não gostei dessa pergunta",
    "aprovar",
    "esse primeiro",
    "qual o salário de mercado?",
    "bom dia, preciso de ajuda com a triagem",  # saudação + conteúdo
])
def test_content_messages_are_not_greetings(msg):
    assert is_greeting_only(msg) is False


@pytest.mark.medium
def test_empty_is_not_greeting():
    assert is_greeting_only("") is False
    assert is_greeting_only(None) is False


@pytest.mark.medium
@pytest.mark.asyncio
async def test_should_pin_blocks_greeting_even_when_active(monkeypatch):
    # wizard ativo, mas msg é saudação → NÃO pina (vai pro chat geral).
    async def _always_active(c, s):
        raise AssertionError("não deve nem checar a sessão p/ saudação")
    monkeypatch.setattr(tid, "is_wizard_session_active", _always_active)
    assert await should_pin_to_wizard("comp-1", "sess-1", "oi") is False


@pytest.mark.medium
@pytest.mark.asyncio
async def test_should_pin_continuation_when_active(monkeypatch):
    async def _active(c, s):
        return True
    monkeypatch.setattr(tid, "is_wizard_session_active", _active)
    assert await should_pin_to_wizard("comp-1", "sess-1", "muda a pergunta 3") is True


@pytest.mark.medium
@pytest.mark.asyncio
async def test_should_pin_false_when_inactive(monkeypatch):
    async def _inactive(c, s):
        return False
    monkeypatch.setattr(tid, "is_wizard_session_active", _inactive)
    assert await should_pin_to_wizard("comp-1", "sess-1", "criar vaga") is False
