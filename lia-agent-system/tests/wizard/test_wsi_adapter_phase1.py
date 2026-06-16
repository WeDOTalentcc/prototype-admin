"""TDD — Consolidação WSI Fase 1: adapter de competências → cv_screening (ACL)."""
from __future__ import annotations
from types import SimpleNamespace
from unittest.mock import patch
import pytest

from app.domains.job_creation.helpers.vacancy_vocab import to_cv_screening_seniority
from app.domains.job_creation.orchestrator.wsi_canonical_adapter import (
    suggest_competencies_canonical,
)


@pytest.mark.easy
@pytest.mark.parametrize("inp,exp", [
    ("Diretor", "executive"), ("diretor", "executive"), ("CEO", "executive"),
    ("gerente", "executive"), ("pleno", "pleno"), ("Sênior", "senior"),
    ("especialista", "senior"), ("lead", "lead"), ("coordenador", "lead"),
    ("junior", "junior"), ("estagiario", "junior"), (None, "pleno"), ("xpto", "pleno"),
])
def test_seniority_map_to_cv(inp, exp):
    assert to_cv_screening_seniority(inp) == exp


def _fake_suggestion():
    C = lambda name, trait=None: SimpleNamespace(name=name, big_five_mapping=trait)
    return SimpleNamespace(
        technical_competencies=[C("Gestão de Caixa"), C("Hedge Cambial")],
        behavioral_competencies=[C("Decisão sob Pressão", "conscientiousness")],
        cultural_competencies=[C("Senso de Dono", "openness")],
    )


@pytest.mark.medium
def test_adapter_maps_canonical_to_wizard_shape():
    captured = {}

    async def _fake_analyze(*, job_description, seniority):
        captured["jd"] = job_description
        captured["seniority"] = seniority
        return _fake_suggestion()

    fake_svc = SimpleNamespace(analyze_jd_and_suggest_competencies=_fake_analyze)
    with patch(
        "app.domains.cv_screening.services.wsi_service.service.get_wsi_service",
        return_value=fake_svc,
    ):
        r = suggest_competencies_canonical(
            title="Gerente Tesouraria", seniority="Diretor",
            jd_text="lidera tesouraria", company_id="c1",
        )
    # senioridade mapeada p/ cv_screening (5 níveis)
    assert captured["seniority"] == "executive"
    assert captured["jd"] == "lidera tesouraria"
    # technical → {skill}
    assert r["technical"] == [{"skill": "Gestão de Caixa"}, {"skill": "Hedge Cambial"}]
    # behavioral + cultural → bloco comportamental com trait
    assert {"competencia": "Decisão sob Pressão", "trait_big_five": "conscientiousness"} in r["behavioral"]
    assert {"competencia": "Senso de Dono", "trait_big_five": "openness"} in r["behavioral"]


@pytest.mark.medium
def test_adapter_falls_back_to_title_when_no_jd():
    captured = {}

    async def _fake_analyze(*, job_description, seniority):
        captured["jd"] = job_description
        return _fake_suggestion()

    with patch(
        "app.domains.cv_screening.services.wsi_service.service.get_wsi_service",
        return_value=SimpleNamespace(analyze_jd_and_suggest_competencies=_fake_analyze),
    ):
        suggest_competencies_canonical(title="Gerente X", seniority="pleno", jd_text="", company_id="c1")
    assert captured["jd"] == "Gerente X"  # usa título quando não há JD


@pytest.mark.medium
def test_adapter_returns_none_on_failure():
    async def _boom(*, job_description, seniority):
        raise RuntimeError("LLM down")

    with patch(
        "app.domains.cv_screening.services.wsi_service.service.get_wsi_service",
        return_value=SimpleNamespace(analyze_jd_and_suggest_competencies=_boom),
    ):
        r = suggest_competencies_canonical(title="X", seniority="pleno", company_id="c1")
    assert r is None  # caller trata fail-loud
