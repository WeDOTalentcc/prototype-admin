'''
Pipeline Stage Management Tool (recruiter_assistant domain).

UC-P2-10 note: This module provides the create_pipeline_stage ToolDefinition
used by recruiter_assistant, orchestrator, and job_planner agents.

The canonical pipeline tools module (app.domains.pipeline.tools.pipeline_tools)
provides langchain @tool functions for candidate-movement operations
(move_candidate_to_stage, reject_candidate, extend_offer, etc.).

Both modules are needed and serve distinct responsibilities:
  - recruiter_assistant: DB-backed stage creation (ToolDefinition + tool_registry)
  - pipeline.tools: Candidate movement operations (langchain @tool)
'''
import logging
import re
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from app.tools.registry import ToolDefinition, tool_registry

if TYPE_CHECKING:
    from app.tools.executor import ToolExecutionContext

logger = logging.getLogger(__name__)


def _extract_context(kwargs: dict[str, Any]) -> Optional["ToolExecutionContext"]:
    return kwargs.pop("_context", None)


def _slugify(name: str) -> str:
    slug = name.lower().strip()
    slug = re.sub(r'[àáâãä]', 'a', slug)
    slug = re.sub(r'[èéêë]', 'e', slug)
    slug = re.sub(r'[ìíîï]', 'i', slug)
    slug = re.sub(r'[òóôõö]', 'o', slug)
    slug = re.sub(r'[ùúûü]', 'u', slug)
    slug = re.sub(r'[ç]', 'c', slug)
    slug = re.sub(r'[^a-z0-9]+', '_', slug)
    slug = slug.strip('_')
    return slug


