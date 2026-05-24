"""
LIA Kanban Assistant Service - AI-powered analysis for recruitment pipelines.
Uses LLMProviderFactory for all LLM calls (Task #93 migration).
"""
import json
import logging
from typing import Any

from tenacity import retry, stop_after_attempt, wait_exponential

from app.domains.recruiter_assistant.prompts.kanban_assistant_prompts import (
    KanbanCommandType,
    build_full_prompt,
    detect_command_type,
    get_kanban_prompt_template,
    get_system_prompt,
    resolve_ui_action,
)
from app.shared.providers.llm_factory import get_provider_for_tenant

# Compatibility alias — tests patch this attribute to isolate LLM calls.
# The service uses LLMProviderFactory internally (Task #93), but older tests
# reference the Anthropic SDK class directly via patch(module.Anthropic).
try:
    from anthropic import Anthropic  # noqa: F401  # W3-027-EXEMPT: compat alias for test patching (noqa F401) — production LLM via LLMProviderFactory
except ImportError:  # pragma: no cover
    Anthropic = None  # type: ignore[assignment,misc]

import os as _os
# Module-level env vars (patchable by tests)
AI_INTEGRATIONS_ANTHROPIC_API_KEY: str | None = _os.getenv("AI_INTEGRATIONS_ANTHROPIC_API_KEY")
AI_INTEGRATIONS_ANTHROPIC_BASE_URL: str | None = _os.getenv("AI_INTEGRATIONS_ANTHROPIC_BASE_URL")

logger = logging.getLogger(__name__)


