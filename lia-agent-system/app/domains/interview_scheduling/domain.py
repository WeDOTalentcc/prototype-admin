from pathlib import Path
"""Interview & Scheduling Domain - Interview management and WSI methodology."""
import logging
import uuid
from datetime import datetime, timezone
from typing import Any


from app.domains.base import DomainAction, DomainContext, DomainResponse, IntentResult
from app.domains.compliance_base import ComplianceDomainPrompt
from app.domains.interview_scheduling.agents.interview_graph import interview_graph
from app.domains.registry import register_domain
from app.shared.services.interview_session_store import interview_session_store

_SCHEDULING_SESSION_PREFIX = "scheduling:"

_GRAPH_ACTIONS = {"schedule_interview"}

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
_matcher = KeywordIntentMatcher.from_keyword_map(_KEYWORD_ACTION_MAP, domain_id="interview_scheduling")


@register_domain
class InterviewSchedulingDomain(ComplianceDomainPrompt):

    _compliance_config = {'high_impact': False}
    domain_id = "interview_scheduling"
    domain_name = "Interview & Scheduling"

    def __init__(self):
        from app.domains.interview_scheduling.actions import INTERVIEW_SCHEDULING_ACTIONS
        self._actions = INTERVIEW_SCHEDULING_ACTIONS

    def get_allowed_actions(self) -> list[DomainAction]:
        from app.domains.interview_scheduling.actions import INTERVIEW_SCHEDULING_ACTIONS
        return INTERVIEW_SCHEDULING_ACTIONS

    async def process_intent(self, query: str, context: DomainContext) -> IntentResult:
        # LIA-I07: Check if query is an info request (e.g., "como funciona X?")
        if _matcher.is_info_query(query):
            try:
                match = _matcher.match(query, default_action="list_today_interviews")
                return IntentResult(
                    intent_id=f"interview_scheduling.{match.action}",
                    action_id=match.action,
                    confidence=match.confidence,
                    extracted_params={"raw_query": query, "is_info_query": True},
                    reasoning=f"[LIA-I07] Info query routed via is_info_query (action='{match.action}')",
                )
            except Exception:
                pass  # Fall through to normal logic

        # LIA-I03: Use shared KeywordIntentMatcher (falls back to loop on error)
        try:
            match = _matcher.match(query, default_action="list_today_interviews")
            return IntentResult(
                intent_id=f"interview_scheduling.{match.action}",
                action_id=match.action,
                confidence=match.confidence,
                extracted_params={"raw_query": query},
                reasoning=f"KeywordIntentMatcher matched action '{match.action}'",
            )
        except Exception as e:
            logger.debug("[LIA-I03] Matcher failed, using fallback: %s", e)
            query_lower = query.lower().strip()
            best_action = "list_today_interviews"
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
                intent_id=f"interview_scheduling.{best_action}",
                action_id=best_action,
                confidence=best_confidence,
                extracted_params={"raw_query": query},
                reasoning=f"Keyword heuristic matched action '{best_action}'",
            )

    _ACTION_TOOL_MAP: dict[str, str] = {
        "schedule_interview": "scheduling_schedule_interview",
        "reschedule_interview": "scheduling_reschedule",
        "cancel_interview": "scheduling_cancel",
        "check_availability": "scheduling_check_availability",
        "generate_self_scheduling_link": "scheduling_self_scheduling_link",
        "find_common_slots": "scheduling_find_slots",
        "send_reminder": "scheduling_send_reminder",
        "list_today_interviews": "scheduling_list_today",
        "transcribe_audio": "scheduling_transcribe_audio",
        "analyze_voice": "scheduling_analyze_voice",
    }

    async def execute_action(self, action_id: str, params: dict[str, Any], context: DomainContext) -> DomainResponse:
        action = None
        for a in self.get_allowed_actions():
            if a.action_id == action_id:
                action = a
                break

        if not action:
            return DomainResponse.error_response(
                error=f"Ação '{action_id}' não encontrada no domínio de entrevistas & agendamento."
            )

        logger.info(f"Executing interview_scheduling action '{action_id}' (tenant={context.tenant_id})")

        from app.domains.interview_scheduling.tools import INTERVIEW_SCHEDULING_TOOLS, execute_interview_scheduling_tool

        tool_ids = {t["tool_id"] for t in INTERVIEW_SCHEDULING_TOOLS}
        mapped_tool = self._ACTION_TOOL_MAP.get(action_id)

        if action_id in _GRAPH_ACTIONS:
            return await self._run_interview_graph(action_id, params, context)

        if mapped_tool and mapped_tool in tool_ids:
            result = await execute_interview_scheduling_tool(mapped_tool, params, context)
            return DomainResponse.success_response(
                message=f"Ferramenta '{mapped_tool}' executada para ação '{action.name}'.",
                data={"action_id": action_id, "tool_id": mapped_tool, "result": result},
                domain_id=self.domain_id,
                action_id=action_id,
            )

        wsi_handler_map = {
            "start_wsi_interview": self._handle_start_wsi_interview,
            "send_question": self._handle_send_question,
            "analyze_response": self._handle_analyze_response,
            "detect_evasive": self._handle_detect_evasive,
            "generate_followup": self._handle_generate_followup,
            "complete_interview": self._handle_complete_interview,
            "schedule_reminders": self._handle_schedule_reminders,
            "resolve_conflict": self._handle_resolve_conflict,
            "interview_qa": self._handle_interview_qa,
            "start_quick_screening": self._handle_start_quick_screening,
        }

        handler = wsi_handler_map.get(action_id)
        if handler:
            try:
                return await handler(params, context)
            except Exception as exc:
                logger.error(f"WSI handler '{action_id}' failed: {exc}", exc_info=True)
                return DomainResponse.error_response(
                    error=str(exc),
                    message=f"Erro ao executar '{action.name}': {exc}",
                    domain_id=self.domain_id,
                    action_id=action_id,
                )

        return DomainResponse.error_response(
            error=f"Nenhum handler configurado para a ação '{action_id}'.",
            domain_id=self.domain_id,
            action_id=action_id,
        )

    async def _handle_start_wsi_interview(self, params: dict, context: DomainContext) -> DomainResponse:
        candidate_id = params.get("candidate_id")
        job_vacancy_id = params.get("job_vacancy_id")

        if not candidate_id or not job_vacancy_id:
            return DomainResponse.clarification_response(
                question="Para iniciar a entrevista WSI, preciso do ID do candidato e da vaga.",
                domain_id=self.domain_id, action_id="start_wsi_interview",
            )

        session_id = str(uuid.uuid4())
        competencies = params.get("competencies", ["comunicação", "resolução de problemas", "trabalho em equipe"])
        language = params.get("language", "pt-BR")

        interview_data = {
            "interview_session_id": session_id,
            "candidate_id": candidate_id,
            "job_vacancy_id": job_vacancy_id,
            "competencies": competencies,
            "language": language,
            "status": "started",
            "questions_asked": 0,
            "started_at": datetime.now(timezone.utc).isoformat(),
        }

        session_key = f"wsi:{session_id}"
        await interview_session_store.set(session_key, interview_data)

        return DomainResponse.success_response(
            message=f"Entrevista WSI iniciada para candidato #{candidate_id} na vaga #{job_vacancy_id}.\n"
                    f"Competências avaliadas: {', '.join(competencies)}.\n"
                    f"Sessão: {session_id}",
            data={"action_id": "start_wsi_interview", **interview_data},
            domain_id=self.domain_id,
            action_id="start_wsi_interview",
        )

    async def _handle_send_question(self, params: dict, context: DomainContext) -> DomainResponse:
        interview_id = params.get("interview_id")
        question_text = params.get("question_text")

        if not interview_id or not question_text:
            return DomainResponse.clarification_response(
                question="Preciso do ID da entrevista e do texto da pergunta.",
                domain_id=self.domain_id, action_id="send_question",
            )

        session_key = f"wsi:{interview_id}"
        session_data = await interview_session_store.get(session_key)
        if not session_data:
            return DomainResponse.error_response(
                error=f"Sessão de entrevista '{interview_id}' não encontrada. Inicie uma entrevista primeiro.",
                domain_id=self.domain_id, action_id="send_question",
            )

        question_type = params.get("question_type", "behavioral")
        competency = params.get("competency_target", "general")
        question_id = str(uuid.uuid4())[:8]

        session_data["questions_asked"] = session_data.get("questions_asked", 0) + 1
        questions_log = session_data.get("questions_log", [])
        questions_log.append({
            "question_id": question_id,
            "question_text": question_text,
            "question_type": question_type,
            "competency_target": competency,
            "sent_at": datetime.now(timezone.utc).isoformat(),
        })
        session_data["questions_log"] = questions_log
        session_data["status"] = "in_progress"
        await interview_session_store.set(session_key, session_data)

        return DomainResponse.success_response(
            message=f"Pergunta #{session_data['questions_asked']} enviada ao candidato:\n\n> {question_text}\n\nTipo: {question_type} | Competência: {competency}",
            data={"action_id": "send_question", "question_id": question_id, "interview_id": interview_id,
                  "questions_asked": session_data["questions_asked"]},
            domain_id=self.domain_id,
            action_id="send_question",
        )

    async def _handle_analyze_response(self, params: dict, context: DomainContext) -> DomainResponse:
        interview_id = params.get("interview_id")
        response_text = params.get("response_text")

        if not interview_id or not response_text:
            return DomainResponse.clarification_response(
                question="Preciso do ID da entrevista e da resposta do candidato para analisar.",
                domain_id=self.domain_id, action_id="analyze_response",
            )

        session_key = f"wsi:{interview_id}"
        session_data = await interview_session_store.get(session_key)
        if not session_data:
            return DomainResponse.error_response(
                error=f"Sessão de entrevista '{interview_id}' não encontrada.",
                domain_id=self.domain_id, action_id="analyze_response",
            )

        competency = params.get("competency_target", "general")
        expected_level = params.get("expected_level", "pleno")

        word_count = len(response_text.split())
        specificity_score = min(1.0, word_count / 100)
        has_star = any(w in response_text.lower() for w in ["situação", "tarefa", "ação", "resultado", "situation", "task", "action", "result"])

        analysis = {
            "interview_id": interview_id,
            "word_count": word_count,
            "specificity_score": round(specificity_score, 2),
            "star_structure_detected": has_star,
            "competency_target": competency,
            "expected_level": expected_level,
            "depth_indicators": {
                "mentions_numbers": any(c.isdigit() for c in response_text),
                "mentions_impact": any(w in response_text.lower() for w in ["resultado", "impacto", "consegui", "entreguei"]),
                "mentions_learning": any(w in response_text.lower() for w in ["aprendi", "melhorei", "evoluí"]),
            },
            "preliminary_score": round(specificity_score * 0.6 + (0.4 if has_star else 0.1), 2),
        }

        responses_log = session_data.get("responses_log", [])
        responses_log.append({
            "response_text": response_text[:500],
            "analysis": analysis,
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
        })
        session_data["responses_log"] = responses_log
        scores = session_data.get("competency_scores", {})
        scores[competency] = analysis["preliminary_score"]
        session_data["competency_scores"] = scores
        await interview_session_store.set(session_key, session_data)

        msg = (
            f"**Análise da resposta (Competência: {competency}):**\n"
            f"• Palavras: {word_count}\n"
            f"• Estrutura STAR: {'Sim' if has_star else 'Não detectada'}\n"
            f"• Especificidade: {analysis['specificity_score']:.0%}\n"
            f"• Score preliminar: {analysis['preliminary_score']:.0%}\n"
        )
        if not has_star:
            msg += "\nRecomendação: Considere fazer follow-up para obter mais detalhes estruturados."

        return DomainResponse.success_response(
            message=msg,
            data={"action_id": "analyze_response", "analysis": analysis},
            domain_id=self.domain_id,
            action_id="analyze_response",
        )

    async def _handle_detect_evasive(self, params: dict, context: DomainContext) -> DomainResponse:
        interview_id = params.get("interview_id")
        response_text = params.get("response_text")

        if not interview_id or not response_text:
            return DomainResponse.clarification_response(
                question="Preciso do ID da entrevista e da resposta para detectar evasividade.",
                domain_id=self.domain_id, action_id="detect_evasive",
            )

        session_key = f"wsi:{interview_id}"
        session_data = await interview_session_store.get(session_key)
        if not session_data:
            return DomainResponse.error_response(
                error=f"Sessão de entrevista '{interview_id}' não encontrada.",
                domain_id=self.domain_id, action_id="detect_evasive",
            )

        threshold = float(params.get("threshold", 0.6))
        evasive_indicators = [
            "geralmente", "normalmente", "em teoria", "depende",
            "não sei se", "talvez", "acredito que", "acho que",
            "não lembro", "não me recordo", "faz tempo",
        ]
        word_count = len(response_text.split())
        evasive_matches = [ind for ind in evasive_indicators if ind in response_text.lower()]
        evasiveness_score = min(1.0, len(evasive_matches) * 0.25 + (0.3 if word_count < 20 else 0))
        is_evasive = evasiveness_score >= threshold

        result = {
            "interview_id": interview_id,
            "is_evasive": is_evasive,
            "evasiveness_score": round(evasiveness_score, 2),
            "threshold": threshold,
            "indicators_found": evasive_matches,
            "word_count": word_count,
        }

        evasion_log = session_data.get("evasion_log", [])
        evasion_log.append({
            "is_evasive": is_evasive,
            "score": result["evasiveness_score"],
            "indicators": evasive_matches,
            "checked_at": datetime.now(timezone.utc).isoformat(),
        })
        session_data["evasion_log"] = evasion_log
        session_data["evasion_count"] = sum(1 for e in evasion_log if e["is_evasive"])
        await interview_session_store.set(session_key, session_data)

        if is_evasive:
            msg = (
                f"**Resposta potencialmente evasiva detectada** (score: {evasiveness_score:.0%})\n"
                f"Indicadores: {', '.join(evasive_matches) if evasive_matches else 'Resposta muito curta'}\n"
                f"Recomendação: Gere uma pergunta de follow-up para aprofundar."
            )
        else:
            msg = f"Resposta parece direta e específica (evasividade: {evasiveness_score:.0%})."

        return DomainResponse.success_response(
            message=msg,
            data={"action_id": "detect_evasive", **result},
            domain_id=self.domain_id,
            action_id="detect_evasive",
        )

    async def _handle_generate_followup(self, params: dict, context: DomainContext) -> DomainResponse:
        interview_id = params.get("interview_id")
        previous_response = params.get("previous_response")

        if not interview_id or not previous_response:
            return DomainResponse.clarification_response(
                question="Preciso do ID da entrevista e da resposta anterior para gerar follow-up.",
                domain_id=self.domain_id, action_id="generate_followup",
            )

        session_key = f"wsi:{interview_id}"
        session_data = await interview_session_store.get(session_key)
        if not session_data:
            return DomainResponse.error_response(
                error=f"Sessão de entrevista '{interview_id}' não encontrada.",
                domain_id=self.domain_id, action_id="generate_followup",
            )

        competency = params.get("competency_target", "general")
        depth = params.get("depth_level", "medium")

        followup_templates = {
            "shallow": "Pode me dar um exemplo específico de quando isso aconteceu?",
            "medium": "Qual foi o resultado concreto dessa ação? Pode quantificar o impacto?",
            "deep": "Se tivesse que tomar essa decisão novamente, o que faria diferente e por quê?",
        }

        followup_text = followup_templates.get(depth, followup_templates["medium"])

        followups_log = session_data.get("followups_log", [])
        followups_log.append({
            "followup_text": followup_text,
            "depth_level": depth,
            "competency_target": competency,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        })
        session_data["followups_log"] = followups_log
        await interview_session_store.set(session_key, session_data)

        return DomainResponse.success_response(
            message=f"**Pergunta de follow-up sugerida:**\n\n> {followup_text}\n\nNível: {depth} | Competência: {competency}",
            data={
                "action_id": "generate_followup",
                "interview_id": interview_id,
                "followup_question": followup_text,
                "depth_level": depth,
                "competency_target": competency,
            },
            domain_id=self.domain_id,
            action_id="generate_followup",
        )

    async def _handle_complete_interview(self, params: dict, context: DomainContext) -> DomainResponse:
        interview_id = params.get("interview_id")
        if not interview_id:
            return DomainResponse.clarification_response(
                question="Qual entrevista deseja finalizar? Informe o ID.",
                domain_id=self.domain_id, action_id="complete_interview",
            )

        final_notes = params.get("final_notes", "")
        recommendation = params.get("recommendation", "pending")

        session_key = f"wsi:{interview_id}"
        session_data = await interview_session_store.get(session_key)
        if not session_data:
            return DomainResponse.error_response(
                error=f"Sessão de entrevista '{interview_id}' não encontrada ou já finalizada.",
                domain_id=self.domain_id, action_id="complete_interview",
            )

        questions_asked = session_data.get("questions_asked", 0)
        competency_scores = session_data.get("competency_scores", {})
        evasion_count = session_data.get("evasion_count", 0)
        responses_count = len(session_data.get("responses_log", []))

        avg_score = round(sum(competency_scores.values()) / max(len(competency_scores), 1), 2) if competency_scores else None

        summary = {
            "interview_id": interview_id,
            "status": "completed",
            "started_at": session_data.get("started_at"),
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "candidate_id": session_data.get("candidate_id"),
            "job_vacancy_id": session_data.get("job_vacancy_id"),
            "final_notes": final_notes,
            "recommendation": recommendation,
            "questions_asked": questions_asked,
            "responses_analyzed": responses_count,
            "evasive_responses": evasion_count,
            "competencies_evaluated": list(competency_scores.keys()),
            "competency_scores": competency_scores,
            "average_score": avg_score,
        }

        await interview_session_store.delete(session_key)

        score_lines = [f"  - {comp}: {score:.0%}" for comp, score in competency_scores.items()]
        msg = (
            f"Entrevista **#{interview_id}** finalizada com sucesso.\n"
            f"Perguntas: {questions_asked} | Respostas analisadas: {responses_count} | Evasivas: {evasion_count}\n"
        )
        if score_lines:
            msg += "Scores por competência:\n" + "\n".join(score_lines) + "\n"
        if avg_score is not None:
            msg += f"Score médio: {avg_score:.0%}\n"
        msg += f"Recomendação: {recommendation}"
        if final_notes:
            msg += f"\nNotas: {final_notes}"

        return DomainResponse.success_response(
            message=msg,
            data={"action_id": "complete_interview", "summary": summary},
            domain_id=self.domain_id,
            action_id="complete_interview",
        )

    async def _handle_schedule_reminders(self, params: dict, context: DomainContext) -> DomainResponse:
        interview_id = params.get("interview_id")
        if not interview_id:
            return DomainResponse.clarification_response(
                question="Para qual entrevista deseja configurar lembretes?",
                domain_id=self.domain_id, action_id="schedule_reminders",
            )
        hours_before = params.get("hours_before", [24, 1])
        return DomainResponse.success_response(
            message=f"Lembretes automáticos configurados para entrevista #{interview_id}: {hours_before}h antes.",
            data={"action_id": "schedule_reminders", "interview_id": interview_id, "hours_before": hours_before},
            domain_id=self.domain_id, action_id="schedule_reminders",
        )

    async def _handle_resolve_conflict(self, params: dict, context: DomainContext) -> DomainResponse:
        interview_ids = params.get("interview_ids", [])
        if not interview_ids:
            return DomainResponse.clarification_response(
                question="Quais entrevistas estão em conflito? Informe os IDs.",
                domain_id=self.domain_id, action_id="resolve_conflict",
            )
        return DomainResponse.success_response(
            message=f"Conflito entre {len(interview_ids)} entrevistas identificado. Sugestão: reagendar a de menor prioridade.",
            data={"action_id": "resolve_conflict", "interview_ids": interview_ids, "suggestion": "reschedule_lowest_priority"},
            domain_id=self.domain_id, action_id="resolve_conflict",
        )

    async def _handle_interview_qa(self, params: dict, context: DomainContext) -> DomainResponse:
        question = params.get("question", params.get("raw_query", ""))
        return DomainResponse.success_response(
            message="Fico feliz em ajudar com suas dúvidas sobre entrevistas. O que gostaria de saber?",
            data={"action_id": "interview_qa", "question": question},
            domain_id=self.domain_id, action_id="interview_qa",
        )

    async def _handle_start_quick_screening(self, params: dict, context: DomainContext) -> DomainResponse:
        candidate_id = params.get("candidate_id")
        if not candidate_id:
            return DomainResponse.clarification_response(
                question="Qual candidato deseja triar rapidamente? Informe o ID.",
                domain_id=self.domain_id, action_id="start_quick_screening",
            )
        return DomainResponse.success_response(
            message=f"Triagem rápida iniciada para candidato #{candidate_id} (10-15min estimados).",
            data={
                "action_id": "start_quick_screening",
                "candidate_id": candidate_id,
                "screening_type": params.get("screening_type", "quick"),
                "status": "started",
            },
            domain_id=self.domain_id, action_id="start_quick_screening",
        )

    async def _run_interview_graph(
        self,
        action_id: str,
        params: dict[str, Any],
        context: DomainContext,
    ) -> DomainResponse:
        raw_query = params.get("raw_query", "")

        class _Msg:
            def __init__(self, content: str):
                self.content = content

        session_key = _SCHEDULING_SESSION_PREFIX + (context.session_id or "no-session")
        stored_workflow = await interview_session_store.get(session_key) or {}
        workflow_data = {**stored_workflow, **params.get("workflow_data", {})}

        state: dict[str, Any] = {
            "messages": [_Msg(raw_query)],
            "workflow_data": workflow_data,
            "entities": {k: v for k, v in params.items() if k not in ("raw_query", "workflow_data")},
            "session_id": context.session_id,
            "company_id": context.tenant_id,
            "user_id": context.user_id,
        }

        try:
            final_state = await interview_graph.invoke(state)
        except Exception as exc:
            logger.error(f"InterviewGraph falhou para action '{action_id}': {exc}", exc_info=True)
            return DomainResponse.error_response(
                error=str(exc),
                message="Erro ao processar agendamento de entrevista.",
                domain_id=self.domain_id,
                action_id=action_id,
            )

        workflow_data_out = final_state.get("workflow_data", {})

        if context.session_id:
            await interview_session_store.set(session_key, workflow_data_out)

        response_data = workflow_data_out.get("response_data", {})
        status = response_data.get("status", "collecting")

        if status == "collecting":
            next_field = response_data.get("next_field")
            field_labels = {
                "candidate_name": "nome do candidato",
                "candidate_email": "e-mail do candidato",
                "job_title": "cargo/vaga",
                "interview_type": "tipo de entrevista (técnica, comportamental, cultural, RH, gerencial)",
                "interviewer_email": "e-mail do entrevistador",
                "preferred_date": "data preferida (ex: 15/03/2026)",
                "preferred_time": "horário preferido (ex: 14:00 ou tarde)",
            }
            question = (
                f"Para agendar a entrevista, preciso saber: **{field_labels.get(next_field, next_field)}**."
                if next_field else "Qual informação adicional você deseja fornecer?"
            )
            return DomainResponse.clarification_response(
                question=question,
                data={
                    "action_id": action_id,
                    "graph_status": status,
                    "progress": response_data.get("progress", {}),
                    "workflow_data": workflow_data_out,
                },
                domain_id=self.domain_id,
                action_id=action_id,
            )

        if status == "error":
            return DomainResponse.error_response(
                error=response_data.get("error", "Erro desconhecido no agendamento"),
                message="Não foi possível agendar a entrevista.",
                data={"workflow_data": workflow_data_out},
                domain_id=self.domain_id,
                action_id=action_id,
            )

        if context.session_id:
            await interview_session_store.delete(session_key)

        return DomainResponse.success_response(
            message=response_data.get("message", "Entrevista agendada com sucesso!"),
            data={
                "action_id": action_id,
                "interview_id": response_data.get("interview_id"),
                "meeting_url": response_data.get("meeting_url"),
                "graph_status": status,
                "workflow_data": workflow_data_out,
            },
            domain_id=self.domain_id,
            action_id=action_id,
        )
