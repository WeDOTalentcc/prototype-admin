"""
Chat API endpoints for LIA conversation.
"""
import json
import logging
import os
import uuid
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse

from app.auth.dependencies import get_current_user_or_demo
from app.auth.models import User
from app.domains.chat.dependencies import get_chat_repo
from app.domains.chat.repositories.chat_repository import ChatRepository
from app.orchestrator.action_executor import (
    ACTIONABLE_INTENTS,
    ActionResult,
    action_executor,
    is_confirmation,
    is_rejection,
)
from app.orchestrator.pending_action import PendingActionState, pending_action_store
from app.schemas.chat import (
    ChatResponse,
    ConversationListResponse,
    ConversationResponse,
    MessageCreate,
    MessageResponse,
)

logger = logging.getLogger(__name__)

INTENT_TO_ACTIONABLE: dict[str, str] = {
    "move_candidate": "mover_candidato",
    "batch_move_candidates": "mover_candidatos_lote",
    "update_candidate_status": "atualizar_status_candidato",
    "update_status": "atualizar_status_candidato",
    "update_candidate_field": "atualizar_campo_candidato",
    "reject_candidate": "reprovar_candidato",
    "approve_candidate": "aprovar_candidato",
    "favorite_candidate": "favoritar_candidato",
    "send_email": "enviar_email",
    "send_message": "enviar_mensagem",
    "send_feedback": "enviar_feedback",
    "send_whatsapp": "enviar_whatsapp",
    "send_screening_invite": "enviar_convite_triagem",
    "share_candidate_profile": "compartilhar_candidato",
    "send_candidate_report": "enviar_relatorio_candidato",
    "send_progress_report": "enviar_relatorio_progresso",
    "schedule_interview": "agendar_entrevista",
    "reschedule_interview": "reagendar_entrevista",
    "cancel_interview": "cancelar_entrevista",
    "send_interview_reminder": "enviar_lembrete_entrevista",
    "list_today_interviews": "listar_entrevistas_hoje",
    "generate_self_scheduling_link": "gerar_link_agendamento",
    "create_generic_event": "criar_compromisso",
    "trigger_screening": "disparar_triagem",
    "dispatch_screening": "disparar_triagem",
    "start_screening": "iniciar_triagem",
    "analyze_profile": "analisar_perfil",
    "detailed_analysis": "analise_detalhada",
    "pause_job": "pausar_vaga",
    "close_job": "fechar_vaga",
    "duplicate_job": "duplicar_vaga",
    "reopen_job": "reabrir_vaga",
    "set_job_urgent": "vaga_urgente",
    "search_candidates": "buscar_candidatos",
    "suggest_candidates": "sugerir_candidatos",
    "rank_candidates": "rankear_candidatos",
    "compare_candidates": "comparar_candidatos",
    "tag_candidates": "taguear_candidatos",
    "add_candidate": "adicionar_candidato",
    "export_candidates": "exportar_candidatos",
    "generate_kpi_report": "gerar_relatorio_kpi",
    "job_health_check": "health_check_vaga",
    "analyze_funnel": "analisar_funil",
    "generate_daily_briefing": "resumo_agenda",
    "create_task": "criar_tarefa",
    "create_note": "criar_nota",
    "check_proactive_alerts": "alertas_proativos",
    "create_automation": "criar_automacao",
}

JOB_ACTION_MAP: dict[str, str] = {
    "pausar": "pausar_vaga",
    "pause": "pausar_vaga",
    "fechar": "fechar_vaga",
    "encerrar": "fechar_vaga",
    "close": "fechar_vaga",
    "reabrir": "reabrir_vaga",
    "reopen": "reabrir_vaga",
    "duplicar": "duplicar_vaga",
    "duplicate": "duplicar_vaga",
    "urgente": "vaga_urgente",
    "urgent": "vaga_urgente",
    "marcar urgente": "vaga_urgente",
}

SKIP_ACTION_INTENTS = {"create_job", "greeting", "general_question", "unknown", "search_candidates"}


def _flatten_entities(entities: dict[str, Any]) -> dict[str, Any]:
    flat = dict(entities)
    if "entidades" in entities and isinstance(entities["entidades"], dict):
        flat.update(entities["entidades"])
    return flat


def map_intent_to_actionable(intent: str, entities: dict[str, Any]) -> str | None:
    if intent in SKIP_ACTION_INTENTS:
        return None
    flat = _flatten_entities(entities)
    if intent == "update_job":
        acao = (flat.get("ação") or flat.get("acao") or flat.get("action") or "").lower().strip()
        return JOB_ACTION_MAP.get(acao)
    # Try EN→PT translation map first
    mapped = INTENT_TO_ACTIONABLE.get(intent)
    if mapped:
        return mapped
    # Fallback: intent is already a PT key in ACTIONABLE_INTENTS
    if intent in ACTIONABLE_INTENTS:
        return intent
    return None


def _build_tool_schema_for_intent(action_id: str, config: dict[str, Any]) -> dict[str, Any]:
    """Constrói schema de tool Claude-compatible a partir de uma config ACTIONABLE_INTENTS."""
    required = config.get("required_params", [])
    optional = config.get("optional_params", [])
    param_labels = config.get("param_labels", {})
    clarification_prompts = config.get("clarification_prompts", {})

    properties: dict[str, Any] = {}
    for param in required + optional:
        label = param_labels.get(param, param)
        description = clarification_prompts.get(param, f"Valor para {label}")
        properties[param] = {"type": "string", "description": description}

    return {
        "name": action_id,
        "description": f"Executa a ação '{action_id}' com os parâmetros extraídos da mensagem.",
        "input_schema": {
            "type": "object",
            "properties": properties,
            "required": required,
        },
    }


