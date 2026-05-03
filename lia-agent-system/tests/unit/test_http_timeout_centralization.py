"""Tests for HTTP timeout centralization (UC-P2-12)."""
import pytest


def test_apify_timeout_uses_settings():
    import re
    with open("/home/runner/workspace/lia-agent-system/app/domains/sourcing/services/apify_mcp_client.py") as f:
        content = f.read()
    assert "HTTP_TIMEOUT_APIFY_SECONDS" in content, "apify_mcp_client must use settings timeout"


def test_github_timeout_uses_settings():
    with open("/home/runner/workspace/lia-agent-system/app/domains/sourcing/services/github_service.py") as f:
        content = f.read()
    assert "HTTP_TIMEOUT_GITHUB_SECONDS" in content, "github_service must use settings timeout"


def test_stackoverflow_timeout_uses_settings():
    with open("/home/runner/workspace/lia-agent-system/app/domains/sourcing/services/stackoverflow_service.py") as f:
        content = f.read()
    assert "HTTP_TIMEOUT_STACKOVERFLOW_SECONDS" in content


def test_settings_has_http_timeout_fields():
    from lia_config.config import settings
    assert hasattr(settings, "HTTP_TIMEOUT_APIFY_SECONDS")
    assert hasattr(settings, "HTTP_TIMEOUT_GITHUB_SECONDS")
    assert hasattr(settings, "HTTP_TIMEOUT_STACKOVERFLOW_SECONDS")
    assert settings.HTTP_TIMEOUT_APIFY_SECONDS == 180.0
    assert settings.HTTP_TIMEOUT_GITHUB_SECONDS == 30.0