async def create_pipeline_stage(
    stage_name: str,
    company_id: str,
    job_id: str | None = None,
    position: str | None = None,
    **kwargs
) -> dict[str, Any]:
    context = _extract_context(kwargs)
    effective_company_id = context.company_id if context else company_id
    user_id = context.user_id if context else "system"

    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
    logger.info(f"🔧 Creating pipeline stage: {stage_name} (company: {effective_company_id})")

    try:
        from app.domains.communication.services.infer_behavior_service import infer_behavior_auto
        behavior_result = await infer_behavior_auto(stage_name)
        suggested_behavior = behavior_result.get("suggested_behavior", "passive")
        behavior_confidence = behavior_result.get("confidence", 0.5)

        logger.info(
            f"🎯 Inferred behavior for '{stage_name}': {suggested_behavior} "
            f"(confidence: {behavior_confidence})"
        )

        from sqlalchemy import and_, func, select

        from app.core.database import AsyncSessionLocal
        from app.models.recruitment_stages import RecruitmentStage

        async with AsyncSessionLocal() as db:
            existing = await db.execute(
                select(RecruitmentStage).where(
                    and_(
                        RecruitmentStage.company_id == effective_company_id,
                        RecruitmentStage.name == _slugify(stage_name),
                        RecruitmentStage.is_active
                    )
                )
            )
            if existing.scalar_one_or_none():
                return {
                    "success": False,
                    "message": f"❌ Já existe uma etapa '{stage_name}' no pipeline desta empresa.",
                    "error": "stage_already_exists"
                }

            max_order_result = await db.execute(
                select(func.max(RecruitmentStage.stage_order)).where(
                    and_(
                        RecruitmentStage.company_id == effective_company_id,
                        RecruitmentStage.is_active
                    )
                )
            )
            max_order = max_order_result.scalar() or 0

            if position == "before_final":
                final_stages = await db.execute(
                    select(RecruitmentStage).where(
                        and_(
                            RecruitmentStage.company_id == effective_company_id,
                            RecruitmentStage.is_final,
                            RecruitmentStage.is_active
                        )
                    ).order_by(RecruitmentStage.stage_order)
                )
                final_list = final_stages.scalars().all()
                if final_list:
                    insert_order = final_list[0].stage_order
                    for fs in final_list:
                        fs.stage_order = fs.stage_order + 1
                    other_stages = await db.execute(
                        select(RecruitmentStage).where(
                            and_(
                                RecruitmentStage.company_id == effective_company_id,
                                RecruitmentStage.is_active,
                                not RecruitmentStage.is_final,
                                RecruitmentStage.stage_order >= insert_order
                            )
                        )
                    )
                    for s in other_stages.scalars().all():
                        s.stage_order = s.stage_order + 1
                    new_order = insert_order
                else:
                    new_order = max_order + 1
            else:
                new_order = max_order + 1

            BEHAVIOR_COLORS = {
                "screening": "#3B82F6",
                "scheduling": "#8B5CF6",
                "evaluation": "#F59E0B",
                "verification": "#6366F1",
                "offer": "#10B981",
                "intake": "#06B6D4",
                "conclusion_hired": "#22C55E",
                "conclusion_rejected": "#EF4444",
                "conclusion_declined": "#F97316",
                "passive": "#6B7280",
            }

            BEHAVIOR_ICONS = {
                "screening": "filter",
                "scheduling": "calendar",
                "evaluation": "clipboard-check",
                "verification": "shield-check",
                "offer": "briefcase",
                "intake": "inbox",
                "conclusion_hired": "check-circle",
                "conclusion_rejected": "x-circle",
                "conclusion_declined": "minus-circle",
                "passive": "circle",
            }

            stage = RecruitmentStage(
                company_id=effective_company_id,
                name=_slugify(stage_name),
                display_name=stage_name.strip(),
                description="Etapa criada via chat LIA",
                stage_order=new_order,
                color=BEHAVIOR_COLORS.get(suggested_behavior, "#6B7280"),
                icon=BEHAVIOR_ICONS.get(suggested_behavior, "circle"),
                stage_type="active",
                is_initial=False,
                is_final=False,
                is_rejection=False,
                is_hired=False,
                is_active=True,
                is_system=False,
                stage_category="custom",
                action_behavior=suggested_behavior,
                default_channel="email",
                created_by=user_id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

            db.add(stage)
            await db.commit()
            await db.refresh(stage)

            stage_id = str(stage.id)

            # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
            logger.info(f"✅ Created pipeline stage: {stage_id} - {stage_name}")

            return {
                "success": True,
                "message": f"✅ Etapa '{stage_name}' criada com sucesso no pipeline.",
                "action_taken": "create_pipeline_stage",
                "affected_entities": [stage_id],
                "data": {
                    "stage_id": stage_id,
                    "name": stage.name,
                    "display_name": stage.display_name,
                    "stage_order": new_order,
                    "action_behavior": suggested_behavior,
                    "behavior_confidence": behavior_confidence,
                    "color": stage.color,
                    "icon": stage.icon,
                    "company_id": effective_company_id,
                    "created_by": user_id,
                    "created_at": datetime.utcnow().isoformat(),
                }
            }

    except Exception as e:
        try:
            await db.rollback()
        except Exception:
            pass
        logger.error(f"❌ Error creating pipeline stage: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"❌ Erro ao criar etapa no pipeline: {str(e)}",
            "error": str(e)
        }


CREATE_PIPELINE_STAGE_SCHEMA = {
    "type": "object",
    "properties": {
        "stage_name": {
            "type": "string",
            "description": "Nome da nova etapa (ex: 'Teste Prático', 'Dinâmica de Grupo', 'Entrevista com Gestor')"
        },
        "company_id": {
            "type": "string",
            "description": "ID da empresa"
        },
        "job_id": {
            "type": "string",
            "description": "ID da vaga (opcional, se não informado aplica ao template da empresa)"
        },
        "position": {
            "type": "string",
            "description": "Posição da etapa no pipeline: 'before_final' para inserir antes das etapas finais, ou omitir para adicionar ao final",
            "enum": ["before_final"]
        }
    },
    "required": ["stage_name", "company_id"]
}

RENAME_PIPELINE_STAGE_SCHEMA = {
    "type": "object",
    "properties": {
        "stage_id": {"type": "string", "description": "ID da etapa a ser renomeada"},
        "new_name": {"type": "string", "description": "Novo nome para a etapa"},
        "company_id": {"type": "string", "description": "ID da empresa"},
    },
    "required": ["stage_id", "new_name", "company_id"],
}

REORDER_PIPELINE_STAGES_SCHEMA = {
    "type": "object",
    "properties": {
        "stage_ids_ordered": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Lista completa de IDs das etapas na nova ordem desejada",
        },
        "company_id": {"type": "string", "description": "ID da empresa"},
    },
    "required": ["stage_ids_ordered", "company_id"],
}

DELETE_PIPELINE_STAGE_SCHEMA = {
    "type": "object",
    "properties": {
        "stage_id": {"type": "string", "description": "ID da etapa a ser excluída"},
        "company_id": {"type": "string", "description": "ID da empresa"},
        "move_candidates_to_stage_id": {
            "type": "string",
            "description": "ID da etapa destino para mover candidatos antes de excluir (obrigatório se a etapa tiver candidatos)",
        },
    },
    "required": ["stage_id", "company_id"],
}