async def _try_extract_params_with_llm(
    user_message: str,
    intent: str,
    config: dict[str, Any],
    collected_params: dict[str, Any],
    missing: list[str],
) -> dict[str, Any] | None:
    """
    Tenta extrair parâmetros faltantes via LLM (generate_with_tools, single-shot).

    Retorna dict com parâmetros completos (collected + extraídos) se conseguir
    preencher todos os required_params. Retorna None se falhar ou parâmetros
    continuarem faltando após a extração.
    """
    try:
        from app.services.llm import LLMService as _LLMService  # lazy import — patchable by tests
        llm_svc = _LLMService()
        tool_schema = _build_tool_schema_for_intent(config["action_id"], config)
        messages = [{"role": "user", "content": user_message}]
        system_prompt = (
            "Você é um assistente de RH. Extraia os parâmetros mencionados na mensagem do usuário "
            "e chame a ferramenta adequada. Se um parâmetro não for mencionado, omita o campo — "
            "nunca invente valores."
        )
        response = await llm_svc.generate_with_tools(
            messages=messages,
            tools=[tool_schema],
            system_prompt=system_prompt,
            max_tokens=512,
        )
        if response.is_tool_call and response.tool_calls:
            extracted = response.tool_calls[0].parameters
            merged = {**collected_params, **extracted}
            still_missing = [p for p in missing if not merged.get(p)]
            if not still_missing:
                return merged
    except Exception as e:
        logger.warning(f"LLM param extraction failed for intent '{intent}': {e}")
    return None



async def resolve_candidate_by_name(
    candidate_name: str,
    company_id: str | None = None,
    job_id: str | None = None,
    db=None,
) -> dict | None:
    """Module-level wrapper around ChatRepository.resolve_candidate_by_name for testability."""
    if db is None:
        return None
    from app.domains.chat.repositories.chat_repository import ChatRepository
    repo = ChatRepository(db)
    return await repo.resolve_candidate_by_name(candidate_name, company_id=company_id, job_id=job_id)


