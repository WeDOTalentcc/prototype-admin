"""Resolve o employment_type default da vaga pela cadeia de heranca
departamento > empresa. FASE 1 / E3 (audit 2026-06-06).

Fail-open: a entrada assincrona NUNCA levanta — em qualquer erro retorna None,
preservando o comportamento atual do publish (caminho irreversivel de criacao
de vaga). A funcao pura `resolve_default_employment_type` e unit-testada.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def resolve_default_employment_type(
    parsed: str | None,
    dept_defaults: dict | None,
    company_primary: str | None,
    company_list: list[str] | None,
) -> str | None:
    """Pura. Precedencia (mais especifico ganha):
    parsed (recrutador) > departamento.primary > departamento.lista[0] >
    empresa.primary > empresa.lista[0] > None.
    """
    if parsed:
        return parsed
    if isinstance(dept_defaults, dict):
        dp = dept_defaults.get("primary_employment_type")
        if dp:
            return dp
        dl = dept_defaults.get("employment_types")
        if isinstance(dl, list) and dl:
            return dl[0]
    if company_primary:
        return company_primary
    if isinstance(company_list, list) and company_list:
        return company_list[0]
    return None


async def resolve_employment_type_for_state(state: dict[str, Any]) -> str | None:
    """Async, fail-open. Le empresa (primary_employment_type/employment_types) +
    department.defaults e aplica a precedencia. None em qualquer erro."""
    try:
        parsed = state.get("parsed_employment_type")
        if parsed:
            return parsed
        company_id = state.get("company_id") or state.get("workspace_id")
        if not company_id:
            return None
        from uuid import UUID
        try:
            cid = UUID(str(company_id))
        except (ValueError, TypeError):
            return None  # workspace_id numerico/slug -> sem heranca (fail-open)

        from app.core.database import AsyncSessionLocal
        from app.domains.cv_screening.repositories.lia_field_config_repository import (
            LiaFieldConfigRepository,
        )

        dept_name = state.get("parsed_department")
        async with AsyncSessionLocal() as db:
            repo = LiaFieldConfigRepository(db)
            profile = await repo.get_company_profile(cid)
            company_primary = getattr(profile, "primary_employment_type", None) if profile else None
            company_list = getattr(profile, "employment_types", None) if profile else None
            dept_defaults = None
            if dept_name:
                dept = await repo.get_department_by_name(cid, str(dept_name))
                dept_defaults = getattr(dept, "defaults", None) if dept else None
        return resolve_default_employment_type(
            parsed, dept_defaults, company_primary, company_list
        )
    except Exception:  # noqa: BLE001 — fail-open: nunca quebra o publish
        logger.warning("[employment_type_resolver] fail-open", exc_info=True)
        return None
