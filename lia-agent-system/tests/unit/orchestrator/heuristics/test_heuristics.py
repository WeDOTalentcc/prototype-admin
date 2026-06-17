"""
Unit tests for orchestrator heuristics module.

Sprint II.3 — extracted from `Orchestrator._is_technical_response()` and
`Orchestrator._is_cv_matching_request()` (V1 LIA-D06 DEPRECATED).

Estes tests garantem que heuristics module mantém comportamento idêntico
ao V1 — pré-requisito para Sprint III migration de V2.

Localização canônica: tests/unit/orchestrator/heuristics/
(parallel a app/orchestrator/heuristics/)

Reference: ADR-019 — Sprint II.3
"""
from __future__ import annotations

import pytest

from app.orchestrator.heuristics import is_cv_matching_request, is_technical_response
from app.orchestrator.heuristics.cv_matching_detector import CV_MATCHING_PATTERNS
from app.orchestrator.heuristics.technical_response_detector import TECHNICAL_PATTERNS


class TestIsTechnicalResponse:
    """Captura o comportamento do detector de respostas técnicas."""

    def test_exact_match_processado_com_sucesso(self):
        """Caso especial: mensagem exata 'Processado com sucesso.' → True."""
        assert is_technical_response("Processado com sucesso.") is True

    def test_exact_match_is_case_sensitive(self):
        """Variantes do exact match não devem casar (apenas exato)."""
        # V1 só faz `message == "Processado com sucesso."`
        assert is_technical_response("processado com sucesso.") is False
        assert is_technical_response("Processado com sucesso") is False  # sem ponto
        assert is_technical_response("Processado com sucesso!") is False  # exclamação

    @pytest.mark.parametrize(
        "pattern",
        TECHNICAL_PATTERNS,
    )
    def test_each_canonical_pattern_matches(self, pattern: str):
        """Cada pattern canônico em isolamento deve retornar True."""
        # Insert in middle of natural sentence
        message = f"Resposta padrão: {pattern} processada com OK"
        assert is_technical_response(message) is True

    def test_keyword_heuristic_pattern(self):
        assert is_technical_response("Keyword heuristic matched") is True
        assert is_technical_response("Resposta tem Keyword heuristic matched no meio") is True

    def test_ferramenta_pattern(self):
        assert is_technical_response("Ferramenta 'analyze_cv' executada") is True

    def test_acao_pattern(self):
        assert is_technical_response("Ação 'create_job' iniciada") is True

    def test_encaminhada_pattern(self):
        assert is_technical_response("Solicitação encaminhada para o agente sourcing") is True

    def test_executada_acao_pattern(self):
        assert is_technical_response("executada para ação criar candidato") is True

    def test_neutral_message_returns_false(self):
        assert is_technical_response("Olá, como posso ajudar?") is False
        assert is_technical_response("Boa tarde") is False
        assert is_technical_response("Mensagem normal sem keywords") is False

    def test_empty_string_returns_false(self):
        assert is_technical_response("") is False
        assert is_technical_response("    ") is False

    def test_returns_bool_type(self):
        """Contract: sempre retorna bool, nunca truthy/falsy."""
        result = is_technical_response("test")
        assert isinstance(result, bool)