class KanbanAssistantService:
    """Service for AI-powered Kanban pipeline analysis via LLMProviderFactory."""

    @property
    def client(self) -> "Anthropic":
        """Return an Anthropic client, raising ValueError when unconfigured.

        Tests patch the module-level ``AI_INTEGRATIONS_ANTHROPIC_API_KEY`` /
        ``AI_INTEGRATIONS_ANTHROPIC_BASE_URL`` to simulate unconfigured state.
        """
        import sys as _sys
        _mod = _sys.modules[__name__]
        _api_key = getattr(_mod, "AI_INTEGRATIONS_ANTHROPIC_API_KEY", AI_INTEGRATIONS_ANTHROPIC_API_KEY)
        if not _api_key:
            raise ValueError("Anthropic client not configured — AI_INTEGRATIONS_ANTHROPIC_API_KEY is not set")
        _cls = getattr(_mod, "Anthropic", Anthropic)
        if _cls is None:  # pragma: no cover
            raise ValueError("anthropic package not installed")
        _base_url = getattr(_mod, "AI_INTEGRATIONS_ANTHROPIC_BASE_URL", AI_INTEGRATIONS_ANTHROPIC_BASE_URL)
        kwargs: dict = {"api_key": _api_key}
        if _base_url:
            kwargs["base_url"] = _base_url
        return _cls(**kwargs)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        reraise=True
    )
    async def process_command(
        self,
        command: str,
        command_type: str | None,
        job_context: dict[str, Any],
        candidates: list[dict[str, Any]],
        selected_candidate_ids: list[str] | None = None
    ) -> dict[str, Any]:
        """
        Process a Kanban assistant command.
        
        Args:
            command: User's natural language command
            command_type: Optional pre-detected command type
            job_context: Job vacancy context
            candidates: List of candidates in the pipeline
            selected_candidate_ids: IDs of selected candidates (for comparison)
            
        Returns:
            Dict with response content and metadata
        """
        detected_type, confidence = detect_command_type(command)
        final_type = command_type if command_type and command_type in [e.value for e in KanbanCommandType] else detected_type
        
        logger.info(f"Processing Kanban command - Type: {final_type} (confidence: {confidence:.2f})")
        
        template = get_kanban_prompt_template(final_type)
        
        full_prompt = build_full_prompt(
            command_type=final_type,
            user_query=command,
            job_data=job_context,
            candidates=candidates,
            selected_ids=selected_candidate_ids
        )
        
        try:
            container = get_provider_for_tenant()
            response_text = await container.generate_with_fallback(
                full_prompt, system=get_system_prompt(),
                agent_type="KanbanAssistantAgent",
            )
            
            structured_data = self._parse_json_response(response_text)
            markdown_content = self._format_markdown_response(final_type, structured_data)
            suggested_actions = self._extract_actions(structured_data)
            follow_up_prompts = template.get("follow_up_prompts", [])
            
            ui_action, ui_action_params = resolve_ui_action(final_type, structured_data, candidates)
            
            return {
                "success": True,
                "response_type": final_type,
                "content": markdown_content,
                "structured_data": structured_data,
                "suggested_actions": suggested_actions,
                "follow_up_prompts": follow_up_prompts,
                "confidence": confidence,
                "ui_action": ui_action,
                "ui_action_params": ui_action_params
            }
            
        except Exception as e:
            logger.error(f"Error processing Kanban command: {e}", exc_info=True)
            raise
    
    def _parse_json_response(self, response_text: str) -> dict[str, Any]:
        """Parse JSON from the AI response, handling markdown code blocks."""
        import re
        text = response_text.strip()
        code_block = re.search(r'```(?:json)?\s*(\{[\s\S]*\})\s*```', text)
        if code_block:
            text = code_block.group(1)

        json_start = text.find('{')
        json_end = text.rfind('}') + 1

        if json_start != -1 and json_end > json_start:
            try:
                return json.loads(text[json_start:json_end])
            except json.JSONDecodeError:
                try:
                    cleaned = re.sub(r',\s*}', '}', text[json_start:json_end])
                    cleaned = re.sub(r',\s*]', ']', cleaned)
                    return json.loads(cleaned)
                except json.JSONDecodeError:
                    pass

        return {"resposta": response_text}
    
    def _format_markdown_response(self, response_type: str, data: dict[str, Any]) -> str:
        """Format structured data as markdown for display."""
        
        if response_type == KanbanCommandType.RANKEAR_CANDIDATOS.value:
            return self._format_ranking_markdown(data)
        elif response_type == KanbanCommandType.PERFORMANCE_FUNIL.value:
            return self._format_performance_markdown(data)
        elif response_type == KanbanCommandType.GARGALOS_PROCESSO.value:
            return self._format_gargalos_markdown(data)
        elif response_type == KanbanCommandType.COMPARAR_CANDIDATOS.value:
            return self._format_comparacao_markdown(data)
        elif response_type == KanbanCommandType.RESUMIR_PERFIL.value:
            return self._format_resumo_markdown(data)
        elif response_type == KanbanCommandType.CANDIDATOS_ATIVOS.value:
            return self._format_ativos_markdown(data)
        elif response_type == KanbanCommandType.TAXA_CONVERSAO.value:
            return self._format_conversao_markdown(data)
        elif response_type == KanbanCommandType.TEMPO_MEDIO.value:
            return self._format_tempo_markdown(data)
        elif response_type == KanbanCommandType.CANDIDATOS_PARADOS.value:
            return self._format_parados_markdown(data)
        elif response_type == KanbanCommandType.TOP_CANDIDATOS.value:
            return self._format_top_markdown(data)
        elif response_type == KanbanCommandType.MOVER_CANDIDATO.value:
            return self._format_mover_markdown(data)
        elif response_type == KanbanCommandType.ENVIAR_EMAIL.value:
            return self._format_email_markdown(data)
        elif response_type == KanbanCommandType.DISPARAR_TRIAGEM.value:
            return self._format_triagem_markdown(data)
        elif response_type == KanbanCommandType.AGENDAR_ENTREVISTA.value:
            return self._format_entrevista_markdown(data)
        elif response_type == KanbanCommandType.SOLICITAR_DADOS.value:
            return self._format_solicitar_dados_markdown(data)
        elif response_type == KanbanCommandType.ANALISAR_PERFIL.value:
            return self._format_analisar_perfil_markdown(data)
        elif response_type == KanbanCommandType.APROVAR_CANDIDATO.value:
            return self._format_aprovar_markdown(data)
        else:
            return self._format_geral_markdown(data)
    
    def _format_ranking_markdown(self, data: dict) -> str:
        lines = ["## 🏆 Ranking de Candidatos\n"]
        
        ranking = data.get("ranking", [])
        for item in ranking[:10]:
            medal = "🥇" if item.get("posicao") == 1 else "🥈" if item.get("posicao") == 2 else "🥉" if item.get("posicao") == 3 else f"#{item.get('posicao', '?')}"
            lines.append(f"### {medal} {item.get('candidato_nome', 'N/A')}")
            lines.append(f"**Score de Fit:** {item.get('score_fit', 'N/A')}%")
            lines.append(f"\n**Forças:** {', '.join(item.get('principais_forcas', []))}")
            if item.get('principais_gaps'):
                lines.append(f"\n**Gaps:** {', '.join(item.get('principais_gaps', []))}")
            lines.append(f"\n> {item.get('justificativa', '')}\n")
        
        if data.get("insights"):
            lines.append(f"---\n### 💡 Insights\n{data['insights']}\n")
        
        if data.get("recomendacao"):
            lines.append(f"### ✅ Recomendação\n{data['recomendacao']}")
        
        return "\n".join(lines)
    
    def _format_performance_markdown(self, data: dict) -> str:
        lines = ["## 📊 Performance do Funil\n"]
        
        metricas = data.get("metricas", {})
        lines.append(f"**Total de Candidatos:** {metricas.get('total_candidatos', 'N/A')}")
        lines.append(f"\n**Taxa de Conversão Geral:** {metricas.get('taxa_conversao_geral', 'N/A')}%\n")
        
        por_etapa = metricas.get("por_etapa", {})
        if por_etapa:
            lines.append("### Distribuição por Etapa")
            for etapa, qtd in por_etapa.items():
                lines.append(f"- {etapa}: {qtd} candidatos")
        
        perf = data.get("performance", {})
        status_emoji = {"saudável": "✅", "atenção": "⚠️", "crítico": "🚨"}.get(perf.get("status", ""), "ℹ️")
        lines.append(f"\n### {status_emoji} Status: {perf.get('status', 'N/A')}")
        
        if perf.get("pontos_fortes"):
            lines.append("\n**Pontos Fortes:**")
            for p in perf["pontos_fortes"]:
                lines.append(f"- ✅ {p}")
        
        if perf.get("pontos_atencao"):
            lines.append("\n**Pontos de Atenção:**")
            for p in perf["pontos_atencao"]:
                lines.append(f"- ⚠️ {p}")
        
        if data.get("recomendacoes"):
            lines.append("\n### 🎯 Recomendações")
            for r in data["recomendacoes"]:
                lines.append(f"- {r}")
        
        return "\n".join(lines)
    
    def _format_gargalos_markdown(self, data: dict) -> str:
        lines = ["## 🚧 Gargalos do Processo\n"]
        
        gargalos = data.get("gargalos", [])
        for g in gargalos:
            sev_emoji = {"alta": "🔴", "média": "🟡", "baixa": "🟢"}.get(g.get("severidade", ""), "⚪")
            lines.append(f"### {sev_emoji} {g.get('etapa', 'N/A')}")
            lines.append(f"**Candidatos impactados:** {g.get('candidatos_impactados', 'N/A')}")
            lines.append(f"\n**Tempo médio parado:** {g.get('tempo_medio_parado', 'N/A')}")
            lines.append(f"\n**Causa provável:** {g.get('causa_provavel', 'N/A')}")
            lines.append(f"\n**Ação sugerida:** {g.get('acao_sugerida', 'N/A')}\n")
        
        criticos = data.get("candidatos_criticos", [])
        if criticos:
            lines.append("### ⚠️ Candidatos Críticos")
            for c in criticos:
                lines.append(f"- **{c.get('nome', 'N/A')}** - {c.get('dias_parado', '?')} dias na etapa {c.get('etapa_atual', '?')}")
                lines.append(f"  - Ação: {c.get('acao_urgente', 'N/A')}")
        
        if data.get("plano_acao"):
            lines.append("\n### 🎯 Plano de Ação")
            for i, a in enumerate(data["plano_acao"], 1):
                lines.append(f"{i}. {a}")
        
        return "\n".join(lines)
    
    def _format_comparacao_markdown(self, data: dict) -> str:
        lines = ["## ⚖️ Comparação de Candidatos\n"]
        
        comparacao = data.get("comparacao", [])
        for c in comparacao:
            lines.append(f"### {c.get('candidato_nome', 'N/A')}")
            lines.append(f"**Score Geral:** {c.get('score_geral', 'N/A')}% | **Técnico:** {c.get('match_tecnico', 'N/A')}% | **Cultural:** {c.get('match_cultural', 'N/A')}%")
            lines.append(f"\n**Pontos Fortes:** {', '.join(c.get('pontos_fortes', []))}")
            if c.get('pontos_fracos'):
                lines.append(f"\n**Pontos a Desenvolver:** {', '.join(c.get('pontos_fracos', []))}")
            lines.append(f"\n**Diferencial:** {c.get('diferencial', 'N/A')}\n")
        
        analise = data.get("analise_comparativa", {})
        if analise:
            lines.append("### 📊 Análise Comparativa")
            if analise.get("melhor_fit_tecnico"):
                lines.append(f"- 🔧 **Melhor Fit Técnico:** {analise['melhor_fit_tecnico'].get('motivo', 'N/A')}")
            if analise.get("melhor_fit_cultural"):
                lines.append(f"- 🎭 **Melhor Fit Cultural:** {analise['melhor_fit_cultural'].get('motivo', 'N/A')}")
        
        rec = data.get("recomendacao_final", {})
        if rec:
            lines.append("\n### ✅ Recomendação Final")
            lines.append(f"**Candidato Recomendado:** {rec.get('candidato_recomendado', 'N/A')}")
            lines.append(f"\n{rec.get('justificativa', '')}")
        
        return "\n".join(lines)
    
    def _format_resumo_markdown(self, data: dict) -> str:
        lines = ["## 📋 Resumo Executivo\n"]
        
        resumo = data.get("resumo_executivo", {})
        lines.append(f"### {resumo.get('candidato_nome', 'N/A')}")
        lines.append(f"*{resumo.get('headline', '')}*\n")
        lines.append(f"**Score de Fit:** {resumo.get('score_fit', 'N/A')}%")
        lines.append(f"\n**Recomendação:** {resumo.get('recomendacao', 'N/A')}\n")
        
        perfil = data.get("perfil_profissional", {})
        if perfil:
            lines.append("### 👤 Perfil Profissional")
            lines.append(f"- **Experiência:** {perfil.get('experiencia_total', 'N/A')}")
            lines.append(f"- **Nível:** {perfil.get('nivel_senioridade', 'N/A')}")
            lines.append(f"- **Especialização:** {perfil.get('especializacao', 'N/A')}")
            if perfil.get('skills_principais'):
                lines.append(f"- **Skills:** {', '.join(perfil['skills_principais'])}")
        
        fit = data.get("analise_fit", {})
        if fit:
            lines.append("\n### 🎯 Análise de Fit")
            lines.append(f"- Match Requisitos: {fit.get('match_requisitos', 'N/A')}%")
            lines.append(f"- Match Cultura: {fit.get('match_cultura', 'N/A')}%")
            if fit.get('principais_forcas'):
                lines.append(f"\n**Forças:** {', '.join(fit['principais_forcas'])}")
            if fit.get('principais_gaps'):
                lines.append(f"\n**Gaps:** {', '.join(fit['principais_gaps'])}")
        
        perguntas = data.get("perguntas_entrevista", [])
        if perguntas:
            lines.append("\n### ❓ Perguntas Sugeridas para Entrevista")
            for p in perguntas:
                lines.append(f"- {p}")
        
        return "\n".join(lines)
    
    def _format_ativos_markdown(self, data: dict) -> str:
        lines = ["## 👥 Candidatos Ativos\n"]
        
        visao = data.get("visao_geral", {})
        lines.append(f"**Total:** {visao.get('total_candidatos', 'N/A')} candidatos")
        lines.append(f"\n**Ativos:** {visao.get('candidatos_ativos', 'N/A')} | **Finalizados:** {visao.get('candidatos_finalizados', 'N/A')}\n")
        
        dist = data.get("distribuicao_etapas", [])
        if dist:
            lines.append("### 📊 Distribuição por Etapa")
            for d in dist:
                status_emoji = {"saudável": "✅", "atenção": "⚠️", "crítico": "🚨"}.get(d.get("status", ""), "ℹ️")
                lines.append(f"- {status_emoji} **{d.get('etapa', 'N/A')}:** {d.get('quantidade', 0)} ({d.get('percentual', 'N/A')})")
        
        alertas = data.get("alertas", [])
        if alertas:
            lines.append("\n### ⚠️ Alertas")
            for a in alertas:
                tipo_emoji = {"warning": "⚠️", "critical": "🚨", "info": "ℹ️"}.get(a.get("tipo", ""), "📌")
                lines.append(f"- {tipo_emoji} {a.get('mensagem', '')}")
        
        return "\n".join(lines)
    
    def _format_conversao_markdown(self, data: dict) -> str:
        lines = ["## 📈 Taxas de Conversão\n"]
        
        geral = data.get("conversao_geral", {})
        lines.append(f"**Conversão Geral (início ao fim):** {geral.get('inicio_fim', 'N/A')}")
        lines.append(f"\n**Benchmark de Mercado:** {geral.get('benchmark_mercado', 'N/A')}")
        lines.append(f"\n**Status:** {geral.get('status', 'N/A')}\n")
        
        por_etapa = data.get("conversao_por_etapa", [])
        if por_etapa:
            lines.append("### 📊 Conversão por Etapa")
            for e in por_etapa:
                lines.append(f"\n**{e.get('de_etapa', '?')} → {e.get('para_etapa', '?')}**")
                lines.append(f"- Taxa: {e.get('taxa', 'N/A')} (benchmark: {e.get('benchmark', 'N/A')})")
                lines.append(f"- Aprovados: {e.get('aprovados', 0)} | Reprovados: {e.get('reprovados', 0)}")
        
        criticas = data.get("etapas_criticas", [])
        if criticas:
            lines.append("\n### 🚨 Etapas Críticas")
            for c in criticas:
                lines.append(f"- **{c.get('etapa', 'N/A')}:** {c.get('problema', 'N/A')}")
                lines.append(f"  - Sugestão: {c.get('sugestao', 'N/A')}")
        
        return "\n".join(lines)
    
    def _format_tempo_markdown(self, data: dict) -> str:
        lines = ["## ⏱️ Análise de Tempo\n"]
        
        tth = data.get("time_to_hire", {})
        status_emoji = {"dentro do prazo": "✅", "atrasado": "🚨", "adiantado": "🎉"}.get(tth.get("status", ""), "ℹ️")
        lines.append(f"### Time-to-Hire {status_emoji}")
        lines.append(f"- **Atual:** {tth.get('atual', 'N/A')}")
        lines.append(f"- **Estimado:** {tth.get('estimado', 'N/A')}")
        lines.append(f"- **Benchmark:** {tth.get('benchmark', 'N/A')}\n")
        
        por_etapa = data.get("tempo_por_etapa", [])
        if por_etapa:
            lines.append("### ⏳ Tempo por Etapa")
            for e in por_etapa:
                status_emoji = {"ok": "✅", "atenção": "⚠️", "crítico": "🚨"}.get(e.get("status", ""), "ℹ️")
                lines.append(f"- {status_emoji} **{e.get('etapa', 'N/A')}:** {e.get('tempo_medio', 'N/A')} (benchmark: {e.get('benchmark', 'N/A')})")
        
        otimizacoes = data.get("otimizacoes", [])
        if otimizacoes:
            lines.append("\n### 🎯 Oportunidades de Otimização")
            for o in otimizacoes:
                prio_emoji = {"alta": "🔴", "média": "🟡", "baixa": "🟢"}.get(o.get("prioridade", ""), "⚪")
                lines.append(f"- {prio_emoji} {o.get('acao', 'N/A')} (economia: {o.get('economia_estimada', 'N/A')})")
        
        return "\n".join(lines)
    
    def _format_parados_markdown(self, data: dict) -> str:
        lines = ["## ⏸️ Candidatos Parados\n"]
        
        resumo = data.get("resumo", {})
        risco_emoji = {"alto": "🔴", "médio": "🟡", "baixo": "🟢"}.get(resumo.get("risco_perda", ""), "⚪")
        lines.append(f"**Total Parados:** {resumo.get('total_parados', 0)}")
        lines.append(f"\n**Críticos:** {resumo.get('criticos', 0)} | **Atenção:** {resumo.get('atencao', 0)}")
        lines.append(f"\n**Risco de Perda:** {risco_emoji} {resumo.get('risco_perda', 'N/A')}\n")
        
        parados = data.get("candidatos_parados", [])
        if parados:
            lines.append("### 📋 Lista de Candidatos")
            for p in parados:
                sev_emoji = {"crítico": "🔴", "atenção": "🟡", "ok": "🟢"}.get(p.get("severidade", ""), "⚪")
                lines.append(f"\n{sev_emoji} **{p.get('nome', 'N/A')}** - {p.get('dias_parado', '?')} dias")
                lines.append(f"- Etapa: {p.get('etapa_atual', 'N/A')}")
                lines.append(f"- Ação: {p.get('acao_sugerida', 'N/A')}")
        
        if data.get("plano_reativacao"):
            lines.append(f"\n### 🔄 Plano de Reativação\n{data['plano_reativacao']}")
        
        return "\n".join(lines)
    
    def _format_top_markdown(self, data: dict) -> str:
        lines = ["## 🌟 Top Candidatos\n"]
        
        top = data.get("top_candidatos", [])
        for c in top[:10]:
            medal = "🥇" if c.get("posicao") == 1 else "🥈" if c.get("posicao") == 2 else "🥉" if c.get("posicao") == 3 else f"#{c.get('posicao', '?')}"
            lines.append(f"### {medal} {c.get('nome', 'N/A')}")
            lines.append(f"**Score LIA:** {c.get('score_lia', 'N/A')} | **Fit:** {c.get('score_fit', 'N/A')}%")
            lines.append(f"\n**Etapa Atual:** {c.get('etapa_atual', 'N/A')}")
            lines.append(f"\n**Forças:** {', '.join(c.get('principais_forcas', []))}")
            lines.append(f"\n**Diferencial:** {c.get('diferencial', 'N/A')}")
            lines.append(f"\n**Próxima Ação:** {c.get('proxima_acao', 'N/A')}\n")
        
        pool = data.get("analise_pool", {})
        if pool:
            lines.append("### 📊 Análise do Pool")
            lines.append(f"- Qualidade Geral: {pool.get('qualidade_geral', 'N/A')}")
            lines.append(f"- Score Médio: {pool.get('score_medio', 'N/A')}")
            if pool.get("observacao"):
                lines.append(f"\n> {pool['observacao']}")
        
        return "\n".join(lines)
    
    def _format_mover_markdown(self, data: dict) -> str:
        lines = ["## 🔄 Movimentação de Candidatos\n"]
        
        if data.get("resposta"):
            lines.append(data["resposta"])
            lines.append("")
        
        candidatos = data.get("candidatos_sugeridos", [])
        if candidatos:
            lines.append("### 👥 Candidatos Sugeridos\n")
            for c in candidatos:
                lines.append(f"**{c.get('nome', 'N/A')}**")
                lines.append(f"- Etapa atual: {c.get('etapa_atual', 'N/A')}")
                if c.get('etapas_possiveis'):
                    lines.append(f"- Próximas etapas possíveis: {', '.join(c['etapas_possiveis'])}")
                if c.get('recomendacao'):
                    lines.append(f"- 💡 {c['recomendacao']}")
                lines.append("")
        
        etapas = data.get("etapas_disponiveis", [])
        if etapas:
            lines.append("### 📋 Etapas Disponíveis")
            for e in etapas:
                lines.append(f"- {e}")
            lines.append("")
        
        if data.get("instrucoes"):
            lines.append(f"### ℹ️ Como Proceder\n{data['instrucoes']}")
        
        return "\n".join(lines)
    
    def _format_email_markdown(self, data: dict) -> str:
        lines = ["## 📧 Envio de Email\n"]
        
        if data.get("resposta"):
            lines.append(data["resposta"])
            lines.append("")
        
        candidatos = data.get("candidatos_alvo", [])
        if candidatos:
            lines.append("### 👥 Candidatos Destinatários\n")
            for c in candidatos:
                lines.append(f"**{c.get('nome', 'N/A')}**")
                if c.get('email'):
                    lines.append(f"- Email: {c['email']}")
                lines.append(f"- Etapa atual: {c.get('etapa_atual', 'N/A')}")
                lines.append("")
        
        if data.get("sugestao_assunto"):
            lines.append(f"### 📝 Assunto Sugerido\n{data['sugestao_assunto']}\n")
        
        if data.get("sugestao_conteudo"):
            lines.append(f"### 💬 Conteúdo Sugerido\n{data['sugestao_conteudo']}")
        
        return "\n".join(lines)
    
    def _format_triagem_markdown(self, data: dict) -> str:
        lines = ["## 🔍 Triagem de Candidatos\n"]
        
        if data.get("resposta"):
            lines.append(data["resposta"])
            lines.append("")
        
        candidatos = data.get("candidatos_alvo", [])
        if candidatos:
            lines.append("### 👥 Candidatos para Triagem\n")
            for c in candidatos:
                lines.append(f"**{c.get('nome', 'N/A')}**")
                lines.append(f"- Etapa atual: {c.get('etapa_atual', 'N/A')}")
                if c.get('score'):
                    lines.append(f"- Score: {c['score']}")
                lines.append("")
        
        if data.get("tipo_triagem"):
            tipo_label = {"wsi_text": "WSI Text", "curricular": "Curricular"}.get(data["tipo_triagem"], data["tipo_triagem"])
            lines.append(f"### 📋 Tipo de Triagem: {tipo_label}\n")
        
        if data.get("recomendacao"):
            lines.append(f"### 💡 Recomendação\n{data['recomendacao']}")
        
        return "\n".join(lines)
    
    def _format_entrevista_markdown(self, data: dict) -> str:
        lines = ["## 📅 Agendamento de Entrevista\n"]
        
        if data.get("resposta"):
            lines.append(data["resposta"])
            lines.append("")
        
        candidatos = data.get("candidatos_alvo", [])
        if candidatos:
            lines.append("### 👥 Candidatos para Entrevista\n")
            for c in candidatos:
                lines.append(f"**{c.get('nome', 'N/A')}**")
                lines.append(f"- Etapa atual: {c.get('etapa_atual', 'N/A')}")
                lines.append("")
        
        if data.get("tipo_entrevista"):
            tipo_label = {"rh": "RH", "tecnica": "Técnica", "gestor": "Gestor", "final": "Final"}.get(data["tipo_entrevista"], data["tipo_entrevista"])
            lines.append(f"### 🎯 Tipo de Entrevista: {tipo_label}\n")
        
        if data.get("sugestao_horario"):
            lines.append(f"### 🕐 Horário Sugerido\n{data['sugestao_horario']}")
        
        return "\n".join(lines)
    
    def _format_solicitar_dados_markdown(self, data: dict) -> str:
        lines = ["## 📋 Solicitação de Dados\n"]
        
        if data.get("resposta"):
            lines.append(data["resposta"])
            lines.append("")
        
        candidatos = data.get("candidatos_alvo", [])
        if candidatos:
            lines.append("### 👥 Candidatos\n")
            for c in candidatos:
                lines.append(f"- **{c.get('nome', 'N/A')}**")
            lines.append("")
        
        dados = data.get("dados_solicitados", [])
        if dados:
            lines.append("### 📝 Dados Solicitados")
            for d in dados:
                lines.append(f"- {d}")
            lines.append("")
        
        if data.get("urgencia"):
            urgencia_emoji = {"alta": "🔴", "media": "🟡", "baixa": "🟢"}.get(data["urgencia"], "⚪")
            lines.append(f"### ⏰ Urgência: {urgencia_emoji} {data['urgencia'].capitalize()}")
        
        return "\n".join(lines)
    
    def _format_analisar_perfil_markdown(self, data: dict) -> str:
        lines = ["## 🔎 Análise de Perfil\n"]
        
        if data.get("resposta"):
            lines.append(data["resposta"])
            lines.append("")
        
        candidato = data.get("candidato_alvo", {})
        if candidato:
            lines.append(f"### 👤 Candidato: {candidato.get('nome', 'N/A')}")
            lines.append(f"- Etapa atual: {candidato.get('etapa_atual', 'N/A')}")
            lines.append("")
        
        if data.get("tipo_analise"):
            tipo_label = {"completa": "Completa", "tecnica": "Técnica", "comportamental": "Comportamental", "cultural": "Cultural"}.get(data["tipo_analise"], data["tipo_analise"])
            lines.append(f"### 📊 Tipo de Análise: {tipo_label}\n")
        
        areas = data.get("areas_foco", [])
        if areas:
            lines.append("### 🎯 Áreas de Foco")
            for a in areas:
                lines.append(f"- {a}")
        
        return "\n".join(lines)
    
    def _format_aprovar_markdown(self, data: dict) -> str:
        lines = ["## ✅ Aprovação de Candidatos\n"]
        
        if data.get("resposta"):
            lines.append(data["resposta"])
            lines.append("")
        
        candidatos = data.get("candidatos_alvo", [])
        if candidatos:
            lines.append("### 👥 Candidatos para Aprovação\n")
            for c in candidatos:
                lines.append(f"**{c.get('nome', 'N/A')}**")
                lines.append(f"- Etapa atual: {c.get('etapa_atual', 'N/A')}")
                if c.get('proxima_etapa'):
                    lines.append(f"- Próxima etapa: {c['proxima_etapa']}")
                lines.append("")
        
        if data.get("justificativa"):
            lines.append(f"### 💡 Justificativa\n{data['justificativa']}")
        
        return "\n".join(lines)
    
    def _format_geral_markdown(self, data: dict) -> str:
        lines = ["## 💡 Análise\n"]
        
        if data.get("resposta"):
            lines.append(data["resposta"])
        
        insights = data.get("insights_adicionais", [])
        if insights:
            lines.append("\n### 💡 Insights Adicionais")
            for i in insights:
                lines.append(f"- {i}")
        
        sugestoes = data.get("sugestoes", [])
        if sugestoes:
            lines.append("\n### 🎯 Sugestões")
            for s in sugestoes:
                lines.append(f"- {s}")
        
        return "\n".join(lines)
    
    def _extract_actions(self, data: dict[str, Any]) -> list[str]:
        """Extract suggested actions from the response data."""
        actions = []
        
        if data.get("recomendacoes"):
            actions.extend(data["recomendacoes"][:3])
        if data.get("plano_acao"):
            actions.extend(data["plano_acao"][:3])
        if data.get("acoes_em_lote"):
            for a in data["acoes_em_lote"][:2]:
                if isinstance(a, dict) and a.get("acao"):
                    actions.append(a["acao"])
        if data.get("proximos_passos"):
            actions.extend(data["proximos_passos"][:2])
        if data.get("otimizacoes"):
            for o in data["otimizacoes"][:2]:
                if isinstance(o, dict) and o.get("acao"):
                    actions.append(o["acao"])
        
        return list(set(actions))[:5]


kanban_assistant_service = KanbanAssistantService()