async def rename_pipeline_stage(
    stage_id: str,
    new_name: str,
    company_id: str,
    **kwargs
) -> dict:
    context = _extract_context(kwargs)
    effective_company_id = context.company_id if context else company_id

    logger.info(f"🔧 Renaming pipeline stage: {stage_id} -> '{new_name}' (company: {effective_company_id})")

    try:
        from sqlalchemy import and_, select

        from app.core.database import AsyncSessionLocal
        from app.models.recruitment_stages import RecruitmentStage

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(RecruitmentStage).where(
                    and_(
                        RecruitmentStage.id == stage_id,
                        RecruitmentStage.company_id == effective_company_id,
                        RecruitmentStage.is_active
                    )
                )
            )
            stage = result.scalar_one_or_none()
            if not stage:
                return {
                    "success": False,
                    "message": f"❌ Etapa não encontrada ou não pertence a esta empresa.",
                    "error": "stage_not_found"
                }

            old_name = stage.display_name
            stage.display_name = new_name.strip()
            stage.name = _slugify(new_name)
            stage.updated_at = datetime.utcnow()

            await db.commit()
            await db.refresh(stage)

            logger.info(f"✅ Renamed pipeline stage {stage_id}: '{old_name}' -> '{new_name}'")

            return {
                "success": True,
                "message": f"✅ Etapa renomeada de '{old_name}' para '{new_name}'.",
                "action_taken": "rename_pipeline_stage",
                "affected_entities": [stage_id],
                "data": {
                    "stage_id": stage_id,
                    "old_name": old_name,
                    "new_name": stage.display_name,
                    "slug": stage.name,
                    "company_id": effective_company_id,
                }
            }

    except Exception as e:
        logger.error(f"❌ Error renaming pipeline stage: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"❌ Erro ao renomear etapa: {str(e)}",
            "error": str(e)
        }


async def reorder_pipeline_stages(
    stage_ids_ordered: list,
    company_id: str,
    **kwargs
) -> dict:
    context = _extract_context(kwargs)
    effective_company_id = context.company_id if context else company_id

    logger.info(f"🔧 Reordering {len(stage_ids_ordered)} pipeline stages (company: {effective_company_id})")

    try:
        from sqlalchemy import and_, select

        from app.core.database import AsyncSessionLocal
        from app.models.recruitment_stages import RecruitmentStage

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(RecruitmentStage).where(
                    and_(
                        RecruitmentStage.company_id == effective_company_id,
                        RecruitmentStage.is_active
                    )
                )
            )
            all_stages = {str(s.id): s for s in result.scalars().all()}

            # Validate all provided IDs belong to this company
            invalid_ids = [sid for sid in stage_ids_ordered if sid not in all_stages]
            if invalid_ids:
                return {
                    "success": False,
                    "message": f"❌ Etapas não encontradas ou não pertencem a esta empresa: {invalid_ids}",
                    "error": "stage_not_found",
                    "invalid_ids": invalid_ids
                }

            # Apply new order
            new_order_result = []
            for idx, stage_id in enumerate(stage_ids_ordered):
                stage = all_stages[stage_id]
                stage.stage_order = idx + 1
                stage.updated_at = datetime.utcnow()
                new_order_result.append({
                    "stage_id": stage_id,
                    "display_name": stage.display_name,
                    "new_order": idx + 1
                })

            await db.commit()

            logger.info(f"✅ Reordered {len(stage_ids_ordered)} pipeline stages")

            return {
                "success": True,
                "message": f"✅ {len(stage_ids_ordered)} etapas reordenadas com sucesso.",
                "action_taken": "reorder_pipeline_stages",
                "affected_entities": list(stage_ids_ordered),
                "data": {
                    "company_id": effective_company_id,
                    "new_order": new_order_result
                }
            }

    except Exception as e:
        logger.error(f"❌ Error reordering pipeline stages: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"❌ Erro ao reordenar etapas: {str(e)}",
            "error": str(e)
        }


