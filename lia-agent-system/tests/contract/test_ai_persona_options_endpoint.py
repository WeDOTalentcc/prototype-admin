"""F3.2 (audit 2026-05-24) — Contract sensors for GET /api/v1/company-ai-persona/options.

Single source of truth: o catálogo retornado pelo endpoint reflete fielmente
CANONICAL_AI_TONES + TONE_INSTRUCTIONS + TONE_UI_METADATA + name constraints
do validator canonical. Adicionar tom no validator propaga automaticamente
para a UI sem deploy frontend — esses sensores pinam o contrato.

Strategy (source-level + handler-level, sem TestClient):
- Source-level: handler tem dependency canonical (require_company_id +
  get_current_active_user) e está registrado no router. Match na branch
  pin "Source-level assertion" usada em test_wedotalent_admin_gate.py.
- Handler-level: chama a função handler diretamente e valida shape do
  AiPersonaOptionsResponse contra os canonical do validator. Mais rápido
  que TestClient + immune a fixture-of-DB drama.
"""
from __future__ import annotations

import asyncio
import inspect

import pytest

from app.api.v1 import company_ai_persona
from app.api.v1.company_ai_persona import (
    AiPersonaOptionsResponse,
    NameConstraints,
    ToneOption,
    get_ai_persona_options,
)
from app.domains.persona.services.ai_persona_validator import (
    CANONICAL_AI_TONES,
    NAME_MAX_LEN,
    NAME_MIN_LEN,
    RESERVED_BRAND_TOKENS,
    TONE_INSTRUCTIONS,
    TONE_UI_METADATA,
)


# ---------------------------------------------------------------------------
# Handler invocation helper
# ---------------------------------------------------------------------------

def _call_options_handler() -> AiPersonaOptionsResponse:
    """Invoca o handler como se viesse via dependency injection.

    Os params `company_id` e `_user` são `Depends(...)` na assinatura;
    chamamos com kwargs explícitos (dummy values) porque o handler
    **não usa** o user/company id — só lê catálogo estático.
    """
    coro = get_ai_persona_options(
        _user=None,  # type: ignore[arg-type]  # handler ignora; só serve pra forçar JWT
    )
    return asyncio.get_event_loop().run_until_complete(coro)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_options_handler_registered_in_router():
    """Pin que /options está exposto pelo router. Remoção acidental
    quebraria o frontend (que consome no mount)."""
    paths = {r.path for r in company_ai_persona.router.routes if hasattr(r, "path")}
    assert "/company-ai-persona/options" in paths, (
        "GET /company-ai-persona/options sumiu do router. Frontend "
        "(plataforma-lia/.../AiPersonaPanel.tsx) chama esse endpoint no "
        "mount via useAiPersonaOptions() — sem ele a tab 'Personalidade "
        "da IA' renderiza loading infinito."
    )


def test_options_handler_requires_auth():
    """Handler declara dependency canonical (require_company_id +
    get_current_active_user). Source-level assertion porque setup do
    TestClient com JWT exige mais infra que vale o custo."""
    src = inspect.getsource(get_ai_persona_options)
    assert "get_current_active_user" in src, (
        "get_ai_persona_options perdeu Depends(get_current_active_user). "
        "Catálogo é tenant-agnóstico (V2.1) mas continua exigindo JWT válido — "
        "sem o gate, anônimos veem catálogo completo + blocklist de marcas IA "
        "terceiras (sinal pra atacante)."
    )


def test_options_returns_all_canonical_tones():
    """Endpoint retorna exatamente os tons em CANONICAL_AI_TONES — nem
    mais, nem menos. Drift teste: adicionar tom em CANONICAL sem rodar
    o sensor i.e. sem mexer em TONE_UI_METADATA faria o handler explodir
    KeyError; esse teste já cobre na invocação."""
    resp = _call_options_handler()
    returned_values = [t.value for t in resp.tones]
    assert returned_values == list(CANONICAL_AI_TONES), (
        f"Catálogo divergente: retornou {returned_values}, canonical "
        f"é {list(CANONICAL_AI_TONES)}. Ordem importa (frontend renderiza "
        f"cards na ordem retornada)."
    )


