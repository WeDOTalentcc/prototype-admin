"""
P0.b defense-in-depth sensor (audit 2026-06-01): gate consumers must coerce
possibly-corrupted policy values instead of trusting raw JSON truthiness.

Root cause pinned: the string "Não" is Python-truthy, so a corrupted boolean
gate slot read via ``rules.get("auto_screening")`` silently evaluated True and
turned automations ON. ``coerce_bool`` / ``coerce_int`` make every gate read
fail safe. These helpers MUST never raise and MUST map PT-BR tokens correctly.
"""
from __future__ import annotations

import pytest

from app.shared.policy_helper import coerce_bool, coerce_int


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("Não", False),
        ("não definido", False),
        ("nao", False),
        ("", False),
        ("Sim", True),
        ("true", True),
        (True, True),
        (False, False),
        (1, True),
        (0, False),
        (None, False),            # unknown -> default
        ("talvez", False),        # non-token -> default
    ],
)
def test_coerce_bool(raw, expected):
    assert coerce_bool(raw) is expected


def test_coerce_bool_truthy_string_trap():
    """The exact regression: 'Não' must be False, never truthy."""
    assert coerce_bool("Não") is False


def test_coerce_bool_respects_default():
    assert coerce_bool("ruído", default=True) is True


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("3", 3),
        (3, 3),
        (3.0, 3),
        ("-5", -5),
        ("umas 3 entrevistas", 0),  # non-numeric -> default
        (True, 0),                   # bool is not a valid int gate value
        (None, 0),
    ],
)
def test_coerce_int(raw, expected):
    assert coerce_int(raw) == expected


def test_coerce_int_respects_default():
    assert coerce_int("não definido", default=48) == 48
