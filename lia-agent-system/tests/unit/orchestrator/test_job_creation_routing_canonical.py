"""Frente 1 (unificacao wizard 2026-05-29) — roteamento canonico de criacao de vaga.

Contrato: TODA intencao de CRIACAO de vaga roteia para o dominio `wizard`
(grafo canonico job_creation), deterministicamente via FastRouter, ANTES da
cascata LLM (Tier 5) e do Vector Cache (Tier 3). Intencoes de GESTAO de vaga
existente (listar/editar/publicar/clonar/fechar/pausar) permanecem em
`job_management`.

Mata o nao-determinismo onde "criar vaga"->wizard mas "abrir/nova vaga"
->job_management (audit 2026-05-29 — duas experiencias divergentes).
"""
from __future__ import annotations

import pytest

from app.orchestrator.routing.fast_router import FastRouter


@pytest.fixture(scope="module")
def fr():
    return FastRouter()


CREATION_PHRASES = [
    "criar vaga",
    "criar uma vaga",
    "quero criar uma vaga",
    "quero abrir uma nova vaga",
    "abrir vaga",
    "abrir uma vaga",
    "nova vaga",
    "nova vaga de engenheiro de software",
    "quero criar uma vaga de designer senior",
    "preciso contratar um desenvolvedor",
    "quero contratar uma pessoa de produto",
    "vou abrir uma posicao de dados",
    "cadastrar nova vaga",
]

MANAGEMENT_PHRASES = [
    "listar vagas",
    "minhas vagas",
    "ver vagas abertas",
    "editar vaga 123",
    "atualizar a vaga de backend",
    "clonar vaga",
    "fechar vaga",
    "pausar vaga",
    "publicar vaga",
    "quantas vagas tenho abertas",  # ranking de vagas removido: colide com sourcing (follow-up separado)
    "detalhes da vaga",
]


@pytest.mark.parametrize("phrase", CREATION_PHRASES)
def test_creation_phrases_route_to_wizard(fr, phrase):
    result = fr.match(phrase)
    assert result is not None, f"FastRouter retornou None para {phrase!r}"
    assert result.domain_id == "wizard", (
        f"Criacao de vaga deve rotear para wizard. "
        f"{phrase!r} -> {result.domain_id} (conf={result.confidence:.2f}, "
        f"matched={result.matched_text!r})"
    )


@pytest.mark.parametrize("phrase", MANAGEMENT_PHRASES)
def test_management_phrases_route_to_job_management(fr, phrase):
    result = fr.match(phrase)
    assert result is not None, f"FastRouter retornou None para {phrase!r}"
    assert result.domain_id == "job_management", (
        f"Gestao de vaga existente deve rotear para job_management. "
        f"{phrase!r} -> {result.domain_id} (conf={result.confidence:.2f}, "
        f"matched={result.matched_text!r})"
    )
