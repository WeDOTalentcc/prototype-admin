"""
WSI Session Repository
======================

Acesso a dados (read-only) das tabelas `wsi_sessions`, `wsi_results` e
`job_vacancies` para o domínio de triagem por voz.

Histórico:
- Audit task #496 (PR3): extraído do `wsi_voice_orchestrator.py`. As funções
  abaixo são thin wrappers em torno de SQL com `text()` — propositalmente
  não usam ORM porque o snapshot do orquestrador foi escrito assim e a
  migração para SQLAlchemy ORM mora em outro ticket. Por enquanto, o ganho
  aqui é isolar o I/O de banco da lógica de orquestração / lifecycle.

Contrato:
- Todas as funções recebem `session: AsyncSession` JÁ aberta. A criação de
  sessão (`AsyncSessionLocal()`) continua responsabilidade do orquestrador,
  que precisa decidir entre reutilizar a sessão recebida pelo caller (rota
  HTTP, evento) e abrir uma própria.
- Falhas de SQL em `get_company_id_for_vacancy` são absorvidas e retornam
  `"unknown"` por design (a chamada é só para enriquecimento de evento;
  derrubar a triagem inteira por falha de lookup acessório seria pior). Já
  os getters de sessão **propagam** exceções — quem chama precisa saber
  que a leitura falhou.
"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def get_company_id_for_vacancy(
    session: AsyncSession, job_vacancy_id: str
) -> str:
    """
    Recupera o `company_id` de uma vaga.

    Returns:
        ID como string, ou `"unknown"` se a vaga não existe ou se houve
        erro de leitura (logado como warning). Nunca lança exceção — esta
        função é usada para enriquecer payload de eventos e o caller já
        trata `"unknown"` graciosamente.
    """
    try:
        result = await session.execute(
            text("SELECT company_id FROM job_vacancies WHERE id = :vacancy_id"),
            {"vacancy_id": job_vacancy_id},
        )
        row = result.fetchone()
        if row and row[0]:
            return str(row[0])

        logger.warning(f"⚠️ No company_id found for vacancy {job_vacancy_id}")
        return "unknown"
    except Exception as e:
        logger.warning(
            f"⚠️ Error fetching company_id for vacancy {job_vacancy_id}: {e}"
        )
        return "unknown"


async def get_session_status(
    session: AsyncSession, session_id: str
) -> dict[str, Any] | None:
    """
    Lê o status agregado de uma sessão WSI (sessão + result via LEFT JOIN).

    Returns:
        Dict com session/result ou `None` se a sessão não existe.
    """
    result = await session.execute(
        text(
            """
            SELECT s.id, s.candidate_id, s.job_vacancy_id, s.screening_type, s.mode,
                   s.status, s.call_id, s.agent_id, s.started_at, s.completed_at,
                   r.overall_wsi, r.technical_wsi, r.behavioral_wsi, r.classification
            FROM wsi_sessions s
            LEFT JOIN wsi_results r ON r.session_id = s.id
            WHERE s.id = :session_id
            """
        ),
        {"session_id": session_id},
    )
    row = result.fetchone()

    if not row:
        return None

    return {
        "session_id": row[0],
        "candidate_id": row[1],
        "job_vacancy_id": row[2],
        "screening_type": row[3],
        "mode": row[4],
        "status": row[5],
        "call_id": row[6],
        "agent_id": row[7],
        "started_at": row[8].isoformat() if row[8] else None,
        "completed_at": row[9].isoformat() if row[9] else None,
        "result": {
            "overall_wsi": float(row[10]) if row[10] else None,
            "technical_wsi": float(row[11]) if row[11] else None,
            "behavioral_wsi": float(row[12]) if row[12] else None,
            "classification": row[13],
        }
        if row[10]
        else None,
    }


async def get_session_by_call_id(
    session: AsyncSession, call_id: str
) -> dict[str, Any] | None:
    """
    Localiza uma sessão pelo `call_id` da chamada de voz e devolve o status
    completo. Internamente reusa `get_session_status`.

    Returns:
        Dict idêntico a `get_session_status` ou `None` se nenhuma sessão
        está vinculada a esse `call_id`.
    """
    result = await session.execute(
        text("SELECT id FROM wsi_sessions WHERE call_id = :call_id"),
        {"call_id": call_id},
    )
    row = result.fetchone()

    if not row:
        return None

    return await get_session_status(session, row[0])
