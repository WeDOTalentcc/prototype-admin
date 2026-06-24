"""Automation ReAct Agent — Tool Registry.

Wraps PlannedTaskService + LLMService operations into ToolDefinition format
so the ReActLoop can autonomously decide which tools to call.
"""
import json
import logging
from datetime import datetime
from typing import Any
from uuid import uuid4

from lia_agents_core.tool_adapter import ToolDefinition
from lia_agents_core.tool_adapter import ToolOutput

from app.shared.tool_handler import tool_handler

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tool wrappers
# ---------------------------------------------------------------------------

TASK_DECOMPOSITION_PROMPT = """Você é um especialista em planejamento e decomposição de tarefas para recrutamento.

## Tarefa Principal:
{task_description}

## Contexto Adicional:
{context}

## Instruções:
Decomponha esta tarefa em subtarefas menores e executáveis. Para cada subtarefa:
1. **Identificar subtarefas**: Liste todas as ações necessárias
2. **Estimar duração**: Em minutos (5min a 120min)
3. **Definir dependências**: Quais subtarefas dependem de outras?
4. **Atribuir domain_id + action_id**: Use APENAS combinações da lista abaixo
5. **Prioridade**: critical, high, medium, low

## Ações Disponíveis (domain_id + action_id):
- sourcing / search_candidates — buscar candidatos por critérios
- cv_screening / score_candidates — avaliar/pontuar candidatos
- cv_screening / evaluate_against_jd — avaliar candidato vs descrição da vaga
- cv_screening / parse_and_create_candidate — criar candidato a partir de CV
- cv_screening / add_to_vacancy — adicionar candidato a uma vaga
- cv_screening / add_approved_to_vacancy — adicionar candidato aprovado a uma vaga
- automation / move_candidate_stage — mover candidato de etapa no pipeline
- communication / send_notification — enviar notificação (email/whatsapp)
- job_management / generate_jd — gerar descrição de vaga

Se a subtarefa não se encaixa em nenhuma ação acima, use domain_id="automation" e action_id="generic_step".

## Formato de Resposta (JSON):
{{
    "main_task_summary": "Resumo",
    "subtasks": [
        {{
            "id": "temp_1",
            "title": "Título curto",
            "description": "Descrição detalhada do que fazer",
            "domain_id": "sourcing",
            "action_id": "search_candidates",
            "agent_type": "sourcing",
            "priority": "high",
            "estimated_duration": 30,
            "dependencies": [],
            "goal_criticality": 0.8,
            "context_mappings": {{"query": "critérios de busca"}}
        }}
    ],
    "execution_notes": "Observações",
    "estimated_total_duration": 90,
    "parallel_opportunities": ["temp_3 e temp_4 podem executar em paralelo"]
}}

IMPORTANTE: Cada subtarefa DEVE ter domain_id e action_id da lista acima.
Responda APENAS com o JSON válido."""

PRIORITY_ANALYSIS_PROMPT = """Você é um especialista em priorização de tarefas de recrutamento.

## Tarefas para Priorizar:
{tasks_json}

## Contexto:
{context}

## Critérios (pesos): Urgência 30% | Impacto 25% | Criticidade 25% | Eficiência 20%

## Responda com JSON:
{{
    "prioritized_tasks": [
        {{
            "task_id": "id",
            "priority_score": 0.85,
            "reasoning": "Justificativa",
            "recommended_priority": "high"
        }}
    ],
    "execution_recommendation": "Sugestão de ordem",
    "quick_wins": ["IDs de tarefas rápidas que desbloqueiam outras"]
}}

Responda APENAS com JSON válido."""


