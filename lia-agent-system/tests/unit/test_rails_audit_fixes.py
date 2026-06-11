"""
TDD tests for rails-elimination audit fixes:
 P2 — graph node tombstones
 P3 — onboarding_orchestrator insecure token default
 P1 — FastAPI onboarding status/progress endpoints exist + proxy routing
"""
import ast
import os
import re
import pytest

BASE = "/home/runner/workspace/lia-agent-system"
NODES_DIR = f"{BASE}/app/domains/job_creation/nodes"
ONBOARDING_PY = f"{BASE}/app/api/v1/onboarding.py"
ORCHESTRATOR_PY = f"{BASE}/app/services/onboarding_orchestrator.py"
PROXY_ROUTE = "/home/runner/workspace/plataforma-lia/src/app/api/backend-proxy/onboarding/[...path]/route.ts"


# ─── P2: Graph node tombstones ────────────────────────────────────────────────

@pytest.mark.parametrize("filename,node_name", [
    ("publish.py", "publish_node"),
    ("review.py", "review_node"),
    ("calibration.py", "calibration_node"),
])
def test_node_has_tombstone_guard(filename, node_name):
    """Each legacy graph node must raise RuntimeError when RAILS_API_URL is absent."""
    with open(os.path.join(NODES_DIR, filename)) as f:
        src = f.read()
    assert "Tombstone: graph path is legacy" in src, \
        f"{filename}: missing tombstone comment"
    assert 'os.environ.get("RAILS_API_URL")' in src, \
        f"{filename}: tombstone must check RAILS_API_URL"
    assert "RuntimeError" in src, \
        f"{filename}: tombstone must raise RuntimeError"


@pytest.mark.parametrize("filename", ["publish.py", "review.py", "calibration.py"])
def test_node_imports_os(filename):
    """Tombstone requires `os` to be imported at module level."""
    with open(os.path.join(NODES_DIR, filename)) as f:
        src = f.read()
    assert "import os\n" in src, f"{filename}: missing `import os` at module level"


# ─── P3: Insecure token fix ───────────────────────────────────────────────────

def test_orchestrator_no_hardcoded_localhost():
    """RAILS_BACKEND_URL must not have insecure localhost default."""
    with open(ORCHESTRATOR_PY) as f:
        src = f.read()
    assert '"RAILS_BACKEND_URL", "http://localhost:3000"' not in src, \
        "RAILS_BACKEND_URL must not fall back to localhost — add early-return guard instead"


def test_orchestrator_no_hardcoded_token():
    """INTERNAL_API_TOKEN must not have insecure 'internal' default."""
    with open(ORCHESTRATOR_PY) as f:
        src = f.read()
    assert '"INTERNAL_API_TOKEN", "internal"' not in src, \
        "INTERNAL_API_TOKEN must not fall back to 'internal' — add early-return guard instead"


def test_orchestrator_has_rails_url_early_return():
    """_sync_rails_state must skip cleanly when RAILS_BACKEND_URL is absent."""
    with open(ORCHESTRATOR_PY) as f:
        src = f.read()
    assert "RAILS_BACKEND_URL not set" in src, \
        "_sync_rails_state must log + return early when RAILS_BACKEND_URL is unset"


def test_orchestrator_has_token_early_return():
    """_sync_rails_state must skip when INTERNAL_API_TOKEN is absent."""
    with open(ORCHESTRATOR_PY) as f:
        src = f.read()
    assert "INTERNAL_API_TOKEN not set" in src, \
        "_sync_rails_state must log + return early when INTERNAL_API_TOKEN is unset"


# ─── P1: FastAPI onboarding endpoints ────────────────────────────────────────

def test_fastapi_has_status_endpoint():
    """FastAPI onboarding router must expose GET /status."""
    with open(ONBOARDING_PY) as f:
        src = f.read()
    assert '@router.get("/status")' in src, \
        'onboarding.py must have @router.get("/status") endpoint'
    assert "get_onboarding_status" in src, \
        "onboarding.py must define get_onboarding_status handler"


def test_fastapi_has_progress_endpoint():
    """FastAPI onboarding router must expose PATCH /progress."""
    with open(ONBOARDING_PY) as f:
        src = f.read()
    assert '@router.patch("/progress")' in src, \
        'onboarding.py must have @router.patch("/progress") endpoint'
    assert "update_onboarding_progress" in src, \
        "onboarding.py must define update_onboarding_progress handler"


def test_fastapi_progress_schema_no_company_id():
    """ProgressUpdateRequest must NOT have company_id field (REGRA 2)."""
    with open(ONBOARDING_PY) as f:
        src = f.read()
    # Extract ProgressUpdateRequest block
    match = re.search(r"class ProgressUpdateRequest.*?(?=\n\n|\nclass |\n@router)", src, re.DOTALL)
    assert match, "ProgressUpdateRequest class not found"
    block = match.group(0)
    assert "company_id" not in block, \
        "ProgressUpdateRequest must not contain company_id (comes from JWT Depends)"


# ─── P1: Proxy route.ts routing ───────────────────────────────────────────────

def test_proxy_routes_status_to_fastapi():
    """Route.ts GET /status must go to FastAPI, not Rails."""
    with open(PROXY_ROUTE) as f:
        src = f.read()
    assert "FastAPI: status" in src, \
        "route.ts must have FastAPI routing comment for status"
    # Ensure the status branch calls FASTAPI_URL not RAILS_URL
    idx = src.index("FastAPI: status")
    snippet = src[idx:idx+200]
    assert "FASTAPI_URL" in snippet, \
        "status route must use FASTAPI_URL"
    assert "RAILS_URL" not in snippet, \
        "status route must NOT call RAILS_URL"


def test_proxy_routes_progress_to_fastapi():
    """Route.ts PATCH /progress must go to FastAPI, not Rails."""
    with open(PROXY_ROUTE) as f:
        src = f.read()
    assert "FastAPI: progress update" in src, \
        "route.ts must have FastAPI routing comment for progress"
    idx = src.index("FastAPI: progress update")
    snippet = src[idx:idx+300]
    assert "FASTAPI_URL" in snippet, \
        "progress route must use FASTAPI_URL"
    assert "RAILS_URL" not in snippet, \
        "progress route must NOT call RAILS_URL"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
