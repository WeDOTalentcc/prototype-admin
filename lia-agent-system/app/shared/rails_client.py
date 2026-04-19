"""Thin convenience wrappers around WeDOTalentATSClient for cross-domain use.

Usage:
    from app.shared.rails_client import rails_get, rails_patch
    data = await rails_get("/v1/companies/123/candidate-portal/lgpd-requests")
    result = await rails_patch("/v1/companies/123/candidate-portal/lgpd-requests/42/respond")
"""
from __future__ import annotations

import logging

from app.domains.ats_integration.services.ats_clients.wedotalent_rails import (
    WeDOTalentATSClient,
)

logger = logging.getLogger(__name__)

_client: WeDOTalentATSClient | None = None


def _get_client() -> WeDOTalentATSClient:
    global _client
    if _client is None:
        _client = WeDOTalentATSClient()
    return _client


async def rails_get(path: str, params: dict | None = None) -> dict:
    """GET request to Rails API. Returns response data dict (empty dict on error)."""
    try:
        resp = await _get_client().get(path, params=params)
        return resp.data if resp and resp.data else {}
    except Exception as exc:
        logger.warning("[rails_client] GET %s failed: %s", path, exc)
        return {}


async def rails_patch(path: str, data: dict | None = None) -> dict:
    """PATCH request to Rails API. Returns response data dict (empty dict on error)."""
    try:
        resp = await _get_client().patch(path, json_body=data or {})
        return resp.data if resp and resp.data else {}
    except Exception as exc:
        logger.warning("[rails_client] PATCH %s failed: %s", path, exc)
        return {}


async def rails_post(path: str, data: dict | None = None) -> dict:
    """POST request to Rails API."""
    try:
        resp = await _get_client().post(path, json_body=data or {})
        return resp.data if resp and resp.data else {}
    except Exception as exc:
        logger.warning("[rails_client] POST %s failed: %s", path, exc)
        return {}
