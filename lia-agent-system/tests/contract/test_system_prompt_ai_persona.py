"""
E2.3 contract sensor — integração SystemPromptBuilder com ai_persona
per-tenant.

Garante:
1. ``build(ai_persona=None)`` preserva comportamento legacy (zero
   override). Pin de back-compat — qualquer caller existente continua
   funcionando.
2. ``build(ai_persona={"name": "LIA", "tone": "profissional"})`` é
   equivalente a None (defaults — não emite override).
3. Nome custom dispara bloco "Override de Persona" com instrução
   explícita ao LLM.
4. Tom canonical não-default emite bloco "Tom de Voz Customizado" com
   instrução textual de TONE_INSTRUCTIONS.
5. Nome E tom customizados — ambos blocos aparecem.
6. Persona base (lia_persona.yaml) NÃO é modificada — só appendamos
   sections. Imutabilidade do canonical.
"""
from __future__ import annotations

import pytest

from app.domains.persona.services.ai_persona_validator import (
    CANONICAL_AI_TONES,
    DEFAULT_AI_NAME,
    DEFAULT_AI_TONE,
    TONE_INSTRUCTIONS,
)
from app.shared.prompts.system_prompt_builder import SystemPromptBuilder


# Strings-âncora do persona base. Se sumirem, o builder está quebrado
# ou os tests precisam ser atualizados — qualquer dos dois bloqueia merge.
PERSONA_BASE_ANCHOR = "Quem é a LIA"


def test_build_without_ai_persona_renders_legacy_prompt():
    """Back-compat: callers existentes que NÃO passam ai_persona devem
    obter o mesmo prompt de antes da E2.3 — zero seção 'Override de
    Persona', zero 'Tom de Voz Customizado'."""
    prompt = SystemPromptBuilder.build()
    assert PERSONA_BASE_ANCHOR in prompt
    assert "Override de Persona" not in prompt
    assert "Tom de Voz Customizado" not in prompt


def test_build_with_defaults_does_not_emit_override_blocks():
    """ai_persona={LIA, profissional} = defaults canonical → comportamento
    idêntico a omissão. Pin para evitar regression de emit-quando-default."""
    prompt = SystemPromptBuilder.build(
        ai_persona={"name": DEFAULT_AI_NAME, "tone": DEFAULT_AI_TONE},
    )
    assert "Override de Persona" not in prompt
    assert "Tom de Voz Customizado" not in prompt


def test_custom_name_emits_persona_override_block():
    prompt = SystemPromptBuilder.build(
        ai_persona={"name": "Sofia", "tone": DEFAULT_AI_TONE},
    )
    assert "Override de Persona" in prompt
    assert "Sofia" in prompt
    # Tom default → bloco tom NÃO aparece
    assert "Tom de Voz Customizado" not in prompt


def test_custom_tone_emits_tone_instruction_block():
    prompt = SystemPromptBuilder.build(
        ai_persona={"name": DEFAULT_AI_NAME, "tone": "amigavel"},
    )
    assert "Tom de Voz Customizado" in prompt
    # A instrução textual completa deve aparecer
    assert TONE_INSTRUCTIONS["amigavel"] in prompt
    # Nome default → bloco override NÃO aparece
    assert "Override de Persona" not in prompt


def test_both_custom_emit_both_blocks():
    prompt = SystemPromptBuilder.build(
        ai_persona={"name": "Maya", "tone": "empatico"},
    )
    assert "Override de Persona" in prompt
    assert "Maya" in prompt
    assert "Tom de Voz Customizado" in prompt
    assert TONE_INSTRUCTIONS["empatico"] in prompt


def test_persona_base_yaml_is_not_mutated():
    """O canonical lia_persona.yaml NÃO pode ser alterado em runtime.
    Build com ai_persona customizado APPENDA — nunca substitui o base.
    Pin contra reintroduzir substituição direta no YAML cached."""
    prompt_legacy = SystemPromptBuilder.build()
    prompt_custom = SystemPromptBuilder.build(
        ai_persona={"name": "Sofia", "tone": "amigavel"},
    )
    # Persona base é prefix do prompt customizado (com possível adição
    # de glossário+domain entre eles). Mas a primeira seção tem que ser
    # idêntica entre os dois.
    base_section_legacy = prompt_legacy.split("##")[0:5]  # primeiros chunks
    base_section_custom = prompt_custom.split("##")[0:5]
    assert base_section_legacy == base_section_custom, (
        "Persona base divergiu entre legacy e custom — ai_persona NÃO pode "
        "mutar o YAML canonical, apenas appendar sections."
    )


@pytest.mark.parametrize("tone", sorted(CANONICAL_AI_TONES))
def test_every_canonical_tone_can_be_injected(tone):
    """Pin: cada tone canonical produz um prompt válido sem exceções.
    Se um tone novo for adicionado a CANONICAL_AI_TONES, ele DEVE estar
    em TONE_INSTRUCTIONS — esse teste captura desalinhamento."""
    prompt = SystemPromptBuilder.build(
        ai_persona={"name": DEFAULT_AI_NAME, "tone": tone},
    )
    if tone == DEFAULT_AI_TONE:
        # Default não emite bloco
        assert "Tom de Voz Customizado" not in prompt
    else:
        assert "Tom de Voz Customizado" in prompt
        assert TONE_INSTRUCTIONS[tone] in prompt


def test_invalid_tone_in_ai_persona_does_not_crash_build():
    """Se o tenant tiver dados corrompidos (DB direto, tone fora do
    canonical), o builder NÃO pode crashar — ignora silently e usa
    persona base. Fail-open em runtime é correto: melhor LLM sem tom
    custom do que LLM offline."""
    # Não esperar exception — só validar que retorna string não-vazia
    prompt = SystemPromptBuilder.build(
        ai_persona={"name": DEFAULT_AI_NAME, "tone": "tone_corrompido"},
    )
    assert isinstance(prompt, str)
    assert len(prompt) > 0
    # E o bloco NÃO foi adicionado (tone inválido = silently ignored)
    assert "tone_corrompido" not in prompt


def test_ai_persona_none_dict_field_does_not_crash():
    """Defensive: dict parcial (sem name OR sem tone) — usa default
    canonical pro campo ausente."""
    prompt_no_name = SystemPromptBuilder.build(ai_persona={"tone": "casual"})
    assert "Tom de Voz Customizado" in prompt_no_name
    # Name default LIA → sem override
    assert "Override de Persona" not in prompt_no_name

    prompt_no_tone = SystemPromptBuilder.build(ai_persona={"name": "Atena"})
    assert "Override de Persona" in prompt_no_tone
    assert "Atena" in prompt_no_tone