class TestIsCvMatchingRequest:
    """Captura o comportamento do detector de requests de CV matching."""

    @pytest.mark.parametrize(
        "pattern",
        CV_MATCHING_PATTERNS,
    )
    def test_each_canonical_pattern_matches(self, pattern: str):
        """Cada um dos 20 patterns canônicos deve retornar True isoladamente."""
        assert is_cv_matching_request(pattern) is True

    def test_case_insensitive_match(self):
        """Match deve ser case-insensitive (V1 usa msg.lower())."""
        assert is_cv_matching_request("ANALISE O CV") is True
        assert is_cv_matching_request("Analise O CV") is True
        assert is_cv_matching_request("aNaLiSe O cV") is True

    def test_substring_match(self):
        """Pattern em substring deve casar."""
        msg = "Bom dia! Por favor, analise o cv desse candidato urgente"
        assert is_cv_matching_request(msg) is True

    def test_match_score_pattern(self):
        assert is_cv_matching_request("Qual o match score do candidato Maria?") is True

    def test_compatibilidade_patterns(self):
        assert is_cv_matching_request("compatibilidade do candidato com a vaga") is True
        assert is_cv_matching_request("análise de compatibilidade requerida") is True

    def test_triagem_patterns(self):
        assert is_cv_matching_request("triagem de cv urgente") is True
        assert is_cv_matching_request("triagem do candidato João") is True

    def test_candidato_alinhado_pattern(self):
        assert is_cv_matching_request("o candidato está alinhado com a vaga") is True

    def test_como_candidato_se_encaixa_pattern(self):
        assert is_cv_matching_request("como o candidato se encaixa na nossa vaga") is True

    def test_neutral_message_returns_false(self):
        assert is_cv_matching_request("Olá, como posso ajudar?") is False
        assert is_cv_matching_request("Boa tarde") is False
        assert is_cv_matching_request("Quais vagas temos abertas?") is False

    def test_empty_string_returns_false(self):
        assert is_cv_matching_request("") is False
        assert is_cv_matching_request("    ") is False

    def test_returns_bool_type(self):
        """Contract: sempre retorna bool."""
        result = is_cv_matching_request("test")
        assert isinstance(result, bool)


class TestEquivalenceWithV1:
    """
    P1 — Validação que heuristics module retorna EXATAMENTE o mesmo
    resultado que V1 para um conjunto representativo de mensagens.
    Sem isso, a extração corre risco de regressão silenciosa.
    """

    @pytest.fixture
    def v1_orchestrator(self):
        """V1 instance para comparação direta."""
        from unittest.mock import AsyncMock, MagicMock, patch

        from app.orchestrator.legacy.orchestrator import Orchestrator

        mock_llm = MagicMock()
        mock_llm.complete = AsyncMock(return_value={"content": "ok"})
        with patch("app.orchestrator.legacy.orchestrator.response_cache_service") as mc:
            mc.is_enabled.return_value = False
            mc.get_stats.return_value = {}
            return Orchestrator(llm_service=mock_llm)

    @pytest.mark.parametrize(
        "message",
        [
            "Processado com sucesso.",
            "Keyword heuristic matched para domain xyz",
            "Ferramenta 'analyze_cv' executada",
            "Olá! Posso ajudar?",
            "Analise o CV desse candidato",
            "Match score do candidato Maria",
            "ANALISE O CV",
            "Triagem de cv urgente",
            "Boa tarde",
            "",
        ],
    )
    def test_technical_detector_matches_v1(self, v1_orchestrator, message):
        """Heuristics module deve retornar IDENTICO ao V1."""
        v1_result = v1_orchestrator._is_technical_response(message)
        new_result = is_technical_response(message)
        assert v1_result == new_result, (
            f"DIVERGENCE para mensagem {message!r}: V1={v1_result}, new={new_result}"
        )

    @pytest.mark.parametrize(
        "message",
        [
            "Analise o CV desse candidato",
            "Match score do candidato Maria",
            "ANALISE O CV",
            "como o candidato se encaixa na vaga",
            "Triagem de cv urgente",
            "candidato está alinhado com a vaga?",
            "Boa tarde",
            "Quais vagas temos abertas?",
            "",
            "Processado com sucesso.",
        ],
    )
    def test_cv_matching_detector_matches_v1(self, v1_orchestrator, message):
        """Heuristics module deve retornar IDENTICO ao V1."""
        v1_result = v1_orchestrator._is_cv_matching_request(message)
        new_result = is_cv_matching_request(message)
        assert v1_result == new_result, (
            f"DIVERGENCE para mensagem {message!r}: V1={v1_result}, new={new_result}"
        )
