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



# ── Fix 2026-06-06: release do pin por data-query/navegação (transcript Paulo) ─
from app.shared.sessions.thread_id import (  # noqa: E402
    _is_non_wizard_query,
)
import app.shared.sessions.thread_id as _tid  # noqa: E402


@pytest.mark.parametrize("msg", [
    "liste os candidatos dessa vaga e rankeie os melhores",
    "voce consegue abrir a vaga de diretor juridico que tem 24 candidatos",
    "me leve para funil de talentos",
    "quer ver kanban com os candidatos",
    "rankeie os melhores candidatos",
    "como está o pipeline",
    "quais candidatos temos",
    "mostre o perfil do candidato",
])
def test_data_query_libera_pin(msg):
    assert _is_non_wizard_query(msg) is True, f"deveria liberar: {msg!r}"


@pytest.mark.parametrize("msg", [
    "sim",
    "a vaga é remota e o salário é 15 mil",
    "muda a pergunta 3",
    "pode publicar",
    "quero um desenvolvedor sênior com Python e AWS",
    "liste as perguntas de triagem",
])
def test_continuacao_wizard_nao_libera(msg):
    assert _is_non_wizard_query(msg) is False, f"NÃO deveria liberar (é wizard): {msg!r}"


@pytest.mark.asyncio
async def test_should_pin_libera_data_query_mesmo_com_wizard_ativo(monkeypatch):
    async def _always_active(*a, **k):
        return True
    monkeypatch.setattr(_tid, "is_wizard_session_active", _always_active)
    # data-query -> NÃO pina (libera pro domínio) apesar do wizard ativo
    assert await _tid.should_pin_to_wizard("c", "s", "liste os candidatos da vaga") is False
    # continuação genuína -> pina (fica no wizard)
    assert await _tid.should_pin_to_wizard("c", "s", "a vaga é remota") is True
