"""Sprint Q.4 sensor — pins M-bucket merges + wsi_endpoints.py marker work.

For Sprint Q.4 we used `# DUPLICATE_OF_INTENT` markers on the non-canonical
side of M-bucket dups (the smaller / wire-format / divergent variant), and
we removed one literally-dead in-file duplicate. This sensor guards both
outcomes:

  1. The hard-deleted duplicate (ArchetypeFromDescriptionRequest line 363)
     does NOT come back — only ONE class declaration of that name remains
     in app/api/v1/candidate_search/archetypes.py.

  2. Every M-bucket non-canonical declaration we marked carries a
     `# DUPLICATE_OF_INTENT:` line within 5 lines above the class.
     The sensor (scripts/check_duplicate_pydantic_schemas.py) honors this
     marker — if it disappears, the dup count regresses.

Run: pytest tests/sensors/test_q4_merges_applied.py -v
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent
INTENT_MARKER = "# DUPLICATE_OF_INTENT:"
LOOKBACK_LINES = 5  # mirror sensor INTENT_MARKER_LOOKBACK_LINES


# --- 1. Hard-deleted in-file duplicate ---------------------------------------

def test_archetype_from_description_request_single_declaration():
    """The dead duplicate at original line ~363 must not return.

    Only ONE class ArchetypeFromDescriptionRequest declaration should exist
    in app/api/v1/candidate_search/archetypes.py (the canonical at line 1280
    range — the one with emoji field).
    """
    path = REPO_ROOT / "app/api/v1/candidate_search/archetypes.py"
    assert path.exists(), "archetypes.py vanished"
    src = path.read_text()
    decls = re.findall(r"^class ArchetypeFromDescriptionRequest\b", src, re.MULTILINE)
    assert len(decls) == 1, (
        f"Expected exactly 1 ArchetypeFromDescriptionRequest declaration "
        f"in archetypes.py, found {len(decls)}. Sprint Q.4 hard-deleted the "
        f"dead duplicate at the original line 363 — if a second declaration "
        f"is back, revert it."
    )


# --- 2. wsi_endpoints.py legacy markers --------------------------------------

# (class_name, expected_canonical_path)
WSI_ENDPOINTS_MARKED = [
    ("CompetencySuggestionResponse", "app/api/v1/skills_catalog.py"),
    ("GenerateQuestionsResponse", "app/api/v1/wsi/_shared.py"),
    ("AnalyzeResponseRequest", "app/api/v1/wsi/_shared.py"),
    ("CalculateWSIRequest", "app/api/v1/interview_notes.py"),
]


@pytest.mark.parametrize("class_name,canonical_hint", WSI_ENDPOINTS_MARKED)
def test_wsi_endpoints_class_has_intent_marker(class_name, canonical_hint):
    """Each Sprint Q.4-marked class in wsi_endpoints.py must have a
    `# DUPLICATE_OF_INTENT:` line within 5 lines above its declaration.
    """
    path = REPO_ROOT / "app/api/wsi_endpoints.py"
    assert path.exists(), "wsi_endpoints.py missing"
    lines = path.read_text().splitlines()
    decl_idx = _find_class_lineno(lines, class_name)
    assert decl_idx is not None, f"class {class_name} not found in wsi_endpoints.py"
    _assert_marker_above(lines, decl_idx, class_name, canonical_hint)


# --- 3. M-bucket markers -----------------------------------------------------

# (file_relpath, class_name, expected_canonical_path_hint)
M_BUCKET_MARKED = [
    ("app/schemas/api_envelope.py", "APIResponse", "app/shared/api/response.py"),
    ("app/api/v1/conversations.py", "ConversationResponse", "app/schemas/chat.py"),
    ("app/api/v1/conversations.py", "MessageResponse", "app/schemas/chat.py"),
    ("app/api/v1/conversations.py", "ConversationListResponse", "app/schemas/chat.py"),
    ("app/api/v1/recruiter_profiles.py", "PersonalizationSettingsUpdate", "app/schemas/recruiter_profile.py"),
    ("app/domains/job_creation/schemas.py", "EnrichedJobDescription", "app/schemas/jd_enrichment.py"),
    ("app/api/v1/bias_audit.py", "BiasAuditReportResponse", "app/schemas/observability.py"),
    ("app/api/v1/stage_transition_automation.py", "WSIScore", "app/api/v1/interview_notes.py"),
    ("app/api/v1/job_analytics.py", "FunnelMetrics", "app/api/v1/job_vacancies/analytics.py"),
    ("app/schemas/job_vacancy_state.py", "InterviewStage", "app/schemas/job_description.py"),
    ("app/api/v1/clients/clients_automations.py", "AutomationCreate", "app/api/v1/recruitment_journey.py"),
    ("app/api/v1/clients/clients_automations.py", "AutomationUpdate", "app/api/v1/recruitment_journey.py"),
]


@pytest.mark.parametrize("file_relpath,class_name,canonical_hint", M_BUCKET_MARKED)
def test_m_bucket_class_has_intent_marker(file_relpath, class_name, canonical_hint):
    """Each Sprint Q.4-marked M-bucket class must carry an intent marker."""
    path = REPO_ROOT / file_relpath
    assert path.exists(), f"{file_relpath} missing"
    lines = path.read_text().splitlines()
    decl_idx = _find_class_lineno(lines, class_name)
    assert decl_idx is not None, f"class {class_name} not found in {file_relpath}"
    _assert_marker_above(lines, decl_idx, class_name, canonical_hint)


# --- helpers -----------------------------------------------------------------

def _find_class_lineno(lines: list[str], class_name: str) -> int | None:
    """Return 0-indexed line number of `class <class_name>(...` declaration."""
    pat = re.compile(rf"^class {re.escape(class_name)}\b")
    for i, line in enumerate(lines):
        if pat.match(line):
            return i
    return None


def _assert_marker_above(
    lines: list[str], class_idx: int, class_name: str, canonical_hint: str
) -> None:
    start = max(0, class_idx - LOOKBACK_LINES)
    window = lines[start:class_idx]
    marker_line = next(
        (ln for ln in window if INTENT_MARKER in ln),
        None,
    )
    assert marker_line is not None, (
        f"class {class_name} missing `{INTENT_MARKER}` marker within "
        f"{LOOKBACK_LINES} lines above declaration. Sensor "
        f"`scripts/check_duplicate_pydantic_schemas.py` will re-flag this "
        f"as a duplicate. Re-add Sprint Q.4 marker pointing to {canonical_hint}."
    )
    # Soft-check that the marker references the expected canonical (just
    # a substring — exact line:column format may vary across markers).
    canonical_basename = canonical_hint.rsplit("/", 1)[-1]
    assert canonical_basename in marker_line, (
        f"class {class_name} marker exists but does not reference "
        f"expected canonical {canonical_hint}. Marker line: {marker_line!r}"
    )
