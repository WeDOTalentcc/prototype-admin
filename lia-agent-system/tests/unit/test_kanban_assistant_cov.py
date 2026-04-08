"""
Coverage tests for app/domains/recruiter_assistant/services/kanban_assistant_service.py
"""
import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def service():
    with patch.dict("os.environ", {
        "AI_INTEGRATIONS_ANTHROPIC_API_KEY": "test-key",
        "AI_INTEGRATIONS_ANTHROPIC_BASE_URL": "https://test.api",
    }):
        with patch("app.domains.recruiter_assistant.services.kanban_assistant_service.Anthropic"):
            from app.domains.recruiter_assistant.services.kanban_assistant_service import KanbanAssistantService
            svc = KanbanAssistantService()
            svc._client = MagicMock()
            yield svc


class TestParseJsonResponse:
    @pytest.mark.easy
    def test_plain_json(self, service):
        assert service._parse_json_response('{"k": "v"}') == {"k": "v"}

    @pytest.mark.easy
    def test_code_block_json(self, service):
        assert service._parse_json_response('```json\n{"k": "v"}\n```') == {"k": "v"}

    @pytest.mark.easy
    def test_trailing_comma(self, service):
        assert service._parse_json_response('{"k": "v",}') == {"k": "v"}

    @pytest.mark.easy
    def test_not_json(self, service):
        assert service._parse_json_response("hello")["resposta"] == "hello"

    @pytest.mark.easy
    def test_embedded_json(self, service):
        assert service._parse_json_response('text {"x": 1} end') == {"x": 1}


