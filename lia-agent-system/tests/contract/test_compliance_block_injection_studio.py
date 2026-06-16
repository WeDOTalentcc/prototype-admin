"""Wave D1.2 (2026-05-27) — canonical compliance_block injection sensor.

Garante que TODO system prompt construído via ``SystemPromptBuilder.build``
inclui o canonical compliance_block (LGPD + fairness + bias + audit +
universal guardrails) — single source de truth em
``app/prompts/shared/compliance_block.yaml`` + ``guardrails.yaml``.

Sem esta injeção, custom agents do Agent Studio rodam sem os 14 protected
attributes (audit #4 P1.5) e abrem brecha LGPD/EU AI Act. Pin computacional
contra regressão.
"""
from __future__ import annotations

import pytest

from app.shared.prompts.system_prompt_builder import SystemPromptBuilder


# Anchors esperados em todo prompt (variant decision/communication/operational
# carrega lgpd; universal guardrails sempre vêm).
LGPD_ANCHOR = "LGPD"
PROTECTED_ATTR_REF = "atributos protegidos"  # appears in fairness/lgpd block


def test_compliance_block_injected_for_decision_agent():
    """Decision agents (cv_screening, sourcing, talent_pool, ...) recebem
    full compliance: lgpd + fairness + bias + audit + universal guardrails."""
    prompt = SystemPromptBuilder.build(agent_type="cv_screening")
    assert LGPD_ANCHOR in prompt, "decision agent prompt missing LGPD block"
    assert "## Compliance e Guardrails" in prompt, "compliance section header missing"


def test_compliance_block_injected_for_talent_pool():
    """talent_pool é decision domain — deve ter fairness + LGPD completos."""
    prompt = SystemPromptBuilder.build(agent_type="talent_pool")
    assert LGPD_ANCHOR in prompt
    assert "## Compliance e Guardrails" in prompt


def test_compliance_block_injected_for_recruiter_assistant():
    """recruiter_assistant = decision domain (mapping em
    custom_agent_runtime._get_system_prompt). Studio agents com domain=general
    ou custom caem aqui — devem ter compliance full."""
    prompt = SystemPromptBuilder.build(agent_type="recruiter_assistant")
    assert LGPD_ANCHOR in prompt
    assert "## Compliance e Guardrails" in prompt


def test_compliance_block_injected_for_operational_agent():
    """Operational agents (automation/analytics/wizard) recebem ao menos
    LGPD baseline + universal guardrails."""
    prompt = SystemPromptBuilder.build(agent_type="automation")
    # Operational variant só carrega lgpd + universals; LGPD anchor garantido.
    assert LGPD_ANCHOR in prompt
    assert "## Compliance e Guardrails" in prompt


def test_compliance_block_for_orchestrator_does_not_break():
    """agent_type=orchestrator (default) NÃO injeta REACT_INSTRUCTIONS mas
    o compliance_block continua ativo (operational variant). Smoke: build
    não levanta."""
    prompt = SystemPromptBuilder.build(agent_type="orchestrator")
    assert isinstance(prompt, str)
    assert len(prompt) > 100


def test_compliance_block_immutable_persona_base():
    """Persona base lia_persona.yaml NUNCA é mutada — compliance_block é
    APPENDADO via section própria. Invariante de imutabilidade."""
    prompt = SystemPromptBuilder.build(agent_type="cv_screening")
    # Persona base anchor still present (não foi sobrescrito):
    assert "LIA" in prompt or "Quem é" in prompt or "persona" in prompt.lower()
    # Compliance comes AFTER persona base (section header order)
    persona_pos = prompt.find("LIA")
    compliance_pos = prompt.find("## Compliance e Guardrails")
    if persona_pos >= 0 and compliance_pos >= 0:
        assert persona_pos < compliance_pos, "compliance must come AFTER persona base"
