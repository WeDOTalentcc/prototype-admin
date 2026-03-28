"""
Audit Writer — persistência dual de execuções de agentes.

PostgreSQL  → metadados leves (execution_id, domain, duration, tools, success, storage_path)
             consulta rápida, dashboards, investigação inicial
Storage obj → payload completo (prompts, respostas LLM, tool I/O, raciocínio)
             investigação profunda, compliance, replay

Uso:
    writer = AuditWriter()
    await writer.persist(record)
"""
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from lia_audit.audit_models import ExecutionAuditRecord
from lia_audit.audit_storage import build_storage_path, get_audit_storage

logger = logging.getLogger(__name__)


class AuditWriter:
    """
    Persiste registros de execução de agentes em dois destinos:
    1. PostgreSQL — tabela audit_execution_metadata (leve, indexável)
    2. AuditStorage — arquivo local ou S3 (payload completo)
    """

    async def persist(self, record: ExecutionAuditRecord, db: Optional[AsyncSession] = None) -> None:
        """
        Persiste o record completo.
        Erros de persistência são logados mas não propagados — nunca bloquear execução do agente.
        """
        try:
            storage_path = await self._save_full_payload(record)
            record.storage_path = storage_path
        except Exception as exc:
            logger.error("[AuditWriter] Falha ao salvar payload completo (exec=%s): %s", record.execution_id, exc)

        try:
            await self._save_metadata(record, db)
        except Exception as exc:
            logger.error("[AuditWriter] Falha ao salvar metadados PG (exec=%s): %s", record.execution_id, exc)

    async def _save_full_payload(self, record: ExecutionAuditRecord) -> str:
        """Salva payload completo (entries) no storage configurado."""
        storage = get_audit_storage()
        path = build_storage_path(record.domain, record.company_id, record.execution_id)
        saved_path = await storage.save(path, record.to_full_dict())
        return saved_path

    async def _save_metadata(self, record: ExecutionAuditRecord, db: Optional[AsyncSession] = None) -> None:
        """Insere metadados leves na tabela audit_execution_metadata."""
        if db is None:
            from lia_config.database import AsyncSessionLocal
            async with AsyncSessionLocal() as session:
                await self._insert_metadata(record, session)
        else:
            await self._insert_metadata(record, db)

    async def _insert_metadata(self, record: ExecutionAuditRecord, db: AsyncSession) -> None:
        """INSERT OR IGNORE na tabela de metadados."""
        import json
        stmt = text("""
            INSERT INTO audit_execution_metadata (
                execution_id, session_id, company_id, user_id,
                domain, agent_type, timestamp, duration_ms,
                nodes_visited, tools_used, success, confidence,
                storage_path, error
            ) VALUES (
                :execution_id, :session_id, :company_id, :user_id,
                :domain, :agent_type, :timestamp, :duration_ms,
                :nodes_visited, :tools_used, :success, :confidence,
                :storage_path, :error
            )
            ON CONFLICT (execution_id) DO NOTHING
        """)
        await db.execute(stmt, {
            "execution_id": record.execution_id,
            "session_id": record.session_id or "",
            "company_id": record.company_id,
            "user_id": record.user_id or "",
            "domain": record.domain,
            "agent_type": record.agent_type,
            "timestamp": record.start_time or datetime.now(timezone.utc).isoformat(),
            "duration_ms": record.total_duration_ms,
            "nodes_visited": json.dumps(record.nodes_visited),
            "tools_used": json.dumps(record.tools_used),
            "success": record.success,
            "confidence": record.confidence,
            "storage_path": record.storage_path,
            "error": record.error,
        })
        await db.commit()

    async def load_full(self, storage_path: str) -> Optional[dict]:
        """Carrega o payload completo de uma execução pelo storage_path."""
        storage = get_audit_storage()
        return await storage.load(storage_path)


# Instância singleton
_audit_writer: Optional[AuditWriter] = None


def get_audit_writer() -> AuditWriter:
    global _audit_writer
    if _audit_writer is None:
        _audit_writer = AuditWriter()
    return _audit_writer
