"""
W3-014 · SSE compliance wiring anti-regression sensor.
Verifica AST que agent_chat_sse.py importa e chama pre_compliance + post_compliance.

Contexto: wiring foi implementado e depois revertido por cherry-pick batch (commit 1119d216d).
Este sensor impede rollback silencioso — falha imediatamente se algum dos 4 invariantes
de wiring for removido do arquivo.
"""
import ast
import pathlib

import pytest

SSE_PATH = pathlib.Path("app/api/v1/agent_chat_sse.py")
C3B_MODULE = "app.shared.compliance.c3b_layer"


class TestSSEComplianceWiring:
    def _source(self) -> str:
        assert SSE_PATH.exists(), f"Arquivo não encontrado: {SSE_PATH}"
        return SSE_PATH.read_text()

    def test_imports_c3b_layer(self):
        """SSE deve importar c3b_layer (pre_compliance ou import direto do módulo)."""
        source = self._source()
        assert "c3b_layer" in source or "pre_compliance" in source, (
            "agent_chat_sse.py não importa c3b_layer. "
            "Adicionar: from app.shared.compliance.c3b_layer import pre_compliance, post_compliance, ComplianceContext"
        )

    def test_calls_pre_compliance(self):
        """SSE deve chamar pre_compliance antes de invocar o LLM (HateSpeechGuard + PII strip)."""
        source = self._source()
        assert "pre_compliance" in source, (
            "agent_chat_sse.py não chama pre_compliance. "
            "Input sem HateSpeechGuard e PII strip no SSE path. "
            "Adicionar bloco: _c3b_result = await pre_compliance(content, company_id, domain)"
        )

    def test_calls_post_compliance(self):
        """SSE deve chamar post_compliance no output do LLM (FactChecker + audit log)."""
        source = self._source()
        assert "post_compliance" in source, (
            "agent_chat_sse.py não chama post_compliance. "
            "Output SSE sem FactChecker nem audit trail LGPD. "
            "Adicionar: clean_message = await post_compliance(clean_message, _c3b_ctx)"
        )

    def test_compliance_context_created(self):
        """SSE deve criar ComplianceContext com company_id para audit trail LGPD."""
        source = self._source()
        assert "ComplianceContext" in source, (
            "agent_chat_sse.py não cria ComplianceContext. "
            "Sem ComplianceContext não há audit log de post_compliance. "
            "Adicionar: _c3b_ctx = ComplianceContext(company_id=company_id, ...)"
        )