async def handle_action_flow(
    conversation_id: str,
    user_message_text: str,
    intent: str,
    entities: dict[str, Any],
    user_id: str,
    current_user: User,
    repo: ChatRepository | None = None,
    db=None,
) -> dict[str, Any] | None:
    # Support both repo and db kwargs for backwards compatibility
    if repo is None and db is not None:
        from app.domains.chat.repositories.chat_repository import ChatRepository as _CR
        repo = _CR(db)
    pending = pending_action_store.get(conversation_id)

    # Multi-turno: coletar parâmetro faltante se já há ação pendente
    if pending and not pending.awaiting_confirmation and pending.missing_params:
        next_param = pending.next_missing_param()
        answer = user_message_text.strip()
        if next_param == "candidate_id":
            cand_info = await resolve_candidate_by_name(
                answer,
                company_id=str(current_user.company_id) if current_user.company_id else None,
                job_id=pending.collected_params.get("job_id"),
                db=db if db is not None else (repo.db if repo else None),
            )
            if cand_info:
                pending.add_param("candidate_id", cand_info["id"])
                pending.add_param("candidate_name", answer)
            else:
                pending.add_param("candidate_name", answer)
        elif next_param == "job_id":
            job_info = await repo.resolve_job_id_by_title(answer, current_user.company_id)
            if job_info:
                pending.add_param("job_id", job_info["id"])
                pending.add_param("job_title", job_info["title"])
            else:
                pending.add_param("job_title", answer)
        else:
            pending.add_param(next_param, answer)

        if pending.is_complete:
            config = action_executor.get_action_config(pending.intent)
            if config and config.get("requires_confirmation", True):
                pending.awaiting_confirmation = True
                pending_action_store.save(conversation_id, pending)
                return {
                    "pending_action": {
                        "pending_id": pending.pending_id,
                        "intent": pending.intent,
                        "action_id": pending.action_id,
                        "awaiting_confirmation": True,
                        "collected_params": pending.collected_params,
                    }
                }
            elif config:
                context = {
                    "user_id": user_id,
                    "conversation_id": conversation_id,
                    "company_id": current_user.company_id,
                }
                result = await action_executor._execute_action(
                    pending.intent, config, pending.collected_params, context
                )
                pending_action_store.remove(conversation_id)
                return {
                    "action_result": {
                        "action_id": result.action_type or pending.action_id,
                        "success": result.status == "executed",
                        "message": result.message,
                        "data": result.data,
                        "status": result.status,
                    }
                }
        else:
            pending_action_store.save(conversation_id, pending)
            return {
                "pending_action": {
                    "pending_id": pending.pending_id,
                    "intent": pending.intent,
                    "action_id": pending.action_id,
                    "awaiting_confirmation": False,
                    "missing_params": pending.missing_params,
                    "collected_params": pending.collected_params,
                }
            }

    if pending and pending.awaiting_confirmation:
        if is_confirmation(user_message_text):
            config = action_executor.get_action_config(pending.intent)
            if config:
                # Security check: verify user access for destructive actions
                destructive_actions = {
            "pause_job", "close_job", "reopen_job", "move_candidate",
            "batch_move_candidates", "set_job_urgent", "cancel_interview",
        }
                if pending.intent in destructive_actions:
                    is_demo_user = current_user.email == "demo@wedotalent.com"
                    if is_demo_user:
                        logger.warning(f"Demo user {current_user.id} executing destructive action: {pending.intent}")
                    # For demo mode, we allow execution with warning. For production, add additional checks as needed.

                context = {"user_id": user_id, "conversation_id": conversation_id, "company_id": current_user.company_id}
                result = await action_executor._execute_action(
                    pending.intent, config, pending.collected_params, context
                )
                pending_action_store.remove(conversation_id)
                return {
                    "action_result": {
                        "action_id": result.action_type or pending.action_id,
                        "success": result.status == "executed",
                        "message": result.message,
                        "data": result.data,
                        "status": result.status,
                    }
                }
        elif is_rejection(user_message_text):
            pending_action_store.remove(conversation_id)
            return {
                "action_result": {
                    "action_id": pending.action_id,
                    "success": False,
                    "message": "Ação cancelada.",
                    "data": None,
                    "status": "cancelled",
                }
            }
        return None

    actionable_intent = map_intent_to_actionable(intent, entities)
    if not actionable_intent:
        return None

    if not action_executor.is_actionable(actionable_intent):
        return None

    config = action_executor.get_action_config(actionable_intent)
    if not config:
        return None

    collected_params: dict[str, Any] = {}
    flat = _flatten_entities(entities)
    cargo = flat.get("cargo") or flat.get("titulo_vaga") or flat.get("job_title") or flat.get("vaga") or flat.get("titulo") or flat.get("title")
    if cargo:
        company_id = current_user.company_id
        job_info = await repo.resolve_job_id_by_title(cargo, company_id)
        if job_info:
            collected_params["job_id"] = job_info["id"]
            collected_params["job_title"] = job_info["title"]
        else:
            collected_params["job_title"] = cargo

    candidato = flat.get("candidato") or flat.get("candidate_name") or flat.get("nome_candidato")
    if candidato:
        cand_info = await repo.resolve_candidate_by_name(
            candidato,
            company_id=str(current_user.company_id) if current_user.company_id else None,
            job_id=collected_params.get("job_id"),
        )
        if cand_info:
            collected_params["candidate_id"] = cand_info["id"]
            collected_params["candidate_name"] = candidato
            if cand_info.get("stage"):
                collected_params["from_stage"] = cand_info["stage"]
        else:
            collected_params["candidate_name"] = candidato

    etapa = flat.get("etapa") or flat.get("stage") or flat.get("to_stage")
    if etapa:
        collected_params["to_stage"] = etapa

    reason = entities.get("motivo") or entities.get("reason")
    if reason:
        collected_params["reason"] = reason

    missing = []
    for req in config.get("required_params", []):
        if req not in collected_params or not collected_params[req]:
            missing.append(req)

    # Tenta extrair parâmetros faltantes via LLM (generate_with_tools) antes de
    # entrar em modo multi-turno. Se bem-sucedido, missing será esvaziado.
    if missing:
        extracted = await _try_extract_params_with_llm(
            user_message=user_message_text,
            intent=actionable_intent,
            config=config,
            collected_params=collected_params,
            missing=missing,
        )
        if extracted:
            collected_params = extracted
            missing = [
                p for p in config.get("required_params", [])
                if not collected_params.get(p)
            ]
            logger.info(
                f"LLM param extraction succeeded for '{actionable_intent}': "
                f"remaining missing={missing}"
            )

    requires_confirmation = config.get("requires_confirmation", True)

    if not missing and requires_confirmation:
        pending_state = PendingActionState(
            pending_id=str(uuid.uuid4()),
            intent=actionable_intent,
            action_id=config["action_id"],
            domain_id=config["domain_id"],
            collected_params=collected_params,
            missing_params=[],
            conversation_id=conversation_id,
            company_id=current_user.company_id,
            awaiting_confirmation=True,
        )
        pending_action_store.save(conversation_id, pending_state)
        return {
            "pending_action": {
                "pending_id": pending_state.pending_id,
                "intent": actionable_intent,
                "action_id": config["action_id"],
                "awaiting_confirmation": True,
                "collected_params": collected_params,
            }
        }

    if not missing and not requires_confirmation:
        # Security check: verify user access for destructive actions
        destructive_actions = {
            "pause_job", "close_job", "reopen_job", "move_candidate",
            "batch_move_candidates", "set_job_urgent", "cancel_interview",
        }
        if actionable_intent in destructive_actions:
            is_demo_user = current_user.email == "demo@wedotalent.com"
            if is_demo_user:
                logger.warning(f"Demo user {current_user.id} executing destructive action: {actionable_intent}")
            # For demo mode, we allow execution with warning. For production, add additional checks as needed.

        context = {"user_id": user_id, "conversation_id": conversation_id, "company_id": current_user.company_id}
        result = await action_executor._execute_action(
            actionable_intent, config, collected_params, context
        )
        return {
            "action_result": {
                "action_id": result.action_type or config["action_id"],
                "success": result.status == "executed",
                "message": result.message,
                "data": result.data,
                "status": result.status,
            }
        }

    if missing:
        pending_state = PendingActionState(
            pending_id=str(uuid.uuid4()),
            intent=actionable_intent,
            action_id=config["action_id"],
            domain_id=config["domain_id"],
            collected_params=collected_params,
            missing_params=missing,
            conversation_id=conversation_id,
            company_id=current_user.company_id,
            awaiting_confirmation=False,
        )
        pending_action_store.save(conversation_id, pending_state)
        return {
            "pending_action": {
                "pending_id": pending_state.pending_id,
                "intent": actionable_intent,
                "action_id": config["action_id"],
                "awaiting_confirmation": False,
                "missing_params": missing,
                "collected_params": collected_params,
            }
        }

    return None


