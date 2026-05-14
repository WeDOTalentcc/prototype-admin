"""Sentinela offline — Task #1055.

Garante que `intake_node` (e por extensão `jd_enrichment_node`, via re-emissão)
sempre publique `data.suggestions_data.pipeline_template` no `ws_stage_payload`
do wizard sempre que houver `parsed_title`. Sem isso, o frontend
`WizardPipelineTemplateCard` (`[data-testid="wizard-template-card"]`) nunca
mostra e o e2e `pw-cenario-A` falha.

A sugestão é determinística (keyword-based, sem LLM e sem DB), então o teste
roda offline e não consome quota de Gemini/Claude.
"""
from __future__ import annotations

import pytest

from app.domains.job_creation.graph import (
    _PIPELINE_TEMPLATE_IDS,
    _suggest_pipeline_template,
    intake_node,
)


class _StubExtraction:
    def __init__(
        self,
        parsed_title: str = "",
        parsed_seniority: str = "",
        parsed_department: str = "",
        parsed_location: str = "",
        parsed_model: str = "",
        confidence: float = 0.5,
        source: str = "regex",
    ):
        self.parsed_title = parsed_title
        self.parsed_seniority = parsed_seniority
        self.parsed_department = parsed_department
        self.parsed_location = parsed_location
        self.parsed_model = parsed_model
        self.confidence = confidence
        self.source = source


class _StubExtractor:
    def __init__(self, extraction: _StubExtraction):
        self._e = extraction

    def extract(self, _query: str) -> _StubExtraction:
        return self._e

    def extract_from_sources(self, **_kwargs) -> _StubExtraction:
        return self._e


@pytest.mark.parametrize(
    "title,expected",
    [
        ("Engenheiro de Software Pleno", "technical"),
        ("Desenvolvedor Backend Sênior", "technical"),
        ("Diretor de Engenharia", "executive"),
        ("CTO", "executive"),
        ("Estagiário de Marketing", "intern"),
        ("Trainee Comercial", "intern"),
        ("Atendente de Loja", "operational"),
        ("Vendedor Externo", "operational"),
        ("Cargo Indefinido XPTO", "technical"),  # default seguro
    ],
)
def test_suggest_pipeline_template_keyword_classification(title, expected):
    block = _suggest_pipeline_template(title)
    assert block is not None, f"esperava bloco para título não-vazio: {title!r}"
    assert block["suggested_type"] == expected
    assert block["templates"] == list(_PIPELINE_TEMPLATE_IDS)


def test_suggest_pipeline_template_no_title_returns_none():
    assert _suggest_pipeline_template("") is None
    assert _suggest_pipeline_template(None) is None
    assert _suggest_pipeline_template("   ") is None


def test_intake_node_emits_pipeline_template_in_payload(monkeypatch):
    """intake_node deve incluir suggestions_data.pipeline_template sempre que
    houver título parseado — contrato consumido por `buildPipelineTemplateCard`
    no `wizard-plan-card.ts`."""
    extractor = _StubExtractor(
        _StubExtraction(parsed_title="Engenheiro de Software", parsed_seniority="Pleno"),
    )
    monkeypatch.setattr(
        "app.domains.job_creation.graph.get_intake_extractor",
        lambda: extractor,
    )

    state = {"user_query": "Quero criar uma vaga de Engenheiro de Software Pleno"}
    out = intake_node(state)

    payload = out["ws_stage_payload"]
    assert payload["type"] == "wizard_stage"
    assert payload["stage"] == "intake"
    data = payload["data"]
    assert "suggestions_data" in data, (
        "intake_node deve emitir 'suggestions_data' no ws_stage_payload "
        "(consumido por WizardPipelineTemplateCard via buildPipelineTemplateCard). "
        "Regressão Task #1055."
    )
    block = data["suggestions_data"]["pipeline_template"]
    assert block is not None
    assert block["suggested_type"] == "technical"
    assert "technical" in block["templates"]


def test_intake_node_pipeline_template_none_when_no_title(monkeypatch):
    """Sem título parseável o bloco deve ser None — frontend pula a injeção
    do card sem quebrar (pipelineTemplateCardsEqual lida com null)."""
    extractor = _StubExtractor(_StubExtraction(parsed_title=""))
    monkeypatch.setattr(
        "app.domains.job_creation.graph.get_intake_extractor",
        lambda: extractor,
    )

    out = intake_node({"user_query": "oi"})
    block = out["ws_stage_payload"]["data"]["suggestions_data"]["pipeline_template"]
    assert block is None
