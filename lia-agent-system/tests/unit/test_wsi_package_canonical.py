"""Consolidacao WSI Fase 2.4b-2: orquestracao canonica unica generate_wsi_package.

Pina o contrato: UMA extracao OCEAN alimenta perguntas + Big Five (profile +
trait_rankings F3). Testes puros (mock _extract_ocean_scores + generate_from_simple_inputs).
"""
import pytest

from app.domains.cv_screening.services.wsi_service import service as svc_mod
from app.domains.cv_screening.services.wsi_service.models import OceanTraitScore


@pytest.mark.medium
@pytest.mark.asyncio
async def test_package_single_ocean_extraction_feeds_questions_and_panel(monkeypatch):
    svc = svc_mod.WSIService()
    calls = {"ocean": 0}

    async def _fake_ocean(jd, names):
        calls["ocean"] += 1
        return [
            OceanTraitScore(trait="conscientiousness", score=80, confidence="high", evidence=["lidera"]),
            OceanTraitScore(trait="openness", score=50),
        ]
    monkeypatch.setattr(svc.question_generator, "_extract_ocean_scores", _fake_ocean)

    captured = {}

    async def _fake_gen(**kw):
        captured.update(kw)
        return ["Q1", "Q2"]
    monkeypatch.setattr(svc, "generate_from_simple_inputs", _fake_gen)

    pkg = await svc.generate_wsi_package(
        skills=["Python"], behavioral=["Comunicacao"], seniority="senior",
        job_description="JD com lideranca e arquitetura", mode="compact",
    )

    assert calls["ocean"] == 1  # UMA extracao OCEAN (sem dupla chamada LLM)
    assert pkg["questions"] == ["Q1", "Q2"]
    # bigfive_profile escala 0-1 (de 0-100)
    assert pkg["bigfive_profile"]["conscientiousness"] == 0.8
    assert pkg["bigfive_profile"]["openness"] == 0.5
    assert "evidences" in pkg["bigfive_profile"]
    # trait_rankings via canonico (5 traits, rank/weight)
    assert {r["trait"] for r in pkg["trait_rankings"]} == {
        "openness", "conscientiousness", "extraversion", "agreeableness", "stability"
    }
    assert all("rank" in r and "weight" in r for r in pkg["trait_rankings"])
    # traits pre-computados passados ao gerador (sem 2a extracao)
    assert captured["precomputed_selected_traits"] is not None


@pytest.mark.medium
@pytest.mark.asyncio
async def test_package_no_jd_skips_bigfive(monkeypatch):
    svc = svc_mod.WSIService()

    async def _fake_ocean(jd, names):
        raise AssertionError("nao deve extrair OCEAN sem JD")
    monkeypatch.setattr(svc.question_generator, "_extract_ocean_scores", _fake_ocean)

    async def _fake_gen(**kw):
        assert kw["precomputed_selected_traits"] is None
        return ["Q"]
    monkeypatch.setattr(svc, "generate_from_simple_inputs", _fake_gen)

    pkg = await svc.generate_wsi_package(skills=["Python"], seniority="pleno", job_description=None)
    assert pkg["bigfive_profile"] is None
    assert pkg["trait_rankings"] == []
    assert pkg["questions"] == ["Q"]


@pytest.mark.medium
@pytest.mark.asyncio
async def test_package_propagates_dropped(monkeypatch):
    svc = svc_mod.WSIService()

    async def _fake_ocean(jd, names):
        return [OceanTraitScore(trait="openness", score=70)]
    monkeypatch.setattr(svc.question_generator, "_extract_ocean_scores", _fake_ocean)

    async def _fake_gen(**kw):
        # simula L4 tendo descartado 1 pergunta
        if kw.get("collect_dropped") is not None:
            kw["collect_dropped"].append({"question": "viesada", "category": "gender"})
        return ["Q"]
    monkeypatch.setattr(svc, "generate_from_simple_inputs", _fake_gen)

    dropped = []
    pkg = await svc.generate_wsi_package(
        skills=["Python"], seniority="pleno", job_description="jd", collect_dropped=dropped,
    )
    assert len(pkg["dropped"]) == 1
    assert pkg["dropped"][0]["category"] == "gender"