# Verbos por action_id para mensagens de confirmação
_ACTION_VERBS: dict[str, str] = {
    "move_candidate": "mover",
    "batch_move_candidates": "mover em lote",
    "pause_job": "pausar",
    "close_job": "fechar",
    "reopen_job": "reabrir",
    "duplicate_job": "duplicar",
    "set_job_urgent": "classificar como urgente",
    "start_screening": "iniciar triagem para",
    "send_email": "enviar email para",
    "send_feedback": "enviar feedback para",
    "send_whatsapp": "enviar WhatsApp para",
    "send_screening_invite": "enviar convite de triagem para",
    "schedule_interview": "agendar entrevista com",
    "reschedule_interview": "reagendar entrevista de",
    "cancel_interview": "cancelar entrevista de",
    "share_candidate_profile": "compartilhar perfil de",
    "send_candidate_report": "enviar parecer de",
    "send_progress_report": "enviar relatório de progresso da",
    "add_candidate": "cadastrar",
    "create_automation": "criar automação",
}

_PARAM_QUESTIONS: dict[str, str] = {
    "candidate_id": "Qual candidato?",
    "candidate_ids": "Quais candidatos?",
    "to_stage": "Para qual etapa do pipeline?",
    "job_id": "Qual vaga?",
    "subject": "Qual o assunto do email?",
    "body": "Qual a mensagem?",
    "message": "Qual a mensagem?",
    "reason": "Qual o motivo?",
    "name": "Qual o nome?",
    "email": "Qual o email?",
    "new_datetime": "Para qual nova data e horário?",
    "trigger": "Qual o gatilho da automação?",
    "action": "Qual ação automática deve ser executada?",
    "tag": "Qual tag/etiqueta deseja aplicar?",
    "query": "Quais critérios de busca?",
    "feedback_type": "Qual o tipo de feedback? (aprovação/rejeição/parcial)",
    "recipient_email": "Qual o email do destinatário?",
}


def _build_response_from_action(action_metadata: dict[str, Any]) -> str | None:
    """Gera texto de resposta para o usuário a partir do resultado da action flow.

    Retorna None quando não há ação ativa (fluxo normal do orquestrador).
    """
    if not action_metadata:
        return None

    # Ação executada (sucesso ou erro)
    if "action_result" in action_metadata:
        result = action_metadata["action_result"]
        status = result.get("status")
        if status == "executed":
            return f"{result.get('message', 'Acao realizada com sucesso.')}"
        if status == "cancelled":
            return "Ação cancelada."
        if status == "error":
            return f"Não foi possível executar a ação: {result.get('message', 'erro desconhecido')}."
        return result.get("message") or "Ação processada."

    # Ação pendente (confirmação ou coleta de params)
    if "pending_action" in action_metadata:
        pending = action_metadata["pending_action"]
        intent = pending.get("intent", "")
        action_id = pending.get("action_id", "")
        collected = pending.get("collected_params", {})

        if pending.get("awaiting_confirmation"):
            verb = _ACTION_VERBS.get(action_id, "executar")
            parts = []
            if "candidate_name" in collected:
                parts.append(f"o candidato **{collected['candidate_name']}**")
            if "to_stage" in collected:
                parts.append(f"para a etapa **{collected['to_stage']}**")
            if "job_title" in collected:
                parts.append(f"na vaga **{collected['job_title']}**")
            summary = " ".join(parts) if parts else "esta ação"
            return f"Vou {verb} {summary}. Confirma? (sim/não)"

        # Coleta de parâmetros — usar clarification_prompts do config ou fallback
        missing = pending.get("missing_params", [])
        if missing:
            next_param = missing[0]
            # Tenta obter prompt do ACTIONABLE_INTENTS
            intent_cfg = ACTIONABLE_INTENTS.get(intent, {})
            clarification_prompts = intent_cfg.get("clarification_prompts", {})
            return clarification_prompts.get(next_param) or _PARAM_QUESTIONS.get(next_param, f"Qual o valor para '{next_param}'?")

    return None

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


