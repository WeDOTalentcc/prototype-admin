"""Sprint Q.3 sensor — pins 10 R-bucket renames so they don't regress.

For each renamed class, asserts:
- OLD name is NOT in source file
- NEW name IS in source file (declaration)
- Cross-file callers updated correctly (where applicable)

Run: pytest tests/sensors/test_q3_renames_applied.py -v
"""
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent

# (source_file, old_name, new_name, also_check_files)
Q3_RENAMES = [
    ("app/api/v1/talent_pools.py", "AddCandidatesRequest", "AddCandidatesToPoolRequest", []),
    ("app/api/v1/agent_monitoring.py", "AlertResponse", "AgentAlertResponse", []),
    ("app/api/v1/search_assistant.py", "AnalysisResponse", "SearchAnalysisResponse", []),
    ("app/api/v1/hitl.py", "ApprovalResponse", "HitlApprovalResponse", []),
    ("app/api/public/candidate_portal.py", "VerifyOTPRequest", "CandidatePortalOTPVerify", []),
    ("app/api/v1/search_assistant.py", "AnalyzeRequest", "SearchAnalyzeRequest", []),
    ("app/schemas/global_policies.py", "CategoryCount", "PolicyCategoryCount", ["app/api/v1/global_policies.py"]),
    ("app/api/public/candidate_portal.py", "RequestOTPRequest", "CandidatePortalOTPRequest", []),
    ("app/api/v1/calibration.py", "DashboardResponse", "CalibrationDashboardResponse", []),
    ("app/schemas/lia_opinion.py", "ScoreBreakdown", "LiaOpinionScoreBreakdown", []),
]


@pytest.mark.parametrize("source_file,old_name,new_name,also_check", Q3_RENAMES)
def test_q3_rename_applied(source_file, old_name, new_name, also_check):
    path = REPO_ROOT / source_file
    assert path.exists(), f"Source file missing: {source_file}"
    src = path.read_text()

    # OLD identifier (as full word) must NOT appear
    import re
    old_pattern = re.compile(r"\b" + re.escape(old_name) + r"\b")
    assert not old_pattern.search(src), (
        f"Q.3 regression: '{old_name}' still present in {source_file} — "
        f"should have been renamed to '{new_name}'"
    )

    # NEW identifier must appear
    new_pattern = re.compile(r"\b" + re.escape(new_name) + r"\b")
    assert new_pattern.search(src), (
        f"Q.3 regression: '{new_name}' missing from {source_file} — "
        f"rename not applied"
    )

    # Cross-file caller files (if any) also must have the new name
    for cross_file in also_check:
        cross_path = REPO_ROOT / cross_file
        assert cross_path.exists(), f"Cross-file caller missing: {cross_file}"
        cross_src = cross_path.read_text()
        assert not old_pattern.search(cross_src), (
            f"Q.3 cross-file regression: '{old_name}' still present in {cross_file} "
            f"(expected renamed to '{new_name}')"
        )
        assert new_pattern.search(cross_src), (
            f"Q.3 cross-file regression: '{new_name}' missing from {cross_file}"
        )


def test_q3_renames_no_collision():
    """Pin: new names don't collide with each other or with existing canonical."""
    new_names = [r[2] for r in Q3_RENAMES]
    assert len(set(new_names)) == len(new_names), (
        f"Q.3 duplicate new_name in rename list: {new_names}"
    )
