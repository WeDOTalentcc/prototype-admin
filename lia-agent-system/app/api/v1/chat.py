"""
Chat API endpoints for LIA conversation.
"""
from typing import List, Optional, Dict, Any, AsyncGenerator
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File, Form, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, text
import uuid
import json
import os
import logging
import asyncio
from pathlib import Path
from datetime import datetime, timedelta

from app.core.database import get_db
from app.models.conversation import Conversation, Message
from app.schemas.chat import MessageCreate, ChatResponse, ConversationListResponse, MessageResponse, ConversationResponse
from app.auth.dependencies import get_current_user_or_demo
from app.auth.models import User
from app.orchestrator.pending_action import PendingActionStore, PendingActionState, pending_action_store
from app.orchestrator.action_executor import (
    ActionExecutorService, action_executor, ActionResult,
    is_confirmation, is_rejection, ACTIONABLE_INTENTS
)

logger = logging.getLogger(__name__)

INTENT_TO_ACTIONABLE: Dict[str, str] = {
    # English → PT (fallback for EN intents from orchestrator)
    "move_candidate": "mover_candidato",
    "update_candidate_status": "atualizar_status_candidato",
    "update_status": "atualizar_status_candidato",
    "reject_candidate": "reprovar_candidato",
    "approve_candidate": "aprovar_candidato",
    "send_email": "enviar_email",
    "send_message": "enviar_mensagem",
    "schedule_interview": "agendar_entrevista",
    "trigger_screening": "disparar_triagem",
    "dispatch_screening": "disparar_triagem",
    "start_screening": "iniciar_triagem",
    "analyze_profile": "analisar_perfil",
    "detailed_analysis": "analise_detalhada",
    "pause_job": "pausar_vaga",
    "close_job": "fechar_vaga",
    "duplicate_job": "duplicar_vaga",
    "reopen_job": "reabrir_vaga",
}

JOB_ACTION_MAP: Dict[str, str] = {
    "pausar": "pausar_vaga",
    "pause": "pausar_vaga",
    "fechar": "fechar_vaga",
    "encerrar": "fechar_vaga",
    "close": "fechar_vaga",
    "reabrir": "reabrir_vaga",
    "reopen": "reabrir_vaga",
    "duplicar": "duplicar_vaga",
    "duplicate": "duplicar_vaga",
}

SKIP_ACTION_INTENTS = {"create_job", "greeting", "general_question", "search_candidates", "unknown"}


def _flatten_entities(entities: Dict[str, Any]) -> Dict[str, Any]:
    flat = dict(entities)
    if "entidades" in entities and isinstance(entities["entidades"], dict):
        flat.update(entities["entidades"])
    return flat


def map_intent_to_actionable(intent: str, entities: Dict[str, Any]) -> Optional[str]:
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


