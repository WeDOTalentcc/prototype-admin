"""UC-P3-08: query_tools.py — canonical location verification.

TDD tests confirming the split architecture:
- analytics/tools/query_tools.py  → backward-compat shim (re-exports from 3 domains)
- sourcing/tools/query_tools.py   → canonical sourcing tools (1312 lines)
- job_management/tools/query_tools.py → canonical job tools (828 lines)

The analytics shim is intentionally thin (64 lines) because it delegates to
analytics_query_tools.py in the same domain.
"""
from __future__ import annotations

import glob


def test_canonical_query_tools_exist():
    """There must be exactly 3 query_tools.py files and at least one in a domain/tools/."""
    files = glob.glob(
        "/home/runner/workspace/lia-agent-system/app/**/query_tools.py",
        recursive=True,
    )
    assert len(files) >= 1, "No query_tools.py found at all"
    # We expect exactly 3 (sourcing, job_management, analytics)
    assert len(files) == 3, (
        f"Expected exactly 3 query_tools.py files (sourcing, job_management, analytics), "
        f"found {len(files)}: {files}"
    )


def test_sourcing_query_tools_is_canonical():
    """sourcing/tools/query_tools.py must be the largest — it is the primary search domain."""
    import os

    sourcing_path = (
        "/home/runner/workspace/lia-agent-system/app/domains/sourcing/tools/query_tools.py"
    )
    assert os.path.exists(sourcing_path), "sourcing/tools/query_tools.py must exist"

    size = os.path.getsize(sourcing_path)
    assert size > 1000, f"sourcing/tools/query_tools.py seems too small ({size} bytes)"


def test_job_management_query_tools_exists():
    """job_management/tools/query_tools.py must exist as a domain-specific tool file."""
    import os

    jm_path = "/home/runner/workspace/lia-agent-system/app/domains/job_management/tools/query_tools.py"
    assert os.path.exists(jm_path), "job_management/tools/query_tools.py must exist"


def test_analytics_query_tools_is_shim():
    """analytics/tools/query_tools.py must be a backward-compat shim (imports, not defines)."""
    analytics_path = (
        "/home/runner/workspace/lia-agent-system/app/domains/analytics/tools/query_tools.py"
    )
    with open(analytics_path) as f:
        content = f.read()

    # The shim must re-export from analytics_query_tools
    assert "from app.domains.analytics.tools.analytics_query_tools import" in content, (
        "analytics/tools/query_tools.py should re-export from analytics_query_tools"
    )
    # It must also re-export from sourcing and job_management
    assert "from app.domains.sourcing.tools.query_tools import" in content
    assert "from app.domains.job_management.tools.query_tools import" in content


def test_analytics_shim_has_register_query_tools():
    """The shim must expose a register_query_tools() function for backward compat."""
    from app.domains.analytics.tools.query_tools import register_query_tools

    assert callable(register_query_tools)


def test_sourcing_query_tools_exports_search_candidates():
    """sourcing/tools/query_tools.py must export search_candidates."""
    from app.domains.sourcing.tools.query_tools import search_candidates

    assert callable(search_candidates)


def test_job_management_query_tools_exports_search_jobs():
    """job_management/tools/query_tools.py must export search_jobs."""
    from app.domains.job_management.tools.query_tools import search_jobs

    assert callable(search_jobs)


def test_no_fourth_query_tools_introduced():
    """Guard: no additional query_tools.py files should be added in future without review."""
    files = glob.glob(
        "/home/runner/workspace/lia-agent-system/app/**/query_tools.py",
        recursive=True,
    )
    non_pycache = [f for f in files if "__pycache__" not in f]
    assert len(non_pycache) == 3, (
        f"Expected exactly 3 source query_tools.py files, found {len(non_pycache)}: "
        f"{non_pycache}\n"
        "If adding a new domain tool file, name it <domain>_query_tools.py instead."
    )