async def delete_pipeline_stage(
    stage_id: str,
    company_id: str,
    move_candidates_to_stage_id: str | None = None,
    **kwargs
) -> dict:
    context = _extract_context(kwargs)
    effective_company_id = context.company_id if context else company_id

    logger.info(f"\U0001f527 Deleting pipeline stage: {stage_id} (company: {effective_company_id})")

    try:
        from sqlalchemy import and_, func, select

        from app.core.database import AsyncSessionLocal
        from app.models.recruitment_stages import RecruitmentStage

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(RecruitmentStage).where(
                    and_(
                        RecruitmentStage.id == stage_id,
                        RecruitmentStage.company_id == effective_company_id,
                        RecruitmentStage.is_active
                    )
                )
            )
            stage = result.scalar_one_or_none()
            if not stage:
                return {
                    "success": False,
                    "message": "❌ Etapa não encontrada ou não pertence a esta empresa.",
                    "error": "stage_not_found"
                }

            if stage.is_system:
                return {
                    "success": False,
                    "message": f"❌ Etapa ‘{stage.display_name}’ é uma etapa do sistema e não pode ser excluída.",
                    "error": "system_stage_protected"
                }

            # P-FAILLOUD: count failure is fatal, not silently swallowed
            candidate_count = 0
            try:
                from lia_models.candidate import VacancyCandidate
                count_result = await db.execute(
                    select(func.count()).where(
                        and_(
                            VacancyCandidate.recruitment_stage_id == stage_id,
                            VacancyCandidate.company_id == effective_company_id,
                        )
                    )
                )
                candidate_count = count_result.scalar() or 0
            except Exception as _count_exc:
                logger.error(
                    "delete_pipeline_stage: failed to count candidates in stage %s: %s",
                    stage_id, _count_exc, exc_info=True
                )
                return {
                    "success": False,
                    "message": "Erro ao contar candidatos na etapa. Operação abortada.",
                    "error": "count_failed",
                }

            # HITL guard: refuse to delete stage with candidates if no move_to provided
            if candidate_count > 0 and not move_candidates_to_stage_id:
                return {
                    "success": False,
                    "message": (
                        f"⚠️ A etapa ‘{stage.display_name}’ possui {candidate_count} candidato(s). "
                        f"Informe ‘move_candidates_to_stage_id’ para mover os candidatos antes de excluir."
                    ),
                    "error": "stage_has_candidates",
                    "requires_confirmation": True,
                    "candidate_count": candidate_count,
                    "ui_action": "open_modal",
                    "ui_action_params": {"modal_id": "confirm_stage_delete"}
                }

            # Move candidates via canonical service (P-SSOT, P-GUARD, P-TENANT)
            _moved_count = 0
            _failed_ids: dict[str, str] = {}

            if candidate_count > 0 and move_candidates_to_stage_id:
                # Validate destination stage belongs to same company
                dest_result = await db.execute(
                    select(RecruitmentStage).where(
                        and_(
                            RecruitmentStage.id == move_candidates_to_stage_id,
                            RecruitmentStage.company_id == effective_company_id,
                            RecruitmentStage.is_active
                        )
                    )
                )
                dest_stage = dest_result.scalar_one_or_none()
                if not dest_stage:
                    return {
                        "success": False,
                        "message": "❌ Etapa de destino não encontrada ou não pertence a esta empresa.",
                        "error": "destination_stage_not_found"
                    }

                # P-GUARD layer 1 (PRIMARY): refuse rejection stage destination.
                # Deleting a workflow stage is NOT a mass-rejection vector.
                if dest_stage.is_rejection:
                    return {
                        "success": False,
                        "message": (
                            f"❌ Não é possível mover candidatos para o estágio de rejeição "
                            f"‘{dest_stage.display_name}’ via exclusão de etapa. "
                            f"Deletar uma etapa de workflow não é um vetor de rejeição em massa. "
                            f"Escolha um estágio neutro ou ativo como destino."
                        ),
                        "error": "destination_is_rejection_stage",
                        "rejected_by": "P-GUARD",
                    }

                # Fetch all VCs in the stage to delete (P-TENANT: filtered by company_id)
                from lia_models.candidate import VacancyCandidate
                vc_result = await db.execute(
                    select(VacancyCandidate).where(
                        and_(
                            VacancyCandidate.recruitment_stage_id == stage_id,
                            VacancyCandidate.company_id == effective_company_id,
                        )
                    )
                )
                all_vcs = vc_result.scalars().all()

                # P-GUARD layer 2 (defense-in-depth) + P-SSOT: per-candidate
                # transition via canonical service — runs fairness gate, writes
                # CandidateStageHistory, fires STAGE_CHANGED, calls AuditService.
                from app.domains.recruiter_assistant.services.pipeline_stage_service import (
                    FairnessBlockedError,
                    pipeline_stage_service,
                )

                for _vc in all_vcs:
                    _vc_id = str(_vc.id)
                    try:
                        await pipeline_stage_service.transition_candidate(
                            vacancy_candidate_id=_vc_id,
                            to_stage=dest_stage.display_name,
                            triggered_by="delete_pipeline_stage",
                            source_agent="pipeline_tools",
                        )
                        _moved_count += 1
                    except FairnessBlockedError as _fb:
                        _failed_ids[_vc_id] = _fb.message
                    except Exception as _ex:
                        _failed_ids[_vc_id] = (
                            f"Erro interno: {type(_ex).__name__} — {str(_ex)[:80]}"
                        )

                if _failed_ids:
                    # Partial failure: do NOT delete the stage — candidates would be orphaned
                    logger.error(
                        "delete_pipeline_stage: %d/%d candidates failed to move — aborting stage deletion",
                        len(_failed_ids), len(all_vcs),
                    )
                    return {
                        "success": False,
                        "message": (
                            f"⚠️ {len(_failed_ids)}/{len(all_vcs)} candidato(s) não puderam ser movidos. "
                            f"A etapa NÃO foi excluída para evitar candidatos órfãos."
                        ),
                        "error": "partial_move_failure",
                        "failed_moves": _failed_ids,
                        "moved_count": _moved_count,
                    }

            stage_name = stage.display_name
            stage.is_active = False
            stage.updated_at = datetime.utcnow()

            await db.commit()

            logger.info(f"✅ Deleted (soft) pipeline stage {stage_id}: ‘{stage_name}’")

            return {
                "success": True,
                "message": f"✅ Etapa ‘{stage_name}’ excluída com sucesso.",
                "action_taken": "delete_pipeline_stage",
                "affected_entities": [stage_id],
                "data": {
                    "stage_id": stage_id,
                    "stage_name": stage_name,
                    "candidates_moved": _moved_count,
                    "move_target": move_candidates_to_stage_id,
                    "company_id": effective_company_id,
                    "failed_moves": _failed_ids,
                }
            }

    except Exception as e:
        logger.error(f"❌ Error deleting pipeline stage: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"❌ Erro ao excluir etapa: {str(e)}",
            "error": str(e)
        }


