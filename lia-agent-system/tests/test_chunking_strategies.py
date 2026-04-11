"""Tests for chunking strategies (Task #126)."""

import os
import pytest

from app.shared.intelligence.chunking.base import Chunk, DocumentType
from app.shared.intelligence.chunking.sliding_window import SlidingWindowChunker
from app.shared.intelligence.chunking.section_aware import SectionAwareChunker
from app.shared.intelligence.chunking.semantic_chunker import SemanticChunker
from app.shared.intelligence.chunking.factory import ChunkingStrategyFactory
from app.shared.intelligence.embedding_service import EmbeddingService


SAMPLE_CV_PT = """
Resumo Profissional
Engenheiro de Software Sênior com 8 anos de experiência em Python.

Experiência Profissional
Tech Corp — Engenheiro Sênior (2020-presente)
- Liderou equipe de 5 desenvolvedores
- Implementou pipeline CI/CD

StartupXYZ — Desenvolvedor Python Pleno (2017-2020)
- Desenvolveu APIs REST com Flask e FastAPI

Formação Acadêmica
Bacharelado em Ciência da Computação — USP (2013-2017)

Habilidades
Python, FastAPI, Flask, PostgreSQL, Redis, Docker, Kubernetes, AWS

Idiomas
Português — Nativo
Inglês — Fluente (C1)
"""

SAMPLE_CV_EN = """
Professional Summary
Senior Software Engineer with 8 years of experience in Python development.

Work Experience
Tech Corp — Senior Software Engineer (2020-present)
- Led a team of 5 developers in redesigning the core platform

Education
BSc Computer Science — University of São Paulo (2013-2017)

Skills
Python, FastAPI, Flask, PostgreSQL, Redis, Docker, Kubernetes, AWS

Languages
Portuguese — Native
English — Fluent (C1)
"""

SAMPLE_JD_PT = """Descrição da Vaga
Buscamos um Engenheiro de Software Sênior para atuar no desenvolvimento de soluções escaláveis em Python para nossa plataforma de RH tech.

Responsabilidades
- Desenvolver e manter microsserviços em Python/FastAPI
- Participar de code reviews e mentoria de desenvolvedores juniores
- Colaborar com equipes de produto na definição de soluções técnicas

Requisitos
- 5+ anos de experiência com Python
- Experiência com FastAPI ou Django
- Conhecimento em PostgreSQL e Redis
- Experiência com Docker e Kubernetes

Benefícios
- Salário competitivo (CLT)
- PLR anual
- Plano de saúde e odontológico
- Vale alimentação e refeição
"""

NO_SECTIONS_TEXT = "This is a plain text without any recognizable section headers. " * 20


class TestSlidingWindowChunker:
    def test_empty_text(self):
        chunker = SlidingWindowChunker()
        assert chunker.chunk("") == []

    def test_short_text(self):
        chunker = SlidingWindowChunker(chunk_size=1000)
        result = chunker.chunk("Hello world")
        assert len(result) == 1
        assert result[0].text == "Hello world"

    def test_long_text_produces_multiple_chunks(self):
        text = "A" * 500 + ". " + "B" * 500 + ". " + "C" * 500
        chunker = SlidingWindowChunker(chunk_size=600, overlap=50)
        result = chunker.chunk(text)
        assert len(result) > 1

    def test_strategy_name(self):
        chunker = SlidingWindowChunker()
        assert chunker.strategy_name == "sliding_window"

    def test_chunks_have_metadata(self):
        text = "Word. " * 300
        chunker = SlidingWindowChunker(chunk_size=200, overlap=20)
        result = chunker.chunk(text)
        assert all(c.metadata.get("strategy") == "sliding_window" for c in result)


class TestSectionAwareChunker:
    def test_cv_pt_detects_sections(self):
        chunker = SectionAwareChunker(document_type="cv")
        chunks = chunker.chunk(SAMPLE_CV_PT)
        sections = [c.metadata.get("section") for c in chunks if c.metadata.get("section")]
        assert len(sections) >= 3
        assert any("profissional" in s.lower() for s in sections)

    def test_cv_en_detects_sections(self):
        chunker = SectionAwareChunker(document_type="cv")
        chunks = chunker.chunk(SAMPLE_CV_EN)
        sections = [c.metadata.get("section") for c in chunks if c.metadata.get("section")]
        assert len(sections) >= 3

    def test_jd_pt_detects_sections(self):
        chunker = SectionAwareChunker(document_type="job_description")
        chunks = chunker.chunk(SAMPLE_JD_PT)
        sections = [c.metadata.get("section") for c in chunks if c.metadata.get("section")]
        assert len(sections) >= 3

    def test_fallback_when_no_sections(self):
        chunker = SectionAwareChunker(document_type="cv")
        chunks = chunker.chunk(NO_SECTIONS_TEXT)
        assert len(chunks) >= 1

    def test_empty_text(self):
        chunker = SectionAwareChunker(document_type="cv")
        assert chunker.chunk("") == []

    def test_strategy_name(self):
        chunker = SectionAwareChunker()
        assert chunker.strategy_name == "section_aware"

    def test_large_section_is_split(self):
        large_section = "Experiência Profissional\n" + ("Desenvolveu sistemas complexos. " * 200)
        chunker = SectionAwareChunker(document_type="cv", max_chunk_size=500)
        chunks = chunker.chunk(large_section)
        assert len(chunks) > 1
        assert all(len(c.text) <= 600 for c in chunks)


