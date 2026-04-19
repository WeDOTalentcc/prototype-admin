"""Facade module exposing job-vacancy lifecycle tools to the chat executor.

Estes wrappers existem para que o `execute_job_management_tool` consiga importar e
resolver os handlers sem `ModuleNotFoundError`. A implementação canônica das
operações de CRUD está nas rotas FastAPI em `app/api/v1/job_vacancies/crud.py`,
que dependem do `JobVacancyCRUDRepository` e de injeção via `Depends(...)` —
não são chamáveis diretamente com `**kwargs`.

Onde possível, delegamos para o repositório acquirindo uma sessão; caso
contrário, levantamos `NotImplementedError` explícito (sem mock silencioso),
para que o chat retorne uma mensagem honesta ao recrutador e o backlog fique
visível.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def _strip_meta(p: dict) -> dict:
    return {k: v for k, v in p.items() if not k.startswith("_")}


async def create_job_vacancy(**params: Any) -> dict[str, Any]:
    """Cria uma vaga de emprego.

    Backlog: extrair a lógica de transformação payload→ORM da rota FastAPI
    (`app.api.v1.job_vacancies.crud.create_job_vacancy`) para um service layer
    reutilizável (`JobVacancyLifecycleService`). Enquanto isso, o chat deve
    orientar o recrutador a usar o wizard ou a API.
    """
    raise NotImplementedError(
        "create_job_vacancy via chat ainda não está conectado ao service layer. "
        "Use o wizard de criação de vaga (rota `/job-vacancies` ou comando `/job`) "
        "ou aguarde implementação de JobVacancyLifecycleService."
    )


async def update_job_vacancy(**params: Any) -> dict[str, Any]:
    """Atualiza uma vaga existente. Vide create_job_vacancy."""
    raise NotImplementedError(
        "update_job_vacancy via chat ainda não está conectado ao service layer. "
        "Backlog: extrair lógica da rota PATCH /job-vacancies/{id} para service."
    )


async def close_job_vacancy(**params: Any) -> dict[str, Any]:
    """Fecha (concluída) uma vaga. Backlog: wire para JobVacancyCRUDRepository
    + update_job_vacancy_status (status='Concluída')."""
    raise NotImplementedError(
        "close_job_vacancy via chat ainda não está conectado. "
        "Use a API: PATCH /job-vacancies/{id}/status com status='Concluída'."
    )


async def pause_job(**params: Any) -> dict[str, Any]:
    """Pausa uma vaga. Backlog: wire para update_job_vacancy_status (status='Pausada')."""
    raise NotImplementedError(
        "pause_job via chat ainda não está conectado. "
        "Use a API: PATCH /job-vacancies/{id}/status com status='Pausada'."
    )