def register_pipeline_tools() -> None:
    tool_registry.register(ToolDefinition(
        name="create_pipeline_stage",
        description="Cria uma nova etapa/coluna no pipeline de recrutamento. Use quando o recrutador pedir para adicionar uma etapa como 'teste prático', 'dinâmica de grupo', 'entrevista com gestor', etc. A LIA infere automaticamente o comportamento da etapa.",
        parameters_schema=CREATE_PIPELINE_STAGE_SCHEMA,
        handler=create_pipeline_stage,
        allowed_agents=["orchestrator", "recruiter_assistant", "job_planner"]
    ))

    tool_registry.register(ToolDefinition(
        name="rename_pipeline_stage",
        description="Renomeia uma etapa existente no pipeline de recrutamento. Use quando o recrutador quiser alterar o nome de uma coluna/etapa do pipeline.",
        parameters_schema=RENAME_PIPELINE_STAGE_SCHEMA,
        handler=rename_pipeline_stage,
        allowed_agents=["orchestrator", "recruiter_assistant", "job_planner"]
    ))

    tool_registry.register(ToolDefinition(
        name="reorder_pipeline_stages",
        description="Reordena as etapas do pipeline de recrutamento. Recebe a lista completa de IDs das etapas na nova ordem desejada.",
        parameters_schema=REORDER_PIPELINE_STAGES_SCHEMA,
        handler=reorder_pipeline_stages,
        allowed_agents=["orchestrator", "recruiter_assistant", "job_planner"]
    ))

    tool_registry.register(ToolDefinition(
        name="delete_pipeline_stage",
        description="Exclui uma etapa do pipeline de recrutamento. Se a etapa tiver candidatos, é necessário informar para qual etapa movê-los antes de excluir (HITL guard).",
        parameters_schema=DELETE_PIPELINE_STAGE_SCHEMA,
        handler=delete_pipeline_stage,
        allowed_agents=["orchestrator", "recruiter_assistant", "job_planner"]
    ))

    logger.info("✅ Registered 4 pipeline tools")