class TestSemanticChunker:
    def test_empty_text(self):
        chunker = SemanticChunker()
        assert chunker.chunk("") == []

    def test_single_sentence(self):
        chunker = SemanticChunker()
        result = chunker.chunk("Hello world.")
        assert len(result) == 1

    def test_without_embeddings_falls_back(self):
        text = "First sentence. " * 50
        chunker = SemanticChunker()
        result = chunker.chunk(text)
        assert len(result) >= 1

    def test_with_embeddings(self):
        sentences_text = "Machine learning is great. Deep learning uses neural networks. I like pizza. The weather is sunny."
        similar_emb = [1.0, 0.0, 0.0]
        different_emb = [0.0, 1.0, 0.0]
        embeddings = [similar_emb, similar_emb, different_emb, different_emb]

        chunker = SemanticChunker(similarity_threshold=0.5, min_chunk_size=5)
        result = chunker.chunk(sentences_text, embeddings=embeddings)
        assert len(result) >= 2

    def test_strategy_name(self):
        chunker = SemanticChunker()
        assert chunker.strategy_name == "semantic"


class TestChunkingStrategyFactory:
    def test_cv_returns_recursive(self):
        strategy = ChunkingStrategyFactory.get_strategy(DocumentType.CV)
        assert strategy.strategy_name == "recursive"

    def test_jd_returns_recursive(self):
        strategy = ChunkingStrategyFactory.get_strategy(DocumentType.JOB_DESCRIPTION)
        assert strategy.strategy_name == "recursive"

    def test_generic_returns_recursive(self):
        strategy = ChunkingStrategyFactory.get_strategy(DocumentType.GENERIC)
        assert strategy.strategy_name == "recursive"

    def test_policy_returns_recursive(self):
        strategy = ChunkingStrategyFactory.get_strategy(DocumentType.POLICY)
        assert strategy.strategy_name == "recursive"

    def test_override_forces_strategy(self):
        strategy = ChunkingStrategyFactory.get_strategy(
            DocumentType.CV, override="sliding_window"
        )
        assert strategy.strategy_name == "sliding_window"

    def test_env_var_override(self, monkeypatch):
        monkeypatch.setenv("CHUNKING_STRATEGY", "sliding_window")
        strategy = ChunkingStrategyFactory.get_strategy(DocumentType.CV)
        assert strategy.strategy_name == "sliding_window"

    def test_unknown_strategy_falls_back(self):
        strategy = ChunkingStrategyFactory.get_strategy(
            DocumentType.GENERIC, override="nonexistent"
        )
        assert strategy.strategy_name == "sliding_window"

    def test_string_document_type(self):
        strategy = ChunkingStrategyFactory.get_strategy("cv")
        assert strategy.strategy_name == "recursive"

    def test_unknown_document_type_string(self):
        strategy = ChunkingStrategyFactory.get_strategy("unknown_doc_type")
        assert strategy.strategy_name == "recursive"


class TestEmbeddingServiceChunkText:
    def test_backward_compatible_default(self):
        svc = EmbeddingService()
        text = "Hello. " * 300
        result = svc.chunk_text(text)
        assert len(result) >= 1
        assert all(isinstance(c, str) for c in result)

    def test_cv_document_type(self):
        svc = EmbeddingService()
        result = svc.chunk_text(SAMPLE_CV_PT, document_type="cv")
        assert len(result) >= 1

    def test_strategy_override(self):
        svc = EmbeddingService()
        long_text = (SAMPLE_CV_PT + "\n") * 10
        result_sw = svc.chunk_text(long_text, strategy_override="sliding_window")
        result_rc = svc.chunk_text(long_text, strategy_override="recursive")
        assert len(result_sw) >= 1 and len(result_rc) >= 1
        assert len(result_rc) != len(result_sw) or result_rc != result_sw

    def test_empty_text(self):
        svc = EmbeddingService()
        assert svc.chunk_text("") == []

    def test_short_text(self):
        svc = EmbeddingService()
        result = svc.chunk_text("Short text")
        assert result == ["Short text"]
