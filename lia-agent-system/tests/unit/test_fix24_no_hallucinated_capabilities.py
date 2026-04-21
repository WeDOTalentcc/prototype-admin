"""FIX 24 (2026-04-21) — Persona must not advertise non-existent capabilities.

Closes chat gap: user asked "o que você é capaz de fazer?" and LIA listed
"Prevejo quanto tempo uma vaga vai levar para ser preenchida" and "Calculo
taxas de conversão entre etapas" — claims that map to NO registered tool.

Canonical-fix (producer-side): audit persona/capability YAMLs and remove or
qualify any claim whose verb implies capabilities not backed by a real tool.

Regression guard: this test parses user-facing capability YAMLs and fails if
forbidden predictive language appears in advertised sections. Allows the word
if it appears inside a clearly scoped `roadmap:` or block-list section
(defensive context).

Non-goals: Initiative I (full Grounded Capability System) is the long-term
replacement. FIX 24 is the deterministic stopgap.
"""
from __future__ import annotations

from pathlib import Path
import re
import yaml


# Files advertised to recruiters as LIA capabilities
CAPABILITY_FILES = [
    "app/prompts/shared/defensive.yaml",
    "app/prompts/domains/recruiter_assistant.yaml",
    "app/prompts/domains/analytics.yaml",
]

# Verbs/nouns that imply prediction/forecasting — no tool exists for any of these
FORBIDDEN_PREDICTIVE_CLAIMS = [
    r"\bpreveja\b",            # "preveja X"
    r"\bprevisão\s+de\b",       # "previsão de fechamento"
    r"\bpredict(ion|s)?\b",
    r"\bforecast(s|ing)?\b",
]


def _repo_root() -> Path:
    """Locate lia-agent-system root from test file."""
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "app" / "prompts").is_dir():
            return parent
    raise RuntimeError("Could not locate lia-agent-system root")


def test_fix24_marker_present() -> None:
    """FIX 24 audit marker (in defensive.yaml since it had the biggest claim)."""
    root = _repo_root()
    defensive = (root / "app/prompts/shared/defensive.yaml").read_text(encoding="utf-8")
    assert "FIX 24" in defensive, (
        "FIX 24: defensive.yaml must contain `FIX 24` marker documenting "
        "removal of predictive capability claims"
    )


def test_no_predictive_claims_in_capability_yamls() -> None:
    """FIX 24: advertised capabilities must not claim prediction/forecasting.

    For each capability-advertising YAML, raw-text scan for forbidden
    predictive verbs. If found in active capability content (not in a
    deny-list or roadmap annotation), fail with the offending file and line.
    """
    root = _repo_root()
    offences: list[str] = []

    for rel in CAPABILITY_FILES:
        path = root / rel
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for i, line in enumerate(text.splitlines(), start=1):
            # Skip lines that are explicitly roadmap/future or out-of-scope markers
            low = line.lower()
            if any(
                marker in low
                for marker in ("roadmap", "em breve", "futuro", "out of scope",
                               "out-of-scope", "fix 24", "not supported",
                               "não suportado", "nao suportado")
            ):
                continue
            # Skip YAML comments
            stripped = line.lstrip()
            if stripped.startswith("#"):
                continue
            for pattern in FORBIDDEN_PREDICTIVE_CLAIMS:
                if re.search(pattern, line, re.IGNORECASE):
                    offences.append(f"{rel}:{i}: {line.strip()!r}")
                    break

    assert not offences, (
        "FIX 24: persona/capability YAMLs advertise predictive capabilities "
        "with no corresponding tool in registry. LIA hallucinates these in chat. "
        "Remove, qualify as roadmap, or back with a real tool:\n  "
        + "\n  ".join(offences)
    )


def test_capability_files_still_parse_as_yaml() -> None:
    """FIX 24 regression: don't break YAML syntax while editing."""
    root = _repo_root()
    for rel in CAPABILITY_FILES:
        path = root / rel
        if not path.exists():
            continue
        # Parse should not raise
        try:
            yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as e:
            raise AssertionError(
                f"FIX 24 edit broke {rel}: YAMLError {e}"
            )