def _build_tool_schema_for_intent(action_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """Constrói schema de tool Claude-compatible a partir de uma config ACTIONABLE_INTENTS."""
    required = config.get("required_params", [])
    optional = config.get("optional_params", [])
    param_labels = config.get("param_labels", {})
    clarification_prompts = config.get("clarification_prompts", {})

    properties: Dict[str, Any] = {}
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
    config: Dict[str, Any],
    collected_params: Dict[str, Any],
    missing: List[str],
) -> Optional[Dict[str, Any]]:
    """
    Tenta extrair parâmetros faltantes via LLM (generate_with_tools, single-shot).

    Retorna dict com parâmetros completos (collected + extraídos) se conseguir
    preencher todos os required_params. Retorna None se falhar ou parâmetros
    continuarem faltando após a extração.
    """
    try:
        from app.services.llm import LLMService  # lazy import para evitar circular
        llm_service = LLMService()
        tool_schema = _build_tool_schema_for_intent(config["action_id"], config)
        messages = [{"role": "user", "content": user_message}]
        system_prompt = (
            "Você é um assistente de RH. Extraia os parâmetros mencionados na mensagem do usuário "
            "e chame a ferramenta adequada. Se um parâmetro não for mencionado, omita o campo — "
            "nunca invente valores."
        )
        response = await llm_service.generate_with_tools(
            messages=messages,
            tools=[tool_schema],
            provider="claude",
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


async def resolve_job_id_by_title(db: AsyncSession, job_title: str, company_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    try:
        query = text("""
            SELECT id, title, status FROM job_vacancies
            WHERE LOWER(title) LIKE :pattern
            AND company_id = :company_id
            ORDER BY updated_at DESC LIMIT 1
        """)
        result = await db.execute(query, {"pattern": f"%{job_title.lower()}%", "company_id": company_id})
        row = result.fetchone()
        if row:
            return {"id": str(row.id), "title": row.title, "status": row.status}
    except Exception as e:
        logger.warning(f"Failed to resolve job by title '{job_title}': {e}")
    return None


async def resolve_candidate_by_name(db: AsyncSession, candidate_name: str) -> Optional[Dict[str, Any]]:
    try:
        query = text("""
            SELECT vc.id, vc.candidate_id, vc.stage, vc.status
            FROM vacancy_candidates vc
            JOIN candidates c ON c.id = vc.candidate_id
            WHERE LOWER(c.name) LIKE :pattern
            ORDER BY vc.updated_at DESC LIMIT 1
        """)
        result = await db.execute(query, {"pattern": f"%{candidate_name.lower()}%"})
        row = result.fetchone()
        if row:
            return {
                "id": str(row.id),
                "candidate_id": str(row.candidate_id),
                "stage": row.stage,
                "status": row.status,
            }
    except Exception as e:
        logger.warning(f"Failed to resolve candidate by name '{candidate_name}': {e}")
    return None


async def handle_action_flow(
    conversation_id: str,
    user_message_text: str,
    intent: str,
    entities: Dict[str, Any],
    user_id: str,
    current_user: User,
    db: AsyncSession,
) -> Optional[Dict[str, Any]]:
    pending = pending_action_store.get(conversation_id)

    # Multi-turno: coletar parâmetro faltante se já há ação pendente
    if pending and not pending.awaiting_confirmation and pending.missing_params:
        next_param = pending.next_missing_param()
        answer = user_message_text.strip()
        if next_param == "candidate_id":
            cand_info = await resolve_candidate_by_name(db, answer)
            if cand_info:
                pending.add_param("candidate_id", cand_info["id"])
                pending.add_param("candidate_name", answer)
            else:
                pending.add_param("candidate_name", answer)
        elif next_param == "job_id":
            job_info = await resolve_job_id_by_title(db, answer, current_user.company_id)
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
                    "company_id": current_user.company_id or "demo_company",
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
                destructive_actions = {"pause_job", "close_job", "reopen_job", "move_candidate"}
                if pending.intent in destructive_actions:
                    is_demo_user = current_user.email == "demo@wedotalent.com"
                    if is_demo_user:
                        logger.warning(f"Demo user {current_user.id} ({current_user.email}) executing destructive action: {pending.intent}")
                    # For demo mode, we allow execution with warning. For production, add additional checks as needed.
                
                context = {"user_id": user_id, "conversation_id": conversation_id, "company_id": current_user.company_id or "demo_company"}
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

    collected_params: Dict[str, Any] = {}
    flat = _flatten_entities(entities)
    cargo = flat.get("cargo") or flat.get("titulo_vaga") or flat.get("job_title") or flat.get("vaga") or flat.get("titulo") or flat.get("title")
    if cargo:
        company_id = current_user.company_id or "demo_company"
        job_info = await resolve_job_id_by_title(db, cargo, company_id)
        if job_info:
            collected_params["job_id"] = job_info["id"]
            collected_params["job_title"] = job_info["title"]
        else:
            collected_params["job_title"] = cargo

    candidato = flat.get("candidato") or flat.get("candidate_name") or flat.get("nome_candidato")
    if candidato:
        cand_info = await resolve_candidate_by_name(db, candidato)
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
            company_id=current_user.company_id or "demo_company",
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
        destructive_actions = {"pause_job", "close_job", "reopen_job", "move_candidate"}
        if actionable_intent in destructive_actions:
            is_demo_user = current_user.email == "demo@wedotalent.com"
            if is_demo_user:
                logger.warning(f"Demo user {current_user.id} ({current_user.email}) executing destructive action: {actionable_intent}")
            # For demo mode, we allow execution with warning. For production, add additional checks as needed.
        
        context = {"user_id": user_id, "conversation_id": conversation_id, "company_id": current_user.company_id or "demo_company"}
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
            company_id=current_user.company_id or "demo_company",
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
_ACTION_VERBS: Dict[str, str] = {
    "move_candidate": "mover",
    "pause_job": "pausar",
    "close_job": "fechar",
    "reopen_job": "reabrir",
    "duplicate_job": "duplicar",
    "start_screening": "iniciar triagem para",
    "send_email": "enviar email para",
}

# Perguntas de clarificação genéricas por parâmetro
_PARAM_QUESTIONS: Dict[str, str] = {
    "candidate_id": "Qual candidato?",
    "to_stage": "Para qual etapa do pipeline?",
    "job_id": "Qual vaga?",
    "subject": "Qual o assunto do email?",
    "body": "Qual a mensagem?",
    "reason": "Qual o motivo?",
}


def _build_response_from_action(action_metadata: Dict[str, Any]) -> Optional[str]:
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

    result = await _orch.process_request(
        user_id=user_id,
        message=user_message,
        conversation_id=conversation_id,
        context={"company_id": company_id},
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
    db: AsyncSession = Depends(get_db)
):
    """
    Send a message to LIA and get response.
    
    This is the REST alternative to WebSocket for simpler integrations.
    """
    user_id = str(current_user.id)
    conversation_id = message_data.conversation_id
    
    # Create or get conversation
    if not conversation_id:
        conversation = Conversation(
            user_id=user_id,
            user_role="recruiter",
            status="active"
        )
        db.add(conversation)
        await db.flush()
        conversation_id = str(conversation.id)
    else:
        result = await db.execute(
            select(Conversation).where(Conversation.id == uuid.UUID(conversation_id))
        )
        conversation = result.scalar_one_or_none()
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Save user message
    user_message = Message(
        conversation_id=conversation.id,
        role="human",
        content=message_data.content
    )
    db.add(user_message)
    await db.flush()
    
    # Run LIA via Orchestrator + ReAct agents
    orch_result = await _invoke_orchestrator(
        user_message=message_data.content,
        user_id=user_id,
        conversation_id=conversation_id,
        company_id=current_user.company_id or "demo_company",
    )
    lia_response = orch_result["response"]
    detected_intent = orch_result["intent"]
    detected_entities = orch_result["entities"]

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
                db=db,
            )
        except Exception as e:
            logger.error(f"Action flow error: {e}", exc_info=True)

        # Ciclo fechado: sobrescreve resposta quando há resultado de ação
        action_response = _build_response_from_action(action_metadata) if action_metadata else None
        final_response = action_response if action_response else lia_response

        msg_metadata = {
            "intent": detected_intent,
            "entities": detected_entities,
        }

        if action_metadata:
            msg_metadata.update(action_metadata)

        ai_message = Message(
            conversation_id=conversation.id,
            role="ai",
            content=final_response,
            message_metadata=msg_metadata
        )
        db.add(ai_message)

        conversation.intent = detected_intent
        conversation.workflow_data = orch_result["workflow_data"]

        if not conversation.title:
            conversation.title = message_data.content[:100]

        await db.commit()
        await db.refresh(ai_message)
        await db.refresh(conversation)

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
                        "credits_consumed": search_results.get("credits_consumed", 0)
                    }
                }
        
        elif "response_plan" in workflow_data:
            response_plan = workflow_data.get("response_plan", {})
            if response_plan.get("render_frame"):
                frame = response_plan["render_frame"]
                context_data = {
                    "type": frame.get("type", "job-creation-progress"),
                    "title": frame.get("title", "Criação de Vaga"),
                    "shouldDisplay": True,
                    "data": frame.get("data", {})
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
                created_at=ai_message.created_at
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
                updated_at=conversation.updated_at
            )
        )
    
    raise HTTPException(status_code=500, detail="Failed to generate response")


