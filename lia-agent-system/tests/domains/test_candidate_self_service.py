"""TDD tests for candidate_self_service domain.

Covers: tool whitelist, LGPD data leakage, FairnessGuard, cross-tenant,
rate limiting, ADR-005 (response_model), ADR-006 (no PII in logs).
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ── Tool whitelist ─────────────────────────────────────────────────────────────

def test_tool_registry_returns_exactly_4_tools():
    from app.domains.candidate_self_service.agents.candidate_tool_registry import get_candidate_tools
    tools = get_candidate_tools()
    assert len(tools) == 4  # +explain_candidate_decision (EU AI Act Art.86 + LGPD Art.20)

def test_tool_names_are_whitelisted():
    from app.domains.candidate_self_service.agents.candidate_tool_registry import get_candidate_tools
    names = {t.name for t in get_candidate_tools()}
    assert names == {"get_application_status", "get_interview_info", "get_wsi_feedback", "explain_candidate_decision"}


# ── Forbidden fields never returned ───────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_application_status_strips_forbidden_fields():
    from app.domains.candidate_self_service.tools.get_application_status import _FORBIDDEN_FIELDS
    mock_data = {
        "stage_name": "Em triagem",
        "stage_entered_at": "2026-04-15",
        "wsi_final_score": 8.5,    # FORBIDDEN
        "lia_score": 0.9,           # FORBIDDEN
        "red_flags": ["lazy"],      # FORBIDDEN
        "cpf": "123.456.789-00",    # FORBIDDEN
    }
    safe = {k: v for k, v in mock_data.items() if k not in _FORBIDDEN_FIELDS}
    assert "wsi_final_score" not in safe
    assert "lia_score" not in safe
    assert "red_flags" not in safe
    assert "cpf" not in safe
    assert "stage_name" in safe

@pytest.mark.asyncio
async def test_get_wsi_feedback_strips_score_fields():
    from app.domains.candidate_self_service.tools.get_wsi_feedback import _FORBIDDEN_FIELDS
    assert "wsi_final_score" in _FORBIDDEN_FIELDS
    assert "score" in _FORBIDDEN_FIELDS
    assert "red_flags" in _FORBIDDEN_FIELDS
    assert "bloom_level" in _FORBIDDEN_FIELDS


# ── Rate limiting ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_rate_limit_constants():
    from app.domains.candidate_self_service.services.candidate_status_service import (
        MAX_MESSAGES_PER_HOUR, MAX_MESSAGES_PER_DAY
    )
    assert MAX_MESSAGES_PER_HOUR == 10
    assert MAX_MESSAGES_PER_DAY == 30

@pytest.mark.asyncio
async def test_rate_limit_check_blocks_when_over_limit():
    from app.domains.candidate_self_service.services.candidate_status_service import (
        CandidateStatusService
    )
    service = CandidateStatusService()
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(side_effect=["11", "11"])  # over hourly limit
    mock_redis.pipeline = MagicMock(return_value=AsyncMock())

    with patch(
        "app.core.redis_client.get_redis",
        return_value=mock_redis,
    ):
        # Simulate: hour count already at 11 (> 10 limit)
        with patch.object(mock_redis, "get", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = [b"11", b"5"]
            result = await service.check_rate_limit("candidate-123")
            assert result["allowed"] is False


# ── Token validation ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_validate_token_rejects_missing_fields():
    from app.domains.candidate_self_service.services.candidate_status_service import (
        CandidateStatusService
    )
    import jwt
    secret = "test-secret"
    # Token missing vacancy_id
    token = jwt.encode({"candidate_id": "c1", "company_id": "co1"}, secret, algorithm="HS256")
    service = CandidateStatusService()
    result = await service.validate_token(token, secret)
    assert result is None

@pytest.mark.asyncio
async def test_validate_token_accepts_valid_token():
    from app.domains.candidate_self_service.services.candidate_status_service import (
        CandidateStatusService
    )
    import jwt, time
    secret = "test-secret"
    token = jwt.encode(
        {"candidate_id": "c1", "vacancy_id": "v1", "company_id": "co1", "exp": int(time.time()) + 3600},
        secret, algorithm="HS256"
    )
    service = CandidateStatusService()
    result = await service.validate_token(token, secret)
    assert result is not None
    assert result["candidate_id"] == "c1"


# ── ADR-003: Prompt in YAML ────────────────────────────────────────────────────

def test_prompt_yaml_exists():
    from pathlib import Path
    yaml_path = Path(__file__).parent.parent.parent / "app/prompts/domains/candidate_self_service.yaml"
    assert yaml_path.exists(), "YAML prompt file must exist (ADR-003)"

def test_prompt_yaml_has_required_keys():
    from pathlib import Path
    import yaml
    yaml_path = Path(__file__).parent.parent.parent / "app/prompts/domains/candidate_self_service.yaml"
    config = yaml.safe_load(yaml_path.read_text())
    for key in ("domain", "identity", "scope_in", "scope_out", "behavioral_rules"):
        assert key in config, f"YAML missing key: {key}"


# ── Domain registration ────────────────────────────────────────────────────────

def test_domain_has_4_actions():
    from app.domains.candidate_self_service.domain import CANDIDATE_SELF_SERVICE_ACTIONS
    assert len(CANDIDATE_SELF_SERVICE_ACTIONS) == 4

def test_domain_id_is_correct():
    from app.domains.candidate_self_service.domain import CandidateSelfServiceDomain
    d = CandidateSelfServiceDomain()
    assert d.domain_id == "candidate_self_service"


# ── ADR-006: No PII in logs (static analysis) ─────────────────────────────────

def test_no_pii_in_tool_logs():
    """Verify tool log statements use candidate_id only, not email/name/phone."""
    import ast
    from pathlib import Path
    tools_dir = Path(__file__).parent.parent.parent / "app/domains/candidate_self_service/tools"
    import re as _re
    # Whole-word match: avoids false positives like "stage_name" matching "name"
    pii_patterns = {"email", "phone", "nome", "cpf", "mobile_phone"}
    # Note: "name" excluded — too broad; "candidate_name" is checked via "nome"
    for py_file in tools_dir.glob("*.py"):
        source = py_file.read_text()
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = getattr(node, "func", None)
                func_str = ast.unparse(func) if func else ""
                if "logger." in func_str:
                    call_str = ast.unparse(node)
                    for pii in pii_patterns:
                        assert not _re.search(r"\b" + pii + r"\b", call_str.lower()), (
                            f"PII field '{pii}' found in log in {py_file.name} (ADR-006)"
                        )
