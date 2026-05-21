"""
E2.1 contract sensor (audit 2026-05-21) — validator canonical para nome +
tom da IA per-tenant (tab "Personalidade da IA" em Minha Empresa).

Hierarquia canonical:
- ``CompanyHiringPolicy.communication_rules.ai_persona`` armazena
  ``{name: str, tone: str}`` por tenant.
- O validator em ``app/domains/persona/services/ai_persona_validator.py``
  é o ÚNICO ponto que decide se um valor é aceitável. Endpoint REST + LLM
  tool + admin WeDOTalent UI usam o mesmo validator (DRY canonical).

TDD: estes testes existem ANTES do validator. Eles definem o contrato
explicitamente. A implementação deve fazê-los passar — não o contrário.

Constraints capturados:
1. Nome: 2-20 chars, alfanumérico + acentos PT-BR + espaço; sem PII;
   blocklist de marcas IA terceiras (evita confusão legal); default 'LIA'.
2. Tone: enum estrito (6 valores canonical); cada tone tem instrução textual
   correspondente que o SystemPromptBuilder injeta no system prompt.
3. Mensagens de erro: PT-BR, actionable (``code`` + ``message`` + ``fix``).
"""
from __future__ import annotations

import pytest


# --- Imports under test ----------------------------------------------------


def _import_validator():
    """Indirection so collecting tests doesn't crash if module doesn't exist
    yet. Each test calls this to get the module; pytest reports a clean
    ImportError at the test level instead of at collection."""
    from app.domains.persona.services import ai_persona_validator
    return ai_persona_validator


# --- Tone enum -------------------------------------------------------------

EXPECTED_TONES = {
    "profissional", "amigavel", "formal", "casual",
    "formal_amigavel", "empatico",
}


def test_canonical_tones_set_is_stable():
    """O conjunto de tones é parte do contrato com o frontend (cards de
    seleção) e com o SystemPromptBuilder (cada tone → instrução textual).
    Adicionar / remover força coordenação com UI."""
    mod = _import_validator()
    assert hasattr(mod, "CANONICAL_AI_TONES")
    assert set(mod.CANONICAL_AI_TONES) == EXPECTED_TONES


def test_each_tone_has_textual_instruction():
    """Cada tone canonical PRECISA ter uma instrução textual em PT-BR que
    o SystemPromptBuilder injeta. Tone sem instrução é UI sem efeito IA."""
    mod = _import_validator()
    for tone in mod.CANONICAL_AI_TONES:
        instruction = mod.TONE_INSTRUCTIONS.get(tone)
        assert instruction, f"Tone '{tone}' sem TONE_INSTRUCTIONS mapping"
        assert isinstance(instruction, str)
        assert len(instruction) >= 30, (
            f"Instrução de tone '{tone}' muito curta ({len(instruction)} "
            f"chars) — precisa de pelo menos 30 caracteres para gerar "
            f"comportamento mensurável no LLM."
        )


# --- validate_tone() -------------------------------------------------------

@pytest.mark.parametrize("tone", sorted(EXPECTED_TONES))
def test_validate_tone_accepts_canonical(tone):
    mod = _import_validator()
    result = mod.validate_tone(tone)
    assert result.is_valid, f"Tone canonical '{tone}' rejeitado: {result.errors}"


@pytest.mark.parametrize(
    "bad_tone",
    [
        "PROFISSIONAL",  # case mismatch
        "amigável",      # com acento (canonical sem)
        "rude",
        "informal",      # próximo mas não canonical
        "",
        None,
        123,
        " amigavel ",    # com espaços
    ],
)
def test_validate_tone_rejects_non_canonical(bad_tone):
    mod = _import_validator()
    result = mod.validate_tone(bad_tone)
    assert not result.is_valid
    codes = {e["code"] for e in result.errors}
    assert "tone_not_canonical" in codes or "tone_invalid_type" in codes


# --- validate_name() -------------------------------------------------------

@pytest.mark.parametrize(
    "good_name",
    [
        "LIA",
        "Sofia",
        "Maya",
        "Atena",
        "Ana Beatriz",     # com espaço
        "João",            # acento PT-BR
        "Lia2025",         # alfanumérico misto
    ],
)
def test_validate_name_accepts_good_inputs(good_name):
    mod = _import_validator()
    result = mod.validate_name(good_name)
    assert result.is_valid, f"Nome '{good_name}' rejeitado: {result.errors}"


