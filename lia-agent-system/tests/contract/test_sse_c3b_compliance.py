"""Contract sensor FIX-C3B-SSE (Fase 0): o caminho SSE DEVE chamar post_compliance
(FactChecker + audit log LGPD) na saida — paridade com o WS. Guard de regressao."""
from pathlib import Path


def test_sse_wires_post_compliance():
    src = Path(__file__).resolve().parents[2] / "app" / "api" / "v1" / "agent_chat_sse.py"
    text = src.read_text(encoding="utf-8")
    assert "ComplianceContext" in text, "SSE deve importar ComplianceContext (C3B)"
    assert "await post_compliance(" in text, "SSE deve AWAIT post_compliance na saida (FactChecker+audit)"
