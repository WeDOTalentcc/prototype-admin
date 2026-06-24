"""Resolve o valor default de um campo escalar da vaga pela cadeia canonica
(departamento > empresa), reusando LiaFieldConfigService.get_field_config — que
ja aplica toggles + department.defaults (0-dept). DRY: nao duplica a logica de
heranca. Fail-open: None em qualquer erro (preserva o comportamento do publish).
FASE 1 (audit 2026-06-06).
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


async def resolve_field_default_for_state(
    state: dict[str, Any], field_key: str
) -> str | None:
    """Async, fail-open. Retorna o valor resolvido (string escalar) do ``field_key``
    pela cadeia canonica, ou None. So retorna strings simples (campos escalares
    como work_model); listas/dicts -> None (nao aplicavel a um campo unico da vaga).
    """
    try:
        company_id = state.get("company_id") or state.get("workspace_id")
        if not company_id:
            return None
        from uuid import UUID
        try:
            UUID(str(company_id))
        except (ValueError, TypeError):
            return None  # workspace_id numerico/slug -> sem heranca (fail-open)

        from app.core.database import AsyncSessionLocal
        from app.domains.cv_screening.services.lia_field_config_service import (
            LiaFieldConfigService,
        )

        job_context = {
            "title": state.get("parsed_title"),
            "department": state.get("parsed_department"),
            "seniority": state.get("parsed_seniority"),
        }
        async with AsyncSessionLocal() as db:
            result = await LiaFieldConfigService(db).get_field_config(
                str(company_id), job_context
            )
        ctx = result.field_contexts.get(field_key)
        val = ctx.value if ctx else None
        return val if isinstance(val, str) and val else None
    except Exception:  # noqa: BLE001 — fail-open
        logger.warning(
            "[vaga_field_inheritance] fail-open field=%s", field_key, exc_info=True
        )
        return None


async def resolve_manager_from_department(state: dict[str, Any]) -> dict | None:
    """Async, fail-open. Quando a vaga e de um departamento que tem gestor
    cadastrado (Department.manager_name/email), devolve {name, email} pra a vaga
    herdar. None se sem departamento/sem gestor/erro. FASE 1 (heranca do gestor;
    o match-or-create de gestor NOVO com HITL vive no orquestrador)."""
    try:
        company_id = state.get("company_id") or state.get("workspace_id")
        dept_name = state.get("parsed_department")
        if not company_id or not dept_name:
            return None
        from uuid import UUID
        try:
            cid = UUID(str(company_id))
        except (ValueError, TypeError):
            return None
        from app.core.database import AsyncSessionLocal
        from app.domains.cv_screening.repositories.lia_field_config_repository import (
            LiaFieldConfigRepository,
        )
        async with AsyncSessionLocal() as db:
            dept = await LiaFieldConfigRepository(db).get_department_by_name(
                cid, str(dept_name)
            )
        if dept is None:
            return None
        name = getattr(dept, "manager_name", None)
        email = getattr(dept, "manager_email", None)
        if name or email:
            return {"name": name, "email": email}
        return None
    except Exception:  # noqa: BLE001 — fail-open
        logger.warning("[vaga_field_inheritance] manager fail-open", exc_info=True)
        return None
