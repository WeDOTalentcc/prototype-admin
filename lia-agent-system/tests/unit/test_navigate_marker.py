"""TDD FIX-NAVIGATE-LEAK (Fase 0): _extract_navigate_marker captura page + id
opcional e faz strip do marker. Reusado pelo orquestrador E pelo SSE (canonical)."""
from app.orchestrator.context.chat_adapter import _extract_navigate_marker


def test_navigate_page_only():
    out = _extract_navigate_marker("Te levando! [NAVIGATE:vagas]")
    assert out is not None
    clean, page, params = out
    assert "[NAVIGATE" not in clean
    assert page and page != "general"
    assert params == {}


def test_navigate_page_com_id_colon():
    out = _extract_navigate_marker(
        "Abrindo [NAVIGATE:vaga_detalhe:def48ec0-a955-54d2-acdc-7b34fe192441]"
    )
    assert out is not None
    clean, page, params = out
    assert "[NAVIGATE" not in clean
    assert params.get("id") == "def48ec0-a955-54d2-acdc-7b34fe192441"


def test_navigate_page_com_id_query():
    out = _extract_navigate_marker("Indo [NAVIGATE:vaga_detalhe?id=abc-123]")
    assert out is not None
    _, _, params = out
    assert params.get("id") == "abc-123"


def test_navigate_sem_marker():
    assert _extract_navigate_marker("Ola, como posso ajudar?") is None


def test_navigate_strip_deixa_texto_limpo():
    out = _extract_navigate_marker("Te levando para Vagas! [NAVIGATE:vagas]")
    assert out is not None
    assert out[0].strip() == "Te levando para Vagas!"


def test_navigate_query_section_only():
    """Fase C: deep-link de secao (settings) -> params.query, sem id."""
    out = _extract_navigate_marker("Abrindo [NAVIGATE:configuracoes?section=beneficios]")
    assert out is not None
    _, page, params = out
    assert page == "configuracoes"
    assert "id" not in params
    assert params.get("query") == {"section": "beneficios"}


def test_navigate_id_colon_plus_query():
    """Fase C: vaga especifica + aba/secao -> id + query."""
    out = _extract_navigate_marker(
        "Editando [NAVIGATE:vaga_detalhe:abc-123?tab=edit&section=descricao]"
    )
    assert out is not None
    _, page, params = out
    assert page == "vaga_detalhe"
    assert params.get("id") == "abc-123"
    assert params.get("query") == {"tab": "edit", "section": "descricao"}


def test_navigate_legacy_id_query_still_works():
    """Forma legada ?id= continua mapeando p/ id (sem virar query)."""
    out = _extract_navigate_marker("Indo [NAVIGATE:vaga_detalhe?id=xyz-9]")
    assert out is not None
    _, _, params = out
    assert params.get("id") == "xyz-9"
    assert "query" not in params