async def _invoke_orchestrator(
    user_message: str,
    user_id: str,
    conversation_id: str,
    company_id: str,
    page_context: dict[str, Any] | None = None,
) -> dict:
    """Executa a mensagem do usuário via Orchestrator + ReAct agents.

    Retorna dict compatível com o restante do handler:
      response      str   — texto da resposta da LIA
      intent        str   — domínio/intent detectado
      entities      dict  — entidades extraídas (se o agente retornar)
      workflow_data dict  — search_results ou response_plan para context_data do FE
    """
    from app.api.orchestrator_routes import orchestrator as _orch

    if _orch is None:
        logger.warning("[chat] Orchestrator não inicializado, retornando resposta de fallback")
        return {
            "response": "Estou inicializando. Por favor, tente novamente em instantes.",
            "intent": "",
            "entities": {},
            "workflow_data": {},
        }

    orch_context: dict[str, Any] = {"company_id": company_id}
    if page_context:
        if page_context.get("job_vacancy_id"):
            orch_context["job_vacancy_id"] = page_context["job_vacancy_id"]
        if page_context.get("job_id"):
            orch_context["job_vacancy_id"] = page_context["job_id"]
        if page_context.get("candidate_ids"):
            orch_context["candidate_ids"] = page_context["candidate_ids"]
        if page_context.get("page_type"):
            orch_context["page_type"] = page_context["page_type"]
        if page_context.get("job_context"):
            orch_context["job_context"] = page_context["job_context"]

    result = await _orch.process_request(
        user_id=user_id,
        message=user_message,
        conversation_id=conversation_id,
        context=orch_context,
    )

    response_text = result.get("message") or ""
    intent = result.get("intent") or ""
    result_data = (result.get("result") or {}).get("data") or {}
    entities: dict = result_data if isinstance(result_data, dict) else {}

    # Mapeia chaves de workflow para context_data do FE (search_results, response_plan)
    workflow_data: dict = {}
    if "search_results" in entities:
        workflow_data["search_results"] = entities["search_results"]
    if "response_plan" in entities:
        workflow_data["response_plan"] = entities["response_plan"]

    return {
        "response": response_text,
        "intent": intent,
        "entities": entities,
        "workflow_data": workflow_data,
    }


router = APIRouter(prefix="/chat", tags=["chat"])


# =============================================
# REST API ENDPOINTS
# =============================================

