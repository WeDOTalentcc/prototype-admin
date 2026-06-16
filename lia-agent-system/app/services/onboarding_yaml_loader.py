"""
onboarding_yaml_loader.py — P2-2 Sprint A canonical loader.

Carrega lia-agent-system/app/prompts/domains/onboarding_questions.yaml
(criado em Phase 0) e expõe API canonical para o OnboardingOrchestrator
SETTINGS_EXTRACTION phase.

Princípios canonical:
- Single source of truth: YAML é canonical (vide P2-2 Phase 0 ADR).
- DRY: módulo cacheado, leitura única por boot.
- Fail-CLOSED: missing block/field retorna None, NUNCA fallback silencioso.
- Multi-tenancy agnostic: este module é puro data — company_id é
  responsabilidade do caller.

Audit ref: ~/Documents/wedotalent_audit_2026-05-26/P2-2_ONBOARDING_CONVERSACIONAL_ADR.md
"""
from __future__ import annotations

import functools
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

YAML_PATH = (
    Path(__file__).resolve().parents[1]
    / "prompts"
    / "domains"
    / "onboarding_questions.yaml"
)


@dataclass(frozen=True)
class OnboardingField:
    """Campo canonical mapeado pra pergunta conversacional."""

    field_key: str
    question: str
    follow_up: str | None = None
    example_response: str | None = None
    validation: str | None = None
    skippable: bool = False
    extract_hint: str | None = None
    depends_on: str | None = None
    skip_if_same_as: str | None = None


@dataclass(frozen=True)
class OnboardingBlock:
    """Bloco conceitual agrupando fields relacionados."""

    id: str
    title: str
    description: str
    fields: tuple[OnboardingField, ...]
    estimated_questions: int
    note: str | None = None

    @property
    def field_keys(self) -> tuple[str, ...]:
        return tuple(f.field_key for f in self.fields)


@dataclass(frozen=True)
class OnboardingConfig:
    """Config completa do onboarding conversacional."""

    version: int
    locale: str
    persona_greeting: str
    persona_closing: str
    persona_hint_skip: str
    blocks: tuple[OnboardingBlock, ...]
    confirmation_template: str
    finalization_threshold_percent: int

    @property
    def total_fields(self) -> int:
        return sum(len(b.fields) for b in self.blocks)

    @property
    def block_ids(self) -> tuple[str, ...]:
        return tuple(b.id for b in self.blocks)

    def get_block(self, block_id: str) -> OnboardingBlock | None:
        """Retorna bloco por id ou None se nao existir. Fail-CLOSED."""
        for b in self.blocks:
            if b.id == block_id:
                return b
        return None

    def get_field(self, field_key: str) -> OnboardingField | None:
        """Resolve field_key em qualquer bloco. Fail-CLOSED."""
        for b in self.blocks:
            for f in b.fields:
                if f.field_key == field_key:
                    return f
        return None


def _parse_field(raw: dict[str, Any]) -> OnboardingField:
    return OnboardingField(
        field_key=raw["field_key"],
        question=raw["question"],
        follow_up=raw.get("follow_up"),
        example_response=raw.get("example_response"),
        validation=raw.get("validation"),
        skippable=bool(raw.get("skippable", False)),
        extract_hint=raw.get("extract_hint"),
        depends_on=raw.get("depends_on"),
        skip_if_same_as=raw.get("skip_if_same_as"),
    )


def _parse_block(raw: dict[str, Any]) -> OnboardingBlock:
    return OnboardingBlock(
        id=raw["id"],
        title=raw["title"],
        description=raw["description"],
        estimated_questions=int(raw.get("estimated_questions", len(raw["fields"]))),
        note=raw.get("note"),
        fields=tuple(_parse_field(f) for f in raw["fields"]),
    )


@functools.lru_cache(maxsize=1)
def load_config() -> OnboardingConfig:
    """Carrega YAML uma única vez (lru_cache). Fail-CLOSED em erro.

    Returns:
        OnboardingConfig com 5 blocks × 34 fields (esperado).

    Raises:
        FileNotFoundError: YAML missing — config drift detectado, fail alto.
        yaml.YAMLError: YAML invalido — fail alto.
        KeyError: schema mismatch — fail alto.
    """
    if not YAML_PATH.exists():
        raise FileNotFoundError(
            f"onboarding_questions.yaml not found at {YAML_PATH}. "
            "P2-2 Phase 0 missing — verifique commit 433b3ffda17."
        )

    with YAML_PATH.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    persona = raw.get("persona", {})
    config = OnboardingConfig(
        version=int(raw["version"]),
        locale=raw["locale"],
        persona_greeting=persona["greeting"].strip(),
        persona_closing=persona["closing"].strip(),
        persona_hint_skip=persona["hint_skip"],
        blocks=tuple(_parse_block(b) for b in raw["blocks"]),
        confirmation_template=raw["confirmation_template"].strip(),
        finalization_threshold_percent=int(raw["finalization_threshold_percent"]),
    )

    logger.info(
        "onboarding_questions.yaml loaded: %d blocks, %d fields total",
        len(config.blocks),
        config.total_fields,
    )
    return config


def get_next_question(
    answered_field_keys: set[str],
    current_block_id: str | None = None,
) -> tuple[OnboardingBlock, OnboardingField] | None:
    """Determina proxima pergunta dado estado.

    Estrategia:
    1. Se current_block_id setado e tem fields nao-respondidos, retorna primeiro nao-respondido desse bloco.
    2. Senao, scaneia blocks na ordem do YAML e retorna primeiro nao-respondido.
    3. Se TODOS respondidos, retorna None (sinal de onboarding completo).

    Respeita:
    - depends_on: pula field se dependencia nao foi respondida AND não foi pulada.
    - skip_if_same_as: pula field se valor seria identico ao field referenciado.
      (caller é responsavel por essa logica — loader so retorna candidato.)

    Returns:
        (block, field) tuple ou None.
    """
    config = load_config()

    # Estrategia 1: continuar no bloco atual
    if current_block_id:
        current = config.get_block(current_block_id)
        if current:
            for field in current.fields:
                if field.field_key not in answered_field_keys:
                    if _can_ask_field(field, answered_field_keys):
                        return (current, field)

    # Estrategia 2: proximo bloco com field nao-respondido
    for block in config.blocks:
        for field in block.fields:
            if field.field_key not in answered_field_keys:
                if _can_ask_field(field, answered_field_keys):
                    return (block, field)

    return None


def _can_ask_field(field: OnboardingField, answered: set[str]) -> bool:
    """Verifica se field pode ser perguntado agora.

    Regra depends_on: se field depende de outro AND o outro nao foi respondido,
    pula esse field por enquanto (sera reconsiderado depois).
    """
    if field.depends_on and field.depends_on not in answered:
        return False
    return True


def calculate_progress(answered_field_keys: set[str]) -> int:
    """Retorna progresso em %% (0-100) baseado em fields respondidos."""
    config = load_config()
    if config.total_fields == 0:
        return 0
    answered_count = sum(
        1 for k in answered_field_keys if config.get_field(k) is not None
    )
    return int((answered_count / config.total_fields) * 100)


def is_complete(answered_field_keys: set[str]) -> bool:
    """Verifica se atingiu threshold de finalizacao canonical."""
    config = load_config()
    return calculate_progress(answered_field_keys) >= config.finalization_threshold_percent
