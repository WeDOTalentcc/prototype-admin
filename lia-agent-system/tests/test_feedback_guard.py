"""Sensor — guard canonico de feedback: fairness + PII de documento + LLM-judge dormente."""
import pytest
from app.shared.compliance.feedback_guard import (
    detect_pii, feedback_block_reason, feedback_llm_judge_reason, llm_judge_enabled,
)


class TestDetectPII:
    def test_cpf_detected(self):
        assert "cpf" in detect_pii("Seu CPF 123.456.789-09 consta no sistema")
    def test_cnpj_detected(self):
        assert "cnpj" in detect_pii("CNPJ 12.345.678/0001-99")
    def test_clean_text_no_pii(self):
        assert detect_pii("Olá Maria, obrigado por participar. Sucesso!") == []
    def test_empty(self):
        assert detect_pii("") == []
        assert detect_pii(None) == []


class TestFeedbackBlockReason:
    def test_blocks_pii_cpf(self):
        r = feedback_block_reason("Olá, seu CPF 123.456.789-09 ...", "co-1")
        assert r and r.startswith("pii:")
    def test_blocks_fairness(self):
        r = feedback_block_reason("Decidimos não seguir; prefiro homens para a vaga.", "co-1")
        assert r and r.startswith("fairness:")
    def test_clean_passes(self):
        assert feedback_block_reason("Olá Maria, obrigado por participar. Sucesso!", "co-1") is None
    def test_empty_passes(self):
        assert feedback_block_reason("", "co-1") is None


class TestLlmJudgeDormant:
    @pytest.mark.asyncio
    async def test_judge_off_by_default(self, monkeypatch):
        monkeypatch.delenv("FEEDBACK_LLM_JUDGE", raising=False)
        assert llm_judge_enabled() is False
        assert await feedback_llm_judge_reason("qualquer texto", "co-1") is None