@tool_handler("automation")
async def _wrap_decompose_task(**kwargs: Any) -> dict[str, Any]:
    """Decompose a complex task into subtasks using LLM + PlannedTaskService."""
    from app.core.database import AsyncSessionLocal
    from app.domains.automation.services.planned_task_service import PlannedTaskService
    from app.models.planned_task import PlannedTaskPriority
    from app.domains.ai.services.llm import LLMService

    task_description = kwargs.get("task_description") or kwargs.get("description", "")
    company_id = kwargs.get("company_id")
    created_by = kwargs.get("user_id")
    goal_id = kwargs.get("goal_id")
    parent_task_id = kwargs.get("parent_task_id")
    deadline = kwargs.get("deadline")
    persist = kwargs.get("persist", True)

    if not task_description:
        return {"success": False, "message": "task_description é obrigatório"}

    context_str = json.dumps(
        {"goal_id": goal_id, "company_id": company_id, "deadline": str(deadline) if deadline else None},
        ensure_ascii=False,
    )

    try:
        llm = LLMService()
        llm_response = await llm.generate_json(
            prompt=TASK_DECOMPOSITION_PROMPT.format(
                task_description=task_description, context=context_str
            ),
            system_message="Você é um especialista em planejamento. Responda APENAS com JSON válido.",
        )
        if isinstance(llm_response, str):
            llm_response = json.loads(llm_response)

        subtasks_data = llm_response.get("subtasks", [])
        if not subtasks_data:
            return {"success": False, "message": "LLM não retornou subtarefas"}

        if not persist:
            return {
                "success": True,
                "subtasks": subtasks_data,
                "execution_notes": llm_response.get("execution_notes"),
                "estimated_total_duration": llm_response.get("estimated_total_duration"),
                "parallel_opportunities": llm_response.get("parallel_opportunities", []),
                "persisted": False,
            }

        svc = PlannedTaskService()
        temp_id_map: dict[str, str] = {}
        created_tasks = []

        async with AsyncSessionLocal() as db:
            for subtask in subtasks_data:
                temp_id = subtask.get("id", f"temp_{uuid4().hex[:8]}")
                real_deps = [
                    temp_id_map[dep]
                    for dep in subtask.get("dependencies", [])
                    if dep in temp_id_map
                ]
                task = await svc.create_planned_task(
                    db=db,
                    title=subtask.get("title"),
                    description=subtask.get("description"),
                    agent_type=subtask.get("agent_type"),
                    priority=PlannedTaskPriority(subtask.get("priority", "medium")),
                    parent_task_id=parent_task_id,
                    dependencies=real_deps,
                    estimated_duration=subtask.get("estimated_duration"),
                    deadline=deadline if isinstance(deadline, datetime) else None,
                    goal_id=goal_id,
                    goal_criticality=subtask.get("goal_criticality", 0.5),
                    company_id=company_id,
                    created_by=created_by,
                )
                temp_id_map[temp_id] = task.id
                created_tasks.append(task)

            task_ids = [t.id for t in created_tasks]
            await svc.reprioritize_tasks(db, task_ids)
            dag_result = await svc.build_task_dag(db, task_ids)
            await db.commit()

        return {
            "success": True,
            "subtasks_created": len(created_tasks),
            "subtasks": [t.to_dict() for t in created_tasks],
            "dag": dag_result,
            "execution_notes": llm_response.get("execution_notes"),
            "estimated_total_duration": llm_response.get("estimated_total_duration"),
            "parallel_opportunities": llm_response.get("parallel_opportunities", []),
        }

    except json.JSONDecodeError as e:
        try:
            await db.rollback()
        except Exception:
            pass
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.error(f"[automation_tools] LLM JSON parse error: {e}")
        return {"success": False, "message": f"Erro ao parsear resposta da IA: {e}"}
    except Exception as e:
        try:
            await db.rollback()
        except Exception:
            pass
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.error(f"[automation_tools] decompose_task error: {e}", exc_info=True)
        return {"success": False, "message": str(e)}


@tool_handler("automation")
async def _wrap_prioritize_tasks(**kwargs: Any) -> dict[str, Any]:
    """Recalculate priority scores for tasks."""
    from app.core.database import AsyncSessionLocal
    from app.domains.automation.services.planned_task_service import PlannedTaskService

    task_ids = kwargs.get("task_ids", [])
    goal_id = kwargs.get("goal_id")

    svc = PlannedTaskService()
    async with AsyncSessionLocal() as db:
        if goal_id and not task_ids:
            tasks = await svc.get_tasks_by_goal(db, goal_id)
            task_ids = [t.id for t in tasks]

        if not task_ids:
            return {"success": False, "message": "Forneça task_ids ou goal_id"}

        prioritized = await svc.reprioritize_tasks(db, task_ids)

    return {
        "success": True,
        "prioritized_count": len(prioritized),
        "tasks": [
            {
                "id": t.id,
                "title": t.title,
                "priority": t.priority.value,
                "priority_score": t.priority_score,
                "status": t.status.value,
            }
            for t in prioritized
        ],
    }
