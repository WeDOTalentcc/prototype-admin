"""JobSeedBuilderService - single producer of JobCreationSeed.

Normalizes a JobTemplate (arquetipo) or an existing JobVacancy into the
canonical JobCreationSeed for review-before-create. Reuses JobTemplateService
(templates) so the template field knowledge lives in one place. The vacancy
path (PR-B) reuses JobCloneService.FIELDS_TO_CLONE for the same reason.

Canonical rules:
- company_id comes from the caller (JWT/session), never a payload field.
- is_system templates (company_id NULL) are TENANT-EXEMPT: readable by any
  company. A company-owned template from another company raises PermissionError
  (fail-closed). Missing template raises ValueError (fail loud, no silent seed).
- Inherited salary is flagged needs_review=True (honest provenance).
- ALWAYS_FRESH_FIELDS are never mapped (guaranteed by construction here).
"""
from __future__ import annotations

import uuid as uuid_mod
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.job_creation.schemas import (
    FieldProvenance,
    JobCreationSeed,
    SourceDescriptor,
)
from app.domains.job_management.services.job_template_service import JobTemplateService
from app.shared.tracing import trace_span

_SEEDABLE_FIELDS = [
    "title",
    "seniority",
    "work_model",
    "department",
    "location",
    "employment_type",
    "salary_min",
    "salary_max",
    "skills",
    "responsibilities",
    "requirements",
    "nice_to_have",
    "description",
    "pipeline_template_id",
]


def _skill_names(raw: Any) -> list[str]:
    """JobTemplate.default_skills is JSON: list[str] or list[{skill|name|nome}]."""
    out: list[str] = []
    for item in raw or []:
        if isinstance(item, str):
            out.append(item)
        elif isinstance(item, dict):
            name = item.get("skill") or item.get("name") or item.get("nome")
            if name:
                out.append(str(name))
    return out


def _vacancy_skill_names(raw: Any) -> list[str]:
    """JobVacancy.technical_requirements e JSON: list[{technology|skill|name}]."""
    out: list[str] = []
    for item in raw or []:
        if isinstance(item, str):
            out.append(item)
        elif isinstance(item, dict):
            name = (
                item.get("technology")
                or item.get("skill")
                or item.get("name")
                or item.get("nome")
            )
            if name:
                out.append(str(name))
    return out


