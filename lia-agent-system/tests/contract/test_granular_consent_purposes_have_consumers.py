"""
WT-2022 P4.1 regression sensor (audit 2026-05-21): every granular consent
purpose MUST either have a real consumer wired in `app/domains/` OR a
canonical helper exposed in `granular_consent_consumers` so future PRs
that promote a "TODO consumer" purpose can do so by wiring, not by
inventing a new helper.

Background: 8 granular purposes were declared in
`GRANULAR_PURPOSE_MAP` but only 3 (ai_screening, ai_scoring,
data_retention) had real call sites in domains/.  The remaining 5 were
"ghost purposes" — UI exposed them to the recruiter, the candidate could
revoke them, and nothing in the agent stack actually respected the
revocation.

This file pins the current state so the wiring can only move forward:

* `PURPOSES_WITH_REAL_CONSUMER` — at least one literal call site in
  `app/domains/` references the purpose string (excluding the
  granular_consent module itself and its tests).
* `PURPOSES_WITH_HELPER_ONLY` — a check function exists in
  `app/domains/lgpd/services/granular_consent_consumers.py` but no
  consumer yet.  Promoting one of these to the real-consumer set
  requires (a) adding the wiring AND (b) moving the literal in this
  file.
"""
from __future__ import annotations

import ast
import pathlib

import pytest

# ---------------------------------------------------------------------------
# Canonical purpose buckets (snapshot 2026-05-21)
# ---------------------------------------------------------------------------

PURPOSES_WITH_REAL_CONSUMER = {"ai_screening", "ai_scoring", "data_retention"}
PURPOSES_WITH_HELPER_ONLY = {
    "ai_video_analysis",
    "ai_comparison",
    "analytics",
    "marketing",
    "training_data",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
_DOMAINS_ROOT = _REPO_ROOT / "app" / "domains"

# Files we must NOT count as "real consumers" — they are the helper module
# itself plus its declarative wiring (where strings appear only to be re-
# exposed, not to gate anything).
_EXCLUDED_PATHS = {
    _DOMAINS_ROOT / "lgpd" / "services" / "granular_consent_consumers.py",
    _DOMAINS_ROOT / "lgpd" / "services" / "granular_consent_service.py",
    _DOMAINS_ROOT / "lgpd" / "services" / "consent_checker_service.py",
}


def _purpose_helper_names(purpose: str) -> set[str]:
    """Return the set of canonical helper-function names that count as a
    real consumer for `purpose`.  Two purposes have `_granular`-suffixed
    helpers because their plain names collide with legacy consent_gate
    namespaces (marketing / training_data).
    """
    if purpose == "marketing":
        return {"check_marketing_granular"}
    if purpose == "training_data":
        return {"check_training_data_granular"}
    return {f"check_{purpose}"}


def _grep_purpose_consumers(purpose: str) -> list[pathlib.Path]:
    """Walk `app/domains/` and return files that *consume* `purpose`.

    A file counts as a consumer if any of the following is true:

    1. It contains a string literal equal to `purpose` (e.g. a literal
       `"ai_screening"` passed into `check_purpose(...)`).
    2. It calls or imports the canonical helper function for that
       purpose (e.g. `check_data_retention(...)` — where the literal
       lives inside the helper, not the caller).

    Both branches use AST so we only count *real* code references — not
    matches in comments, docstrings, or unrelated substrings such as
    "marketing_email_template".

    The granular_consent helper modules themselves are excluded so they
    don't self-vouch.
    """
    helper_names = _purpose_helper_names(purpose)
    matches: list[pathlib.Path] = []
    if not _DOMAINS_ROOT.exists():
        pytest.skip(f"app/domains/ not found at {_DOMAINS_ROOT}")

    for py_path in _DOMAINS_ROOT.rglob("*.py"):
        if py_path in _EXCLUDED_PATHS:
            continue
        if "__pycache__" in py_path.parts:
            continue
        # Skip .bak and similar artifacts that may have leaked in.
        if py_path.suffix != ".py":
            continue
        try:
            source = py_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        try:
            tree = ast.parse(source, filename=str(py_path))
        except SyntaxError:
            continue
        matched = False
        for node in ast.walk(tree):
            # Branch 1: literal string equal to the purpose name.
            if isinstance(node, ast.Constant) and node.value == purpose:
                matched = True
                break
            # Branch 2: call to or import of the canonical helper.
            if isinstance(node, ast.Call):
                func = node.func
                func_name = None
                if isinstance(func, ast.Name):
                    func_name = func.id
                elif isinstance(func, ast.Attribute):
                    func_name = func.attr
                if func_name in helper_names:
                    matched = True
                    break
            if isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if alias.name in helper_names:
                        matched = True
                        break
                if matched:
                    break
        if matched:
            matches.append(py_path)
    return matches


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("purpose", sorted(PURPOSES_WITH_REAL_CONSUMER))
def test_purpose_has_real_consumer(purpose: str) -> None:
    """Each purpose in PURPOSES_WITH_REAL_CONSUMER MUST have at least one
    real string-literal reference inside `app/domains/`, excluding the
    granular_consent helper modules themselves.
    """
    found = _grep_purpose_consumers(purpose)
    assert len(found) > 0, (
        f"purpose '{purpose}' is declared as wired in PURPOSES_WITH_REAL_CONSUMER "
        f"but no real consumer was found in app/domains/. "
        f"Either (a) the wiring was removed and this is a regression, or "
        f"(b) the purpose was demoted and should be moved to PURPOSES_WITH_HELPER_ONLY."
    )


@pytest.mark.parametrize("purpose", sorted(PURPOSES_WITH_HELPER_ONLY))
def test_purpose_helper_exists(purpose: str) -> None:
    """Each purpose in PURPOSES_WITH_HELPER_ONLY MUST have a canonical
    `check_<purpose>` helper exported by
    `app/domains/lgpd/services/granular_consent_consumers.py`.

    Two purposes use a `_granular` suffix on the helper name because their
    namespace collides with the legacy consent_gate module
    (marketing/training_data exist there for company-level consent).
    """
    from app.domains.lgpd.services import granular_consent_consumers as mod

    if purpose == "marketing":
        helper_name = "check_marketing_granular"
    elif purpose == "training_data":
        helper_name = "check_training_data_granular"
    else:
        helper_name = f"check_{purpose}"

    assert hasattr(mod, helper_name), (
        f"purpose '{purpose}' has no canonical helper '{helper_name}' in "
        f"granular_consent_consumers. Add the helper before declaring the "
        f"purpose in PURPOSES_WITH_HELPER_ONLY."
    )
