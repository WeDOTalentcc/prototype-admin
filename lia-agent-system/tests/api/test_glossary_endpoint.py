"""Behavioural tests for the canonical glossary lookup endpoints (Task #745)."""
from __future__ import annotations

import textwrap

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1 import glossary as glossary_v1
from app.shared.prompts import glossary_loader


@pytest.fixture()
def fake_glossary(tmp_path, monkeypatch):
    md = textwrap.dedent(
        """
        # Glossario de teste

        ## W

        ### WSI (Workforce Suitability Index)
        | Campo | Valor |
        |---|---|
        | **Sigla** | WSI |
        | **Definicao** | Indice composto que mede aderencia tecnica e comportamental do candidato a uma vaga. |
        | **Categoria** | Scoring |

        ### Bloom
        | Campo | Valor |
        |---|---|
        | **Sigla** | — |
        | **Definicao** | Taxonomia de niveis de complexidade cognitiva usada para calibrar perguntas. |
        | **Categoria** | Behavioral |
        """
    ).strip()
    path = tmp_path / "GLOSSARY.md"
    path.write_text(md, encoding="utf-8")
    monkeypatch.setenv("LIA_GLOSSARY_PATH", str(path))
    glossary_loader.get_glossary.cache_clear()
    yield path
    glossary_loader.get_glossary.cache_clear()


@pytest.fixture()
def client(fake_glossary):
    app = FastAPI()
    app.include_router(glossary_v1.router, prefix="/api/v1/glossary")
    return TestClient(app, raise_server_exceptions=False)


def test_lookup_returns_canonical_definition(client):
    resp = client.get("/api/v1/glossary/terms/WSI")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["success"] is True
    data = body["data"]
    assert data["sigla"] == "WSI"
    assert "Indice composto" in data["definition"]
    assert data["category"] == "Scoring"


def test_lookup_is_case_and_accent_tolerant(client):
    # Lowercase variant maps to the same entry.
    resp_lower = client.get("/api/v1/glossary/terms/wsi")
    assert resp_lower.status_code == 200
    assert resp_lower.json()["data"]["sigla"] == "WSI"

    # Term without a sigla still resolves cleanly.
    resp_bloom = client.get("/api/v1/glossary/terms/Bloom")
    assert resp_bloom.status_code == 200
    assert resp_bloom.json()["data"]["category"] == "Behavioral"


def test_unknown_term_returns_404(client):
    resp = client.get("/api/v1/glossary/terms/inexistente-xyz")
    assert resp.status_code == 404


def test_list_terms_returns_only_loaded_canonical_terms(client):
    resp = client.get("/api/v1/glossary/terms")
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    names = [t["name"] for t in body["data"]["terms"]]
    # Both WSI and Bloom are in CANONICAL_PROMPT_TERMS and present in the
    # fake glossary, so they should be listed.
    assert any("WSI" in n for n in names)
    assert any("Bloom" in n for n in names)
    # `total_loaded` mirrors what glossary_loader could parse.
    assert body["data"]["total_loaded"] >= 2