@router.post("/with-attachments", response_model=ChatResponse)
async def send_message_with_attachments(
    content: str = Form(...),
    conversation_id: Optional[str] = Form(None),
    attachments: List[UploadFile] = File(default=[]),
    audio: Optional[UploadFile] = File(default=None),
    current_user: User = Depends(get_current_user_or_demo),
    db: AsyncSession = Depends(get_db)
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
                "path": str(file_path)
            })
    
    if audio:
        audio_path = UPLOAD_DIR / f"{uuid.uuid4()}_audio.webm"
        audio_content = await audio.read()
        with open(audio_path, "wb") as f:
            f.write(audio_content)
        audio_info = {
            "path": str(audio_path),
            "size_kb": round(len(audio_content) / 1024, 1)
        }
    
    augmented_content = content
    if attachment_info:
        files_summary = ", ".join([f"{a['filename']} ({a['size_kb']}KB)" for a in attachment_info])
        augmented_content = f"[Arquivos anexados: {files_summary}]\n\n{content}"
    
    if audio_info:
        augmented_content = f"[Áudio gravado para análise]\n\n{augmented_content}"
    
    user_id = str(current_user.id)
    if not conversation_id:
        conversation = Conversation(
            user_id=user_id,
            user_role="recruiter",
            status="active"
        )
        db.add(conversation)
        await db.flush()
        conversation_id = str(conversation.id)
    else:
        result = await db.execute(
            select(Conversation).where(Conversation.id == uuid.UUID(conversation_id))
        )
        conversation = result.scalar_one_or_none()
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
    
    user_message = Message(
        conversation_id=conversation.id,
        role="human",
        content=augmented_content,
        message_metadata={
            "attachments": attachment_info,
            "audio": audio_info
        }
    )
    db.add(user_message)
    await db.flush()
    
    # Augmented content includes attachment/audio context for the orchestrator
    orch_result = await _invoke_orchestrator(
        user_message=augmented_content,
        user_id=user_id,
        conversation_id=conversation_id,
        company_id=current_user.company_id or "demo_company",
    )
    lia_response = orch_result["response"]

    if lia_response:
        ai_message = Message(
            conversation_id=conversation.id,
            role="ai",
            content=lia_response,
            message_metadata={
                "intent": orch_result["intent"],
                "entities": orch_result["entities"],
                "processed_attachments": attachment_info,
                "processed_audio": audio_info,
            }
        )
        db.add(ai_message)

        conversation.intent = orch_result["intent"]
        conversation.workflow_data = orch_result["workflow_data"]

        if not conversation.title:
            if attachment_info:
                conversation.title = f"Análise de {len(attachment_info)} arquivo(s)"
            elif audio_info:
                conversation.title = "Análise de áudio"
            else:
                conversation.title = content[:100]

        await db.commit()
        await db.refresh(ai_message)
        await db.refresh(conversation)

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
                        "credits_consumed": search_results.get("credits_consumed", 0)
                    }
                }
        
        elif "response_plan" in workflow_data:
            response_plan = workflow_data.get("response_plan", {})
            if response_plan.get("render_frame"):
                frame = response_plan["render_frame"]
                context_data = {
                    "type": frame.get("type", "job-creation-progress"),
                    "title": frame.get("title", "Criação de Vaga"),
                    "shouldDisplay": True,
                    "data": frame.get("data", {})
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
                created_at=ai_message.created_at
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
                updated_at=conversation.updated_at
            )
        )
    
    raise HTTPException(status_code=500, detail="Failed to generate response")


