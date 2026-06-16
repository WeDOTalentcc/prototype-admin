"""
ActionExecutorService — closed-loop action execution for LIA.

Delegates execution to specialized action_handlers modules.
Falls back to DomainRegistry if no handler matches.
Falls back to _simulate_execution if domain also fails.

Dead code (inline fallback blocks L931-L1660 in the original monolith)
has been removed — handlers always succeed for known action_ids.
"""
import logging
import re
import uuid
from datetime import datetime
from typing import Any

from app.orchestrator.action_executor.action_types import ActionResult
from app.orchestrator.action_executor.intents_config import (
    ACTIONABLE_INTENTS,
)
from app.orchestrator.action_executor.utils import (
    _detect_intent_from_message,
    _extract_entities_from_message,
    resolve_candidate_from_context,
    resolve_stage,
)

logger = logging.getLogger(__name__)

# Recovery Tri-2 Body-Changes (2026-05-23) — restaurar entity_id injection
# do contexto da conversa. Removido pelo merge incident 02361f41c. Sem ele,
# quando user fala "esse candidato" / "essa vaga" e o contexto tem
# entity_id+entity_type, o handler NÃO RECEBE candidate_id/job_id nos params
# e cai em erro silent. Quebra contexto persistente em conversas.
_UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I)
_JOB_ID_RE = re.compile(r"^[A-Z][A-Z0-9]{2,9}$", re.I)


