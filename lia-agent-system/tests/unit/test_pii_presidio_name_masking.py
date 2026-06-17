"""D-10 — Regressão de privacidade: strip_pii_for_llm_prompt DEVE mascarar o
NOME (PERSON) do candidato antes de qualquer prompt de LLM (LGPD Art. 12).

Contexto do bug: `_get_presidio_analyzer()` instanciava `AnalyzerEngine()` sem
configurar o modelo NER. O default tentava baixar o modelo INGLÊS em runtime,
falhava no ambiente externally-managed e caía no fail-safe silencioso — ou seja,
o nome do candidato NUNCA era mascarado, mesmo com a flag ligada. O fix configura
o `NlpEngineProvider` com o modelo spaCy PT (pt_core_news_sm).
"""
import importlib

import pytest


def _reload(monkeypatch, **env):
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    from app.shared import pii_masking

    importlib.reload(pii_masking)
    return pii_masking


@pytest.fixture
def presidio_available():
    pytest.importorskip("presidio_analyzer")
    pytest.importorskip("pt_core_news_sm")


def test_name_masked_by_default(monkeypatch, presidio_available):
    """Por padrão (Presidio ON) o nome completo é substituído por placeholder."""
    p = _reload(monkeypatch)
    assert p._PRESIDIO_ENABLED is True
    out = p.strip_pii_for_llm_prompt("Candidato Joao da Silva Pereira, engenheiro.")
    assert "Joao" not in out
    assert "Pereira" not in out
    assert "PERSON" in out


def test_disabled_flag_leaves_name(monkeypatch, presidio_available):
    """Com a flag OFF o NER não roda e o nome permanece (regex não cobre nome)."""
    p = _reload(monkeypatch, LLM_PROMPT_PRESIDIO_ENABLED="false")
    assert p._PRESIDIO_ENABLED is False
    out = p.strip_pii_for_llm_prompt("Joao da Silva Pereira")
    assert "Joao" in out


def test_uuid_of_tenant_or_job_is_preserved(monkeypatch, presidio_available):
    """O shield de UUID não pode ser destruído pelo NER (T-F)."""
    p = _reload(monkeypatch)
    uid = "11111111-2222-4333-a444-555555555555"
    out = p.strip_pii_for_llm_prompt(f"Vaga {uid} para Maria Souza")
    assert uid in out
    assert "Maria" not in out


def test_regex_backstop_still_masks_cpf(monkeypatch, presidio_available):
    """A camada regex continua mascarando CPF (backstop determinístico)."""
    p = _reload(monkeypatch)
    out = p.strip_pii_for_llm_prompt("Documento CPF 123.456.789-00 do candidato.")
    assert "123.456.789-00" not in out


def test_entities_are_configurable_via_env(monkeypatch, presidio_available):
    """LLM_PROMPT_PRESIDIO_ENTITIES permite ligar LOCATION (privacidade máxima)."""
    p = _reload(
        monkeypatch,
        LLM_PROMPT_PRESIDIO_ENTITIES="PERSON,EMAIL_ADDRESS,PHONE_NUMBER,NRP,LOCATION",
    )
    assert "LOCATION" in p._PRESIDIO_ENTITIES
    out = p.strip_pii_for_llm_prompt("Candidata mora em Belo Horizonte.")
    assert "Belo Horizonte" not in out
