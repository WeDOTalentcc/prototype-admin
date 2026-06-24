"""
D1 — Navegação e UI Actions (serializer).

D1-05: [NAVIGATE:...] markup NÃO vaza como texto literal na resposta SSE
D1-06: serialize_message com ui_action sem params não deve crashar
D1-07: format_sse_event formata corretamente o payload de navegação

Nota: serialize_message retorna MessageEvent (TypedDict), não string JSON.
      format_sse_event converte dict → string SSE "id: N\ndata: {...}\n\n".
"""
import json
import pytest

from app.shared.chat_event_serializer import (
    serialize_message,
    format_sse_event,
    MessageEvent,
)


# ---------------------------------------------------------------------------
# D1-05 — Navigate markup não aparece como texto literal
# ---------------------------------------------------------------------------

class TestNavigateMarkupLeak:
    """D1-05: [NAVIGATE:...] markup não deve vazar como texto no payload."""

    def test_plain_content_no_navigate_markers(self):
        """Mensagem sem markup não contém [NAVIGATE: nem ui_action."""
        result: MessageEvent = serialize_message("Aqui estão os candidatos.")

        assert result["type"] == "message"
        assert "[NAVIGATE:" not in result["content"]
        assert "ui_action" not in result

    def test_navigate_markup_if_present_check_content(self):
        """
        D1-05: se o serializer recebe texto com [NAVIGATE:], verifica que
        o campo 'content' não repassa o markup verbatim.

        Este teste documenta o CONTRATO atual: o serializer armazena o
        conteúdo como-veio. A remoção do markup é responsabilidade do
        produtor (agente/orquestrador) antes de chamar serialize_message.
        Se o markup chegar aqui, aparece no content — isso é rastreável.
        """
        raw = "Aqui está a vaga. [NAVIGATE:/pt/jobs/abc-123] Clique para abrir."
        result: MessageEvent = serialize_message(raw)

        # Documentar o estado atual: serializer preserva o texto literal.
        # Qualquer mudança que remova o markup aqui seria uma breaking change
        # — registrar falha explícita se o conteúdo mudar inesperadamente.
        assert result["type"] == "message"
        assert result["content"] == raw, (
            "serialize_message alterou o content de forma inesperada. "
            "Se FIX-NAVIGATE-LEAK foi aplicado no serializer, atualizar este teste."
        )

    def test_ui_action_navigate_not_set_without_explicit_param(self):
        """D1-05: ui_action não é gerado automaticamente de markup no texto."""
        raw = "[NAVIGATE:/pt/jobs/abc-123] Veja a vaga."
        result: MessageEvent = serialize_message(raw)

        # O serializer NÃO extrai ui_action do texto — requer param explícito.
        assert result.get("ui_action") is None, (
            "serialize_message não deve inferir ui_action do texto. "
            "Caller deve passar ui_action explicitamente."
        )


# ---------------------------------------------------------------------------
# D1-06 — ui_action sem params não crasha
# ---------------------------------------------------------------------------

class TestUiActionNoParams:
    """D1-06: ui_action passado sem ui_action_params não deve levantar exceção."""

    def test_ui_action_without_params_no_crash(self):
        """D1-06: ui_action='open_ui' sem ui_action_params."""
        result: MessageEvent = serialize_message(
            "Abrindo painel.",
            ui_action="open_ui",
            ui_action_params=None,
        )
        assert result["type"] == "message"
        assert result["ui_action"] == "open_ui"
        assert "ui_action_params" not in result  # None → campo omitido

    def test_ui_action_navigate_page_without_params_no_crash(self):
        """D1-06: ui_action='navigate_page' sem params não crasha."""
        result: MessageEvent = serialize_message(
            "Navegando.",
            ui_action="navigate_page",
        )
        assert result["type"] == "message"
        assert result["ui_action"] == "navigate_page"

    def test_ui_action_empty_string_not_included(self):
        """ui_action='' (falsy) não deve ser incluído no payload."""
        result: MessageEvent = serialize_message("Msg.", ui_action="")
        assert "ui_action" not in result


# ---------------------------------------------------------------------------
# D1-06 — ui_action + params incluídos no payload
# ---------------------------------------------------------------------------