@tool_handler("automation")
async def _wrap_get_execution_plan(**kwargs: Any) -> dict[str, Any]:
    """Generate an execution plan with parallel levels."""
    from app.core.database import AsyncSessionLocal
    from app.domains.automation.services.planned_task_service import CycleDetectedError, PlannedTaskService

    task_ids = kwargs.get("task_ids", [])
    goal_id = kwargs.get("goal_id")
    plan_name = kwargs.get("name", f"Plano - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    company_id = kwargs.get("company_id")
    created_by = kwargs.get("user_id")

    try:
        svc = PlannedTaskService()
        async with AsyncSessionLocal() as db:
            if goal_id and not task_ids:
                tasks = await svc.get_tasks_by_goal(db, goal_id)
                task_ids = [t.id for t in tasks]

            if not task_ids:
                return {"success": False, "message": "Forneça task_ids ou goal_id"}

            dag = await svc.build_task_dag(db, task_ids)
            if dag.get("has_cycle"):
                return {
                    "success": False,
                    "has_cycle": True,
                    "cycle_path": dag.get("cycle_path", []),
                    "message": "Ciclo detectado nas dependências",
                }

            plan = await svc.create_execution_plan(
                db=db,
                name=plan_name,
                task_ids=task_ids,
                goal_id=goal_id,
                company_id=company_id,
                created_by=created_by,
            )
            return {"success": True, "plan": plan.to_dict(), "dag": dag}

    except CycleDetectedError as e:
        return {"success": False, "has_cycle": True, "message": str(e)}
@tool_handler("automation")
async def _wrap_build_dag(**kwargs: Any) -> dict[str, Any]:
    """Build and validate a DAG from task dependencies."""
    from app.core.database import AsyncSessionLocal
    from app.domains.automation.services.planned_task_service import PlannedTaskService

    task_ids = kwargs.get("task_ids", [])
    if not task_ids:
        return {"success": False, "message": "Forneça task_ids"}

    svc = PlannedTaskService()
    async with AsyncSessionLocal() as db:
        result = await svc.build_task_dag(db, task_ids)
    return {"success": True, **result}
@tool_handler("automation")
async def _wrap_check_dependencies(**kwargs: Any) -> dict[str, Any]:
    """Check dependency status for a task."""
    from app.core.database import AsyncSessionLocal
    from app.domains.automation.services.planned_task_service import PlannedTaskService

    task_id = kwargs.get("task_id")
    if not task_id:
        return {"success": False, "message": "Forneça task_id"}

    svc = PlannedTaskService()
    async with AsyncSessionLocal() as db:
        result = await svc.check_dependencies(db, task_id)
    return {"success": True, **result}
@tool_handler("automation")
async def _wrap_get_next_tasks(**kwargs: Any) -> dict[str, Any]:
    """Get tasks ready for execution."""
    from app.core.database import AsyncSessionLocal
    from app.domains.automation.services.planned_task_service import PlannedTaskService

    svc = PlannedTaskService()
    async with AsyncSessionLocal() as db:
        tasks = await svc.get_next_tasks(
            db=db,
            goal_id=kwargs.get("goal_id"),
            parent_task_id=kwargs.get("parent_task_id"),
            company_id=kwargs.get("company_id"),
            agent_type=kwargs.get("agent_type"),
            limit=kwargs.get("limit", 5),
        )
    return {"success": True, "tasks": [t.to_dict() for t in tasks], "count": len(tasks)}

# ─── Webhook Event Types wizard tools (audit 2026-05-20 Sprint 5 F5) ────────
# 3 tools canonical pro wizard conversacional de configuracao de webhook
# manusear o catalogo dinamico de webhook_event_types (substitui catalogo
# hardcoded em plataforma-lia/.../webhook-types.ts + ALLOWED_EVENTS schema
# + JOB_STATUS_WEBHOOK_EVENTS + WebhookEvent enum).

import re as _re_we

_EVENT_TYPE_SLUG_RE = _re_we.compile(r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$")


@tool_handler("automation")
async def _wrap_suggest_webhook_event_types(**kwargs: Any) -> dict[str, Any]:
    """
    Sugere event types de webhook canonical relevantes para a company,
    opcionalmente filtrando por categoria (agents | candidates | jobs |
    interviews | offers | ats | system).

    Multi-tenancy: company_id obrigatorio via ContextVar JWT (@tool_handler).
    Retorna master + customs (ranqueados: customs primeiro, depois master,
    depreciados por ultimo).
    """
    from app.core.database import AsyncSessionLocal
    from app.domains.automation.repositories.webhook_event_type_repository import (
        WebhookEventTypeRepository,
    )

    company_id = kwargs.get("company_id")
    category_filter = (kwargs.get("category") or "").strip().lower() or None

    async with AsyncSessionLocal() as db:
        repo = WebhookEventTypeRepository(db)
        items = await repo.list_for_company(
            company_id=company_id, include_master=True
        )

    suggestions = []
    for item in items:
        data = item.data or {}
        category = (data.get("category") or "").lower()
        if category_filter and category != category_filter:
            continue
        deprecated = bool(data.get("deprecated", False))
        # Score: custom > master > deprecated
        score = 0
        if not item.is_master_template:
            score += 5
        if not deprecated:
            score += 3
        suggestions.append({
            "id": str(item.id),
            "event_type": data.get("event_type", ""),
            "label": data.get("label", ""),
            "category": category,
            "description": data.get("description"),
            "is_master": item.is_master_template,
            "deprecated": deprecated,
            "score": score,
        })

    suggestions.sort(key=lambda s: s["score"], reverse=True)
    top = suggestions[:20]

    filter_suffix = f", filtro categoria={category_filter}" if category_filter else ""
    return {
        "success": True,
        "data": {
            "suggestions": top,
            "total_in_catalog": len(items),
            "category_filter": category_filter,
        },
        "message": (
            f"{len(top)} event type(s) de webhook sugerido(s) "
            f"(top 20 de {len(items)} no catalogo da empresa{filter_suffix})."
        ),
    }


@tool_handler("automation")
async def _wrap_apply_webhook_event_subscription(**kwargs: Any) -> dict[str, Any]:
    """
    Aplica subscricao de evento canonical a um webhook target da company.

    Snapshot canonical B1: copia o event_type slug (e o data shape) do
    catalogo per-tenant para o array events da subscricao do webhook
    (in-memory; persistencia final ocorre via PATCH /webhooks/{id} ou na
    criacao do webhook). NAO sincroniza com master apos aplicacao.

    Multi-tenancy: company_id obrigatorio via ContextVar JWT.
    """
    from app.core.database import AsyncSessionLocal
    from app.domains.automation.repositories.webhook_event_type_repository import (
        WebhookEventTypeRepository,
    )
    import uuid as _uuid_we

    company_id = kwargs.get("company_id")
    event_type_id_raw = kwargs.get("event_type_id")
    webhook_target_url = (kwargs.get("webhook_target_url") or "").strip()
    target_company_webhook_id = kwargs.get("target_company_webhook_id")

    if not event_type_id_raw:
        return {
            "success": False,
            "fallback_used": True,
            "needs_manual_review": True,
            "message": "event_type_id obrigatorio",
        }
    if not webhook_target_url:
        return {
            "success": False,
            "fallback_used": True,
            "needs_manual_review": True,
            "message": "webhook_target_url obrigatorio",
        }

    try:
        event_type_uuid = (
            _uuid_we.UUID(event_type_id_raw)
            if isinstance(event_type_id_raw, str)
            else event_type_id_raw
        )
    except (ValueError, TypeError):
        return {
            "success": False,
            "fallback_used": True,
            "needs_manual_review": True,
            "message": f"event_type_id invalido: {event_type_id_raw}",
        }

    async with AsyncSessionLocal() as db:
        repo = WebhookEventTypeRepository(db)
        record = await repo.get_by_id(event_type_uuid, company_id)

    if not record:
        return {
            "success": False,
            "fallback_used": True,
            "needs_manual_review": True,
            "message": "Event type nao encontrado ou fora do escopo da empresa",
        }

    data = record.data or {}
    event_type_slug = data.get("event_type", "")
    if data.get("deprecated"):
        return {
            "success": False,
            "fallback_used": True,
            "needs_manual_review": True,
            "message": (
                f"Event type '{event_type_slug}' esta marcado como deprecated; "
                "use uma alternativa nao-deprecated."
            ),
        }

    snapshot = {
        "_event_type_id": str(record.id),
        "_is_master_origin": record.is_master_template,
        "event_type": event_type_slug,
        "label": data.get("label", ""),
        "category": data.get("category", ""),
        "description": data.get("description"),
        "payload_schema": data.get("payload_schema"),
    }

    return {
        "success": True,
        "data": {
            "webhook_target_url": webhook_target_url,
            "target_company_webhook_id": target_company_webhook_id,
            "event_type_id": str(record.id),
            "snapshot": snapshot,
            "is_master_origin": record.is_master_template,
        },
        "message": (
            f"Evento '{event_type_slug}' aplicado ao webhook "
            f"{webhook_target_url[:60]} (snapshot canonical B1; "
            "persistencia ocorre via PATCH /webhooks/[id] ou criacao)."
        ),
    }


@tool_handler("automation")
async def _wrap_create_custom_webhook_event_type(**kwargs: Any) -> dict[str, Any]:
    """
    Cria event type custom canonical via wizard conversacional.

    Valida slug canonical namespace.action (lowercase, letras/digitos/underscore
    separados por ponto) + label min 2 chars + category canonical.

    Permissoes: recrutador + admin (decisao Paulo C 2026-05-20).
    Persistido per-company com is_master_template=False.
    """
    from app.core.database import AsyncSessionLocal
    from app.domains.automation.repositories.webhook_event_type_repository import (
        WebhookEventTypeRepository,
    )

    VALID_CATEGORIES = {
        "candidates", "jobs", "interviews", "offers", "ats", "agents", "system",
    }

    company_id = kwargs.get("company_id")
    user_id = kwargs.get("user_id")
    event_type = (kwargs.get("event_type") or "").strip().lower()
    label = (kwargs.get("label") or "").strip()
    category = (kwargs.get("category") or "").strip().lower()
    description = kwargs.get("description")
    payload_schema = kwargs.get("payload_schema") or {}

    if not event_type or not _EVENT_TYPE_SLUG_RE.match(event_type):
        return {
            "success": False,
            "fallback_used": True,
            "needs_manual_review": True,
            "message": (
                "event_type deve ser slug canonical no padrao "
                "'namespace.action' (lowercase, letras/digitos/underscore "
                "separados por ponto). Ex: candidate.created"
            ),
        }
    if not label or len(label) < 2:
        return {
            "success": False,
            "fallback_used": True,
            "needs_manual_review": True,
            "message": "label obrigatorio (min 2 caracteres)",
        }
    if category not in VALID_CATEGORIES:
        return {
            "success": False,
            "fallback_used": True,
            "needs_manual_review": True,
            "message": (
                f"category invalida ({category!r}); use uma de "
                f"{sorted(VALID_CATEGORIES)}"
            ),
        }
    if not isinstance(payload_schema, dict):
        return {
            "success": False,
            "fallback_used": True,
            "needs_manual_review": True,
            "message": "payload_schema deve ser objeto JSON (dict)",
        }

    data = {
        "event_type": event_type,
        "label": label,
        "category": category,
        "description": description,
        "payload_schema": payload_schema or None,
        "deprecated": False,
        "metadata": None,
    }

    async with AsyncSessionLocal() as db:
        repo = WebhookEventTypeRepository(db)
        try:
            record = await repo.create_custom(
                company_id=company_id,
                data=data,
                created_by=str(user_id) if user_id else None,
            )
            await db.commit()
        except Exception as e:
            await db.rollback()
            # pii-logs ok: nome de entidade/config (nao PII per LGPD Art.5 V)
            logger.error(
                f"[automation_tools] create_custom_webhook_event_type error: {e}",
                exc_info=True,
            )
            return {
                "success": False,
                "fallback_used": True,
                "needs_manual_review": True,
                "message": f"Falha ao criar event type: {e}",
            }

    return {
        "success": True,
        "data": {
            "id": str(record.id),
            "company_id": record.company_id,
            "is_master_template": False,
            "event_type": event_type,
            "label": label,
            "category": category,
        },
        "message": (
            f"Event type custom '{event_type}' criado para a empresa "
            f"(id={str(record.id)[:8]}...)."
        ),
    }



# ---------------------------------------------------------------------------
# Public registry
# ---------------------------------------------------------------------------

def get_automation_tools() -> list[ToolDefinition]:
    return [
        ToolDefinition(
            name="decompose_task",
            description="Decompor uma tarefa complexa em subtarefas usando IA. Parâmetros: task_description (str, obrigatório), goal_id (str, opcional), company_id (str, opcional), persist (bool, padrão True).",
            output_schema=ToolOutput,
            function=_wrap_decompose_task,
        ),
        ToolDefinition(
            name="prioritize_tasks",
            description="Calcular e atualizar prioridades de tarefas. Parâmetros: task_ids (list[str]) ou goal_id (str).",
            output_schema=ToolOutput,
            function=_wrap_prioritize_tasks,
        ),
        ToolDefinition(
            name="get_execution_plan",
            description="Gerar plano de execução com níveis paralelos. Parâmetros: task_ids (list[str]) ou goal_id (str), name (str, opcional).",
            output_schema=ToolOutput,
            function=_wrap_get_execution_plan,
        ),
        ToolDefinition(
            name="build_dag",
            description="Construir e validar DAG de dependências. Parâmetros: task_ids (list[str]).",
            output_schema=ToolOutput,
            function=_wrap_build_dag,
        ),
        ToolDefinition(
            name="check_dependencies",
            description="Verificar status das dependências de uma tarefa. Parâmetros: task_id (str).",
            output_schema=ToolOutput,
            function=_wrap_check_dependencies,
        ),
        ToolDefinition(
            name="get_next_tasks",
            description="Obter próximas tarefas prontas para execução. Parâmetros: goal_id (str, opcional), agent_type (str, opcional), limit (int, padrão 5).",
            output_schema=ToolOutput,
            function=_wrap_get_next_tasks,
        ),
        # ── Webhook Event Types canonical (Sprint 5 F5) ─────────────────────
        ToolDefinition(
            name="suggest_webhook_event_types",
            description=(
                "Sugere event types de webhook canonical relevantes para a "
                "company. Filtro opcional por categoria. Retorna top 20 ranked "
                "(customs primeiro, depois master, depreciados por ultimo)."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "enum": [
                            "candidates", "jobs", "interviews", "offers",
                            "ats", "agents", "system",
                        ],
                        "description": "Filtro opcional por categoria canonical.",
                    },
                },
                "required": [],
            },
            output_schema=ToolOutput,
            function=_wrap_suggest_webhook_event_types,
        ),
        ToolDefinition(
            name="apply_webhook_event_subscription",
            description=(
                "Aplica subscricao de event type canonical a um webhook target "
                "via snapshot canonical (B1). NAO sincroniza com master apos "
                "aplicacao. Persistencia final ocorre via PATCH /webhooks/[id]."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "event_type_id": {
                        "type": "string",
                        "description": "UUID do event type canonical.",
                    },
                    "webhook_target_url": {
                        "type": "string",
                        "description": "URL do webhook subscriber (HTTPS).",
                    },
                    "target_company_webhook_id": {
                        "type": "string",
                        "description": "UUID do webhook existente (opcional).",
                    },
                },
                "required": ["event_type_id", "webhook_target_url"],
            },
            output_schema=ToolOutput,
            function=_wrap_apply_webhook_event_subscription,
        ),
        ToolDefinition(
            name="create_custom_webhook_event_type",
            description=(
                "Cria event type custom canonical persistido per-company. "
                "Valida slug 'namespace.action' (lowercase, dot-separated) + "
                "label min 2 chars + categoria canonical. Recrutador + admin "
                "podem criar (decisao Paulo C 2026-05-20)."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "event_type": {
                        "type": "string",
                        "description": "Slug canonical 'namespace.action'.",
                    },
                    "label": {
                        "type": "string",
                        "description": "Label humano (min 2 chars).",
                    },
                    "category": {
                        "type": "string",
                        "enum": [
                            "candidates", "jobs", "interviews", "offers",
                            "ats", "agents", "system",
                        ],
                    },
                    "description": {"type": "string"},
                    "payload_schema": {
                        "type": "object",
                        "description": "JSONSchema do payload (opcional).",
                    },
                },
                "required": ["event_type", "label", "category"],
            },
            output_schema=ToolOutput,
            function=_wrap_create_custom_webhook_event_type,
        ),
    ]


def get_stage_tools(stage: str) -> list[ToolDefinition]:
    """Return tools available for a given stage."""
    from app.domains.automation.agents.automation_stage_context import get_stage_tools as _stage_tools
    stage_tool_names = set(_stage_tools(stage))
    return [t for t in get_automation_tools() if t.name in stage_tool_names]
