"""
V2.1 sensor (2026-06-01): GET /company-ai-persona/options is a tenant-agnostic
catalog (tones + name constraints). It must NOT require company_id — requiring
it broke "Não foi possível carregar as opções de tom" for sessions whose JWT
doesn't resolve a company_id. Auth (get_current_active_user) is still required.
"""
from __future__ import annotations

import asyncio
import inspect

from app.api.v1.company_ai_persona import get_ai_persona_options


def test_options_endpoint_has_no_company_id_dependency():
    params = inspect.signature(get_ai_persona_options).parameters
    assert "company_id" not in params, (
        "get_ai_persona_options must not require company_id — it is a "
        "WeDOTalent-wide catalog. Re-adding company_id reintroduces the "
        "'opções de tom' load failure."
    )


def test_options_returns_full_tone_catalog():
    result = asyncio.run(get_ai_persona_options(_user=None))
    assert len(result.tones) >= 1
    for t in result.tones:
        assert t.value and t.label_pt and t.instruction
    assert result.name_constraints.max_length > result.name_constraints.min_length
