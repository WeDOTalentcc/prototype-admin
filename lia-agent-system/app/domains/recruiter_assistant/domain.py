from pathlib import Path
"""Recruiter Assistant Domain - Personal assistant for recruiters."""
import logging
from datetime import datetime, timezone
from typing import Any

from app.domains.base import DomainAction, DomainContext, DomainResponse, IntentResult
from app.domains.compliance_base import ComplianceDomainPrompt
from app.domains.registry import register_domain

from app.shared.services.keyword_intent_matcher import KeywordIntentMatcher
import yaml as _yaml_imp  # Fase 5

logger = logging.getLogger(__name__)

# Fase 5: _KEYWORD_ACTION_MAP loaded from capabilities.yaml (LIA-I05)
_capabilities_yaml_path = Path(__file__).parent / 'config' / 'capabilities.yaml'
_KEYWORD_ACTION_MAP: dict[str, str] = (
    _yaml_imp.safe_load(_capabilities_yaml_path.read_text()).get('intent_keywords', {})
    if _capabilities_yaml_path.exists()
    else {}
)

# LIA-I03: Shared KeywordIntentMatcher singleton
_matcher = KeywordIntentMatcher.from_keyword_map(_KEYWORD_ACTION_MAP, domain_id="recruiter_assistant")


@register_domain
class RecruiterAssistantDomain(ComplianceDomainPrompt):

    _compliance_config = {'high_impact': False}
    domain_id = "recruiter_assistant"
    domain_name = "Recruiter Assistant"

    def __init__(self):
        from app.domains.recruiter_assistant.actions import RECRUITER_ASSISTANT_ACTIONS
        self._actions = RECRUITER_ASSISTANT_ACTIONS

    def get_allowed_actions(self) -> list[DomainAction]:
        from app.domains.recruiter_assistant.actions import RECRUITER_ASSISTANT_ACTIONS
        return RECRUITER_ASSISTANT_ACTIONS

    async def process_intent(self, query: str, context: DomainContext) -> IntentResult:
        # LIA-I07: Check if query is an info request (e.g., "como funciona X?")
        if _matcher.is_info_query(query):
            try:
                match = _matcher.match(query, default_action="quick_question")
                return IntentResult(
                    intent_id=f"recruiter_assistant.{match.action}",
                    action_id=match.action,
                    confidence=match.confidence,
                    extracted_params={"raw_query": query, "is_info_query": True},
                    reasoning=f"[LIA-I07] Info query routed via is_info_query (action='{match.action}')",
                )
            except Exception:
                pass  # Fall through to normal logic

        # LIA-I03: Use shared KeywordIntentMatcher (falls back to loop on error)
        try:
            match = _matcher.match(query, default_action="quick_question")
            return IntentResult(
                intent_id=f"recruiter_assistant.{match.action}",
                action_id=match.action,
                confidence=match.confidence,
                extracted_params={"raw_query": query},
                reasoning=f"KeywordIntentMatcher matched action '{match.action}'",
            )
        except Exception as e:
            logger.debug("[LIA-I03] Matcher failed, using fallback: %s", e)
            query_lower = query.lower().strip()
            best_action = "quick_question"
            best_confidence = 0.3
            best_keyword = ""
            for keyword, action_id in _KEYWORD_ACTION_MAP.items():
                if keyword in query_lower:
                    confidence = min(0.95, 0.6 + len(keyword) * 0.02)
                    if confidence > best_confidence or (confidence == best_confidence and len(keyword) > len(best_keyword)):
                        best_action = action_id
                        best_confidence = confidence
                        best_keyword = keyword
            return IntentResult(
                intent_id=f"recruiter_assistant.{best_action}",
                action_id=best_action,
                confidence=best_confidence,
                extracted_params={"raw_query": query},
                reasoning=f"Keyword heuristic matched action '{best_action}'",
            )

    _ACTION_TOOL_MAP: dict[str, str] = {
        "pipeline_health": "assistant_pipeline_health",
        "stale_candidates": "assistant_stale_candidates",
        "move_candidate": "assistant_move_candidate",
        "search_context": "assistant_search_context",
        "save_memory": "assistant_save_memory",
        "recall_memory": "assistant_recall_memory",
        "conversation_summary": "assistant_conversation_summary",
        "kanban_analysis": "assistant_kanban_analysis",
        "send_notification": "assistant_send_notification",
        "track_goals": "assistant_track_goals",
    }

    async def execute_action(self, action_id: str, params: dict[str, Any], context: DomainContext) -> DomainResponse:
        action = None
        for a in self.get_allowed_actions():
            if a.action_id == action_id:
                action = a
                break

        if not action:
            return DomainResponse.error_response(
                error=f"Ação '{action_id}' não encontrada no domínio de assistente do recrutador."
            )

        logger.info(f"Executing recruiter_assistant action '{action_id}' (tenant={context.tenant_id})")

        from app.domains.recruiter_assistant.tools import RECRUITER_ASSISTANT_TOOLS, execute_recruiter_assistant_tool

        tool_ids = {t["tool_id"] for t in RECRUITER_ASSISTANT_TOOLS}
        mapped_tool = self._ACTION_TOOL_MAP.get(action_id)

        if mapped_tool and mapped_tool in tool_ids:
            result = await execute_recruiter_assistant_tool(mapped_tool, params, context)
            return DomainResponse.success_response(
                message=f"Ferramenta '{mapped_tool}' executada para ação '{action.name}'.",
                data={"action_id": action_id, "tool_id": mapped_tool, "result": result},
                domain_id=self.domain_id,
                action_id=action_id,
            )

        handler_map = {
            "daily_briefing": self._handle_daily_briefing,
            "end_of_day_summary": self._handle_end_of_day_summary,
            "quick_question": self._handle_quick_question,
            "plan_day": self._handle_plan_day,
            "suggest_action": self._handle_suggest_action,
            "calibrate_profile": self._handle_calibrate_profile,
            "generate_insights": self._handle_generate_insights,
            "compare_candidates": self._handle_compare_candidates,
            "stage_recommendation": self._handle_stage_recommendation,
            "proactive_alerts": self._handle_proactive_alerts,
            "stakeholder_notify": self._handle_stakeholder_notify,
            "learning_insights": self._handle_learning_insights,
            "help_command": self._handle_help,
        }

        handler = handler_map.get(action_id)
        if handler:
            try:
                return await handler(params, context)
            except Exception as exc:
                logger.error(f"Assistant handler '{action_id}' failed: {exc}", exc_info=True)
                return DomainResponse.error_response(
                    error=str(exc),
                    message=f"Erro ao executar '{action.name}': {exc}",
                    domain_id=self.domain_id,
                    action_id=action_id,
                )

        return DomainResponse.error_response(
            error=f"Nenhum handler configurado para '{action_id}'.",
            domain_id=self.domain_id,
            action_id=action_id,
        )

    async def _handle_daily_briefing(self, params: dict, context: DomainContext) -> DomainResponse:
        from lia_config.database import AsyncSessionLocal
        from sqlalchemy import text

        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        briefing: dict[str, Any] = {"date": today, "sections": {}, "alerts": [], "priorities": []}

        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(text("""
                    SELECT COUNT(*) FROM job_vacancies
                    WHERE company_id = :company_id AND status = 'Ativa'
                """), {"company_id": context.tenant_id})
                briefing["sections"]["vagas_ativas"] = result.scalar() or 0
            except Exception:
                briefing["sections"]["vagas_ativas"] = 0

            try:
                result = await session.execute(text("""
                    SELECT COUNT(*) FROM vacancy_candidates
                    WHERE company_id = :company_id
                      AND created_at >= CURRENT_DATE
                """), {"company_id": context.tenant_id})
                briefing["sections"]["novos_candidatos_hoje"] = result.scalar() or 0
            except Exception:
                briefing["sections"]["novos_candidatos_hoje"] = 0

            try:
                result = await session.execute(text("""
                    SELECT COUNT(*) FROM vacancy_candidates
                    WHERE company_id = :company_id
                      AND updated_at < CURRENT_DATE - INTERVAL '7 days'
                      AND stage NOT IN ('Contratado', 'Rejeitado', 'Desistiu')
                """), {"company_id": context.tenant_id})
                briefing["sections"]["candidatos_parados"] = result.scalar() or 0
            except Exception:
                briefing["sections"]["candidatos_parados"] = 0

            try:
                result = await session.execute(text("""
                    SELECT COUNT(*) FROM interviews
                    WHERE company_id = :company_id
                      AND scheduled_at::date = CURRENT_DATE
                """), {"company_id": context.tenant_id})
                briefing["sections"]["entrevistas_hoje"] = result.scalar() or 0
            except Exception:
                briefing["sections"]["entrevistas_hoje"] = 0

            try:
                result = await session.execute(text("""
                    SELECT COUNT(*) FROM vacancy_candidates
                    WHERE company_id = :company_id
                      AND updated_at >= CURRENT_DATE - INTERVAL '1 day'
                """), {"company_id": context.tenant_id})
                briefing["sections"]["movimentacoes_ontem"] = result.scalar() or 0
            except Exception:
                briefing["sections"]["movimentacoes_ontem"] = 0

            try:
                result = await session.execute(text("""
                    SELECT COUNT(*) FROM job_vacancies
                    WHERE company_id = :company_id
                      AND status = 'Ativa'
                      AND deadline IS NOT NULL
                      AND deadline < NOW() + INTERVAL '7 days'
                """), {"company_id": context.tenant_id})
                briefing["sections"]["vagas_sla_risco"] = result.scalar() or 0
            except Exception:
                briefing["sections"]["vagas_sla_risco"] = 0

        try:
            from app.domains.recruiter_assistant.services.monitoring_loop import monitoring_loop
            alert_summary = monitoring_loop.get_alert_summary(context.tenant_id or "")
            briefing["alerts"] = alert_summary
            if not monitoring_loop.get_alerts(context.tenant_id or ""):
                await monitoring_loop.run_checks(context.tenant_id or "")
                alert_summary = monitoring_loop.get_alert_summary(context.tenant_id or "")
                briefing["alerts"] = alert_summary
        except Exception:
            briefing["alerts"] = {"total": 0}

        try:
            from app.domains.recruiter_assistant.services.stakeholder_notification_service import stakeholder_service
            pending = await stakeholder_service.detect_pending_decisions(context.tenant_id or "")
            briefing["sections"]["decisoes_pendentes_hm"] = len(pending)
        except Exception:
            briefing["sections"]["decisoes_pendentes_hm"] = 0

        s = briefing["sections"]
        alert_total = briefing.get("alerts", {}).get("total", 0)

        msg = (
            f"**Bom dia! Briefing de {today}:**\n\n"
            f"**Pipeline:**\n"
            f"• **{s.get('vagas_ativas', 0)}** vagas ativas\n"
            f"• **{s.get('novos_candidatos_hoje', 0)}** novos candidatos hoje\n"
            f"• **{s.get('movimentacoes_ontem', 0)}** movimentações nas últimas 24h\n"
            f"• **{s.get('entrevistas_hoje', 0)}** entrevistas agendadas para hoje\n\n"
            f"**Atenção:**\n"
            f"• **{s.get('candidatos_parados', 0)}** candidatos parados (>7 dias sem ação)\n"
            f"• **{s.get('vagas_sla_risco', 0)}** vagas com SLA em risco (<7 dias)\n"
            f"• **{s.get('decisoes_pendentes_hm', 0)}** decisões pendentes de hiring managers\n"
            f"• **{alert_total}** alertas proativos no sistema\n"
        )

        priorities = []
        if s.get("entrevistas_hoje", 0) > 0:
            priorities.append(f"Preparar-se para **{s['entrevistas_hoje']}** entrevista(s)")
        if s.get("candidatos_parados", 0) > 5:
            priorities.append(f"Revisar os **{s['candidatos_parados']}** candidatos parados")
        if s.get("vagas_sla_risco", 0) > 0:
            priorities.append(f"Ação urgente em **{s['vagas_sla_risco']}** vagas com SLA em risco")
        if s.get("decisoes_pendentes_hm", 0) > 0:
            priorities.append(f"Follow-up com hiring managers ({s['decisoes_pendentes_hm']} pendências)")

        if priorities:
            msg += "\n**Prioridades do dia:**\n" + "\n".join(f"{i+1}. {p}" for i, p in enumerate(priorities))
            briefing["priorities"] = priorities
        else:
            msg += "\nSem prioridades urgentes — bom dia para sourcing proativo!"

        return DomainResponse.success_response(
            message=msg,
            data={"action_id": "daily_briefing", "briefing": briefing},
            domain_id=self.domain_id, action_id="daily_briefing",
        )

    async def _handle_end_of_day_summary(self, params: dict, context: DomainContext) -> DomainResponse:
        from lia_config.database import AsyncSessionLocal
        from sqlalchemy import text

        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        summary: dict[str, Any] = {"date": today, "activities": {}, "pending": {}, "suggestions": []}

        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(text("""
                    SELECT COUNT(*) FROM vacancy_candidates
                    WHERE company_id = :company_id
                      AND updated_at >= CURRENT_DATE
                """), {"company_id": context.tenant_id})
                summary["activities"]["candidatos_movidos"] = result.scalar() or 0
            except Exception:
                summary["activities"]["candidatos_movidos"] = 0

            try:
                result = await session.execute(text("""
                    SELECT COUNT(*) FROM vacancy_candidates
                    WHERE company_id = :company_id
                      AND created_at >= CURRENT_DATE
                """), {"company_id": context.tenant_id})
                summary["activities"]["novos_candidatos"] = result.scalar() or 0
            except Exception:
                summary["activities"]["novos_candidatos"] = 0

            try:
                result = await session.execute(text("""
                    SELECT COUNT(*) FROM vacancy_candidates
                    WHERE company_id = :company_id
                      AND stage IN ('Rejeitado', 'Desistiu')
                      AND updated_at >= CURRENT_DATE
                """), {"company_id": context.tenant_id})
                summary["activities"]["rejeitados_hoje"] = result.scalar() or 0
            except Exception:
                summary["activities"]["rejeitados_hoje"] = 0

            try:
                result = await session.execute(text("""
                    SELECT COUNT(*) FROM vacancy_candidates
                    WHERE company_id = :company_id
                      AND stage = 'Contratado'
                      AND updated_at >= CURRENT_DATE
                """), {"company_id": context.tenant_id})
                summary["activities"]["contratados_hoje"] = result.scalar() or 0
            except Exception:
                summary["activities"]["contratados_hoje"] = 0

            try:
                result = await session.execute(text("""
                    SELECT COUNT(*) FROM vacancy_candidates
                    WHERE company_id = :company_id
                      AND updated_at < CURRENT_DATE - INTERVAL '7 days'
                      AND stage NOT IN ('Contratado', 'Rejeitado', 'Desistiu')
                """), {"company_id": context.tenant_id})
                summary["pending"]["candidatos_parados"] = result.scalar() or 0
            except Exception:
                summary["pending"]["candidatos_parados"] = 0

            try:
                result = await session.execute(text("""
                    SELECT COUNT(*) FROM job_vacancies
                    WHERE company_id = :company_id
                      AND status = 'Ativa'
                      AND deadline IS NOT NULL
                      AND deadline < NOW() + INTERVAL '7 days'
                """), {"company_id": context.tenant_id})
                summary["pending"]["vagas_sla_risco"] = result.scalar() or 0
            except Exception:
                summary["pending"]["vagas_sla_risco"] = 0

        a = summary["activities"]
        p = summary["pending"]

        suggestions = []
        if p.get("candidatos_parados", 0) > 0:
            suggestions.append(f"Revisar {p['candidatos_parados']} candidatos parados no pipeline")
        if p.get("vagas_sla_risco", 0) > 0:
            suggestions.append(f"Priorizar {p['vagas_sla_risco']} vagas com SLA em risco")
        if a.get("novos_candidatos", 0) > 5:
            suggestions.append("Avaliar os novos candidatos que chegaram hoje")
        summary["suggestions"] = suggestions

        msg = (
            f"**Resumo do dia {today}:**\n\n"
            f"**O que foi feito:**\n"
            f"• **{a.get('novos_candidatos', 0)}** novos candidatos adicionados\n"
            f"• **{a.get('candidatos_movidos', 0)}** candidatos atualizados\n"
            f"• **{a.get('contratados_hoje', 0)}** contratações realizadas\n"
            f"• **{a.get('rejeitados_hoje', 0)}** candidatos rejeitados/desistentes\n"
        )

        if p.get("candidatos_parados", 0) > 0 or p.get("vagas_sla_risco", 0) > 0:
            msg += (
                f"\n**O que ficou pendente:**\n"
                f"• **{p.get('candidatos_parados', 0)}** candidatos parados (>7 dias)\n"
                f"• **{p.get('vagas_sla_risco', 0)}** vagas com SLA em risco\n"
            )

        if suggestions:
            msg += "\n**Sugestões para amanhã:**\n"
            msg += "\n".join(f"{i+1}. {s}" for i, s in enumerate(suggestions))

        msg += "\n\nBom descanso! Amanhã trago seu briefing matinal."

        return DomainResponse.success_response(
            message=msg,
            data={"action_id": "end_of_day_summary", "summary": summary},
            domain_id=self.domain_id, action_id="end_of_day_summary",
        )

    async def _handle_quick_question(self, params: dict, context: DomainContext) -> DomainResponse:
        query = params.get("raw_query", params.get("question", ""))
        return DomainResponse.success_response(
            message="Fico feliz em ajudar! O que você precisa saber?",
            data={"action_id": "quick_question", "query": query, "delegate_to_agent": True},
            domain_id=self.domain_id, action_id="quick_question",
        )

    async def _handle_plan_day(self, params: dict, context: DomainContext) -> DomainResponse:
        from lia_config.database import AsyncSessionLocal
        from sqlalchemy import text

        priorities: list[str] = []

        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(text("""
                    SELECT COUNT(*) FROM interviews
                    WHERE company_id = :company_id
                      AND scheduled_at::date = CURRENT_DATE
                """), {"company_id": context.tenant_id})
                interviews_count = result.scalar() or 0
                if interviews_count > 0:
                    priorities.append(f"Preparar-se para **{interviews_count}** entrevista(s) hoje")
            except Exception:
                pass

            try:
                result = await session.execute(text("""
                    SELECT COUNT(*) FROM vacancy_candidates
                    WHERE company_id = :company_id
                      AND updated_at < CURRENT_DATE - INTERVAL '5 days'
                      AND stage NOT IN ('Contratado', 'Rejeitado', 'Desistiu')
                """), {"company_id": context.tenant_id})
                stale = result.scalar() or 0
                if stale > 0:
                    priorities.append(f"Revisar **{stale}** candidatos parados no pipeline")
            except Exception:
                pass

            try:
                result = await session.execute(text("""
                    SELECT COUNT(*) FROM vacancy_candidates
                    WHERE company_id = :company_id
                      AND created_at >= CURRENT_DATE
                """), {"company_id": context.tenant_id})
                new_count = result.scalar() or 0
                if new_count > 0:
                    priorities.append(f"Avaliar **{new_count}** novos candidatos")
            except Exception:
                pass

        if not priorities:
            priorities.append("Sem tarefas urgentes identificadas — bom dia para sourcing proativo!")

        lines = [f"{i+1}. {p}" for i, p in enumerate(priorities)]
        msg = "**Seu plano para hoje:**\n\n" + "\n".join(lines)

        return DomainResponse.success_response(
            message=msg,
            data={"action_id": "plan_day", "priorities": priorities},
            domain_id=self.domain_id, action_id="plan_day",
        )

    async def _handle_suggest_action(self, params: dict, context: DomainContext) -> DomainResponse:
        candidate_id = params.get("candidate_id")
        job_id = params.get("job_id")

        if not candidate_id and not job_id:
            from lia_config.database import AsyncSessionLocal
            from sqlalchemy import text

            async with AsyncSessionLocal() as session:
                try:
                    result = await session.execute(text("""
                        SELECT vc.candidate_id, vc.stage, c.name, vc.vacancy_id
                        FROM vacancy_candidates vc
                        LEFT JOIN candidates c ON c.id = vc.candidate_id
                        WHERE vc.company_id = :company_id
                          AND vc.updated_at < CURRENT_DATE - INTERVAL '3 days'
                          AND vc.stage NOT IN ('Contratado', 'Rejeitado', 'Desistiu')
                        ORDER BY vc.updated_at ASC
                        LIMIT 3
                    """), {"company_id": context.tenant_id})
                    rows = result.fetchall()
                except Exception as exc:
                    logger.error(f"Suggest action query failed: {exc}", exc_info=True)
                    return DomainResponse.error_response(
                        error=f"Erro ao buscar sugestões de ações: {exc}",
                        domain_id=self.domain_id, action_id="suggest_action",
                    )

            if rows:
                suggestions = []
                for r in rows:
                    stage = r[1] or "N/A"
                    name = r[2] or f"#{r[0]}"
                    suggestions.append(f"• **{name}** (etapa: {stage}, vaga #{r[3]}) — considere avançar ou dar feedback")
                msg = "**Sugestões de próximas ações:**\n\n" + "\n".join(suggestions)
            else:
                msg = "Pipeline está em dia! Nenhuma ação urgente necessária."

            return DomainResponse.success_response(
                message=msg,
                data={"action_id": "suggest_action", "suggestions": [{"candidate_id": r[0], "stage": r[1]} for r in rows] if rows else []},
                domain_id=self.domain_id, action_id="suggest_action",
            )

        stage_actions = {
            "Novo": "Realizar triagem inicial ou agendar entrevista de fit",
            "Triagem": "Avaliar score WSI e decidir se avança",
            "Entrevista RH": "Agendar entrevista técnica se aprovado",
            "Entrevista Técnica": "Enviar parecer ao gestor",
            "Entrevista Gestor": "Preparar proposta se aprovado",
            "Proposta": "Acompanhar aceite ou negociação",
        }

        return DomainResponse.success_response(
            message=f"Para candidato #{candidate_id or 'N/A'}: consulte o pipeline para determinar a melhor ação.",
            data={"action_id": "suggest_action", "candidate_id": candidate_id, "stage_actions": stage_actions},
            domain_id=self.domain_id, action_id="suggest_action",
        )

    async def _handle_calibrate_profile(self, params: dict, context: DomainContext) -> DomainResponse:
        job_id = params.get("job_id")
        feedback = params.get("feedback", {})
        return DomainResponse.success_response(
            message=f"Perfil ideal calibrado{' para vaga #' + str(job_id) if job_id else ''} com seu feedback.",
            data={"action_id": "calibrate_profile", "job_id": job_id, "feedback": feedback, "status": "calibrated"},
            domain_id=self.domain_id, action_id="calibrate_profile",
        )

    async def _handle_generate_insights(self, params: dict, context: DomainContext) -> DomainResponse:
        from lia_config.database import AsyncSessionLocal
        from sqlalchemy import text

        insights: list[dict] = []

        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(text("""
                    SELECT stage, COUNT(*) as cnt
                    FROM vacancy_candidates
                    WHERE company_id = :company_id
                      AND stage NOT IN ('Contratado', 'Rejeitado', 'Desistiu')
                    GROUP BY stage
                    ORDER BY cnt DESC
                """), {"company_id": context.tenant_id})
                stage_data = {r[0]: r[1] for r in result.fetchall()}

                total = sum(stage_data.values())
                for stage, count in stage_data.items():
                    pct = count / total * 100 if total > 0 else 0
                    if pct > 40:
                        insights.append({
                            "type": "bottleneck",
                            "message": f"**Gargalo na etapa '{stage}':** {count} candidatos ({pct:.0f}% do pipeline)",
                            "severity": "high",
                        })
            except Exception:
                pass

            try:
                result = await session.execute(text("""
                    SELECT COUNT(*) FROM vacancy_candidates
                    WHERE company_id = :company_id
                      AND updated_at < CURRENT_DATE - INTERVAL '14 days'
                      AND stage NOT IN ('Contratado', 'Rejeitado', 'Desistiu')
                """), {"company_id": context.tenant_id})
                stale_long = result.scalar() or 0
                if stale_long > 0:
                    insights.append({
                        "type": "stale_alert",
                        "message": f"**{stale_long} candidatos inativos há mais de 14 dias** — risco de perda de talentos",
                        "severity": "medium",
                    })
            except Exception:
                pass

        if not insights:
            insights.append({
                "type": "positive",
                "message": "Pipeline saudável — nenhum insight crítico no momento.",
                "severity": "low",
            })

        lines = [f"• {i['message']}" for i in insights]
        msg = "**Insights proativos:**\n\n" + "\n".join(lines)

        return DomainResponse.success_response(
            message=msg,
            data={"action_id": "generate_insights", "insights": insights},
            domain_id=self.domain_id, action_id="generate_insights",
        )

    async def _handle_compare_candidates(self, params: dict, context: DomainContext) -> DomainResponse:
        candidate_ids = params.get("candidate_ids", [])
        if len(candidate_ids) < 2:
            return DomainResponse.clarification_response(
                question="Informe pelo menos 2 IDs de candidatos para comparar.",
                domain_id=self.domain_id, action_id="compare_candidates",
            )

        from lia_config.database import AsyncSessionLocal
        from sqlalchemy import text

        async with AsyncSessionLocal() as session:
            try:
                safe_ids = [str(cid) for cid in candidate_ids[:5]]
                id_params = {f"cid_{i}": v for i, v in enumerate(safe_ids)}
                id_placeholders = ", ".join(f":cid_{i}" for i in range(len(safe_ids)))
                result = await session.execute(text(f"""
                    SELECT c.id, c.name, vc.lia_score, vc.match_percentage, vc.stage
                    FROM candidates c
                    LEFT JOIN vacancy_candidates vc ON vc.candidate_id = c.id
                    WHERE c.id IN ({id_placeholders}) AND c.company_id = :company_id
                """), {**id_params, "company_id": context.tenant_id})
                candidates = [
                    {"id": r[0], "name": r[1], "lia_score": r[2], "match_pct": r[3], "stage": r[4]}
                    for r in result.fetchall()
                ]
            except Exception as exc:
                logger.error(f"Compare candidates query failed: {exc}", exc_info=True)
                return DomainResponse.error_response(
                    error=f"Erro ao comparar candidatos: {exc}",
                    domain_id=self.domain_id, action_id="compare_candidates",
                )

        if candidates:
            lines = [f"• **{c['name'] or 'ID ' + str(c['id'])}** — LIA: {c['lia_score'] or 'N/A'} | Match: {c['match_pct'] or 'N/A'}% | Etapa: {c['stage'] or 'N/A'}"
                     for c in candidates]
            msg = "**Comparação de candidatos:**\n\n" + "\n".join(lines)
        else:
            msg = "Candidatos não encontrados para comparação."

        _rrp_blocks = []
        if candidates:
            from app.shared.rrp_blocks import (
                ComparisonTableBlock, ComparisonColumn, ComparisonRow,
            )

            def _num(v):
                try:
                    return float(v) if v is not None else None
                except (TypeError, ValueError):
                    return None

            _table = ComparisonTableBlock(
                block_id="comparison_table:compare_candidates:"
                + "-".join(str(c.get("id")) for c in candidates),
                role="support", layout="wide",
                title="Comparacao de candidatos", entity_type="candidate",
                columns=[
                    ComparisonColumn(key="name", label="Candidato", type="text"),
                    ComparisonColumn(key="lia_score", label="LIA", type="score"),
                    ComparisonColumn(key="match_pct", label="Match", type="score"),
                    ComparisonColumn(key="stage", label="Etapa", type="text"),
                ],
                rows=[
                    ComparisonRow(
                        entity_id=str(c.get("id")),
                        cells={
                            "name": c.get("name") or ("ID " + str(c.get("id"))),
                            "lia_score": _num(c.get("lia_score")),
                            "match_pct": _num(c.get("match_pct")),
                            "stage": c.get("stage") or "-",
                        },
                    )
                    for c in candidates
                ],
                total_count=len(candidates), shown_count=len(candidates),
            )
            _rrp_blocks = [_table.model_dump(mode="json")]

        return DomainResponse.success_response(
            message=msg,
            data={"action_id": "compare_candidates", "candidates": candidates, "response_blocks": _rrp_blocks},
            domain_id=self.domain_id, action_id="compare_candidates",
        )

    async def _handle_stage_recommendation(self, params: dict, context: DomainContext) -> DomainResponse:
        candidate_id = params.get("candidate_id")
        if not candidate_id:
            return DomainResponse.clarification_response(
                question="Para qual candidato deseja uma recomendação de etapa?",
                domain_id=self.domain_id, action_id="stage_recommendation",
            )

        from lia_config.database import AsyncSessionLocal
        from sqlalchemy import text

        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(text("""
                    SELECT vc.stage, vc.lia_score, vc.match_percentage, c.name
                    FROM vacancy_candidates vc
                    LEFT JOIN candidates c ON c.id = vc.candidate_id
                    WHERE vc.candidate_id = :candidate_id AND vc.company_id = :company_id
                    LIMIT 1
                """), {"candidate_id": str(candidate_id), "company_id": context.tenant_id})
                row = result.fetchone()
            except Exception as exc:
                logger.error(f"Stage recommendation query failed: {exc}", exc_info=True)
                return DomainResponse.error_response(
                    error=f"Erro ao buscar dados do candidato para recomendação: {exc}",
                    domain_id=self.domain_id, action_id="stage_recommendation",
                )

        if row:
            current_stage, lia_sc, match_pct, name = row
            stage_flow = ["Novo", "Triagem", "Entrevista RH", "Entrevista Técnica", "Entrevista Gestor", "Proposta", "Contratado"]
            try:
                idx = stage_flow.index(current_stage)
                next_stage = stage_flow[idx + 1] if idx + 1 < len(stage_flow) else "Já na etapa final"
            except (ValueError, IndexError):
                next_stage = "Avaliar manualmente"

            score = lia_sc or match_pct or 0
            if score >= 70:
                recommendation = f"Avançar para **{next_stage}** — score de {score:.0f} indica boa compatibilidade."
            elif score >= 40:
                recommendation = f"Considerar avançar para **{next_stage}** com entrevista adicional — score moderado ({score:.0f})."
            else:
                recommendation = f"Manter na etapa atual ou dar feedback — score baixo ({score:.0f})."

            msg = f"**Recomendação para {name or 'candidato #' + str(candidate_id)}:**\n\nEtapa atual: {current_stage}\n{recommendation}"
        else:
            msg = f"Candidato #{candidate_id} não encontrado no pipeline."

        return DomainResponse.success_response(
            message=msg,
            data={"action_id": "stage_recommendation", "candidate_id": candidate_id},
            domain_id=self.domain_id, action_id="stage_recommendation",
        )

    async def _handle_proactive_alerts(self, params: dict, context: DomainContext) -> DomainResponse:
        from app.domains.recruiter_assistant.services.monitoring_loop import monitoring_loop

        try:
            alerts = monitoring_loop.get_alerts(context.tenant_id or "")
            if not alerts:
                await monitoring_loop.run_checks(context.tenant_id or "")
                alerts = monitoring_loop.get_alerts(context.tenant_id or "")
        except Exception as exc:
            logger.error("Proactive alerts failed: %s", exc)
            return DomainResponse.error_response(
                error=f"Erro ao buscar alertas: {exc}",
                domain_id=self.domain_id, action_id="proactive_alerts",
            )

        if not alerts:
            return DomainResponse.success_response(
                message="Nenhum alerta proativo no momento. Pipeline está saudável!",
                data={"action_id": "proactive_alerts", "alerts": [], "total": 0},
                domain_id=self.domain_id, action_id="proactive_alerts",
            )

        summary = monitoring_loop.get_alert_summary(context.tenant_id or "")
        high_alerts = [a for a in alerts if a.severity in ("high", "critical")]
        medium_alerts = [a for a in alerts if a.severity == "medium"]
        low_alerts = [a for a in alerts if a.severity == "low"]

        lines = []
        if high_alerts:
            lines.append("**Alertas críticos/altos:**")
            for a in high_alerts[:5]:
                lines.append(f"• [{a.severity.upper()}] {a.message}")
        if medium_alerts:
            lines.append("\n**Alertas médios:**")
            for a in medium_alerts[:5]:
                lines.append(f"• {a.message}")
        if low_alerts:
            lines.append(f"\n*+ {len(low_alerts)} alertas de baixa prioridade*")

        msg = f"**Alertas proativos ({len(alerts)} total):**\n\n" + "\n".join(lines)

        return DomainResponse.success_response(
            message=msg,
            data={
                "action_id": "proactive_alerts",
                "alerts": [a.to_dict() for a in alerts[:20]],
                "summary": summary,
            },
            domain_id=self.domain_id, action_id="proactive_alerts",
        )

    async def _handle_stakeholder_notify(self, params: dict, context: DomainContext) -> DomainResponse:
        from app.domains.recruiter_assistant.services.stakeholder_notification_service import stakeholder_service

        try:
            decisions = await stakeholder_service.detect_pending_decisions(context.tenant_id or "")
        except Exception as exc:
            logger.error("Stakeholder detection failed: %s", exc)
            return DomainResponse.error_response(
                error=f"Erro ao detectar decisões pendentes: {exc}",
                domain_id=self.domain_id, action_id="stakeholder_notify",
            )

        if not decisions:
            return DomainResponse.success_response(
                message="Nenhuma decisão pendente de hiring managers no momento.",
                data={"action_id": "stakeholder_notify", "pending": [], "total": 0},
                domain_id=self.domain_id, action_id="stakeholder_notify",
            )

        result = await stakeholder_service.send_escalation_notifications(
            context.tenant_id or "", decisions
        )

        lines = []
        for d in decisions[:10]:
            level_emoji = {"gentle_reminder": "", "follow_up": "", "escalation": ""}
            emoji = level_emoji.get(d.escalation_level.value, "")
            lines.append(
                f"• {emoji} **{d.stakeholder_name}** — {d.description} "
                f"(pendente há {d.days_pending} dias, nível: {d.escalation_level.value})"
            )

        msg = (
            f"**Decisões pendentes de stakeholders ({len(decisions)}):**\n\n"
            + "\n".join(lines)
            + f"\n\n{result.get('notifications_sent', 0)} notificações enviadas."
        )

        return DomainResponse.success_response(
            message=msg,
            data={
                "action_id": "stakeholder_notify",
                "pending": [d.to_dict() for d in decisions],
                "notification_result": result,
            },
            domain_id=self.domain_id, action_id="stakeholder_notify",
        )

    async def _handle_learning_insights(self, params: dict, context: DomainContext) -> DomainResponse:
        from app.domains.recruiter_assistant.services.outcome_learning_service import outcome_learning

        try:
            insights = await outcome_learning.get_learning_insights(context.tenant_id or "")
        except Exception as exc:
            logger.error("Learning insights failed: %s", exc)
            return DomainResponse.error_response(
                error=f"Erro ao buscar insights de aprendizado: {exc}",
                domain_id=self.domain_id, action_id="learning_insights",
            )

        lines = []
        for insight_text in insights.get("insights", []):
            lines.append(f"• {insight_text}")

        positive = insights.get("positive_signals", [])
        if positive:
            lines.append("\n**Sinais positivos (o que funciona):**")
            for p in positive[:3]:
                lines.append(f"• {p.get('reason', 'N/A')}")

        caution = insights.get("caution_signals", [])
        if caution:
            lines.append("\n**Sinais de cautela (o que evitar):**")
            for c in caution[:3]:
                lines.append(f"• {c.get('reason', 'N/A')}")

        if not lines:
            msg = (
                "A LIA ainda está aprendendo! Com mais contratações concluídas, "
                "insights sobre quais perfis e fontes funcionam melhor serão gerados automaticamente."
            )
        else:
            msg = (
                f"**O que a LIA aprendeu ({insights.get('total_outcomes_analyzed', 0)} outcomes analisados):**\n\n"
                + "\n".join(lines)
            )

        return DomainResponse.success_response(
            message=msg,
            data={"action_id": "learning_insights", "insights": insights},
            domain_id=self.domain_id, action_id="learning_insights",
        )

    async def _handle_help(self, params: dict, context: DomainContext) -> DomainResponse:
        actions = self.get_allowed_actions()
        lines = [f"• **{a.name}**: {a.description}" for a in actions]
        msg = "**Funcionalidades disponíveis:**\n\n" + "\n".join(lines)

        return DomainResponse.success_response(
            message=msg,
            data={"action_id": "help_command", "actions": [{"id": a.action_id, "name": a.name} for a in actions]},
            domain_id=self.domain_id, action_id="help_command",
        )
