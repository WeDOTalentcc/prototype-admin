"""Task #386 — English equivalents of canonical biased phrases promoted to
Layer-1 hard block.

Task #364 promoted the Portuguese canonical biased phrases ("boa aparência",
"jovem dinâmico", "energia jovem", "sangue novo") from Layer-2 educational
warnings to Layer-1 hard blocks. The English equivalents — "good looking",
"presentable", "young and dynamic", "young blood", "energetic" — were still
only Layer-2 educational warnings (IMPLICIT_BIAS_TERMS_EN), creating an
asymmetric enforcement for multi-language tenants where the same intent
typed in English bypassed the hard block.

After this task they MUST:
  1. Be hard-blocked by FairnessGuard.check (is_blocked=True) under the
     correct category (appearance_en / age_en, the EN counterparts of
     aparencia_fisica / idade).
  2. Still surface the existing educational soft-warning message as the
     user-facing explanation (preserved via IMPLICIT_BIAS_TERMS_EN).
"""
from __future__ import annotations

import pytest

from app.shared.compliance.fairness_guard import FairnessGuard


_GUARD = FairnessGuard()


@pytest.mark.parametrize(
    "phrase,expected_category",
    [
        # appearance_en — EN counterpart of aparencia_fisica
        ("We are looking for a good looking candidate", "appearance_en"),
        ("Must be good-looking and well dressed", "appearance_en"),
        ("Candidate must be presentable", "appearance_en"),
        ("Looking for a clean-cut professional", "appearance_en"),
        ("We need an attractive candidate for this client-facing role",
         "appearance_en"),
        # age_en — EN counterpart of idade
        ("We are looking for a young and dynamic professional",
         "age_en"),
        ("Looking for young, dynamic team members", "age_en"),
        ("Dynamic and young profile preferred", "age_en"),
        ("We need young blood in this team", "age_en"),
        ("Looking for fresh blood for the squad", "age_en"),
        ("We want energetic people for this role", "age_en"),
    ],
)
def test_canonical_en_phrase_is_hard_blocked(phrase: str, expected_category: str) -> None:
    result = _GUARD.check(phrase)
    assert result.is_blocked is True, (
        f"Phrase {phrase!r} must be hard-blocked after task #386, "
        f"got is_blocked={result.is_blocked}"
    )
    assert result.category == expected_category, (
        f"Phrase {phrase!r} should be categorized under {expected_category!r}, "
        f"got {result.category!r}"
    )
    assert result.educational_message, (
        "Hard block must carry the category-level educational message"
    )
    assert result.blocked_terms, "blocked_terms must list the matched phrase"


@pytest.mark.parametrize(
    "phrase,expected_marker",
    [
        ("We are looking for a good looking candidate", "good looking"),
        ("Candidate must be presentable", "presentable"),
        ("We are looking for a young and dynamic professional",
         "young and dynamic"),
        ("We need young blood in this team", "young blood"),
        ("We want energetic people for this role", "energetic"),
    ],
)
def test_canonical_en_phrase_preserves_soft_warning(
    phrase: str, expected_marker: str
) -> None:
    """The Layer-2 educational soft-warning must still surface on the block.

    IMPLICIT_BIAS_TERMS_EN continues to carry the user-facing explanation;
    the block adds the regulator-facing category message on top.
    """
    from app.shared.compliance.fairness_guard import IMPLICIT_BIAS_TERMS_EN

    result = _GUARD.check(phrase)
    assert result.is_blocked is True
    expected_message = IMPLICIT_BIAS_TERMS_EN[expected_marker]
    assert expected_message in result.soft_warnings, (
        f"Soft warning for {expected_marker!r} should be preserved alongside "
        f"the hard block, got soft_warnings={result.soft_warnings}"
    )


def test_clean_en_text_still_passes() -> None:
    """Sanity check: phrases that only sound similar must NOT be hard-blocked."""
    result = _GUARD.check(
        "We are looking for a professional with strong communication skills"
    )
    assert result.is_blocked is False