@router.post("", response_model=ChatResponse)
async def send_message(
    message_data: MessageCreate,
    current_user: User = Depends(get_current_user_or_demo),
    repo: ChatRepository = Depends(get_chat_repo),
):
    """
    Send a message to LIA and get response.

    This is the REST alternative to WebSocket for simpler integrations.
    """
    user_id = str(current_user.id)
    conversation_id = message_data.conversation_id

    # Create or get conversation
    if not conversation_id:
        conversation = await repo.create_conversation(user_id)
        conversation_id = str(conversation.id)
    else:
        conversation = await repo.get_conversation_by_id(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

    # Save user message
    await repo.add_user_message(conversation.id, message_data.content)

    page_context = message_data.context or {}

    orch_result = await _invoke_orchestrator(
        user_message=message_data.content,
        user_id=user_id,
        conversation_id=conversation_id,
        company_id=current_user.company_id,
        page_context=page_context,
    )
    lia_response = orch_result["response"]
    detected_intent = orch_result["intent"]
    detected_entities = orch_result["entities"]

    if page_context.get("job_vacancy_id") and "job_id" not in detected_entities:
        detected_entities["job_id"] = page_context["job_vacancy_id"]

    if lia_response:
        action_metadata = None
        try:
            action_metadata = await handle_action_flow(
                conversation_id=conversation_id,
                user_message_text=message_data.content,
                intent=detected_intent,
                entities=detected_entities,
                user_id=user_id,
                current_user=current_user,
                repo=repo,
            )
        except Exception as e:
            logger.error(f"Action flow error: {e}", exc_info=True)

        # Ciclo fechado: sobrescreve resposta quando há resultado de ação
        action_response = _build_response_from_action(action_metadata) if action_metadata else None
        final_response = action_response if action_response else lia_response

        msg_metadata: dict[str, Any] = {
            "intent": detected_intent,
            "entities": detected_entities,
        }

        if action_metadata:
            msg_metadata.update(action_metadata)

        ai_message = await repo.add_ai_message(
            conversation.id,
            final_response,
            msg_metadata,
        )

        await repo.update_conversation_intent(conversation, detected_intent, orch_result["workflow_data"])
        await repo.set_conversation_title(conversation, message_data.content[:100])

        await repo.commit_and_refresh(ai_message, conversation)

        workflow_data = orch_result["workflow_data"]
        context_data = None

        if "search_results" in workflow_data:
            search_results = workflow_data["search_results"]
            candidates = search_results.get("candidates", [])
            total_found = search_results.get("total_found", 0)

            if total_found > 0 and len(candidates) > 0:
                context_data = {
                    "type": "candidates",
                    "title": f"Candidatos Encontrados ({total_found})",
                    "shouldDisplay": True,
                    "data": {
                        "candidates": candidates,
                        "total_found": total_found,
                        "source": search_results.get("source"),
                        "local_count": search_results.get("local_count", 0),
                        "global_count": search_results.get("global_count", 0),
                        "credits_consumed": search_results.get("credits_consumed", 0),
                    },
                }

        elif "response_plan" in workflow_data:
            response_plan = workflow_data.get("response_plan", {})
            if response_plan.get("render_frame"):
                frame = response_plan["render_frame"]
                context_data = {
                    "type": frame.get("type", "job-creation-progress"),
                    "title": frame.get("title", "Criação de Vaga"),
                    "shouldDisplay": True,
                    "data": frame.get("data", {}),
                }

        if context_data:
            ai_message.message_metadata = ai_message.message_metadata or {}
            ai_message.message_metadata["context_data"] = context_data

        return ChatResponse(
            message=MessageResponse(
                id=str(ai_message.id),
                conversation_id=str(ai_message.conversation_id),
                role=ai_message.role,
                content=ai_message.content,
                message_metadata=ai_message.message_metadata or {},
                created_at=ai_message.created_at,
            ),
            conversation=ConversationResponse(
                id=str(conversation.id),
                user_id=conversation.user_id,
                user_role=conversation.user_role or "",
                title=conversation.title,
                intent=conversation.intent,
                workflow_type=conversation.workflow_type,
                workflow_step=conversation.workflow_step,
                workflow_data=conversation.workflow_data or {},
                status=conversation.status,
                created_at=conversation.created_at,
                updated_at=conversation.updated_at,
            ),
        )

    raise HTTPException(status_code=500, detail="Failed to generate response")


@router.post("/with-attachments", response_model=ChatResponse)
async def send_message_with_attachments(
    content: str = Form(...),
    conversation_id: str | None = Form(None),
    attachments: list[UploadFile] = File(default=[]),
    audio: UploadFile | None = File(default=None),
    current_user: User = Depends(get_current_user_or_demo),
    repo: ChatRepository = Depends(get_chat_repo),
):
    """
    Send a message to LIA with file attachments and/or audio.
    Uses the same conversation flow as send_message with attachment metadata.
    """
    attachment_info = []
    audio_info = None

    if attachments:
        for file in attachments:
            file_path = UPLOAD_DIR / f"{uuid.uuid4()}_{file.filename}"
            file_content = await file.read()
            with open(file_path, "wb") as f:
                f.write(file_content)

            file_size_kb = len(file_content) / 1024
            attachment_info.append({
                "filename": file.filename,
                "content_type": file.content_type,
                "size_kb": round(file_size_kb, 1),
                "path": str(file_path),
            })

    if audio:
        audio_path = UPLOAD_DIR / f"{uuid.uuid4()}_audio.webm"
        audio_content = await audio.read()
        with open(audio_path, "wb") as f:
            f.write(audio_content)
        audio_info = {
            "path": str(audio_path),
            "size_kb": round(len(audio_content) / 1024, 1),
        }

    augmented_content = content
    if attachment_info:
        files_summary = ", ".join([f"{a['filename']} ({a['size_kb']}KB)" for a in attachment_info])
        augmented_content = f"[Arquivos anexados: {files_summary}]\n\n{content}"

    if audio_info:
        augmented_content = f"[Áudio gravado para análise]\n\n{augmented_content}"

    user_id = str(current_user.id)
    if not conversation_id:
        conversation = await repo.create_conversation(user_id)
        conversation_id = str(conversation.id)
    else:
        conversation = await repo.get_conversation_by_id(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

    await repo.add_user_message(
        conversation.id,
        augmented_content,
        {"attachments": attachment_info, "audio": audio_info},
    )

    # Augmented content includes attachment/audio context for the orchestrator
    orch_result = await _invoke_orchestrator(
        user_message=augmented_content,
        user_id=user_id,
        conversation_id=conversation_id,
        company_id=current_user.company_id,
    )
    lia_response = orch_result["response"]

    if lia_response:
        ai_message = await repo.add_ai_message(
            conversation.id,
            lia_response,
            {
                "intent": orch_result["intent"],
                "entities": orch_result["entities"],
                "processed_attachments": attachment_info,
                "processed_audio": audio_info,
            },
        )

        await repo.update_conversation_intent(conversation, orch_result["intent"], orch_result["workflow_data"])

        if not conversation.title:
            if attachment_info:
                conversation.title = f"Análise de {len(attachment_info)} arquivo(s)"
            elif audio_info:
                conversation.title = "Análise de áudio"
            else:
                conversation.title = content[:100]

        await repo.commit_and_refresh(ai_message, conversation)

        workflow_data = orch_result["workflow_data"]
        context_data = None

        if "search_results" in workflow_data:
            search_results = workflow_data["search_results"]
            candidates = search_results.get("candidates", [])
            total_found = search_results.get("total_found", 0)

            if total_found > 0 and len(candidates) > 0:
                context_data = {
                    "type": "candidates",
                    "title": f"Candidatos Encontrados ({total_found})",
                    "shouldDisplay": True,
                    "data": {
                        "candidates": candidates,
                        "total_found": total_found,
                        "source": search_results.get("source"),
                        "local_count": search_results.get("local_count", 0),
                        "global_count": search_results.get("global_count", 0),
                        "credits_consumed": search_results.get("credits_consumed", 0),
                    },
                }

        elif "response_plan" in workflow_data:
            response_plan = workflow_data.get("response_plan", {})
            if response_plan.get("render_frame"):
                frame = response_plan["render_frame"]
                context_data = {
                    "type": frame.get("type", "job-creation-progress"),
                    "title": frame.get("title", "Criação de Vaga"),
                    "shouldDisplay": True,
                    "data": frame.get("data", {}),
                }

        if context_data:
            ai_message.message_metadata = ai_message.message_metadata or {}
            ai_message.message_metadata["context_data"] = context_data

        return ChatResponse(
            message=MessageResponse(
                id=str(ai_message.id),
                conversation_id=str(ai_message.conversation_id),
                role=ai_message.role,
                content=ai_message.content,
                message_metadata=ai_message.message_metadata or {},
                created_at=ai_message.created_at,
            ),
            conversation=ConversationResponse(
                id=str(conversation.id),
                user_id=conversation.user_id,
                user_role=conversation.user_role or "",
                title=conversation.title,
                intent=conversation.intent,
                workflow_type=conversation.workflow_type,
                workflow_step=conversation.workflow_step,
                workflow_data=conversation.workflow_data or {},
                status=conversation.status,
                created_at=conversation.created_at,
                updated_at=conversation.updated_at,
            ),
        )

    raise HTTPException(status_code=500, detail="Failed to generate response")


@router.get("/conversations", response_model=ConversationListResponse)
async def list_conversations(
    current_user: User = Depends(get_current_user_or_demo),
    page: int = 1,
    page_size: int = 20,
    repo: ChatRepository = Depends(get_chat_repo),
):
    """
    List user's conversations.
    """
    user_id = str(current_user.id)
    conversations, total = await repo.list_conversations(user_id, page, page_size)

    return ConversationListResponse(
        conversations=conversations,
        total=total,
        page=page,
        page_size=page_size,
    )


# =============================================
# WEBSOCKET ENDPOINT
# =============================================

class ConnectionManager:
    """Manage WebSocket connections."""

    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]

    async def send_message(self, user_id: str, message: dict):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_json(message)


manager = ConnectionManager()


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: str,
    repo: ChatRepository = Depends(get_chat_repo),
):
    """
    WebSocket endpoint for real-time chat with LIA.

    Message format:
    {
        "type": "message",
        "content": "text",
        "conversation_id": "uuid" (optional)
    }

    Response format:
    {
        "type": "message",
        "content": "text",
        "conversation_id": "uuid",
        "metadata": {...}
    }
    """
    await manager.connect(user_id, websocket)
    company_id = None

    try:
        while True:
            data = await websocket.receive_json()

            if data["type"] == "message":
                conversation_id = data.get("conversation_id")
                user_content = data["content"]

                # Create or get conversation
                if not conversation_id:
                    conversation = await repo.create_conversation(user_id)
                    conversation_id = str(conversation.id)
                else:
                    conversation = await repo.get_conversation_by_id(conversation_id)

                # Save user message
                await repo.add_user_message(conversation.id, user_content)

                # Run LIA via Orchestrator + ReAct agents
                ws_orch = await _invoke_orchestrator(
                    user_message=user_content,
                    user_id=user_id,
                    conversation_id=conversation_id,
                    company_id=company_id,
                )
                lia_response = ws_orch["response"]

                if lia_response:
                    ws_action_metadata = None
                    try:
                        _ws_user = type("_U", (), {
                            "id": user_id,
                            "email": "",
                            "company_id": None,
                        })()
                        ws_action_metadata = await handle_action_flow(
                            conversation_id=conversation_id,
                            user_message_text=user_content,
                            intent=ws_orch["intent"],
                            entities=ws_orch["entities"],
                            user_id=user_id,
                            current_user=_ws_user,
                            repo=repo,
                        )
                    except Exception as _e:
                        logger.error(f"WS action flow error: {_e}", exc_info=True)

                    ws_action_response = _build_response_from_action(ws_action_metadata) if ws_action_metadata else None
                    ws_final_response = ws_action_response if ws_action_response else lia_response

                    ws_msg_metadata: dict[str, Any] = {
                        "intent": ws_orch["intent"],
                        "entities": ws_orch["entities"],
                    }
                    if ws_action_metadata:
                        ws_msg_metadata.update(ws_action_metadata)

                    await repo.add_ai_message(
                        conversation.id,
                        ws_final_response,
                        ws_msg_metadata,
                    )
                    conversation.intent = ws_orch["intent"]

                    await repo.commit()

                    await manager.send_message(user_id, {
                        "type": "message",
                        "content": ws_final_response,
                        "conversation_id": conversation_id,
                        "metadata": ws_msg_metadata,
                    })

    except WebSocketDisconnect:
        manager.disconnect(user_id)