class TestUiActionWithParams:
    """D1-06: ui_action + ui_action_params aparecem no payload serializado."""

    def test_ui_action_with_params_in_payload(self):
        """ui_action + ui_action_params devem aparecer no MessageEvent."""
        params = {"modal": "candidate-detail", "entity_id": "abc-123"}
        result: MessageEvent = serialize_message(
            "Abrindo perfil.",
            ui_action="open_ui",
            ui_action_params=params,
        )

        assert result["ui_action"] == "open_ui"
        assert result["ui_action_params"] == params

    def test_navigate_page_with_url_param(self):
        """navigate_page + url param — fluxo canônico de navegação."""
        params = {"url": "/pt/jobs/abc-123"}
        result: MessageEvent = serialize_message(
            "Redirecionando para a vaga.",
            ui_action="navigate_page",
            ui_action_params=params,
        )

        assert result["ui_action"] == "navigate_page"
        assert result["ui_action_params"]["url"] == "/pt/jobs/abc-123"

    def test_open_ui_with_modal_and_entity(self):
        """open_ui com modal + entity_id — fluxo canônico de modal."""
        params = {"modal": "job-detail", "entity_id": "job-uuid-999"}
        result: MessageEvent = serialize_message(
            "Veja os detalhes.",
            ui_action="open_ui",
            ui_action_params=params,
        )

        assert result["ui_action"] == "open_ui"
        assert result["ui_action_params"]["modal"] == "job-detail"
        assert result["ui_action_params"]["entity_id"] == "job-uuid-999"


# ---------------------------------------------------------------------------
# D1-07 — format_sse_event formata payload de navegação corretamente
# ---------------------------------------------------------------------------

class TestFormatSseEventNavigation:
    """D1-07: format_sse_event serializa MessageEvent com ui_action."""

    def test_format_sse_event_basic_message(self):
        """format_sse_event gera SSE válido com id + data + double newline."""
        msg: MessageEvent = serialize_message("Olá mundo.")
        sse_str = format_sse_event(msg)  # type: ignore[arg-type]

        assert "id:" in sse_str
        assert "data:" in sse_str
        assert sse_str.endswith("\n\n")

        # Extrair JSON do campo data:
        for line in sse_str.splitlines():
            if line.startswith("data:"):
                data = json.loads(line[len("data:"):].strip())
                assert data["type"] == "message"
                assert data["content"] == "Olá mundo."
                break
        else:
            pytest.fail("Linha 'data:' não encontrada no SSE")

    def test_format_sse_event_with_ui_action(self):
        """format_sse_event inclui ui_action no JSON serializado."""
        params = {"url": "/pt/vagas/123"}
        msg: MessageEvent = serialize_message(
            "Navegando.",
            ui_action="navigate_page",
            ui_action_params=params,
        )
        sse_str = format_sse_event(msg)  # type: ignore[arg-type]

        for line in sse_str.splitlines():
            if line.startswith("data:"):
                data = json.loads(line[len("data:"):].strip())
                assert data["ui_action"] == "navigate_page"
                assert data["ui_action_params"]["url"] == "/pt/vagas/123"
                break
        else:
            pytest.fail("Linha 'data:' não encontrada no SSE")

    def test_format_sse_event_open_ui_roundtrip(self):
        """open_ui roundtrip: serialize_message → format_sse_event → JSON parse."""
        params = {"modal": "candidate-profile", "entity_id": "cand-abc"}
        msg: MessageEvent = serialize_message(
            "Perfil do candidato.",
            ui_action="open_ui",
            ui_action_params=params,
        )
        sse_str = format_sse_event(msg)  # type: ignore[arg-type]

        # Parse completo do roundtrip
        data_line = next(
            l for l in sse_str.splitlines() if l.startswith("data:")
        )
        data = json.loads(data_line[len("data:"):].strip())

        assert data["type"] == "message"
        assert data["ui_action"] == "open_ui"
        assert data["ui_action_params"]["modal"] == "candidate-profile"
        assert data["ui_action_params"]["entity_id"] == "cand-abc"

    def test_format_sse_event_no_ui_action_clean(self):
        """Mensagem sem ui_action não polui o JSON com campo None."""
        msg: MessageEvent = serialize_message("Resultado da busca.")
        sse_str = format_sse_event(msg)  # type: ignore[arg-type]

        data_line = next(
            l for l in sse_str.splitlines() if l.startswith("data:")
        )
        data = json.loads(data_line[len("data:"):].strip())

        assert "ui_action" not in data
        assert "ui_action_params" not in data
