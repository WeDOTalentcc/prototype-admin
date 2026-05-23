"""LearningSignalRepository — persistence canonical para CorrectionCaptureService.

W3-021 (2026-05-23) do MASTER_PLAN.md.

Tabela `learning_signals` (migration 184) armazena corrections capturadas
durante interação LIA → recrutador. Fanout para FewShotEvolutionService:
- `consumed_for_fewshot=false` (default) — signal disponível pra processamento
- `consumed_for_fewshot=true` — já virou candidate em `few_shot_candidates`
  ou descartado por low quality

Multi-tenancy fail-closed via `_require_company_id` em todo método público
(ADR-001 Repository Pattern).
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class LearningSignalRepository:
    """Repository canonical para learning_signals table."""

    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def _require_company_id(company_id: Any) -> str:
        if not company_id:
            raise ValueError(
                "company_id is required for fail-closed multi-tenancy "
                "(W3-021 LearningSignalRepository)"
            )
        return str(company_id)

    async def insert(
        self,
        *,
        company_id: str,
        user_id: str,
        conversation_id: str | None,
        domain: str | None,
        original_response: str,
        corrected_response: str,
        feedback_type: str,
        confidence_at_generation: float | None = None,
        metadata: dict | None = None,
    ) -> UUID:
        """Persist um learning signal. Returns the inserted id.

        Args:
            company_id: tenant uuid (mandatory).
            user_id: user uuid quem fez correction.
            conversation_id: LIA session uuid (opcional).
            domain: agent domain (automation, cv_screening, etc) — usado pelo
                evolution service para fanout pro YAML correto.
            original_response: resposta IA antes do correction.
            corrected_response: resposta humano sugeriu.
            feedback_type: "correction" | "thumbs_down" | "explicit_correction".
            confidence_at_generation: score IA no momento da generation.
            metadata: extensible (intent, model_used, etc).

        Returns:
            UUID do row inserido.
        """
        company_id = self._require_company_id(company_id)
        if not user_id:
            raise ValueError("user_id is required (LGPD audit trail)")
        if not original_response or not corrected_response:
            raise ValueError("original_response and corrected_response required")

        result = await self.db.execute(
            text(
                "INSERT INTO learning_signals "
                "(company_id, user_id, conversation_id, domain, "
                "original_response, corrected_response, feedback_type, "
                "confidence_at_generation, signal_metadata, "
                "consumed_for_fewshot, created_at) "
                "VALUES (:cid, :uid, :conv, :dom, :orig, :corr, :ftype, "
                ":conf, CAST(:meta AS jsonb), false, :ts) "
                "RETURNING id"
            ),
            {
                "cid": company_id,
                "uid": user_id,
                "conv": conversation_id,
                "dom": domain,
                "orig": original_response,
                "corr": corrected_response,
                "ftype": feedback_type,
                "conf": confidence_at_generation,
                "meta": (
                    __import__("json").dumps(metadata)
                    if metadata is not None
                    else None
                ),
                "ts": datetime.now(timezone.utc),
            },
        )
        await self.db.commit()
        row = result.first()
        signal_id = row[0]
        logger.info(
            "[LearningSignalRepository] inserted signal id=%s company=%s domain=%s type=%s",
            signal_id, company_id, domain, feedback_type,
        )
        return signal_id

    async def list_unconsumed_by_domain(
        self,
        *,
        domain: str,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Lista signals ainda não consumidos por domain (cross-tenant analytics).

        Usado pelo FewShotEvolutionService daily job.
        Cross-tenant intencional (analytics agregada) — NÃO requer company_id.
        """
        result = await self.db.execute(
            text(
                "SELECT id, company_id, user_id, conversation_id, domain, "
                "original_response, corrected_response, feedback_type, "
                "confidence_at_generation, signal_metadata, created_at "
                "FROM learning_signals "
                "WHERE domain = :dom AND consumed_for_fewshot = false "
                "ORDER BY created_at ASC "
                "LIMIT :lim"
            ),
            {"dom": domain, "lim": limit},
        )
        rows = result.fetchall()
        return [
            {
                "id": row[0],
                "company_id": row[1],
                "user_id": row[2],
                "conversation_id": row[3],
                "domain": row[4],
                "original_response": row[5],
                "corrected_response": row[6],
                "feedback_type": row[7],
                "confidence_at_generation": row[8],
                "metadata": row[9],
                "created_at": row[10],
            }
            for row in rows
        ]

    async def mark_consumed(self, signal_id: UUID) -> None:
        """Mark signal como consumido — não vai mais aparecer em list_unconsumed."""
        await self.db.execute(
            text(
                "UPDATE learning_signals SET consumed_for_fewshot = true, "
                "consumed_at = :ts WHERE id = :id"
            ),
            {"id": str(signal_id), "ts": datetime.now(timezone.utc)},
        )
        await self.db.commit()

    async def count_by_company_and_domain(
        self, *, company_id: str, domain: str | None = None
    ) -> int:
        """Conta signals per-tenant (analytics tenant-scoped)."""
        company_id = self._require_company_id(company_id)
        if domain:
            result = await self.db.execute(
                text(
                    "SELECT COUNT(*) FROM learning_signals "
                    "WHERE company_id = :cid AND domain = :dom"
                ),
                {"cid": company_id, "dom": domain},
            )
        else:
            result = await self.db.execute(
                text(
                    "SELECT COUNT(*) FROM learning_signals WHERE company_id = :cid"
                ),
                {"cid": company_id},
            )
        return int(result.scalar() or 0)
