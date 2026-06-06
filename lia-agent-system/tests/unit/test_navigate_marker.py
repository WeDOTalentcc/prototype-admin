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
