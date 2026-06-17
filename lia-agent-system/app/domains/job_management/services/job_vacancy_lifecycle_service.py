"""Service layer canônico para o ciclo de vida de vagas (create/update/close/pause).

**Fonte da verdade** para operações de write de vagas que podem ser disparadas
fora do contexto de uma rota FastAPI (ex.: via chat / tool executor). A rota
em `app/api/v1/job_vacancies/crud.py` deve migrar para chamar este service
em vez de manipular o repositório diretamente — isso elimina a duplicação de
lógica de transformação payload→ORM apontada pela auditoria.

Características:
- Stateless. Cada método abre sua própria sessão via `AsyncSessionLocal`.
- Multi-tenant obrigatório: `company_id` é parâmetro obrigatório em todas as
  operações que tocam dados (vem do `_tenant_id` injetado pelo executor).
- Falha alta e explícita: validações ausentes ou vagas não encontradas levantam
  `ValueError`/`LookupError`. Sem fallback silencioso.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from lia_config.database import AsyncSessionLocal
from lia_models.job_vacancy import JobVacancy

from app.domains.job_management.repositories.job_vacancy_crud_repository import (
    JobVacancyCRUDRepository,
)

logger = logging.getLogger(__name__)

_UPDATABLE_FIELDS: set[str] = {
    # Identidade básica
    "title",
    "department",
    "location",
    "work_model",
    "employment_type",
    "seniority_level",
    # Descrição e requisitos
    "description",
    "requirements",
    "technical_requirements",
    "languages",
    "behavioral_competencies",
    # Remuneração
    "salary",
    "salary_range",
    "bonus_range",
    "benefits",
    # Status e workflow
    "status",
    "stage",
    "priority",
    "urgency_level",
    # Datas
    "open_date",
    "deadline",
    "deadline_screening",
    "deadline_shortlist",
    "deadline_closing",
    # Pessoas
    "manager",
    "manager_email",
    "recruiter",
    "recruiter_email",
    # Estrutura e processo
    "organizational_structure",
    "interview_stages",
    "screening_questions",
    "disabled_eligibility_question_ids",
    "eligibility_questions",
    "pipeline_config",
    # Confidencialidade e ação afirmativa
    "is_confidential",
    "is_affirmative",
    "affirmative_criteria_primary",
    "affirmative_criteria_secondary",
    "affirmative_description",
    "affirmative_document_required",
    "affirmative_document_types",
    "visibility",
    "access_list",
    "masked_company_name",
    "exclude_from_sync",
    "whatsapp_template_type",
    "confidentiality_config",
    # Orçamento
    "budget",
    # Tags e segmentação
    "tags",
    "hiring_process",
    "target_audience",
    "target_sector",
    "target_segment",
    # Próximas ações e governança
    "next_actions",
    "timeline",
    "governance_rules",
    "screening_config",
    # JD enriquecido
    "enriched_jd",
}


def _coerce_uuid(value: Any) -> UUID:
    if isinstance(value, UUID):
        return value
    return UUID(str(value))


class JobVacancyLifecycleService:
    """Operações canônicas de ciclo de vida da vaga.

    Não mantém estado entre chamadas. Cada método encapsula sua própria
    transação (commit ao final do bloco `async with`).
    """

    async def create(
        self,
        *,
        company_id: str,
        title: str,
        department: str | None = None,
        location: str | None = None,
        work_model: str | None = None,
        description: str | None = None,
        status: str = "Rascunho",
        **extra: Any,
    ) -> dict[str, Any]:
        if not company_id:
            raise ValueError("company_id é obrigatório para criar vaga")
        if not title or not title.strip():
            raise ValueError("title é obrigatório para criar vaga")

        async with AsyncSessionLocal() as session:
            repo = JobVacancyCRUDRepository(session)
            vacancy = JobVacancy(
                company_id=str(company_id),
                title=title.strip(),
                department=department,
                location=location,
                work_model=work_model,
                description=description,
                # T-1166 — lifecycle.create is a thin wrapper around the model;
                # ensure the new ARRAY column is initialized to [].
                responsibilities=[],
                status=status,
                created_at=datetime.utcnow(),
            )
            created = await repo.create_vacancy(vacancy)
            await session.commit()
            logger.info(
                "JobVacancyLifecycleService.create",
                extra={"company_id": company_id, "job_vacancy_id": str(created.id)},
            )
            return {
                "success": True,
                "id": str(created.id),
                "title": created.title,
                "status": created.status,
            }

    async def update(
        self,
        *,
        company_id: str,
        job_id: str,
        **fields: Any,
    ) -> dict[str, Any]:
        if not company_id:
            raise ValueError("company_id é obrigatório")
        if not job_id:
            raise ValueError("job_id é obrigatório")

        patch = {k: v for k, v in fields.items() if k in _UPDATABLE_FIELDS and v is not None}
        if not patch:
            raise ValueError(
                f"Nenhum campo atualizável fornecido. Esperado um de: {sorted(_UPDATABLE_FIELDS)}"
            )

        async with AsyncSessionLocal() as session:
            repo = JobVacancyCRUDRepository(session)
            vacancy = await repo.get_vacancy_by_id_and_company(
                _coerce_uuid(job_id), str(company_id)
            )
            if vacancy is None:
                raise LookupError(f"Vaga {job_id} não encontrada para company {company_id}")

            for field, value in patch.items():
                setattr(vacancy, field, value)
            await repo.flush_and_refresh(vacancy)
            await session.commit()
            logger.info(
                "JobVacancyLifecycleService.update",
                extra={
                    "company_id": company_id,
                    "job_vacancy_id": str(vacancy.id),
                    "fields": sorted(patch.keys()),
                },
            )
            return {
                "success": True,
                "id": str(vacancy.id),
                "updated_fields": sorted(patch.keys()),
                "status": vacancy.status,
            }

    async def set_status(
        self,
        *,
        company_id: str,
        job_id: str,
        status: str,
        reason: str | None = None,
    ) -> dict[str, Any]:
        if not status:
            raise ValueError("status é obrigatório")

        async with AsyncSessionLocal() as session:
            repo = JobVacancyCRUDRepository(session)
            vacancy = await repo.get_vacancy_by_id_and_company(
                _coerce_uuid(job_id), str(company_id)
            )
            if vacancy is None:
                raise LookupError(f"Vaga {job_id} não encontrada para company {company_id}")

            vacancy.status = status
            if status == "Concluída" and hasattr(vacancy, "closed_at"):
                vacancy.closed_at = datetime.utcnow()
            await repo.flush_and_refresh(vacancy)
            await session.commit()
            logger.info(
                "JobVacancyLifecycleService.set_status",
                extra={
                    "company_id": company_id,
                    "job_vacancy_id": str(vacancy.id),
                    "new_status": status,
                    "reason": reason,
                },
            )
            return {
                "success": True,
                "id": str(vacancy.id),
                "status": vacancy.status,
                "reason": reason,
            }


job_vacancy_lifecycle_service = JobVacancyLifecycleService()
