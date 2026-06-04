"""Task #1306 sentinel: every candidate-stage write path records the stage id.

When a path writes ``VacancyCandidate.stage`` (free-form text) it MUST also
record the structural ``recruitment_stage_id`` so the SLA-near-expiration
detector can join by id instead of fragile name matching. This sentinel fails
the build if a known writer drops the id, or if a NEW file starts writing
``stage`` without ``recruitment_stage_id`` (forcing the author to wire the
resolver — or the canonical transition service — on the new path).
"""
from __future__ import annotations

import re
from pathlib import Path

# Repo root = three parents up from tests/contract/<file>.
_APP = Path(__file__).resolve().parents[2] / "app"

# Files known to write VacancyCandidate.stage AND now record recruitment_stage_id.
# The canonical transition service sets it via ``to_stage_obj.id`` rather than the
# resolver, so we only assert the column token is present, not the helper import.
KNOWN_WRITERS = [
    "api/v1/candidates/candidates_crud.py",
    "api/v1/candidates/candidates_metadata.py",
    "api/v1/candidate_search/calibration.py",
    "api/v1/job_vacancies/public.py",
    "api/v1/shared_searches.py",
    "domains/automation/services/automation_handlers.py",
    "domains/candidate_lists/repositories/candidate_list_repository.py",
    "domains/cv_screening/tools/candidate_tools.py",
    "domains/cv_screening/tools/cv_upload_tool.py",
    "domains/job_management/services/job_clone_service.py",
    "domains/pipeline/tools/pipeline_tools.py",
    "domains/recruiter_assistant/services/conversation_manager.py",
    "domains/recruiter_assistant/services/pipeline_stage_service.py",
    "domains/recruitment/repositories/application_repository.py",
]

# Pre-existing seed/dev paths intentionally excluded from the id requirement.
ALLOWLIST_NO_STAGE_ID = {
    "shared/services/seed_service.py",
}

# Matches a ``stage=`` kwarg (but not ``stage_id=``, ``recruitment_stage=`` etc.).
_STAGE_KWARG = re.compile(r"(?<![\w.])stage\s*=(?!=)")


def _vacancy_candidate_constructions(text: str):
    """Yield the source of each ``VacancyCandidate(...)`` call (paren-matched)."""
    needle = "VacancyCandidate("
    idx = 0
    while True:
        start = text.find(needle, idx)
        if start == -1:
            return
        open_paren = start + len(needle) - 1
        depth = 0
        end = open_paren
        for i in range(open_paren, len(text)):
            ch = text[i]
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0:
                    end = i
                    break
        yield text[open_paren : end + 1]
        idx = end + 1


def test_known_writers_record_recruitment_stage_id():
    missing = []
    for rel in KNOWN_WRITERS:
        path = _APP / rel
        assert path.exists(), f"sentinel references a missing file: {rel}"
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "recruitment_stage_id" not in text:
            missing.append(rel)
    assert not missing, (
        "These candidate-stage writers no longer set recruitment_stage_id "
        f"(Task #1306 regression): {missing}"
    )


def test_no_new_unguarded_stage_writers():
    """Any ``VacancyCandidate(...)`` that sets ``stage=`` must also set the id."""
    known = set(KNOWN_WRITERS) | ALLOWLIST_NO_STAGE_ID
    offenders = []
    for path in _APP.rglob("*.py"):
        rel = path.relative_to(_APP).as_posix()
        if rel in known:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "VacancyCandidate(" not in text:
            continue
        for call in _vacancy_candidate_constructions(text):
            if _STAGE_KWARG.search(call) and "recruitment_stage_id" not in call:
                offenders.append(rel)
                break
    assert not offenders, (
        "New candidate-stage write path(s) found without recruitment_stage_id. "
        "Resolve the id via app.shared.services.stage_id_resolver (or route "
        f"through the canonical transition service), then add to the sentinel: {offenders}"
    )