class JobSeedBuilderService:
    """Produces a JobCreationSeed from a source. Single source of truth."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._templates = JobTemplateService(db)
        # Import local p/ evitar ciclo (mesmo padrao das tools de vaga).
        from app.domains.job_management.repositories.job_vacancy_crud_repository import (
            JobVacancyCRUDRepository,
        )
        self._vacancies = JobVacancyCRUDRepository(db)

    @trace_span("job_seed.build_from_template")
    async def build_seed_from_template(
        self, template_id: str | uuid_mod.UUID, company_id: str
    ) -> JobCreationSeed:
        tid = (
            template_id
            if isinstance(template_id, uuid_mod.UUID)
            else uuid_mod.UUID(str(template_id))
        )
        tpl = await self._templates.get_template_by_id(tid)
        if tpl is None:
            raise ValueError(f"Template {template_id} nao encontrado")

        # is_system (company_id NULL) = TENANT-EXEMPT; else must match (fail-closed).
        if tpl.company_id is not None and str(tpl.company_id) != str(company_id):
            raise PermissionError("Template fora do escopo da empresa")

        name = tpl.title
        prov: dict[str, FieldProvenance] = {}
        fields: dict[str, Any] = {}

        def mark(key: str, value: Any, needs_review: bool = False) -> None:
            if value in (None, "", [], {}):
                return
            fields[key] = value
            prov[key] = FieldProvenance(
                source_type="template",
                source_id=str(tpl.id),
                source_name=name,
                needs_review=needs_review,
            )

        mark("title", tpl.title)
        mark("seniority", getattr(tpl, "seniority", None))
        mark("work_model", getattr(tpl, "work_model", None))
        mark("description", getattr(tpl, "default_description", None))
        mark("requirements", getattr(tpl, "default_requirements", None))
        mark("nice_to_have", getattr(tpl, "default_nice_to_have", None))
        mark("responsibilities", list(getattr(tpl, "default_responsibilities", None) or []))
        mark("skills", _skill_names(getattr(tpl, "default_skills", None)))
        # Inherited salary -> needs_review (honest provenance).
        mark("salary_min", getattr(tpl, "salary_range_min", None), needs_review=True)
        mark("salary_max", getattr(tpl, "salary_range_max", None), needs_review=True)

        return JobCreationSeed(
            **fields,
            provenance=prov,
            source=SourceDescriptor(type="template", id=str(tpl.id), name=name),
            coverage_filled=sum(1 for k in _SEEDABLE_FIELDS if k in fields),
            coverage_total=len(_SEEDABLE_FIELDS),
        )

    @trace_span("job_seed.build_from_vacancy")
    async def build_seed_from_vacancy(
        self, vacancy_id: str | uuid_mod.UUID, company_id: str
    ) -> JobCreationSeed:
        """Clona uma vaga existente em JobCreationSeed (PR-B1, decisao Paulo
        2026-06-05: conservador). Campos de intake + salario (needs_review) +
        JD text. Reuso rico (enriched_jd/WSI/competencias/elegibilidade) e o
        PR-B2 (precisa de guard por-no mantendo os gates de fairness)."""
        vac = await self._vacancies.get_by_id_strict_company(
            str(vacancy_id), str(company_id)
        )
        if vac is None:
            # get_by_id_strict_company devolve None p/ inexistente E cross-tenant
            # (opaco — nao vaza existencia). Fail-loud canonical (REGRA 4).
            raise ValueError(
                f"Vaga {vacancy_id} nao encontrada no escopo da empresa"
            )

        name = vac.title
        prov: dict[str, FieldProvenance] = {}
        fields: dict[str, Any] = {}

        def mark(key: str, value: Any, needs_review: bool = False) -> None:
            if value in (None, "", [], {}):
                return
            fields[key] = value
            prov[key] = FieldProvenance(
                source_type="vacancy",
                source_id=str(vac.id),
                source_name=name,
                needs_review=needs_review,
            )

        mark("title", vac.title)
        mark("seniority", getattr(vac, "seniority_level", None))
        mark("work_model", getattr(vac, "work_model", None))
        mark("department", getattr(vac, "department", None))
        mark("location", getattr(vac, "location", None))
        mark("employment_type", getattr(vac, "employment_type", None))
        mark("description", getattr(vac, "description", None))
        mark("responsibilities", list(getattr(vac, "responsibilities", None) or []))
        # requirements no model e ARRAY(String); o seed carrega str (Optional[str]).
        _reqs = getattr(vac, "requirements", None) or []
        if isinstance(_reqs, (list, tuple)):
            _reqs = "\n".join(str(r) for r in _reqs if r)
        mark("requirements", _reqs)
        # skills: technical_requirements e [{technology,...}] — PR-B1 leva so os
        # nomes; o detalhe estruturado e reuso rico do PR-B2.
        mark("skills", _vacancy_skill_names(getattr(vac, "technical_requirements", None)))
        # salario: salary_range JSON {min,max} -> needs_review (proveniencia honesta).
        _sr = getattr(vac, "salary_range", None) or {}
        if isinstance(_sr, dict):
            mark("salary_min", _sr.get("min"), needs_review=True)
            mark("salary_max", _sr.get("max"), needs_review=True)

        return JobCreationSeed(
            **fields,
            provenance=prov,
            source=SourceDescriptor(type="vacancy", id=str(vac.id), name=name),
            coverage_filled=sum(1 for k in _SEEDABLE_FIELDS if k in fields),
            coverage_total=len(_SEEDABLE_FIELDS),
        )
