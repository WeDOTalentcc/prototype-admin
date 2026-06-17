"""LGPD sensor (audit 2026-06-06): EmbeddingService redige PII no chokepoint
ANTES de enviar pro provedor. Estruturada sempre (default); nomes via Presidio
quando mask_names=True (superficies de candidato/conversa). Sem isso, texto cru
(incl. PII de candidato) ia pro OpenAI/Gemini.
"""
from __future__ import annotations

import asyncio


def _patch_capture(monkeypatch):
    captured: dict = {}

    async def fake_embed(text, preferred_provider=None, company_id=None):
        captured["text"] = text
        return ([0.0] * 768, "openai", "text-embedding-3-small")

    monkeypatch.setattr(
        "app.shared.providers.embedding_factory.EmbeddingProviderFactory.embed_with_fallback",
        fake_embed,
    )
    return captured


def test_default_redacts_structured_pii_keeps_name(monkeypatch):
    captured = _patch_capture(monkeypatch)
    from app.shared.intelligence.embedding_service import EmbeddingService

    svc = EmbeddingService()
    asyncio.run(
        svc.generate_embedding(
            "Felipe Almeida CPF 123.456.789-00 email joao@acme.com"
        )
    )
    txt = captured["text"]
    assert "123.456.789-00" not in txt, "CPF deveria ter sido redigido"
    assert "joao@acme.com" not in txt, "email deveria ter sido redigido"
    # default (mask_names=False): NOME e mantido (vaga/JD precisa de matching)
    assert "Felipe" in txt


def test_mask_names_removes_person(monkeypatch):
    captured = _patch_capture(monkeypatch)
    from app.shared.intelligence.embedding_service import EmbeddingService

    svc = EmbeddingService()
    asyncio.run(
        svc.generate_embedding(
            "Felipe Almeida e forte em Python", mask_names=True
        )
    )
    txt = captured["text"]
    assert "Felipe Almeida" not in txt, "nome deveria ter sido redigido (Presidio)"
