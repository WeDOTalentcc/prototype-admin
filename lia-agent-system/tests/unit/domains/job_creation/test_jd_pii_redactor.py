"""TDD red-phase — PII redactor for JD embedding texts (Sprint B Phase 1, gap C4).

Harness taxonomy: Sensor (computacional, feedforward) — protects against
candidate PII leaking into pgvector embeddings via free-text JD fields
like `responsibilities` and `requirements`.

Why this exists: `_build_embedding_text` filters BY FIELD (only title +
responsibilities + requirements) but does NOT REDACT field content. If a
recruiter pastes "Responsabilidade: substituir o José Silva CPF 111.222.333-44
(j.silva@example.com, +55 11 99999-1234) no time" into the JD, that PII
was being shipped to OpenAI text-embedding-3-small. This sensor stops it.

If a test below fails: read the test name and the regex pattern. If the
pattern is too strict (false positive on legit text) widen it; if too loose
(real PII slips through) tighten it. Update _redact_pii in
app/domains/job_creation/services/jd_similar_service.py.
"""
from __future__ import annotations

import pytest


# Lazy import to keep tests RED until function exists
def _redact(text: str) -> str:
    from app.domains.job_creation.services.jd_similar_service import _redact_pii
    return _redact_pii(text)


class TestRedactCpf:
    def test_redact_cpf_formatted(self):
        out = _redact("Substituir o colaborador 111.222.333-44 que saiu")
        assert "111.222.333-44" not in out
        assert "[CPF]" in out

    def test_redact_cpf_unformatted(self):
        out = _redact("Documento 11122233344 anexado")
        assert "11122233344" not in out
        assert "[CPF]" in out

    def test_redact_multiple_cpfs(self):
        out = _redact("CPFs: 111.222.333-44 e 555.666.777-88")
        assert "111.222.333-44" not in out
        assert "555.666.777-88" not in out
        assert out.count("[CPF]") == 2


class TestRedactCnpj:
    def test_redact_cnpj_formatted(self):
        out = _redact("Empresa parceira CNPJ 12.345.678/0001-90")
        assert "12.345.678/0001-90" not in out
        assert "[CNPJ]" in out


class TestRedactEmail:
    def test_redact_email_simple(self):
        out = _redact("Reportar para joao@empresa.com")
        assert "joao@empresa.com" not in out
        assert "[EMAIL]" in out

    def test_redact_email_with_dots_and_dashes(self):
        out = _redact("Contact j.silva-recruiter@sub.example.co.uk for info")
        assert "j.silva-recruiter@sub.example.co.uk" not in out
        assert "[EMAIL]" in out


class TestRedactPhone:
    def test_redact_phone_br_with_parens(self):
        out = _redact("Ligar para (11) 99999-1234")
        assert "99999-1234" not in out
        assert "[TEL]" in out

    def test_redact_phone_br_intl(self):
        out = _redact("WhatsApp +55 11 99999-1234 disponivel")
        assert "99999-1234" not in out
        assert "[TEL]" in out

    def test_redact_phone_br_without_parens(self):
        out = _redact("Telefone 11999991234")
        assert "11999991234" not in out
        assert "[TEL]" in out


class TestPreservesNonPii:
    def test_preserves_role_responsibilities(self):
        text = "Responsavel por arquitetura distribuida com Python e PostgreSQL"
        assert _redact(text) == text

    def test_preserves_seniority_keywords(self):
        text = "Senior Backend Engineer com 5+ anos de experiencia em microservicos"
        assert _redact(text) == text

    def test_preserves_versions_and_numbers(self):
        # "5+", "10+", "2024", "v3.2" should NOT be flagged as CPF/phone
        text = "Python 3.11, Django 4.2, 5+ anos de experiencia, ano 2024"
        assert _redact(text) == text

    def test_short_numbers_not_flagged(self):
        text = "Equipe de 12 pessoas, budget 500k"
        assert _redact(text) == text


class TestNestedStructures:
    def test_redact_inside_responsibilities_list(self):
        """_build_embedding_text should redact inside list elements."""
        from app.domains.job_creation.services.jd_similar_service import (
            _build_embedding_text,
        )
        out = _build_embedding_text(
            title="Backend Engineer",
            jd_enriched={
                "responsibilities": [
                    "Substituir Maria CPF 111.222.333-44",
                    "Reportar para boss@empresa.com",
                ],
                "requirements": ["Python 3.11", "Telefone (11) 99999-0000 do recrutador"],
            },
        )
        assert "111.222.333-44" not in out
        assert "boss@empresa.com" not in out
        assert "99999-0000" not in out
        assert "[CPF]" in out
        assert "[EMAIL]" in out
        assert "[TEL]" in out
        # Non-PII content preserved
        assert "Backend Engineer" in out
        assert "Python 3.11" in out
