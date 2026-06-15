"""
Pipeline management endpoints:
- Initialize company stages
- Sync canonical sub-statuses
- Company pipeline GET/PUT
- Job pipeline GET/PUT
- Pipeline inheritance status, copy-from-company, mark-customized
"""
import uuid
import logging
from datetime import datetime

from fastapi import APIRouter, Body, Depends, HTTPException, Query

from ._shared import (
    CANONICAL_SUB_STATUSES,
    DEFAULT_SUB_STATUSES,
    GUPY_STAGE_MAPPINGS,
    PANDAPE_STAGE_MAPPINGS,
    STANDARD_STAGE_CATALOG,
    RecruitmentStage,
    CompanyPipelineUpdate,
    JobPipelineUpdate,
    _get_company_pipeline,
    assert_resource_ownership,
    get_current_active_user,
    get_current_user_or_demo,
    get_user_company_id,
    require_admin_or_recruiter,
    get_ats_mapping_repo,
    get_stage_repo,
    get_sub_status_repo,
    ATSMappingRepository,
    RecruitmentStageRepository,
    SubStatusRepository,
    pipeline_stage_service,
    User,
)
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Recruitment Stages - Pipeline"])


@router.post("/initialize", response_model=None)
async def initialize_company_stages(
    ats_type: str | None = Query(default=None, description="Also initialize ATS mappings"),
    current_user: User = Depends(require_admin_or_recruiter),
    stage_repo: RecruitmentStageRepository = Depends(get_stage_repo),
    ats_repo: ATSMappingRepository = Depends(get_ats_mapping_repo),
company_id: str = Depends(require_company_id)):
    """
    Initialize default stages and sub-statuses for the authenticated user's company.
    Optionally also initializes ATS mappings for Gupy or Pandapé.
    """
    try:
        effective_company_id = get_user_company_id(current_user)

        stages = await pipeline_stage_service.initialize_company_stages(
            company_id=effective_company_id,
            db=stage_repo.db
        )

        ats_mappings_created = 0
        if ats_type and stages:
            stage_name_to_id = {}
            all_stages = await stage_repo.list_for_company(effective_company_id, include_inactive=True)
            for s in all_stages:
                stage_name_to_id[s.name] = s.id

            mappings_config = []
            if ats_type == "gupy":
                mappings_config = GUPY_STAGE_MAPPINGS
            elif ats_type == "pandape":
                mappings_config = PANDAPE_STAGE_MAPPINGS

            for mapping in mappings_config:
                wedo_stage = mapping.get("wedotalent_stage")
                if wedo_stage in stage_name_to_id:
                    await ats_repo.create_no_commit({
                        "company_id": effective_company_id,
                        "ats_type": ats_type,
                        "ats_stage_name": mapping["ats_stage_name"],
                        "wedotalent_stage_id": stage_name_to_id[wedo_stage],
                        "is_default_for_sync": mapping.get("is_default_for_sync", False),
                    })
                    ats_mappings_created += 1

            await ats_repo.commit()

        return {
            "success": True,
            "stages_created": len(stages),
            "ats_mappings_created": ats_mappings_created
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error initializing stages: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/sync-canonical-sub-statuses", response_model=None)
async def sync_canonical_sub_statuses(
    current_user: User = Depends(require_admin_or_recruiter),
    stage_repo: RecruitmentStageRepository = Depends(get_stage_repo),
    sub_status_repo: SubStatusRepository = Depends(get_sub_status_repo),
company_id: str = Depends(require_company_id)):
    """
    Idempotent sync: inserts any CANONICAL_SUB_STATUSES entries missing from
    the company's existing stages. Safe to run multiple times.
    Call once after deploys that expand CANONICAL_SUB_STATUSES.
    """
    try:
        effective_company_id = get_user_company_id(current_user)

        stages = await stage_repo.list_for_company(effective_company_id)

        inserted_total = 0
        for stage in stages:
            canonical = CANONICAL_SUB_STATUSES.get(stage.name, [])
            if not canonical:
                continue

            existing_names = await sub_status_repo.get_existing_names_for_stage(stage.id)
            next_order = await sub_status_repo.get_max_order_for_stage(stage.id)

            for sub_data in canonical:
                if sub_data["name"] not in existing_names:
                    await sub_status_repo.create_no_commit({
                        "stage_id": stage.id,
                        "company_id": effective_company_id,
                        "sub_status_order": next_order,
                        "name": sub_data["name"],
                        "display_name": sub_data["display_name"],
                        "is_default": sub_data.get("is_default", False),
                        "is_waiting": sub_data.get("is_waiting", False),
                        "waiting_for": sub_data.get("waiting_for"),
                    })
                    next_order += 1
                    inserted_total += 1

        await sub_status_repo.commit()
        logger.info(
            "[sync_canonical] company=%s inserted=%d sub-statuses",
            effective_company_id, inserted_total
        )
        return {"success": True, "inserted": inserted_total}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("[sync_canonical] error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")



@router.post("/apply-template-sub-statuses", response_model=None)
async def apply_template_sub_statuses(
    payload: dict = Body(...),
    current_user: User = Depends(require_admin_or_recruiter),
    stage_repo: RecruitmentStageRepository = Depends(get_stage_repo),
    sub_status_repo: SubStatusRepository = Depends(get_sub_status_repo),
company_id: str = Depends(require_company_id)):
    """Upsert sub-statuses do template nas etapas da empresa.

    Chamado após PUT /company-pipeline + sync-canonical quando um template
    é aplicado como Padrão. Garante que sub-statuses customizados do template
    sejam recriados nas etapas da empresa.

    Body: { "stages": [{ "stage_name": str, "sub_statuses": [...] }] }
    Cada sub_status: { name, display_name, order, color, icon,
                       is_default, is_waiting, waiting_for, sla_hours }

    Multi-tenancy: todas as operações filtradas por company_id do JWT.
    Idempotente: skip se sub_status.name já existe na stage.
    """
    try:
        effective_company_id = get_user_company_id(current_user)
        stages_payload = payload.get("stages", [])
        upserted_total = 0

        for stage_data in stages_payload:
            stage_name = stage_data.get("stage_name", "")
            sub_statuses = stage_data.get("sub_statuses", [])
            if not stage_name or not sub_statuses:
                continue

            stage = await stage_repo.get_by_name(effective_company_id, stage_name)
            if not stage:
                logger.debug("[apply_template_sub_statuses] stage %r não encontrada, skip", stage_name)
                continue

            existing_names = await sub_status_repo.get_existing_names_for_stage(stage.id)
            next_order = await sub_status_repo.get_max_order_for_stage(stage.id)

            for ss in sub_statuses:
                ss_name = ss.get("name", "")
                if not ss_name or ss_name in existing_names:
                    continue
                await sub_status_repo.create_no_commit({
                    "stage_id": stage.id,
                    "company_id": effective_company_id,
                    "sub_status_order": ss.get("order", next_order),
                    "name": ss_name,
                    "display_name": ss.get("display_name", ss_name),
                    "color": ss.get("color"),
                    "icon": ss.get("icon"),
                    "is_default": ss.get("is_default", False),
                    "is_waiting": ss.get("is_waiting", False),
                    "waiting_for": ss.get("waiting_for"),
                    "sla_hours": ss.get("sla_hours"),
                    "is_active": True,
                })
                next_order += 1
                upserted_total += 1

        await sub_status_repo.commit()
        logger.info(
            "[apply_template_sub_statuses] company=%s upserted=%d sub-statuses",
            effective_company_id, upserted_total,
        )
        return {"success": True, "upserted": upserted_total}

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("[apply_template_sub_statuses] error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Erro ao aplicar sub-statuses do template")


@router.get("/company-pipeline", response_model=None)
async def get_company_pipeline(
    current_user: User = Depends(get_current_user_or_demo),
    stage_repo: RecruitmentStageRepository = Depends(get_stage_repo),
    sub_status_repo: SubStatusRepository = Depends(get_sub_status_repo),
company_id: str = Depends(require_company_id)):
    try:
        effective_company_id = get_user_company_id(current_user)
        pipeline = await _get_company_pipeline(effective_company_id, stage_repo, sub_status_repo)
        return {"pipeline": pipeline, "total": len(pipeline)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting company pipeline: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/company-pipeline", response_model=None)
async def update_company_pipeline(
    payload: CompanyPipelineUpdate,
    current_user: User = Depends(get_current_user_or_demo),
    stage_repo: RecruitmentStageRepository = Depends(get_stage_repo),
    sub_status_repo: SubStatusRepository = Depends(get_sub_status_repo),
company_id: str = Depends(require_company_id)):
    try:
        effective_company_id = get_user_company_id(current_user)

        all_stages = await stage_repo.list_for_company(effective_company_id, include_inactive=True)
        existing_stages = {str(s.id): s for s in all_stages}

        catalog_by_id = {c["id"]: c for c in STANDARD_STAGE_CATALOG}
        incoming_ids = set()

        for item in payload.stages:
            if item.id and item.id in existing_stages:
                stage = existing_stages[item.id]
                incoming_ids.add(item.id)
                updates: dict = {"stage_order": item.stage_order, "is_active": item.is_active}
                if item.display_name is not None:
                    updates["display_name"] = item.display_name
                if item.sla_hours is not None:
                    updates["sla_hours"] = item.sla_hours
                if item.color is not None:
                    updates["color"] = item.color
                if item.icon is not None:
                    updates["icon"] = item.icon
                if item.action_behavior is not None:
                    updates["action_behavior"] = item.action_behavior
                if item.default_channel is not None:
                    updates["default_channel"] = item.default_channel
                await stage_repo.update_fields_uuid(stage.id, updates)
            elif item.catalog_id and item.catalog_id in catalog_by_id:
                catalog_entry = catalog_by_id[item.catalog_id]
                new_stage = RecruitmentStage(
                    company_id=effective_company_id,
                    name=catalog_entry["name"],
                    display_name=item.display_name or catalog_entry["display_name"],
                    stage_order=item.stage_order,
                    color=item.color or catalog_entry.get("color", "#6B7280"),
                    icon=item.icon or catalog_entry.get("icon", "circle"),
                    stage_type="active" if not catalog_entry.get("is_final") else "final",
                    is_initial=catalog_entry.get("is_initial", False),
                    is_final=catalog_entry.get("is_final", False),
                    is_system=catalog_entry.get("is_system", False),
                    stage_category=catalog_entry.get("stage_category", "custom"),
                    action_behavior=item.action_behavior or catalog_entry.get("action_behavior", "passive"),
                    sla_hours=item.sla_hours,
                    is_active=item.is_active,
                )
                stage_repo.db.add(new_stage)
                await stage_repo.db.flush()

                sub_status_defs = DEFAULT_SUB_STATUSES.get(catalog_entry["name"], [])
                for idx, sub_def in enumerate(sub_status_defs):
                    await sub_status_repo.create_no_commit({
                        "stage_id": new_stage.id,
                        "company_id": effective_company_id,
                        "name": sub_def["name"],
                        "display_name": sub_def["display_name"],
                        "sub_status_order": idx,
                        "is_default": sub_def.get("is_default", False),
                        "is_waiting": sub_def.get("is_waiting", False),
                        "waiting_for": sub_def.get("waiting_for"),
                    })

        for stage_id, stage in existing_stages.items():
            if stage_id not in incoming_ids:
                if not stage.is_system:  # type: ignore[truthy-bool]
                    await stage_repo.update_fields_uuid(
                        stage.id, {"is_active": False}
                    )

        await stage_repo.db.commit()

        pipeline = await _get_company_pipeline(effective_company_id, stage_repo, sub_status_repo)
        return {"pipeline": pipeline, "total": len(pipeline)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating company pipeline: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/jobs/{job_id}/pipeline", response_model=None)
async def get_job_pipeline(
    job_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    current_user: User = Depends(get_current_user_or_demo),
    stage_repo: RecruitmentStageRepository = Depends(get_stage_repo),
    sub_status_repo: SubStatusRepository = Depends(get_sub_status_repo),
company_id: str = Depends(require_company_id)):
    try:
        from app.models.job_vacancy import JobVacancy

        effective_company_id = get_user_company_id(current_user)

        job = await stage_repo.db.get(JobVacancy, uuid.UUID(job_id))
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        if str(job.company_id) != effective_company_id:
            raise HTTPException(status_code=403, detail="Access denied")

        pipeline_config = getattr(job, "pipeline_config", None)

        if pipeline_config:
            config_map = {item["stage_name"]: item for item in pipeline_config}
            company_pipeline = await _get_company_pipeline(effective_company_id, stage_repo, sub_status_repo)
            customized = []
            for stage in company_pipeline:
                override = config_map.get(stage["name"])
                if override:
                    stage["stage_order"] = override.get("stage_order", stage["stage_order"])
                    stage["is_active"] = override.get("is_active", stage["is_active"])
                    if override.get("sla_hours") is not None:
                        stage["sla_hours"] = override["sla_hours"]
                    if override.get("display_name"):
                        stage["display_name"] = override["display_name"]
                    if override.get("color"):
                        stage["color"] = override["color"]
                    if override.get("icon"):
                        stage["icon"] = override["icon"]
                    customized.append(stage)
                else:
                    customized.append(stage)
            customized.sort(key=lambda s: s["stage_order"])
            return {
                "pipeline": customized,
                "total": len(customized),
                "is_inherited": False,
                "source": "custom",
            }
        else:
            company_pipeline = await _get_company_pipeline(effective_company_id, stage_repo, sub_status_repo)
            return {
                "pipeline": company_pipeline,
                "total": len(company_pipeline),
                "is_inherited": True,
                "source": "company",
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job pipeline: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/jobs/{job_id}/pipeline", response_model=None)
async def update_job_pipeline(
    job_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    payload: JobPipelineUpdate,
    current_user: User = Depends(get_current_user_or_demo),
    stage_repo: RecruitmentStageRepository = Depends(get_stage_repo),
    sub_status_repo: SubStatusRepository = Depends(get_sub_status_repo),
company_id: str = Depends(require_company_id)):
    try:
        from app.models.job_vacancy import JobVacancy

        effective_company_id = get_user_company_id(current_user)

        job = await stage_repo.db.get(JobVacancy, uuid.UUID(job_id))
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        if str(job.company_id) != effective_company_id:
            raise HTTPException(status_code=403, detail="Access denied")

        config = [
            {
                "stage_name": s.stage_name,
                "stage_order": s.stage_order,
                "is_active": s.is_active,
                "sla_hours": s.sla_hours,
                "display_name": s.display_name,
                "color": s.color,
                "icon": s.icon,
            }
            for s in payload.stages
        ]

        job.pipeline_config = config  # type: ignore[assignment]
        job.updated_at = datetime.utcnow()  # type: ignore[assignment]
        await stage_repo.db.commit()
        await stage_repo.db.refresh(job)

        config_map = {item["stage_name"]: item for item in config}
        company_pipeline = await _get_company_pipeline(effective_company_id, stage_repo, sub_status_repo)
        customized = []
        for stage in company_pipeline:
            override = config_map.get(stage["name"])
            if override:
                stage["stage_order"] = override.get("stage_order", stage["stage_order"])
                stage["is_active"] = override.get("is_active", stage["is_active"])
                if override.get("sla_hours") is not None:
                    stage["sla_hours"] = override["sla_hours"]
                if override.get("display_name"):
                    stage["display_name"] = override["display_name"]
                if override.get("color"):
                    stage["color"] = override["color"]
                if override.get("icon"):
                    stage["icon"] = override["icon"]
            customized.append(stage)
        customized.sort(key=lambda s: s["stage_order"])

        return {
            "pipeline": customized,
            "total": len(customized),
            "is_inherited": False,
            "source": "custom",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating job pipeline: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/pipeline/job/{job_id}/inheritance-status", response_model=None)
async def get_pipeline_inheritance_status(
    job_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    current_user: User = Depends(get_current_active_user),
    stage_repo: RecruitmentStageRepository = Depends(get_stage_repo),
company_id: str = Depends(require_company_id)):
    """Check if a job's pipeline is customized or inherited from company default.

    P0-W1-02 fix (2026-05-24): after fetching the job, verify that
    job.company_id matches the authenticated user's company_id (JWT).
    Cross-tenant read attempts raise 403 before any data is returned.
    """
    try:
        from sqlalchemy import select as sa_select

        from app.models.job_vacancy import JobVacancy

        effective_company_id = get_user_company_id(current_user)

        result = await stage_repo.db.execute(
            sa_select(JobVacancy).where(JobVacancy.id == job_id)
        )
        job = result.scalars().first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        # P0-W1-02: ownership check — prevent cross-tenant info disclosure
        if str(job.company_id) != str(effective_company_id):
            raise HTTPException(status_code=403, detail="Access denied")

        return {
            "job_id": str(job.id),
            "is_customized": bool(getattr(job, 'is_pipeline_customized', False)),  # type: ignore[truthy-bool]
            "pipeline_config": job.pipeline_config if hasattr(job, 'pipeline_config') else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking pipeline inheritance: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/pipeline/job/{job_id}/copy-from-company", response_model=None)
async def copy_company_pipeline_to_job(
    job_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    current_user: User = Depends(get_current_active_user),
    stage_repo: RecruitmentStageRepository = Depends(get_stage_repo),
company_id: str = Depends(require_company_id)):
    """Copy company's default pipeline configuration to a job (reset to default)."""
    try:
        from sqlalchemy import select as sa_select
        from sqlalchemy import update as sa_update

        from app.models.job_vacancy import JobVacancy

        job_result = await stage_repo.db.execute(
            sa_select(JobVacancy).where(JobVacancy.id == job_id)
        )
        job = job_result.scalars().first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        effective_user_company = get_user_company_id(current_user)
        if str(job.company_id) != effective_user_company:
            raise HTTPException(status_code=403, detail="Access denied")

        company_id = str(job.company_id)  # type: ignore[truthy-bool]

        company_stages = await stage_repo.list_for_company(company_id)

        pipeline_config = []
        for stage in company_stages:
            pipeline_config.append({
                "stage_id": str(stage.id),
                "name": stage.name,  # type: ignore[truthy-bool]
                "display_name": stage.display_name,  # type: ignore[truthy-bool]
                "stage_order": stage.stage_order,
                "action_behavior": stage.action_behavior or "passive",  # type: ignore[truthy-bool]
                "color": stage.color or "#6B7280",  # type: ignore[truthy-bool]
                "icon": stage.icon or "circle",  # type: ignore[truthy-bool]
                "stage_type": stage.stage_type or "active",  # type: ignore[truthy-bool]
                "is_system": bool(stage.is_initial or stage.is_final),  # type: ignore[truthy-bool]
                "sla_hours": stage.sla_hours,
                "default_channel": getattr(stage, 'default_channel', 'email') or "email",
            })

        stmt = (
            sa_update(JobVacancy)
            .where(JobVacancy.id == job_id)
            .values(
                pipeline_config=pipeline_config,
                is_pipeline_customized=False,
                updated_at=datetime.utcnow(),
            )
        )
        await stage_repo.db.execute(stmt)
        await stage_repo.db.commit()

        return {
            "success": True,
            "job_id": str(job.id),
            "is_customized": False,
            "stages_copied": len(pipeline_config),
            "pipeline_config": pipeline_config,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error copying company pipeline to job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/pipeline/job/{job_id}/mark-customized", response_model=None)
async def mark_pipeline_customized(
    job_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    current_user: User = Depends(get_current_active_user),
    stage_repo: RecruitmentStageRepository = Depends(get_stage_repo),
company_id: str = Depends(require_company_id)):
    """Mark a job's pipeline as customized (no longer inherits from company).

    Phase G.3 — multi-tenancy fix. The original implementation issued
    UPDATE ... WHERE id = :job_id without scoping to company_id, which
    is a classic IDOR risk: any authenticated user could mutate any
    company's vacancy by guessing its UUID. Now scopes the WHERE clause
    by both id AND company_id; cross-tenant attempts result in
    rowcount=0 -> 404 (same response as not-found, no enumeration leak).
    """
    company_id = get_user_company_id(current_user)
    if not company_id:
        raise HTTPException(status_code=403, detail="company_id missing from token")

    try:
        from sqlalchemy import update as sa_update

        from app.models.job_vacancy import JobVacancy

        stmt = (
            sa_update(JobVacancy)
            .where(
                JobVacancy.id == job_id,
                JobVacancy.company_id == company_id,
            )
            .values(
                is_pipeline_customized=True,
                updated_at=datetime.utcnow(),
            )
        )
        result = await stage_repo.db.execute(stmt)
        await stage_repo.db.commit()

        row_count = getattr(result, 'rowcount', 0)  # type: ignore[union-attr]
        if row_count == 0:
            raise HTTPException(status_code=404, detail="Job not found")

        return {"success": True, "job_id": job_id, "is_customized": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking pipeline as customized: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# ── data_fields ───────────────────────────────────────────────────────────────


class StageDataFieldItem(WeDoBaseModel):
    """Campo de coleta de dados para um estágio do pipeline."""
    id: str
    displayName: str
    category: str  # basic | document | financial | admissional
    required: bool = False
    auto_collect: bool = False


class UpdateStageDataFieldsRequest(WeDoBaseModel):
    data_fields: list[StageDataFieldItem]


@router.patch("/stages/{stage_id}/data-fields", response_model=None)
async def update_stage_data_fields(
    stage_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    payload: UpdateStageDataFieldsRequest,
    stage_repo: RecruitmentStageRepository = Depends(get_stage_repo),
    company_id: str = Depends(require_company_id),
):
    """Atualiza campos de coleta (data_fields) de um estágio do pipeline da empresa.

    Multi-tenancy: verifica que o estágio pertence à company do JWT (assert_resource_ownership).
    Retorna o stage atualizado completo (to_dict).
    """
    stage = await stage_repo.get_by_id_str(stage_id)
    if stage is None:
        raise HTTPException(status_code=404, detail="Stage não encontrado")
    assert_resource_ownership(stage.company_id, company_id)

    updated = await stage_repo.update_fields_uuid(
        stage.id,
        {"data_fields": [df.model_dump() for df in payload.data_fields]},
    )
    if not updated:
        raise HTTPException(status_code=500, detail="Falha ao atualizar data_fields")

    refreshed = await stage_repo.get_by_id(stage.id)
    return {"success": True, "stage": refreshed.to_dict() if refreshed else None}