def test_options_each_tone_has_required_fields():
    """Cada ToneOption tem value+label_pt+short_pt+instruction+previews
    non-empty. Schema é extra='forbid' — adicionar campo no backend
    sem mirror no frontend type falharia tsc."""
    resp = _call_options_handler()
    for tone in resp.tones:
        assert tone.value, f"Tone {tone!r} sem value"
        assert tone.label_pt, f"Tone {tone.value} sem label_pt"
        assert tone.short_pt, f"Tone {tone.value} sem short_pt"
        assert tone.instruction, f"Tone {tone.value} sem instruction"
        assert tone.preview_message_pt, f"Tone {tone.value} sem preview_message_pt"
        assert tone.preview_chat_pt, f"Tone {tone.value} sem preview_chat_pt"


def test_options_tone_fields_match_validator_canonical():
    """Os campos retornados batem exatamente com os do validator
    (TONE_INSTRUCTIONS + TONE_UI_METADATA). Pin de coerência: alterar
    label/short no validator propaga; alterar no endpoint (e ninguém
    mais consome) seria drift inverso."""
    resp = _call_options_handler()
    for tone in resp.tones:
        assert tone.instruction == TONE_INSTRUCTIONS[tone.value], (
            f"Tone {tone.value}: instruction diverge do validator"
        )
        meta = TONE_UI_METADATA[tone.value]
        assert tone.label_pt == meta["label_pt"]
        assert tone.short_pt == meta["short_pt"]
        assert tone.preview_message_pt == meta["preview_message_pt"]
        assert tone.preview_chat_pt == meta["preview_chat_pt"]


def test_options_includes_name_constraints():
    """Response inclui constraints de nome canonical: min/max length
    + blocklist case-insensitive de marcas IA terceiras."""
    resp = _call_options_handler()
    nc = resp.name_constraints
    assert nc.min_length == NAME_MIN_LEN, (
        f"min_length divergiu do validator: {nc.min_length} vs {NAME_MIN_LEN}"
    )
    assert nc.max_length == NAME_MAX_LEN, (
        f"max_length divergiu do validator: {nc.max_length} vs {NAME_MAX_LEN}"
    )
    assert set(nc.blocked_brand_tokens) == set(RESERVED_BRAND_TOKENS), (
        "blocked_brand_tokens divergiu do validator. Adicionar marca "
        "nova em RESERVED_BRAND_TOKENS propaga; remover de uma das pontas "
        "sem a outra cria janela onde nome banido pode ser submetido."
    )
    assert len(nc.blocked_brand_tokens) > 0, "blocklist não pode estar vazia"


def test_options_response_schema_is_extra_forbid():
    """Audit 2026-05-20 REGRA 1: request body schemas usam extra='forbid'.
    Embora /options seja response (não request), o schema canonical
    deve ser estrito para detectar mismatch frontend↔backend logo."""
    for schema in (ToneOption, NameConstraints, AiPersonaOptionsResponse):
        cfg = schema.model_config
        assert cfg.get("extra") == "forbid", (
            f"{schema.__name__} deveria ter extra='forbid'; tem {cfg.get('extra')}"
        )


def test_options_tones_canonical_order_preserved():
    """Cards renderizam na ordem que o backend retorna. Garantir que
    CANONICAL_AI_TONES (tuple ordenada) é preservada — não usar sorted()
    no handler. Audit 2026-05-24: F3.2 spec original sugeria sorted();
    decidimos manter ordem canonical para preservar UX existente
    (profissional primeiro, depois variations crescentes de calor)."""
    resp = _call_options_handler()
    expected_order = list(CANONICAL_AI_TONES)
    actual_order = [t.value for t in resp.tones]
    assert actual_order == expected_order, (
        f"Ordem dos tons divergiu: backend retorna {actual_order}, "
        f"esperado {expected_order}. Mudar ordem aqui afeta UX (cards "
        f"reordenam visualmente sem warning ao usuário)."
    )
