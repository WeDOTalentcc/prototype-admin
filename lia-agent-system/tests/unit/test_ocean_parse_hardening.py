"""Robustez (2026-05-31): _extract_ocean_scores resiste a JSON malformado do LLM.

Antes: prompt exigia aspas duplas aninhadas em evidence -> LLM quebrava o JSON
('Unterminated string') -> fallback NEUTRO (score 60) -> bigfive_profile generico
no painel. Fix: prompt sem aspas internas + max_tokens 1500 + retry 1x.
"""
from types import SimpleNamespace

import pytest

from app.domains.cv_screening.services.wsi_service.service import WSIService

_VALID = (
    '{"big_five_jd": {'
    '"openness": {"score": 80, "evidence": ["lidera design"], "confidence": "high"}, '
    '"conscientiousness": {"score": 70, "evidence": [], "confidence": "medium"}, '
    '"extraversion": {"score": 50, "evidence": [], "confidence": "low"}, '
    '"agreeableness": {"score": 55, "evidence": [], "confidence": "low"}, '
    '"stability": {"score": 60, "evidence": [], "confidence": "low"}}}'
)


@pytest.mark.medium
@pytest.mark.asyncio
async def test_ocean_retry_recovers_from_malformed_json():
    svc = WSIService()
    qg = svc.question_generator
    calls = {"n": 0}

    async def _fake_invoke(prompt, **kw):
        calls["n"] += 1
        if calls["n"] == 1:
            return '{"big_five_jd": {"openness": {"score": 80, "evidence": [quebrado'  # malformado
        return _VALID
    qg.llm = SimpleNamespace(safe_invoke=_fake_invoke)

    res = await qg._extract_ocean_scores("jd rico", ["Lideranca"])
    assert calls["n"] == 2  # retry aconteceu
    o = next(r for r in res if r.trait == "openness")
    assert o.score == 80  # parse da 2a tentativa (nao neutro)


@pytest.mark.medium
@pytest.mark.asyncio
async def test_ocean_neutral_fallback_after_two_failures():
    svc = WSIService()
    qg = svc.question_generator

    async def _bad(prompt, **kw):
        return "isto nao e json"
    qg.llm = SimpleNamespace(safe_invoke=_bad)

    res = await qg._extract_ocean_scores("jd")
    assert len(res) == 5
    assert all(r.score == 60 for r in res)  # neutro apos 2 falhas (fail-loud no log)


@pytest.mark.medium
@pytest.mark.asyncio
async def test_ocean_first_try_success_no_retry():
    svc = WSIService()
    qg = svc.question_generator
    calls = {"n": 0}

    async def _ok(prompt, **kw):
        calls["n"] += 1
        return _VALID
    qg.llm = SimpleNamespace(safe_invoke=_ok)

    res = await qg._extract_ocean_scores("jd")
    assert calls["n"] == 1  # sem retry quando ja parseia
    assert next(r for r in res if r.trait == "openness").score == 80
