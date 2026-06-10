"""Sensor anti-regressão (computacional) Fase 1 Step 5 (ADR-LGPD-002 resolve-then-strip).

Garante que o caminho SSE federado/supervisor resolve entidades sobre o conteúdo CRU
(_raw_content) ANTES do strip — senão o match por identificador (CPF/email/telefone)
quebra silenciosamente (o resolver receberia '[CPF REMOVIDO]'). Sensor de fonte: barato,
falha em <1s, mensagem auto-explicativa pro LLM consumidor."""
import os
import re

os.environ.setdefault("IS_DEVELOPMENT", "true")

_SSE = os.path.join(
    os.path.dirname(__file__), "..", "..", "app", "api", "v1", "agent_chat_sse.py"
)


def _read_sse():
    with open(os.path.abspath(_SSE)) as f:
        return f.read()


def test_resolve_named_entities_uses_raw_content_not_stripped():
    """resolve_named_entities DEVE ser chamado com _raw_content (resolve-then-strip).

    Se este teste falhar: alguém reverteu o order fix. O resolver precisa do texto CRU
    (com CPF/email/telefone) para casar candidato por identificador. Fix: passar
    _raw_content (não `content`, que já foi stripado por strip_pii_for_llm_prompt)."""
    src = _read_sse()
    m = re.search(r"resolve_named_entities\(\s*([A-Za-z_][A-Za-z0-9_]*)", src)
    assert m is not None, "Chamada resolve_named_entities(...) não encontrada em agent_chat_sse.py"
    first_arg = m.group(1)
    assert first_arg == "_raw_content", (
        f"resolve_named_entities recebe '{first_arg}', esperado '_raw_content'. "
        "resolve-then-strip quebrado: o resolver receberia conteúdo já mascarado e não "
        "casaria candidato por CPF/email/telefone. Passe _raw_content."
    )


def test_raw_content_captured_before_strip():
    """_raw_content deve ser capturado ANTES do strip_pii_for_llm_prompt."""
    src = _read_sse()
    idx_raw = src.find("_raw_content = content")
    idx_strip = src.find("strip_pii_for_llm_prompt(content")
    assert idx_raw != -1, "_raw_content = content não encontrado (captura do cru)"
    assert idx_strip != -1, "strip_pii_for_llm_prompt(content...) não encontrado"
    assert idx_raw < idx_strip, "_raw_content deve ser capturado ANTES do strip"
