"""
P0.a anti-corruption sensor (audit 2026-06-01): the hiring-policy write paths
(PUT /, PATCH /, PATCH /block) used a blind merge of ``data: dict[str, Any]``
into typed gate slots. The narrative Políticas UI wrote free-text strings
("Sim"/"Não"/prose) into boolean/int gates; consumers then read raw values
where the string "Não" is Python-truthy -> automations (auto_screening,
auto_stage_advance, salary filter) silently turned ON.

Contract under test: ``coerce_and_validate_block`` is the single canonical
boundary. It MUST:
  1. Coerce PT-BR "Sim"/"Não" -> True/False on boolean gate slots.
  2. Reject non-coercible free text on a boolean slot (HTTP 422 upstream).
  3. Coerce numeric strings ("3") -> int and enforce Field ranges (ge/le).
  4. Reject unknown keys (extra='forbid') so ghost fields never persist.
  5. Return ONLY the provided keys (partial merge — never inject defaults).

Pure-unit: no DB, no app boot. Pins the producer, not each consumer.
"""
from __future__ import annotations

import pytest

from app.schemas.company_hiring_policy import (
    PolicyBlockValidationError,
    coerce_and_validate_block,
)


# --- 1. PT-BR boolean coercion (THE regression) -----------------------------
@pytest.mark.parametrize(
    "raw,expected",
    [
        ("Não", False),
        ("nao", False),
        ("Não definido", False),
        ("Sim", True),
        ("true", True),
        (True, True),
        (False, False),
        (1, True),
        (0, False),
    ],
)
def test_auto_screening_bool_coercion(raw, expected):
    out = coerce_and_validate_block("automation_rules", {"auto_screening": raw})
    assert out == {"auto_screening": expected}
    assert isinstance(out["auto_screening"], bool)


def test_string_nao_never_stays_truthy_string():
    """The exact corruption: 'Não' must NOT survive as a truthy string."""
    out = coerce_and_validate_block("automation_rules", {"auto_stage_advance": "Não"})
    assert out["auto_stage_advance"] is False


# --- 2. Non-coercible free text on a boolean gate is rejected ---------------
def test_freetext_prose_on_bool_gate_rejected():
    with pytest.raises(PolicyBlockValidationError):
        coerce_and_validate_block(
            "automation_rules",
            {"auto_screening": "Depende do perfil do candidato"},
        )


# --- 3. Numeric coercion + range enforcement --------------------------------
def test_min_interviews_numeric_string_coerced():
    out = coerce_and_validate_block("pipeline_rules", {"min_interviews_before_offer": "3"})
    assert out == {"min_interviews_before_offer": 3}
    assert isinstance(out["min_interviews_before_offer"], int)


def test_min_interviews_out_of_range_rejected():
    with pytest.raises(PolicyBlockValidationError):
        coerce_and_validate_block("pipeline_rules", {"min_interviews_before_offer": 99})


def test_duration_prose_rejected():
    with pytest.raises(PolicyBlockValidationError):
        coerce_and_validate_block(
            "scheduling_rules",
            {"default_duration_minutes": "umas 3 entrevistas"},
        )


# --- 4. extra='forbid' — ghost fields never persist -------------------------
def test_unknown_key_rejected():
    with pytest.raises(PolicyBlockValidationError):
        coerce_and_validate_block("automation_rules", {"ghost_field": "x"})


# --- 5. Partial merge — no defaults injected --------------------------------
def test_partial_returns_only_provided_keys():
    out = coerce_and_validate_block("communication_rules", {"preferred_channel": "email"})
    assert out == {"preferred_channel": "email"}


def test_unknown_block_passes_through_untouched():
    """pipeline_templates / structural blocks are not scalar-gate vectors."""
    payload = {"name": "Default", "stages": ["triagem"]}
    assert coerce_and_validate_block("pipeline_templates", payload) == payload


# --- P3a: 3 narrative fields reclassified as typed gates --------------------
def test_p3a_manager_approval_sla_hours_int_gate():
    out = coerce_and_validate_block("pipeline_rules", {"manager_approval_sla_hours": "48"})
    assert out == {"manager_approval_sla_hours": 48}


def test_p3a_vacancy_approval_required_bool_gate():
    out = coerce_and_validate_block("pipeline_rules", {"vacancy_approval_required": "Sim"})
    assert out == {"vacancy_approval_required": True}


def test_p3a_minimum_compatibility_score_int_gate():
    out = coerce_and_validate_block("screening_rules", {"minimum_compatibility_score": "65"})
    assert out == {"minimum_compatibility_score": 65}


def test_p3a_min_compat_out_of_range_rejected():
    with pytest.raises(PolicyBlockValidationError):
        coerce_and_validate_block("screening_rules", {"minimum_compatibility_score": 150})
