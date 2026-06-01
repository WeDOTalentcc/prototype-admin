"""
P3b sensor (2026-06-01): policy narrative instructions are free-text prompt
hints stored SEPARATELY from the typed gate blocks. validate_policy_instructions
must reject unknown concepts (no ghost keys), coerce to stripped strings, and
never let a non-string through. Pins the 11 canonical concepts.
"""
from __future__ import annotations

import pytest

from app.schemas.company_hiring_policy import (
    POLICY_INSTRUCTION_KEYS,
    POLICY_INSTRUCTION_LABELS,
    PolicyBlockValidationError,
    validate_policy_instructions,
)


def test_eleven_canonical_concepts():
    assert len(POLICY_INSTRUCTION_KEYS) == 11
    # every key has a human label (used in the prompt section)
    assert set(POLICY_INSTRUCTION_LABELS) == POLICY_INSTRUCTION_KEYS


def test_accepts_known_keys_and_strips():
    out = validate_policy_instructions({
        "diversity_inclusion_guidelines": "  Priorizar PcD e mulheres em tech.  ",
        "no_show_policy": "Recontato em 48h.",
    })
    assert out == {
        "diversity_inclusion_guidelines": "Priorizar PcD e mulheres em tech.",
        "no_show_policy": "Recontato em 48h.",
    }


def test_rejects_unknown_concept():
    with pytest.raises(PolicyBlockValidationError):
        validate_policy_instructions({"auto_screening": "Sim"})  # gate key, not an instruction


def test_rejects_non_string_value():
    with pytest.raises(PolicyBlockValidationError):
        validate_policy_instructions({"no_show_policy": True})


def test_none_becomes_empty_string():
    out = validate_policy_instructions({"remote_work_policy": None})
    assert out == {"remote_work_policy": ""}


def test_gate_keys_are_not_instruction_keys():
    """Safety invariant: gate concepts never overlap instruction concepts."""
    from app.schemas.company_hiring_policy import BLOCK_SCHEMAS
    gate_fields = set()
    for schema in BLOCK_SCHEMAS.values():
        gate_fields |= set(schema.model_fields)
    assert POLICY_INSTRUCTION_KEYS.isdisjoint(gate_fields)