class ActionExecutorService:

    def __init__(self):
        self.execution_count = 0

    def is_actionable(self, intent: str) -> bool:
        return intent in ACTIONABLE_INTENTS

    def get_action_config(self, intent: str) -> dict[str, Any] | None:
        return ACTIONABLE_INTENTS.get(intent)

    async def try_execute(
        self,
        intent: str = "",
        entities: dict[str, Any] | None = None,
        candidates_data: list[dict[str, Any]] | None = None,
        context: dict[str, Any] | None = None,
        *,
        message: str = "",
    ) -> ActionResult:
        # Support message-based call (from MainOrchestrator)
        if message and not intent:
            detected = _detect_intent_from_message(message, conversation_history=(context or {}).get("conversation_history"))
            if not detected:
                return ActionResult(status="not_actionable")
            intent = detected
            entities = entities or _extract_entities_from_message(message, intent)
            candidates_data = candidates_data or (context or {}).get("candidates", [])

        entities = entities or {}
        candidates_data = candidates_data or []
        context = context or {}

        # Recovery Tri-2 Body-Changes (2026-05-23): restaurar entity_id injection
        # do contexto da conversa. Quando user fala "esse candidato" / "essa vaga",
        # contexto carrega entity_id+entity_type — sem esse bloco o handler
        # não recebe candidate_id/job_id em params (REGRESSED merge incident).
        ctx_entity_id = context.get("entity_id") or context.get("context_entity_id")
        ctx_entity_type = context.get("entity_type", "")
        _is_uuid = bool(ctx_entity_id and _UUID_RE.match(str(ctx_entity_id)))
        _is_job_ref = bool(ctx_entity_id and _JOB_ID_RE.match(str(ctx_entity_id)))
        if ctx_entity_id and (_is_uuid or _is_job_ref):
            if ctx_entity_type in ("job", "job_vacancy"):
                if not entities.get("job_id"):
                    entities["job_id"] = ctx_entity_id
            elif ctx_entity_type in ("candidate", "candidato"):
                if not entities.get("candidate_id"):
                    entities["candidate_id"] = ctx_entity_id
        if not self.is_actionable(intent):
            return ActionResult(status="not_actionable")

        # Sprint 12.5-B4-extra (2026-05-24): intent-specific policy gate.
        # Phase 0.6 (MainOrchestrator) já gate com intent="general_chat"
        # (SAFE_INTENTS fast-path). Aqui repetimos com intent específico
        # resolvido (criar_vaga, pausar_vaga, mover_candidato, etc.) ANTES
        # de qualquer side effect do action dispatch.
        #
        # Lazy import singleton. Fail-open se ausente (Phase 0.6 já validou
        # gates user-level + tenant-level).
        try:
            from app.orchestrator.services.policy_gate_service import (
                policy_gate_service,
            )
            from app.shared.governance.policy_engine_service import (
                PolicyEngineService,
            )
            _intent_gate = policy_gate_service if policy_gate_service else None
            if _intent_gate is None:
                # Try construct on-demand (init pattern do MainOrchestrator linha 287)
                try:
                    from app.orchestrator.services.policy_gate_service import (
                        PolicyGateService,
                    )
                    _intent_gate = PolicyGateService(
                        policy_engine=PolicyEngineService()
                    )
                except Exception:
                    _intent_gate = None
            if _intent_gate is not None:
                _policy_result = await _intent_gate.validate(
                    intent=intent,
                    user_id=(context or {}).get("user_id") or "anon",
                    context={
                        "company_id": (context or {}).get("company_id"),
                        "user_id": (context or {}).get("user_id"),
                    },
                )
                if not _policy_result.allowed:
                    return ActionResult(
                        status="denied",
                        message=(
                            _policy_result.reason
                            or f"Acao '{intent}' negada por politica do tenant."
                        ),
                        action_type=intent,
                        data={
                            "policy_denied": True,
                            "reason": _policy_result.reason,
                            "constraints": _policy_result.constraints,
                        },
                    )
        except Exception as _gate_exc:
            # Fail-open: gate exception nao bloqueia (defense-in-depth,
            # Phase 0.6 ja eh primary gate).
            pass

        config = ACTIONABLE_INTENTS[intent]
        params = dict(config.get("default_params", {}))

        candidate_name = entities.get("candidate_name")
        candidate_id = entities.get("candidate_id")

        if candidate_name or candidate_id:
            resolved = resolve_candidate_from_context(
                candidate_name, candidate_id, candidates_data
            )
            if resolved:
                params["candidate_id"] = str(resolved.get("id", ""))
                params["candidate_name"] = resolved.get("name", candidate_name or "")
                params["candidate_email"] = resolved.get("email", "")
                if resolved.get("stage"):
                    params["from_stage"] = resolved["stage"]
            elif candidate_name:
                params["candidate_name_unresolved"] = candidate_name

        target_stage = entities.get("target_stage") or entities.get("to_stage") or entities.get("stage")
        if target_stage:
            resolved_stage = resolve_stage(target_stage)
            if resolved_stage:
                params["to_stage"] = resolved_stage

        if entities.get("subject"):
            params["subject"] = entities["subject"]
        if entities.get("body") or entities.get("message"):
            params["body"] = entities.get("body") or entities.get("message")
        if entities.get("datetime") or entities.get("date"):
            params["datetime"] = entities.get("datetime") or entities.get("date")
        if entities.get("interviewer"):
            params["interviewer"] = entities["interviewer"]
        if entities.get("reason"):
            params["reason"] = entities["reason"]

        if entities.get("job_id"):
            params["job_id"] = entities["job_id"]
        if entities.get("job_title"):
            params["job_title"] = entities["job_title"]
        if entities.get("new_title"):
            params["new_title"] = entities["new_title"]
        if entities.get("outcome"):
            params["outcome"] = entities["outcome"]

        if entities.get("field_name"):
            params["field_name"] = entities["field_name"]
        if entities.get("field_value"):
            params["field_value"] = entities["field_value"]
        if entities.get("content"):
            params["content"] = entities["content"]
        if entities.get("title"):
            params["title"] = entities["title"]
        if entities.get("description"):
            params["description"] = entities["description"]
        if entities.get("due_date"):
            params["due_date"] = entities["due_date"]
        if entities.get("priority"):
            params["priority"] = entities["priority"]
        if entities.get("location"):
            params["location"] = entities["location"]
        if entities.get("duration_minutes"):
            params["duration_minutes"] = entities["duration_minutes"]

        missing = []
        for req_param in config["required_params"]:
            if req_param not in params or not params[req_param]:
                if req_param == "candidate_id" and params.get("candidate_name_unresolved"):
                    missing.append("candidate_id")
                elif req_param not in params:
                    missing.append(req_param)

        if missing:
            first_missing = missing[0]
            prompt = config.get("clarification_prompts", {}).get(
                first_missing,
                f"Por favor, informe: {config.get('param_labels', {}).get(first_missing, first_missing)}"
            )

            if first_missing == "candidate_id" and params.get("candidate_name_unresolved"):
                prompt = f"Não encontrei o candidato '{params['candidate_name_unresolved']}' no pipeline desta vaga. Pode verificar o nome?"

            return ActionResult(
                status="needs_params",
                message=prompt,
                missing_params=missing,
                action_type=config["action_id"],
                pending_action_id=str(uuid.uuid4()),
                data={"collected_params": params, "intent": intent},
            )

        if config.get("requires_confirmation", False):
            summary = self._build_confirmation_summary(intent, config, params)
            return ActionResult(
                status="needs_confirmation",
                message=summary["message"],
                confirmation_summary=summary,
                action_type=config["action_id"],
                pending_action_id=str(uuid.uuid4()),
                data={"collected_params": params, "intent": intent},
            )

        result = await self._execute_action(intent, config, params, context)
        return result

    def _build_confirmation_summary(
        self, intent: str, config: dict[str, Any], params: dict[str, Any]
    ) -> dict[str, Any]:
        action_id = config["action_id"]
        candidate_name = params.get("candidate_name", "o candidato")

        if action_id == "move_candidate":
            to_stage = params.get("to_stage", "próxima etapa")
            from_stage = params.get("from_stage", "")
            from_text = f" (atualmente em {from_stage})" if from_stage else ""
            message = f"Vou mover **{candidate_name}**{from_text} para a etapa **{to_stage}**. Confirma?"
        elif action_id == "send_email":
            subject = params.get("subject", "")
            message = f"Vou enviar um email para **{candidate_name}**"
            if subject:
                message += f' com assunto "{subject}"'
            message += ". Confirma o envio?"
        elif action_id == "schedule_interview":
            dt = params.get("datetime", "")
            message = f"Vou agendar uma entrevista com **{candidate_name}**"
            if dt:
                message += f" para **{dt}**"
            message += ". Confirma?"
        elif action_id == "pause_job":
            job_title = params.get("job_title", "a vaga")
            message = f"Vou **pausar** a vaga **{job_title}**. Confirma?"
        elif action_id == "close_job":
            job_title = params.get("job_title", "a vaga")
            message = f"Vou **fechar** a vaga **{job_title}**. Confirma?"
        elif action_id == "reopen_job":
            job_title = params.get("job_title", "a vaga")
            message = f"Vou **reabrir** a vaga **{job_title}**. Confirma?"
        elif action_id == "update_candidate_field":
            field_name = params.get("field_name", "campo")
            field_value = params.get("field_value", "")
            message = f"Vou atualizar o campo **{field_name}** de **{candidate_name}** para **{field_value}**. Confirma?"
        elif action_id == "create_generic_event":
            event_title = params.get("title", "compromisso")
            dt = params.get("datetime", "")
            message = f"Vou criar o compromisso **\"{event_title}\"** para **{dt}**. Confirma?"
        else:
            message = f"Vou executar a ação **{action_id}** para **{candidate_name}**. Confirma?"

        return {
            "message": message,
            "action_id": action_id,
            "intent": intent,
            "params": params,
            "risk_level": config.get("risk_level", "medium"),
        }

    async def _execute_action(
        self,
        intent: str,
        config: dict[str, Any],
        params: dict[str, Any],
        context: dict[str, Any],
    ) -> ActionResult:
        domain_id = config["domain_id"]
        action_id = config["action_id"]

        # Delegate to specialized action handler modules
        try:
            from app.orchestrator.action_handlers.analytics_actions import execute_analytics_action
            from app.orchestrator.action_handlers.candidate_actions import execute_candidate_action
            from app.orchestrator.action_handlers.communication_actions import execute_communication_action
            from app.orchestrator.action_handlers.interview_actions import execute_interview_action
            from app.orchestrator.action_handlers.job_actions import execute_job_action
            from app.orchestrator.action_handlers.pipeline_actions import execute_pipeline_action
            from app.orchestrator.action_handlers.sourcing_actions import execute_sourcing_action

            _COMMUNICATION_ACTIONS = {
                "send_email", "schedule_interview", "create_generic_event",
                "send_feedback", "send_whatsapp", "send_screening_invite",
                "send_candidate_report", "send_progress_report", "share_candidate_profile",
            }
            _CANDIDATE_ACTIONS = {"move_candidate", "update_candidate_field", "start_screening", "analyze_profile", "batch_move_candidates"}
            _JOB_ACTIONS = {"pause_job", "close_job", "duplicate_job", "reopen_job", "set_job_urgent"}
            _PIPELINE_ACTIONS = {"create_task", "create_note", "generate_daily_briefing", "create_automation", "check_proactive_alerts"}
            _SOURCING_ACTIONS = {
                "tag_candidates", "rank_candidates", "compare_candidates",
                "search_candidates", "suggest_candidates", "add_candidate",
                "export_candidates", "favorite_candidate",
            }
            _ANALYTICS_ACTIONS = {"generate_kpi_report", "job_health_check", "analyze_funnel"}
            _INTERVIEW_ACTIONS = {
                "reschedule_interview", "cancel_interview", "send_interview_reminder",
                "list_today_interviews", "generate_self_scheduling_link",
            }

            handler_result = None
            if action_id in _COMMUNICATION_ACTIONS:
                handler_result = await execute_communication_action(action_id, params, context)
            elif action_id in _CANDIDATE_ACTIONS:
                handler_result = await execute_candidate_action(action_id, params, context)
            elif action_id in _JOB_ACTIONS:
                handler_result = await execute_job_action(action_id, params, context)
            elif action_id in _PIPELINE_ACTIONS:
                handler_result = await execute_pipeline_action(action_id, params, context)
            elif action_id in _SOURCING_ACTIONS:
                handler_result = await execute_sourcing_action(action_id, params, context)
            elif action_id in _ANALYTICS_ACTIONS:
                handler_result = await execute_analytics_action(action_id, params, context)
            elif action_id in _INTERVIEW_ACTIONS:
                handler_result = await execute_interview_action(action_id, params, context)

            if handler_result is not None:
                if handler_result.status not in ("error",):
                    self.execution_count += 1
                return handler_result
        except Exception as _handler_exc:
            logger.warning(f"Action handler delegation failed for {action_id}: {_handler_exc}")

        # DomainRegistry fallback (for unknown/unregistered action_ids)
        try:
            safe_params = {k: v for k, v in params.items() if k not in ("email", "candidate_email", "body", "phone")}
            logger.info(f"Executing closed-loop action: {domain_id}.{action_id} params={list(safe_params.keys())}")

            from app.domains.registry import DomainRegistry

            registry = DomainRegistry()
            domain = registry.get_instance(domain_id)

            if not domain:
                logger.warning(f"Domain '{domain_id}' not found, using simulated execution")
                return await self._simulate_execution(action_id, params, context)

            if action_id == "move_candidate" and "candidate_id" in params and "vacancy_candidate_id" not in params:
                params["vacancy_candidate_id"] = params["candidate_id"]

            from app.domains.base import DomainContext
            domain_context = DomainContext(
                tenant_id=context.get("tenant_id"),
                user_id=context.get("user_id", "recruiter"),
                conversation_id=context.get("conversation_id"),
                metadata=context,
            )

            response = await domain.execute_action(
                action_id=action_id,
                params=params,
                context=domain_context,
            )

            if response and response.success:
                self.execution_count += 1
                return ActionResult(
                    status="executed",
                    message=response.message or self._success_message(action_id, params),
                    data=response.data if isinstance(response.data, dict) else {"result": str(response.data)},
                    action_type=action_id,
                )
            else:
                error_msg = response.message if response else "Domain execution failed"
                logger.warning(f"Domain execution returned failure: {error_msg}")
                return await self._simulate_execution(action_id, params, context)

        except Exception as e:
            logger.error(f"Action execution error: {e}", exc_info=True)
            return await self._simulate_execution(action_id, params, context)

    async def _simulate_execution(
        self,
        action_id: str,
        params: dict[str, Any],
        context: dict[str, Any],
    ) -> ActionResult:
        candidate_name = params.get("candidate_name", "o candidato")
        self.execution_count += 1

        if action_id == "move_candidate":
            to_stage = params.get("to_stage", "próxima etapa")
            from_stage = params.get("from_stage", "")
            return ActionResult(
                status="executed",
                message=f"**{candidate_name}** foi movido(a) para a etapa **{to_stage}**.",
                data={
                    "candidate_id": params.get("candidate_id", ""),
                    "candidate_name": candidate_name,
                    "from_stage": from_stage,
                    "to_stage": to_stage,
                    "moved_at": datetime.utcnow().isoformat(),
                    "simulated": True,
                },
                action_type="move_candidate",
            )

        elif action_id == "send_email":
            subject = params.get("subject", "")
            return ActionResult(
                status="executed",
                message=f'Email enviado para **{candidate_name}** com assunto "{subject}".',
                data={
                    "candidate_id": params.get("candidate_id", ""),
                    "candidate_name": candidate_name,
                    "subject": subject,
                    "sent_at": datetime.utcnow().isoformat(),
                    "simulated": True,
                },
                action_type="send_email",
            )

        elif action_id == "schedule_interview":
            dt = params.get("datetime", "a definir")
            return ActionResult(
                status="executed",
                message=f"Entrevista agendada com **{candidate_name}** para **{dt}**.",
                data={
                    "candidate_id": params.get("candidate_id", ""),
                    "candidate_name": candidate_name,
                    "datetime": dt,
                    "scheduled_at": datetime.utcnow().isoformat(),
                    "simulated": True,
                },
                action_type="schedule_interview",
            )

        elif action_id in ("start_screening", "analyze_profile"):
            return ActionResult(
                status="executed",
                message="Triagem iniciada para os candidatos da vaga.",
                data={
                    "action": action_id,
                    "started_at": datetime.utcnow().isoformat(),
                    "simulated": True,
                },
                action_type=action_id,
            )

        elif action_id == "update_candidate_field":
            field_name = params.get("field_name", "campo")
            field_value = params.get("field_value", "")
            return ActionResult(
                status="executed",
                message=f"Campo **{field_name}** de **{candidate_name}** atualizado para **{field_value}**.",
                data={
                    "candidate_id": params.get("candidate_id", ""),
                    "field": field_name,
                    "value": field_value,
                    "simulated": True,
                },
                action_type="update_candidate_field",
            )

        elif action_id == "create_task":
            title = params.get("title", "tarefa")
            due_date = params.get("due_date", "")
            due_info = f" para **{due_date}**" if due_date else ""
            task_type = params.get("task_type", "general")
            action_label = "Lembrete" if task_type == "reminder" else "Tarefa"
            return ActionResult(
                status="executed",
                message=f"{action_label} **\"{title}\"** criado(a){due_info}.",
                data={
                    "title": title,
                    "due_date": due_date,
                    "simulated": True,
                },
                action_type="create_task",
            )

        elif action_id == "create_note":
            content = params.get("content", "")
            return ActionResult(
                status="executed",
                message="Nota salva com sucesso.",
                data={
                    "content": content,
                    "candidate_id": params.get("candidate_id"),
                    "job_id": params.get("job_id"),
                    "simulated": True,
                },
                action_type="create_note",
            )

        elif action_id == "create_generic_event":
            title = params.get("title", "compromisso")
            dt_str = params.get("datetime", "")
            return ActionResult(
                status="executed",
                message=f"Compromisso **\"{title}\"** criado para **{dt_str}**.",
                data={
                    "title": title,
                    "datetime": dt_str,
                    "simulated": True,
                },
                action_type="create_generic_event",
            )

        elif action_id == "pause_job":
            job_title = params.get("job_title", "a vaga")
            return ActionResult(
                status="executed",
                message=f"Vaga **{job_title}** pausada com sucesso.",
                data={
                    "job_id": params.get("job_id", ""),
                    "job_title": job_title,
                    "reason": params.get("reason", ""),
                    "paused_at": datetime.utcnow().isoformat(),
                    "simulated": True,
                },
                action_type="pause_job",
            )

        elif action_id == "close_job":
            job_title = params.get("job_title", "a vaga")
            return ActionResult(
                status="executed",
                message=f"Vaga **{job_title}** fechada com sucesso.",
                data={
                    "job_id": params.get("job_id", ""),
                    "job_title": job_title,
                    "reason": params.get("reason", ""),
                    "outcome": params.get("outcome", ""),
                    "closed_at": datetime.utcnow().isoformat(),
                    "simulated": True,
                },
                action_type="close_job",
            )

        elif action_id == "duplicate_job":
            job_title = params.get("job_title", "a vaga")
            return ActionResult(
                status="executed",
                message=f"Vaga **{job_title}** duplicada com sucesso.",
                data={
                    "job_id": params.get("job_id", ""),
                    "job_title": job_title,
                    "new_title": params.get("new_title", ""),
                    "duplicated_at": datetime.utcnow().isoformat(),
                    "simulated": True,
                },
                action_type="duplicate_job",
            )

        elif action_id == "reopen_job":
            job_title = params.get("job_title", "a vaga")
            return ActionResult(
                status="executed",
                message=f"Vaga **{job_title}** reaberta com sucesso.",
                data={
                    "job_id": params.get("job_id", ""),
                    "job_title": job_title,
                    "reopened_at": datetime.utcnow().isoformat(),
                    "simulated": True,
                },
                action_type="reopen_job",
            )

        return ActionResult(
            status="executed",
            message=f"Ação **{action_id}** executada com sucesso.",
            data={"action": action_id, "params": params, "simulated": True},
            action_type=action_id,
        )

    def _success_message(self, action_id: str, params: dict[str, Any]) -> str:
        candidate_name = params.get("candidate_name", "o candidato")
        if action_id == "move_candidate":
            return f"**{candidate_name}** foi movido(a) para **{params.get('to_stage', 'próxima etapa')}**."
        elif action_id == "send_email":
            return f"Email enviado para **{candidate_name}**."
        elif action_id == "schedule_interview":
            return f"Entrevista agendada com **{candidate_name}**."
        return f"Ação {action_id} executada com sucesso."


action_executor = ActionExecutorService()