class TestFormatMarkdownRouting:
    @pytest.mark.easy
    def test_ranking(self, service):
        data = {"ranking": [{"posicao": 1, "candidato_nome": "Ana", "score_fit": 90, "principais_forcas": ["Python"], "justificativa": "Good"}]}
        assert "Ana" in service._format_markdown_response("rankear_candidatos", data)

    @pytest.mark.easy
    def test_performance(self, service):
        data = {"metricas_gerais": {"total": 10}, "desempenho_por_etapa": [{"etapa": "Triagem"}]}
        result = service._format_markdown_response("performance_funil", data)
        assert "Funil" in result or "Performance" in result

    @pytest.mark.easy
    def test_gargalos(self, service):
        data = {"gargalos_identificados": [{"etapa": "X", "severidade": "alta", "problema": "Lento", "impacto": "Bad", "sugestao": "Fix"}]}
        result = service._format_markdown_response("gargalos_processo", data)
        assert "Gargalo" in result

    @pytest.mark.easy
    def test_comparacao(self, service):
        data = {"comparacao": [{"candidato_nome": "Ana", "score_geral": 80, "match_tecnico": 85, "match_cultural": 75, "pontos_fortes": ["Exp"], "diferencial": "Expert"}]}
        assert "Ana" in service._format_markdown_response("comparar_candidatos", data)

    @pytest.mark.easy
    def test_resumo(self, service):
        data = {"resumo_executivo": {"candidato": "Ana"}}
        result = service._format_markdown_response("resumir_perfil", data)
        assert "Resumo" in result

    @pytest.mark.easy
    def test_ativos(self, service):
        data = {"visao_geral": {"total_candidatos": 5, "candidatos_ativos": 3, "candidatos_finalizados": 2}, "distribuicao_etapas": [], "alertas": [{"tipo": "warning", "mensagem": "Check"}]}
        result = service._format_markdown_response("candidatos_ativos", data)
        assert "5" in result

    @pytest.mark.easy
    def test_conversao(self, service):
        data = {"conversao_geral": {"inicio_fim": "30%"}, "conversao_por_etapa": [{"de_etapa": "A", "para_etapa": "B", "taxa": "50%", "benchmark": "40%", "aprovados": 5, "reprovados": 5}]}
        result = service._format_markdown_response("taxa_conversao", data)
        assert "Conversão" in result

    @pytest.mark.easy
    def test_tempo(self, service):
        data = {"time_to_hire": {"atual": "10 dias", "estimado": "15 dias", "benchmark": "12 dias"}, "tempo_por_etapa": [{"etapa": "Triagem", "tempo_medio": "3d", "benchmark": "2d", "status": "ok"}]}
        result = service._format_markdown_response("tempo_medio", data)
        assert "Tempo" in result

    @pytest.mark.easy
    def test_parados(self, service):
        data = {"resumo": {"total_parados": 2}, "candidatos_parados": [{"candidato_nome": "Ana", "etapa_atual": "Triagem", "dias_parado": 10, "risco": "alto", "motivo_provavel": "Waiting"}]}
        result = service._format_markdown_response("candidatos_parados", data)
        assert "Parado" in result

    @pytest.mark.easy
    def test_top(self, service):
        data = {"top_candidatos": [{"posicao": 1, "candidato_nome": "Ana", "score_geral": 90, "destaques": ["Expert"], "recomendacao": "Avançar"}]}
        result = service._format_markdown_response("top_candidatos", data)
        assert "Top" in result

    @pytest.mark.easy
    def test_mover(self, service):
        data = {"movimentacao": {"candidato": "Ana", "etapa_atual": "Triagem", "etapa_destino": "Entrevista"}, "validacao": {}, "acoes_automaticas": []}
        result = service._format_markdown_response("mover_candidato", data)
        assert "Mover" in result or "Movimentação" in result

    @pytest.mark.easy
    def test_email(self, service):
        data = {"email_proposto": {"destinatario": "Ana", "assunto": "Parabéns", "tipo": "aprovacao"}}
        result = service._format_markdown_response("enviar_email", data)
        assert "Email" in result or "📧" in result

    @pytest.mark.easy
    def test_triagem(self, service):
        data = {"triagem": {"candidatos_selecionados": [{"nome": "Ana"}]}}
        result = service._format_markdown_response("disparar_triagem", data)
        assert "Triagem" in result

    @pytest.mark.easy
    def test_entrevista(self, service):
        data = {"agendamento": {"candidato": "Ana", "data": "2025-01-15"}}
        result = service._format_markdown_response("agendar_entrevista", data)
        assert "Entrevista" in result

    @pytest.mark.easy
    def test_solicitar_dados(self, service):
        data = {"solicitacao": {"candidato": "Ana", "dados_pendentes": ["CPF"]}}
        result = service._format_markdown_response("solicitar_dados", data)
        assert "Dados" in result or "Solicita" in result

    @pytest.mark.easy
    def test_analisar_perfil(self, service):
        data = {"analise": {"candidato": "Ana", "score_geral": 85}}
        result = service._format_markdown_response("analisar_perfil", data)
        assert "Perfil" in result or "Análise" in result

    @pytest.mark.easy
    def test_aprovar(self, service):
        data = {"aprovacao": {"candidato": "Ana", "decisao": "aprovado"}}
        result = service._format_markdown_response("aprovar_candidato", data)
        assert "Aprovar" in result or "Aprovação" in result

    @pytest.mark.easy
    def test_geral_fallback(self, service):
        data = {"resposta": "General analysis"}
        result = service._format_markdown_response("unknown_type", data)
        assert len(result) > 0


class TestExtractActions:
    @pytest.mark.easy
    def test_with_actions(self, service):
        data = {"recomendacoes": ["A", "B"], "plano_acao": ["C"], "proximos_passos": ["D"]}
        result = service._extract_actions(data)
        assert "A" in result and "C" in result

    @pytest.mark.easy
    def test_no_actions(self, service):
        assert service._extract_actions({}) == []


class TestClientProperty:
    @pytest.mark.easy
    def test_unconfigured_raises(self):
        with patch("app.domains.recruiter_assistant.services.kanban_assistant_service.AI_INTEGRATIONS_ANTHROPIC_API_KEY", None), \
             patch("app.domains.recruiter_assistant.services.kanban_assistant_service.AI_INTEGRATIONS_ANTHROPIC_BASE_URL", None):
            from app.domains.recruiter_assistant.services.kanban_assistant_service import KanbanAssistantService
            svc = KanbanAssistantService()
            with pytest.raises(ValueError, match="not configured"):
                _ = svc.client
