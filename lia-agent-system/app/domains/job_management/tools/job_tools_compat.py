"""Wrappers do executor de chat para o ciclo de vida de vagas.

Cada wrapper:
- Extrai `_tenant_id` (injetado pelo executor) → `company_id`.
- Remove chaves prefixadas com `_` antes de delegar ao service.
- Delega para `JobVacancyLifecycleService` (fonte da verdade canônica).

Erros conhecidos (`ValueError`, `LookupError`) viram resposta estruturada com
`success=False`; erros inesperados sobem para o executor logar com stack.
"""
from __future__ import annotations

import logging
from typing import Any

from app.domains.job_management.services.job_vacancy_lifecycle_service import (
    job_vacancy_lifecycle_service,
)
from app.domains.job_management.services.job_clone_service import job_clone_service
from lia_config.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


def _split_meta(params: dict[str, Any]) -> tuple[str | None, dict[str, Any]]:
    tenant_id = params.get("_tenant_id")
    cleaned = {k: v for k, v in params.items() if not k.startswith("_")}
    return (str(tenant_id) if tenant_id else None), cleaned


def _resolve_company_id(payload: dict[str, Any], tenant_id: str | None) -> str:
    company_id = payload.pop("company_id", None) or tenant_id
    if not company_id:
        raise ValueError(
            "company_id/tenant_id ausente — chat tool não pode operar sem contexto multi-tenant."
        )
    return str(company_id)


def _structured_error(operation: str, exc: Exception) -> dict[str, Any]:
    code = "validation_error" if isinstance(exc, ValueError) else (
        "not_found" if isinstance(exc, LookupError) else "internal_error"
    )
    return {
        "success": False,
        "operation": operation,
        "error": code,
        "message": str(exc),
    }


async def create_job_vacancy(**params: Any) -> dict[str, Any]:
    tenant_id, payload = _split_meta(params)
    try:
        company_id = _resolve_company_id(payload, tenant_id)
        return await job_vacancy_lifecycle_service.create(company_id=company_id, **payload)
    except (ValueError, LookupError) as exc:
        return _structured_error("create_job_vacancy", exc)


async def update_job_vacancy(**params: Any) -> dict[str, Any]:
    tenant_id, payload = _split_meta(params)
    try:
        company_id = _resolve_company_id(payload, tenant_id)
        job_id = payload.pop("job_id", None)
        if not job_id:
            raise ValueError("job_id é obrigatório para atualizar vaga")
        return await job_vacancy_lifecycle_service.update(
            company_id=company_id, job_id=str(job_id), **payload
        )
    except (ValueError, LookupError) as exc:
        return _structured_error("update_job_vacancy", exc)


async def close_job_vacancy(**params: Any) -> dict[str, Any]:
    tenant_id, payload = _split_meta(params)
    try:
        company_id = _resolve_company_id(payload, tenant_id)
        job_id = payload.pop("job_id", None)
        if not job_id:
            raise ValueError("job_id é obrigatório para fechar vaga")
        reason = payload.get("reason")
        return await job_vacancy_lifecycle_service.set_status(
            company_id=company_id, job_id=str(job_id), status="Concluída", reason=reason
        )
    except (ValueError, LookupError) as exc:
        return _structured_error("close_job_vacancy", exc)


async def duplicate_job_vacancy(**params: Any) -> dict[str, Any]:
    """Duplica uma vaga existente (clone completo, opcionalmente com candidatos).

    Aceita `job_id` como UUID, código WDT ou trecho do título — resolvido via
    `JobCloneService.get_job_by_id_or_title`.
    """
    tenant_id, payload = _split_meta(params)
    try:
        company_id = _resolve_company_id(payload, tenant_id)
        job_identifier = payload.pop("job_id", None) or payload.pop("source_job_id", None)
        if not job_identifier:
            raise ValueError("job_id é obrigatório para duplicar vaga")

        copies = int(payload.pop("copies", 1) or 1)
        raw_include = payload.pop("include_candidates", True)
        if isinstance(raw_include, str):
            include_candidates = raw_include.strip().lower() not in {"false", "0", "no", "nao", "não", ""}
        else:
            include_candidates = bool(raw_include)
        candidate_filter = payload.pop("candidate_filter", None)
        candidate_status_override = payload.pop("candidate_status_override", None)
        overrides = payload.pop("overrides", None)
        created_by = payload.pop("created_by", None) or payload.pop("user_id", None)

        async with AsyncSessionLocal() as session:
            source_job = await job_clone_service.get_job_by_id_or_title(
                session, str(job_identifier), company_id
            )
            if not source_job:
                raise LookupError(
                    f"Vaga '{job_identifier}' não encontrada para o tenant {company_id}."
                )
            return await job_clone_service.duplicate_job(
                db=session,
                source_job_id=source_job.id,
                company_id=company_id,
                copies=copies,
                include_candidates=include_candidates,
                candidate_filter=candidate_filter,
                candidate_status_override=candidate_status_override,
                overrides=overrides,
                created_by=created_by,
            )
    except (ValueError, LookupError) as exc:
        return _structured_error("duplicate_job_vacancy", exc)


async def clone_job_vacancy(**params: Any) -> dict[str, Any]:
    """Clona uma vaga existente como template (sem candidatos).

    Aceita `job_id` como UUID, código WDT ou trecho do título. Opcionalmente
    aceita `new_title` para renomear a cópia, e `overrides` com campos a
    sobrescrever.
    """
    tenant_id, payload = _split_meta(params)
    try:
        company_id = _resolve_company_id(payload, tenant_id)
        job_identifier = payload.pop("job_id", None) or payload.pop("source_job_id", None)
        if not job_identifier:
            raise ValueError("job_id é obrigatório para clonar vaga")

        new_title = payload.pop("new_title", None) or payload.pop("title", None)
        overrides = payload.pop("overrides", None)
        created_by = payload.pop("created_by", None) or payload.pop("user_id", None)

        async with AsyncSessionLocal() as session:
            source_job = await job_clone_service.get_job_by_id_or_title(
                session, str(job_identifier), company_id
            )
            if not source_job:
                raise LookupError(
                    f"Vaga '{job_identifier}' não encontrada para o tenant {company_id}."
                )
            return await job_clone_service.clone_from_template(
                db=session,
                source_job_id=source_job.id,
                company_id=company_id,
                new_title=new_title,
                overrides=overrides,
                created_by=created_by,
            )
    except (ValueError, LookupError) as exc:
        return _structured_error("clone_job_vacancy", exc)


async def pause_job(**params: Any) -> dict[str, Any]:
    tenant_id, payload = _split_meta(params)
    try:
        company_id = _resolve_company_id(payload, tenant_id)
        job_id = payload.pop("job_id", None)
        if not job_id:
            raise ValueError("job_id é obrigatório para pausar vaga")
        reason = payload.get("reason")
        return await job_vacancy_lifecycle_service.set_status(
            company_id=company_id, job_id=str(job_id), status="Pausada", reason=reason
        )
    except (ValueError, LookupError) as exc:
        return _structured_error("pause_job", exc)