@pytest.mark.parametrize(
    "bad_name,expected_code",
    [
        ("A", "name_too_short"),              # 1 char
        ("X" * 21, "name_too_long"),          # 21 chars
        ("", "name_empty"),
        (None, "name_invalid_type"),
        ("Sofia@Acme", "name_invalid_chars"),  # @
        ("Sofia<script>", "name_invalid_chars"),  # html injection
        ("Claude", "name_reserved_brand"),    # marca IA terceira
        ("CLAUDE", "name_reserved_brand"),    # case-insensitive
        ("ChatGPT", "name_reserved_brand"),
        ("GPT4", "name_reserved_brand"),  # sem hífen — testa blocklist puro
        ("Gemini", "name_reserved_brand"),
        ("anthropic", "name_reserved_brand"),
    ],
)
def test_validate_name_rejects_bad_inputs(bad_name, expected_code):
    mod = _import_validator()
    result = mod.validate_name(bad_name)
    assert not result.is_valid, f"Nome '{bad_name}' deveria ter sido rejeitado"
    codes = {e["code"] for e in result.errors}
    assert expected_code in codes, (
        f"Para nome '{bad_name}', esperava code '{expected_code}', "
        f"recebi {codes}"
    )


def test_validate_name_error_messages_are_actionable_pt_br():
    """Mensagens devem ser em PT-BR + ter campo ``fix`` actionable. UI
    renderiza diretamente — não pode ser cryptic."""
    mod = _import_validator()
    result = mod.validate_name("Claude")
    assert not result.is_valid
    err = next(e for e in result.errors if e["code"] == "name_reserved_brand")
    assert err.get("message")
    assert err.get("fix")
    # Mensagem deve mencionar a alternativa (escolher outro nome)
    assert any(
        word in err["fix"].lower()
        for word in ("escolha", "outro", "diferente")
    ), f"Mensagem fix não é actionable: {err['fix']!r}"


# --- Combinação: validate_persona() ----------------------------------------

def test_validate_persona_accepts_complete_valid_input():
    mod = _import_validator()
    result = mod.validate_persona(name="Sofia", tone="amigavel")
    assert result.is_valid
    assert result.errors == []


def test_validate_persona_aggregates_errors_from_both_fields():
    """Se nome E tom são inválidos, validator deve reportar ambos numa
    única chamada (não falhar no primeiro). UI renderiza todos os erros
    juntos."""
    mod = _import_validator()
    result = mod.validate_persona(name="Claude", tone="rude")
    assert not result.is_valid
    codes = {e["code"] for e in result.errors}
    assert "name_reserved_brand" in codes
    assert "tone_not_canonical" in codes


def test_validate_persona_allows_partial_update_just_name():
    """Update parcial — só nome, sem tom — é caso comum. Validator deve
    aceitar tone=None significando 'não vou mudar'."""
    mod = _import_validator()
    result = mod.validate_persona(name="Sofia", tone=None)
    assert result.is_valid


def test_validate_persona_allows_partial_update_just_tone():
    mod = _import_validator()
    result = mod.validate_persona(name=None, tone="empatico")
    assert result.is_valid


def test_validate_persona_rejects_completely_empty_update():
    """Se nome=None E tone=None, nada está sendo atualizado — caller bug."""
    mod = _import_validator()
    result = mod.validate_persona(name=None, tone=None)
    assert not result.is_valid
    codes = {e["code"] for e in result.errors}
    assert "no_change_requested" in codes


# --- Default name ----------------------------------------------------------

def test_default_name_is_lia():
    """Quando tenant não customizou nome, default é 'LIA' — preserva
    o branding original WeDOTalent. Mudar default é decisão estratégica
    de produto, não bug fix."""
    mod = _import_validator()
    assert mod.DEFAULT_AI_NAME == "LIA"


def test_default_tone_is_profissional():
    """Default tone é 'profissional' — alinha com persona base.
    lia_persona.yaml descreve LIA como 'profissional e acessível'."""
    mod = _import_validator()
    assert mod.DEFAULT_AI_TONE == "profissional"
