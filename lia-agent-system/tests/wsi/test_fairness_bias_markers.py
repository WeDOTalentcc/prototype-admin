"""Phase H — fairness preamble sensor.

The wsi_service/question_generator.py uses a regex (_BIAS_MARKERS_RE)
to detect questions that mention protected attributes (gender, race,
ethnicity, religion, family status, disability, pregnancy). Any question
that triggers this regex is flagged with 'bias_marker_detected' and
rejected before being persisted.

This sensor pins the regex coverage so future edits cannot accidentally
DROP a protected attribute. CLAUDE.md golden rule: zero raça / religião /
gênero / idade in AI decisions.

If a recruiter argues a specific protected attribute should be
allow-listed (e.g. an aerospace company asking about pregnancy due to
G-force constraints — extremely rare), they MUST add an
ADR-style comment to the regex and update this test in the same PR.
That makes the legal/compliance review explicit.
"""
from __future__ import annotations

import pytest

# Import the question generator class (it lives behind a heavy module path).
from app.domains.cv_screening.services.wsi_service.question_generator import (
    WSIQuestionGenerator,
)


# Protected attributes that MUST be flagged. Each tuple = (sample_text, label).
# Sample texts are realistic fragments a careless prompt or LLM hallucination
# might emit; the regex must catch them.
PROTECTED_CASES = [
    ("Você é casado?", "marital_status_male"),
    ("Você é casada?", "marital_status_female"),
    ("Quantos filhos você tem?", "children"),
    ("Está grávida?", "pregnancy"),
    ("Qual é seu gênero?", "gender_explicit"),
    ("Você é homem ou mulher?", "binary_gender"),
    ("Qual é sua raça?", "race"),
    ("Qual sua etnia?", "ethnicity"),
    ("Qual sua origem?", "origin"),
    ("Qual sua religião?", "religion"),
    ("Você tem alguma deficiência?", "disability"),
]


# Counter-cases: legit recruitment questions that should NOT trigger the
# bias regex (otherwise we have a false positive and recruiters can't ask
# legitimate things).
ALLOWED_CASES = [
    "Conte sobre um projeto técnico desafiador.",
    "Descreva como você resolveu um conflito de prioridades.",
    "Qual sua experiência com Python e bancos relacionais?",
    "Fale de uma situação onde você precisou liderar sem autoridade formal.",
]


@pytest.fixture
def gen() -> WSIQuestionGenerator:
    """Build a minimal service. Constructor needs an LLM client; we don't
    call any LLM-bound method so passing None is safe."""
    return WSIQuestionGenerator.__new__(WSIQuestionGenerator)


@pytest.mark.parametrize("text,label", PROTECTED_CASES)
def test_bias_regex_flags_protected_attribute(gen, text, label):
    """Phase H sensor: every protected attribute MUST be flagged."""
    flags = gen._validate_deterministic(text + " " + " ".join(["palavra"] * 20))
    assert "bias_marker_detected" in flags, (
        f"Bias regex failed to detect protected attribute ({label}) "
        f"in text: {text!r}\nFlags: {flags}"
    )


@pytest.mark.parametrize("text", ALLOWED_CASES)
def test_bias_regex_does_not_false_positive_on_legit_questions(gen, text):
    """Counter-case: legit recruitment questions must not trigger bias flag."""
    # Pad with neutral words so length validator doesn't add unrelated flags.
    padded = text + " " + " ".join(["palavra"] * 20)
    flags = gen._validate_deterministic(padded)
    assert "bias_marker_detected" not in flags, (
        f"FALSE POSITIVE: legit question flagged as bias.\n"
        f"Text: {text!r}\nFlags: {flags}"
    )


def test_bias_regex_covers_all_clauder_required_attributes():
    """Documentary sensor: list out every attribute CLAUDE.md > Multi-tenancy
    + LGPD requires we exclude. If this test fails, either the regex was
    weakened OR CLAUDE.md was updated and we need to widen coverage.

    Cross-reference: ~/.claude/CLAUDE.md > 'Non-Negotiable Rules' #2 lists
    race / religion / gender / ethnicity / marital_status / health.
    """
    pattern_str = WSIQuestionGenerator._BIAS_MARKERS_RE.pattern.lower()
    must_contain_substrings = [
        "homem", "mulher",       # gender (binary)
        "masculino", "feminino", # gender (adjective)
        "gênero",                # gender (explicit)
        "raça",                  # race
        "etnia",                 # ethnicity
        "religião",              # religion
        "casad",                 # marital
        "filh",                  # family
        "grávid",                # pregnancy
        "deficiência",           # disability
    ]
    missing = [s for s in must_contain_substrings if s not in pattern_str]
    assert not missing, (
        f"Bias regex missing required protected-attribute markers: {missing}\n"
        f"Current pattern: {pattern_str}\n"
        f"See CLAUDE.md > 'Non-Negotiable Rules' #2."
    )
