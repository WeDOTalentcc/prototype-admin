"""
Validator canonical para nome + tom da IA per-tenant (tab "Personalidade
da IA" em Minha Empresa, audit 2026-05-21 E2.1).

## Onde isto se encaixa

`CompanyHiringPolicy.communication_rules.ai_persona` armazena por tenant:

    {
      "name": "Sofia",
      "tone": "amigavel"
    }

Endpoint REST + LLM tool + admin WeDOTalent UI usam o MESMO validator.
Centralização canonical fail-closed — qualquer caller passa pelos mesmos
gates. DRY: regra de "Sofia" ser rejeitada (ou aceita) vive em um único
lugar; mudança força commit reviewable.

## Por que blocklist de marcas IA terceiras

Permitir o cliente nomear sua IA de "Claude" / "ChatGPT" / "Gemini" cria:

1. **Confusão legal** — usuário final pode acreditar que está conversando
   com a Anthropic / OpenAI / Google. Risco de trademark.
2. **Confusão suporte** — cliente liga "minha Claude não responde",
   suporte WeDOTalent precisa decifrar.
3. **Misleading branding** — IA realmente roda em outro provider; usar
   o nome do provider concorrente é dishonest signaling.

Blocklist é estrita case-insensitive. Substring matching em "Claude"
captura "MyClaude", "ClaudeBot", etc.

## Por que enum de tones e não free-text

Cada tone canonical mapeia para uma instrução textual específica que
o `SystemPromptBuilder` injeta no system prompt da LIA. Free-text quebra
o contrato — frontend mostra X, backend não sabe traduzir pra LLM.

## TDD anchor

Testes em `tests/contract/test_ai_persona_validator.py` definem o
contrato. A implementação aqui é a resposta deterministic a esses testes.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# Canonical tones
# ---------------------------------------------------------------------------

CANONICAL_AI_TONES: tuple[str, ...] = (
    "profissional",
    "amigavel",
    "formal",
    "casual",
    "formal_amigavel",
    "empatico",
)


TONE_INSTRUCTIONS: dict[str, str] = {
    "profissional": (
        "Tom profissional: cordial, direto, focado em resultados. Linguagem "
        "clara e objetiva. Evite gírias e excesso de informalidade, mas "
        "também não seja distante — uma colega sênior em ambiente corporativo."
    ),
    "amigavel": (
        "Tom amigável: caloroso, acessível, com leveza. Use expressões "
        "cordiais como 'que bom', 'fico feliz', 'vamos juntos', sem perder "
        "profissionalismo. Demonstre interesse genuíno pelas pessoas."
    ),
    "formal": (
        "Tom formal: rigor protocolar, tratamento por 'você' sempre, sem "
        "contrações ('não' em vez de 'né'). Estrutura de mensagem completa "
        "com saudação + corpo + encerramento. Adequado a setores tradicionais."
    ),
    "casual": (
        "Tom casual: descontraído, próximo, como uma conversa de WhatsApp "
        "entre colegas. Pode usar expressões coloquiais comuns. NÃO use "
        "gírias regionais que possam confundir ou excluir."
    ),
    "formal_amigavel": (
        "Tom formal-amigável: equilibra rigor profissional com calor humano. "
        "Estruturas completas + expressões cordiais ocasionais. Indicado "
        "quando precisa transmitir competência sem soar frio."
    ),
    "empatico": (
        "Tom empático: ênfase em escuta, reconhecimento de esforço, "
        "acolhimento. Use frases como 'entendo', 'sei que pode ser "
        "desafiador', 'estamos juntos nisso'. Especialmente útil em "
        "rejeições, follow-ups demorados e situações sensíveis."
    ),
}


# ---------------------------------------------------------------------------
# UI metadata canonical (labels/shorts/preview PT-BR)
# ---------------------------------------------------------------------------

# Source of truth para labels/shorts/preview consumidos pela UI. Audit
# 2026-05-24 (F3.2): antes desse bloco, TONE_OPTIONS estava hardcoded em
# plataforma-lia/src/components/settings/AiPersonaPanel.tsx criando drift
# garantido — adicionar tom novo no backend exigia commit coordenado no
# frontend e ninguém lembrava. Agora frontend consome via
# GET /api/v1/company-ai-persona/options e a propagação é automática.
#
# label_pt: rótulo curto pro cartão de seleção (UI mostra como título)
# short_pt: subtítulo de 1 linha (descrição curta do tom)
# preview_message_pt: exemplo do que a IA escreveria PARA o candidato
#   (e-mail/WhatsApp outbound). Use "LIA" como placeholder do nome — o
#   frontend substitui dinamicamente pelo nome customizado.
# preview_chat_pt: exemplo do que a IA escreveria PARA o recrutador no
#   chat lateral. Não inclui o nome.
TONE_UI_METADATA: dict[str, dict[str, str]] = {
    "profissional": {
        "label_pt": "Profissional",
        "short_pt": "Cordial, direto, focado em resultados.",
        "preview_message_pt": (
            "Olá! Identificamos seu perfil para a vaga de Desenvolvedor. "
            "Podemos agendar uma conversa para esta semana?"
        ),
        "preview_chat_pt": (
            "Encontrei 12 candidatos compatíveis com a vaga. Quer que eu "
            "priorize por experiência ou faixa salarial?"
        ),
    },
    "amigavel": {
        "label_pt": "Amigável",
        "short_pt": "Caloroso, acessível, com leveza.",
        "preview_message_pt": (
            "Oi! Que bom encontrar seu perfil para a vaga de Desenvolvedor. "
            "Você teria um tempinho essa semana pra gente conversar?"
        ),
        "preview_chat_pt": (
            "Boa! Achei 12 candidatos legais pra essa vaga — quer que eu "
            "te mostre os mais alinhados primeiro?"
        ),
    },
    "formal": {
        "label_pt": "Formal",
        "short_pt": "Rigor protocolar, sem contrações, estrutura completa.",
        "preview_message_pt": (
            "Prezado(a) candidato(a), tenho o prazer de convidá-lo(a) para "
            "conversarmos sobre a oportunidade de Desenvolvedor. Aguardo "
            "seu retorno."
        ),
        "preview_chat_pt": (
            "Foram identificados 12 candidatos compatíveis. Solicito sua "
            "orientação quanto ao critério de priorização."
        ),
    },
    "casual": {
        "label_pt": "Casual",
        "short_pt": "Descontraído, próximo, como conversa de WhatsApp.",
        "preview_message_pt": (
            "Ei! Vi que seu perfil bate com a vaga de Dev. Tem um tempinho "
            "pra gente bater um papo essa semana?"
        ),
        "preview_chat_pt": (
            "Achei uns 12 candidatos pra essa vaga. Qual ordem você prefere? "
            "Por experiência ou por fit cultural?"
        ),
    },
    "formal_amigavel": {
        "label_pt": "Formal-amigável",
        "short_pt": "Equilibra rigor profissional com calor humano.",
        "preview_message_pt": (
            "Olá! Foi um prazer encontrar seu perfil. Gostaria de convidar "
            "você para conversarmos sobre a vaga de Desenvolvedor — quando "
            "seria um bom momento?"
        ),
        "preview_chat_pt": (
            "Encontrei 12 candidatos com boa aderência. Posso te mostrar "
            "agrupados por senioridade, se ajudar?"
        ),
    },
    "empatico": {
        "label_pt": "Empático",
        "short_pt": "Escuta, reconhecimento, acolhimento.",
        "preview_message_pt": (
            "Olá! Entendo que processos seletivos podem ser intensos. "
            "Adoraria conversar com você sobre a vaga de Desenvolvedor — "
            "escolha um horário que funcione bem pra você."
        ),
        "preview_chat_pt": (
            "Sei que escolher entre vários candidatos não é fácil. Encontrei "
            "12 perfis — quer que eu te ajude a pensar critério a critério?"
        ),
    },
}


# ---------------------------------------------------------------------------
# Legacy dispatcher mapping (PT-BR → EN)
# ---------------------------------------------------------------------------

# Translator at the boundary: dispatcher legacy (_apply_tone em
# communication_dispatcher.py) espera enum EN. Mantemos PT-BR como
# canonical da feature Ai Persona (UX, validator, SystemPromptBuilder
# via TONE_INSTRUCTIONS) e mapeamos no service antes de gravar em
# `communication_rules.lia_tone` (legacy outbound key).
#
# Audit 2026-05-24 (F3.1): descoberto drift. Service gravava enum PT-BR
# em `lia_tone`; dispatcher só reconhece "friendly" e "formal" (resto
# cai no default "professional"). Recrutador escolhia "empatico" e o
# outbound saía com tom default silenciosamente.
#
# Approach A escolhido per CLAUDE.md "lia_tone canonical precedence" —
# manter 2 representações coerentes: ai_persona.tone (PT-BR canonical)
# + communication_rules.lia_tone (EN para o dispatcher legacy).
#
# Sobre os mappings de tons sem equivalente direto no dispatcher:
#   - dispatcher só tem 2 buckets reais ("friendly", "formal") + default.
#   - "casual" → "friendly" (greeting informal "Oi, X!" é o mais próximo)
#   - "formal_amigavel" → "formal" (mantém tratamento formal "Prezado(a)")
#   - "empatico" → "friendly" (greeting caloroso é mais alinhado que formal)
# Approach B (migrar dispatcher pra usar `ai_persona.tone` + `TONE_INSTRUCTIONS`)
# fica em backlog técnico — risco baixo + reescrita do dispatcher.
TONE_PT_TO_EN_LEGACY: dict[str, str] = {
    "profissional": "professional",      # default fallthrough no dispatcher
    "amigavel": "friendly",              # reconhecido pelo dispatcher
    "formal": "formal",                  # reconhecido pelo dispatcher
    "casual": "friendly",                # closest match — bucket informal
    "formal_amigavel": "formal",         # closest match — bucket formal
    "empatico": "friendly",              # closest match — bucket caloroso
}


# ---------------------------------------------------------------------------
# Name constraints
# ---------------------------------------------------------------------------

DEFAULT_AI_NAME: str = "LIA"
DEFAULT_AI_TONE: str = "profissional"

_NAME_MIN_LEN = 2
_NAME_MAX_LEN = 20

# Public aliases (audit 2026-05-24 F3.2): expostos pelo endpoint /options
# para o frontend renderizar constraints inline. Mantemos os underscored
# como privados pra não quebrar imports legacy desse módulo.
NAME_MIN_LEN: int = _NAME_MIN_LEN
NAME_MAX_LEN: int = _NAME_MAX_LEN

# Alfanumérico (incluindo acentos PT-BR comuns) + espaço.
# - Aceita: "LIA", "Sofia", "Ana Beatriz", "João", "Lia2025"
# - Rejeita: "Sofia@Acme", "Sofia<script>", "Lia/Bot", emojis, símbolos
_NAME_PATTERN = re.compile(
    r"^[A-Za-zÀ-ÖØ-öø-ÿ0-9 ]+$"
)

# Marcas IA terceiras + variações. Match é substring case-insensitive
# — bloqueia "MyClaude", "GPT-4 Pro", "claudia" (esta é falsa coincidência
# infeliz mas o trade-off é defender contra acidente). Se um nome legítimo
# entrar no blocklist por falsa coincidência, ajustar aqui.
RESERVED_BRAND_TOKENS: tuple[str, ...] = (
    "claude",
    "anthropic",
    "chatgpt",
    "gpt",
    "openai",
    "gemini",
    "google bard",
    "bard",
    "copilot",
    "llama",
    "mistral",
)

# Private alias mantido para compat com validate_name (que ainda referencia
# _RESERVED_BRAND_TOKENS internamente). Audit 2026-05-24 F3.2.
_RESERVED_BRAND_TOKENS = RESERVED_BRAND_TOKENS


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------

@dataclass
class ValidationResult:
    """Outcome de uma chamada do validator.

    Shape mirror de :class:`tenant_persona_validator.ValidationResult`
    — admin WeDOTalent UI já sabe consumir. JSON-serializable (errors são
    dicts).
    """
    is_valid: bool
    errors: list[dict[str, str]] = field(default_factory=list)
    warnings: list[dict[str, str]] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def validate_tone(tone: Any) -> ValidationResult:
    """Valida o campo `tone`. Strict enum match contra
    :data:`CANONICAL_AI_TONES`.

    Trade-off de strictness: rejeita variações comuns (case mismatch,
    acentos, espaços extras) em vez de tentar normalizar. Frontend
    DEVE enviar o valor canonical exato — protege contra typos
    silenciosos que iriam parar o `SystemPromptBuilder`.
    """
    result = ValidationResult(is_valid=True)
    if not isinstance(tone, str):
        result.is_valid = False
        result.errors.append({
            "code": "tone_invalid_type",
            "message": (
                f"Tom deve ser string; recebi {type(tone).__name__}."
            ),
            "fix": (
                f"Use um dos tons canonical: {', '.join(CANONICAL_AI_TONES)}."
            ),
        })
        return result
    if tone not in CANONICAL_AI_TONES:
        result.is_valid = False
        result.errors.append({
            "code": "tone_not_canonical",
            "message": f"Tom '{tone}' não é canonical.",
            "fix": (
                f"Use um dos tons canonical: {', '.join(CANONICAL_AI_TONES)}."
            ),
        })
    return result


def validate_name(name: Any) -> ValidationResult:
    """Valida o campo `name`. Regras canonical:

    - Tipo string obrigatório
    - Comprimento entre 2 e 20 chars (sem espaços trim)
    - Charset alfanumérico + acentos PT-BR + espaço
    - Não pode conter (substring case-insensitive) marca IA terceira
      conhecida — vide :data:`_RESERVED_BRAND_TOKENS`
    """
    result = ValidationResult(is_valid=True)
    if name is None:
        result.is_valid = False
        result.errors.append({
            "code": "name_invalid_type",
            "message": "Nome não pode ser nulo.",
            "fix": "Envie uma string entre 2 e 20 caracteres.",
        })
        return result
    if not isinstance(name, str):
        result.is_valid = False
        result.errors.append({
            "code": "name_invalid_type",
            "message": f"Nome deve ser string; recebi {type(name).__name__}.",
            "fix": "Envie uma string entre 2 e 20 caracteres.",
        })
        return result

    stripped = name.strip()
    if not stripped:
        result.is_valid = False
        result.errors.append({
            "code": "name_empty",
            "message": "Nome não pode ser vazio.",
            "fix": "Escolha um nome curto e memorável (ex.: Sofia, Maya, Atena).",
        })
        return result
    if len(stripped) < _NAME_MIN_LEN:
        result.is_valid = False
        result.errors.append({
            "code": "name_too_short",
            "message": f"Nome muito curto ({len(stripped)} char); mínimo {_NAME_MIN_LEN}.",
            "fix": "Escolha um nome com pelo menos 2 caracteres.",
        })
        return result
    if len(stripped) > _NAME_MAX_LEN:
        result.is_valid = False
        result.errors.append({
            "code": "name_too_long",
            "message": f"Nome muito longo ({len(stripped)} char); máximo {_NAME_MAX_LEN}.",
            "fix": f"Encurte o nome para até {_NAME_MAX_LEN} caracteres.",
        })
        return result
    if not _NAME_PATTERN.match(stripped):
        result.is_valid = False
        result.errors.append({
            "code": "name_invalid_chars",
            "message": (
                "Nome contém caracteres inválidos. Use apenas letras "
                "(com acentos), números e espaços."
            ),
            "fix": "Remova símbolos como @, /, <, >, emojis.",
        })
        return result

    # Blocklist marcas IA terceiras (substring case-insensitive)
    lowered = stripped.lower()
    for token in _RESERVED_BRAND_TOKENS:
        if token in lowered:
            result.is_valid = False
            result.errors.append({
                "code": "name_reserved_brand",
                "message": (
                    f"O nome '{stripped}' contém uma marca de IA reservada "
                    f"('{token}')."
                ),
                "fix": (
                    "Escolha outro nome único para sua IA. Exemplos: "
                    "Sofia, Maya, Atena, Iris, Nova, Ada."
                ),
            })
            return result

    return result


def validate_persona(
    *,
    name: str | None = None,
    tone: str | None = None,
) -> ValidationResult:
    """Valida update parcial de persona. Agrega erros de ambos os campos
    (não falha no primeiro — UI renderiza todos os problemas juntos).

    Se ambos forem ``None``, retorna ``no_change_requested`` (caller bug:
    chamou update sem nada pra atualizar).
    """
    result = ValidationResult(is_valid=True)
    if name is None and tone is None:
        result.is_valid = False
        result.errors.append({
            "code": "no_change_requested",
            "message": "Nenhum campo enviado para atualização (nome ou tom).",
            "fix": "Envie pelo menos um dos campos: name, tone.",
        })
        return result
    if name is not None:
        name_result = validate_name(name)
        if not name_result.is_valid:
            result.is_valid = False
            result.errors.extend(name_result.errors)
    if tone is not None:
        tone_result = validate_tone(tone)
        if not tone_result.is_valid:
            result.is_valid = False
            result.errors.extend(tone_result.errors)
    return result


__all__ = [
    "CANONICAL_AI_TONES",
    "TONE_INSTRUCTIONS",
    "TONE_UI_METADATA",
    "TONE_PT_TO_EN_LEGACY",
    "NAME_MIN_LEN",
    "NAME_MAX_LEN",
    "RESERVED_BRAND_TOKENS",
    "DEFAULT_AI_NAME",
    "DEFAULT_AI_TONE",
    "ValidationResult",
    "validate_tone",
    "validate_name",
    "validate_persona",
]
