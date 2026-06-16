"""Task #364 — canonical biased phrases promoted to Layer-1 hard block.

The Brazilian recruiter phrases "boa aparência" and "jovem dinâmico" — and
their close equivalents "boa apresentação pessoal", "energia jovem", and
"sangue novo" — are explicitly cited by Brazilian labor jurisprudence and
the EU AI Act guidance as discriminatory. Until task #364 they were
registered only as Layer-2 educational warnings (IMPLICIT_BIAS_TERMS), so a
job description containing them was scored normally and only produced a soft
warning.

After this task they MUST:
  1. Be hard-blocked by FairnessGuard.check (is_blocked=True) under the
     correct category (aparencia_fisica / idade).
  2. Still surface the existing educational soft-warning message as the
     user-facing explanation (preserved via IMPLICIT_BIAS_TERMS).
"""
from __future__ import annotations

import pytest

from app.shared.compliance.fairness_guard import FairnessGuard


_GUARD = FairnessGuard()


@pytest.mark.parametrize(
    "phrase,expected_category",
    [
        # aparencia_fisica
        ("Buscamos profissional com boa aparência", "aparencia_fisica"),
        ("Procuramos candidato com boa aparencia", "aparencia_fisica"),
        ("Exigimos boa apresentação pessoal", "aparencia_fisica"),
        ("Boa apresentacao pessoal é diferencial", "aparencia_fisica"),
        # idade
        ("Buscamos profissional jovem e dinâmico para a equipe", "idade"),
        ("Queremos uma jovem dinâmica para a área", "idade"),
        ("Time jovens dinâmicos preferencialmente", "idade"),
        ("Queremos alguém com energia jovem", "idade"),
        ("Precisamos de sangue novo no time", "idade"),
    ],
)
def test_canonical_phrase_is_hard_blocked(phrase: str, expected_category: str) -> None:
    result = _GUARD.check(phrase)
    assert result.is_blocked is True, (
        f"Phrase {phrase!r} must be hard-blocked after task #364, "
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
        ("Buscamos profissional com boa aparência", "boa aparência"),
        ("Queremos alguém com energia jovem", "energia jovem"),
    ],
)
def test_canonical_phrase_preserves_soft_warning(phrase: str, expected_marker: str) -> None:
    """The Layer-2 educational soft-warning must still surface on the block.

    IMPLICIT_BIAS_TERMS continues to carry the user-facing explanation; the
    block adds the regulator-facing category message on top.
    """
    result = _GUARD.check(phrase)
    assert result.is_blocked is True
    joined = " ".join(result.soft_warnings).lower()
    assert expected_marker.lower() in joined or any(
        expected_marker.lower() in w.lower() for w in result.soft_warnings
    ), (
        f"Soft warning referring to {expected_marker!r} should be preserved "
        f"alongside the hard block, got soft_warnings={result.soft_warnings}"
    )


def test_clean_text_still_passes() -> None:
    """Sanity check: phrases that only sound similar must NOT be hard-blocked."""
    result = _GUARD.check("Buscamos profissional com boa comunicação e proatividade")
    assert result.is_blocked is False