@router.get("/conversations", response_model=ConversationListResponse)
async def list_conversations(
    current_user: User = Depends(get_current_user_or_demo),
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """
    List user's conversations.
    """
    user_id = str(current_user.id)
    offset = (page - 1) * page_size
    
    # Get conversations
    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == user_id)
        .where(Conversation.is_archived == False)
        .order_by(desc(Conversation.updated_at))
        .limit(page_size)
        .offset(offset)
    )
    conversations = result.scalars().all()
    
    # Get total count
    count_result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == user_id)
        .where(Conversation.is_archived == False)
    )
    total = len(count_result.scalars().all())
    
    return ConversationListResponse(
        conversations=conversations,
        total=total,
        page=page,
        page_size=page_size
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
    db: AsyncSession = Depends(get_db)
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
    
    try:
        while True:
            # Receive message
            data = await websocket.receive_json()
            
            if data["type"] == "message":
                conversation_id = data.get("conversation_id")
                user_content = data["content"]
                
                # Create or get conversation
                if not conversation_id:
                    conversation = Conversation(
                        user_id=user_id,
                        user_role="recruiter",
                        status="active"
                    )
                    db.add(conversation)
                    await db.flush()
                    conversation_id = str(conversation.id)
                else:
                    result = await db.execute(
                        select(Conversation).where(Conversation.id == uuid.UUID(conversation_id))
                    )
                    conversation = result.scalar_one_or_none()
                
                # Save user message
                user_message = Message(
                    conversation_id=conversation.id,
                    role="human",
                    content=user_content
                )
                db.add(user_message)
                await db.flush()
                
                # Run LIA via Orchestrator + ReAct agents
                ws_orch = await _invoke_orchestrator(
                    user_message=user_content,
                    user_id=user_id,
                    conversation_id=conversation_id,
                    company_id="demo_company",
                )
                lia_response = ws_orch["response"]

                if lia_response:
                    ws_action_metadata = None
                    try:
                        from app.auth.models import User as _User
                        # WebSocket usa user_id string; cria user mínimo para action flow
                        _ws_user = type("_U", (), {
                            "id": user_id,
                            "email": "",
                            "company_id": "demo_company",
                        })()
                        ws_action_metadata = await handle_action_flow(
                            conversation_id=conversation_id,
                            user_message_text=user_content,
                            intent=ws_orch["intent"],
                            entities=ws_orch["entities"],
                            user_id=user_id,
                            current_user=_ws_user,
                            db=db,
                        )
                    except Exception as _e:
                        logger.error(f"WS action flow error: {_e}", exc_info=True)

                    ws_action_response = _build_response_from_action(ws_action_metadata) if ws_action_metadata else None
                    ws_final_response = ws_action_response if ws_action_response else lia_response

                    ws_msg_metadata: Dict[str, Any] = {
                        "intent": ws_orch["intent"],
                        "entities": ws_orch["entities"],
                    }
                    if ws_action_metadata:
                        ws_msg_metadata.update(ws_action_metadata)

                    ai_message = Message(
                        conversation_id=conversation.id,
                        role="ai",
                        content=ws_final_response,
                        message_metadata=ws_msg_metadata,
                    )
                    db.add(ai_message)
                    conversation.intent = ws_orch["intent"]

                    await db.commit()

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
    history: List[Dict[str, str]],
    db: AsyncSession,
    conversation_obj,
) -> AsyncGenerator[str, None]:
    """Streams Claude tokens as SSE events and persists the full response."""
    from anthropic import AsyncAnthropic

    api_key = os.environ.get("AI_INTEGRATIONS_ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        yield f"data: {json.dumps({'error': 'LLM not configured'})}\n\n"
        return

    client = AsyncAnthropic(api_key=api_key)
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
        ai_message = Message(
            conversation_id=conversation_obj.id,
            role="ai",
            content=full_response,
            message_metadata={"stream": True},
        )
        db.add(ai_message)
        await db.commit()

    except Exception as exc:
        logger.error(f"SSE stream error: {exc}", exc_info=True)
        yield f"data: {json.dumps({'error': str(exc)})}\n\n"


@router.post("/stream")
async def stream_message(
    request: Request,
    current_user: User = Depends(get_current_user_or_demo),
    db: AsyncSession = Depends(get_db),
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
    conversation_id: Optional[str] = body.get("conversation_id")

    if not user_content:
        raise HTTPException(status_code=422, detail="content is required")

    user_id = str(current_user.id)

    # Create or retrieve conversation
    if not conversation_id:
        conversation = Conversation(user_id=user_id, user_role="recruiter", status="active")
        db.add(conversation)
        await db.flush()
        conversation_id = str(conversation.id)
    else:
        result = await db.execute(
            select(Conversation).where(Conversation.id == uuid.UUID(conversation_id))
        )
        conversation = result.scalar_one_or_none()
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

    # Save user message
    user_msg = Message(conversation_id=conversation.id, role="human", content=user_content)
    db.add(user_msg)
    await db.flush()

    # Build history for Claude (last 20 messages to stay within context limits)
    hist_result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.created_at.desc())
        .limit(20)
    )
    history_msgs = list(reversed(hist_result.scalars().all()))
    history = [
        {"role": "user" if m.role == "human" else "assistant", "content": m.content}
        for m in history_msgs
    ]

    return StreamingResponse(
        _sse_event_generator(conversation_id, user_content, history, db, conversation),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.post("/actions/candidate-field-update")
async def direct_candidate_field_update(
    request: Request,
    current_user: User = Depends(get_current_user_or_demo),
    db: AsyncSession = Depends(get_db),
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
            name_result = await db.execute(
                text("SELECT id FROM candidates WHERE LOWER(name) LIKE LOWER(:name) LIMIT 1"),
                {"name": f"%{candidate_name}%"},
            )
            row = name_result.fetchone()
            if row:
                candidate_id = str(row[0])
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
            ownership_result = await db.execute(
                text("SELECT 1 FROM vacancy_candidates WHERE candidate_id = CAST(:cid AS uuid) AND company_id = CAST(:co AS uuid) LIMIT 1"),
                {"cid": candidate_id, "co": str(company_id)},
            )
            if ownership_result.fetchone() is None:
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
        "tenant_id": str(company_id or "default"),
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