# =============================================
# SSE STREAMING ENDPOINT
# =============================================

_LIA_STREAM_SYSTEM_PROMPT = """Você é LIA, a assistente de recrutamento inteligente da WeDOTalent.
Você ajuda recrutadores a criar vagas, buscar candidatos, avaliar perfis e gerenciar pipelines de contratação.
Seja objetiva, profissional e útil. Responda sempre em português brasileiro.
Use markdown quando útil (listas, negrito), mas evite formatação excessiva em respostas simples."""


async def _sse_event_generator(
    conversation_id: str,
    user_message: str,
    history: list[dict[str, str]],
    repo: ChatRepository,
    conversation_obj,
) -> AsyncGenerator[str, None]:
    """Streams Claude tokens as SSE events and persists the full response."""
    from anthropic import AsyncAnthropic

    api_key = os.environ.get("AI_INTEGRATIONS_ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
    base_url = os.environ.get("AI_INTEGRATIONS_ANTHROPIC_BASE_URL")
    if not api_key:
        yield f"data: {json.dumps({'error': 'LLM not configured'})}\n\n"
        return

    client_kwargs: dict = {"api_key": api_key}
    if base_url:
        client_kwargs["base_url"] = base_url
    client = AsyncAnthropic(**client_kwargs)
    full_response = ""

    try:
        async with client.messages.stream(
            model="claude-sonnet-4-6",
            max_tokens=2048,
            system=_LIA_STREAM_SYSTEM_PROMPT,
            messages=history,
        ) as stream:
            async for text_chunk in stream.text_stream:
                full_response += text_chunk
                yield f"data: {json.dumps({'token': text_chunk})}\n\n"

        yield "data: [DONE]\n\n"

        # Persist AI response to DB after streaming completes
        await repo.add_ai_message(
            conversation_obj.id,
            full_response,
            {"stream": True},
        )
        await repo.commit()

    except Exception as exc:
        logger.error(f"SSE stream error: {exc}", exc_info=True)
        yield f"data: {json.dumps({'error': str(exc)})}\n\n"


@router.post("/stream", response_model=None)
async def stream_message(
    request: Request,
    current_user: User = Depends(get_current_user_or_demo),
    repo: ChatRepository = Depends(get_chat_repo),
):
    """
    Stream LIA response as SSE (Server-Sent Events).

    Request body: {"content": "...", "conversation_id": "..." (optional)}

    Events emitted:
      data: {"token": "..."} — incremental token
      data: [DONE]           — stream finished
      data: {"error": "..."}  — on error
    """
    body = await request.json()
    user_content: str = body.get("content", "").strip()
    conversation_id: str | None = body.get("conversation_id")

    if not user_content:
        raise HTTPException(status_code=422, detail="content is required")

    user_id = str(current_user.id)

    # Create or retrieve conversation
    if not conversation_id:
        conversation = await repo.create_conversation(user_id)
        conversation_id = str(conversation.id)
    else:
        conversation = await repo.get_conversation_by_id(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

    # Save user message
    await repo.add_user_message(conversation.id, user_content)

    # Build history for Claude (last 20 messages to stay within context limits)
    history_msgs = await repo.get_recent_messages(conversation.id, limit=20)
    history = [
        {"role": "user" if m.role == "human" else "assistant", "content": m.content}
        for m in history_msgs
    ]

    return StreamingResponse(
        _sse_event_generator(conversation_id, user_content, history, repo, conversation),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.post("/actions/candidate-field-update", response_model=None)
async def direct_candidate_field_update(
    request: Request,
    current_user: User = Depends(get_current_user_or_demo),
    repo: ChatRepository = Depends(get_chat_repo),
):
    """
    Structured endpoint to update one or more candidate fields directly.
    Used by the CV upload closed-loop confirmation flow to avoid
    reconstructing actions from natural language text.
    """
    body = await request.json()
    candidate_id: str = body.get("candidate_id", "")
    candidate_name: str = body.get("candidate_name", "").strip()
    fields: dict = body.get("fields", {})

    if not fields:
        raise HTTPException(status_code=400, detail="fields are required")

    # Resolve candidate_id by name if not provided directly
    if not candidate_id and candidate_name:
        try:
            found_id = await repo.lookup_candidate_id_by_name(candidate_name)
            if found_id:
                candidate_id = found_id
            else:
                raise HTTPException(status_code=404, detail=f"Candidato '{candidate_name}' não encontrado.")
        except HTTPException:
            raise
        except Exception as lookup_err:
            logger.warning(f"Candidate name lookup failed: {lookup_err}")
            raise HTTPException(status_code=400, detail="Não foi possível localizar o candidato pelo nome.")

    if not candidate_id:
        raise HTTPException(status_code=400, detail="candidate_id or candidate_name is required")

    intent_key = "atualizar_campo_candidato"
    action_config = ACTIONABLE_INTENTS.get(intent_key)
    if not action_config:
        raise HTTPException(status_code=500, detail="Action config not found for atualizar_campo_candidato")

    company_id = getattr(current_user, "company_id", None)

    # Authorization: verify the candidate belongs to the requester's company.
    # Uses vacancy_candidates join table which has both company_id and candidate_id.
    # If the user has no company_id (e.g. demo mode), skip the check and allow update.
    if company_id:
        try:
            owns = await repo.check_candidate_ownership(candidate_id, str(company_id))
            if not owns:
                raise HTTPException(
                    status_code=403,
                    detail="Candidate does not belong to your company or does not exist.",
                )
        except HTTPException:
            raise
        except Exception as authz_err:
            logger.warning(f"Authz check failed, proceeding cautiously: {authz_err}")
            # If vacancy_candidates table doesn't exist or query fails, reject
            raise HTTPException(status_code=403, detail="Unable to verify candidate ownership.")

    ctx = {
        "user_id": str(current_user.id),
        "company_id": company_id,
        "tenant_id": str(company_id) if company_id else None,
    }

    results = []
    for field_name, field_value in fields.items():
        result: ActionResult = await action_executor._execute_action(
            intent=intent_key,
            config=action_config,
            params={
                "candidate_id": candidate_id,
                "field_name": field_name,
                "field_value": str(field_value),
            },
            context=ctx,
        )
        results.append({
            "field": field_name,
            "value": field_value,
            "status": result.status,
            "message": result.message,
            "error": getattr(result, "error_detail", None),
        })

    all_ok = all(r["status"] in ("executed", "success") for r in results)
    updated_count = sum(1 for r in results if r["status"] in ("executed", "success"))
    return {
        "success": all_ok,
        "updated_count": updated_count,
        "total": len(results),
        "results": results,
    }
