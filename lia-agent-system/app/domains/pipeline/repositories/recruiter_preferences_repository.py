"""RecruiterPreferencesRepository — ADR-001 canonical.

Queries de leitura/escrita de preferências aprendidas do recrutador.
Migrado de pipeline_tool_registry.py: _wrap_get_recruiter_preferences,
_wrap_save_recruiter_preference.
Multi-tenancy: a tabela recruiter_preferences não tem company_id (scoped por
recruiter_id que pertence a um tenant). _require_company_id garante que o
caller passou company_id (defesa em profundidade), mas a query usa recruiter_id
como discriminador primário (design da tabela existente).

Schema source of truth: app/domains/pipeline/models/recruiter_preferences.py
Tabela: recruiter_preferences — colunas: id, recruiter_id, preference_key,
preference_value, frequency, context (JSON), last_used, created_at.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class RecruiterPreferencesRepository:
    """Repository canonical com multi-tenancy fail-closed."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    @staticmethod
    def _require_company_id(company_id: str) -> None:
        if not company_id:
            raise ValueError("company_id is required — multi-tenancy fail-closed")

    async def get_preferences(
        self,
        recruiter_id: str,
        company_id: str,
        action_behavior: str = "",
        limit: int = 10,
    ) -> list[dict]:
        """Busca preferências do recrutador filtradas por contexto. Fail-closed.

        Args:
            recruiter_id: UUID do recrutador.
            company_id: UUID do tenant (fail-closed guard).
            action_behavior: filtro por contexto de ação (opcional).
            limit: máximo de registros.
        """
        self._require_company_id(company_id)
        result = await self.db.execute(
            text("""
                SELECT preference_key, preference_value, frequency, context, last_used
                FROM recruiter_preferences
                WHERE recruiter_id = :rid
                  AND (context->>'action_behavior' = :behavior OR context->>'action_behavior' IS NULL)
                ORDER BY frequency DESC, last_used DESC
                LIMIT :limit
            """),
            {"rid": recruiter_id, "behavior": action_behavior, "limit": limit},
        )
        rows = result.mappings().all()
        prefs = []
        for row in rows:
            p = dict(row)
            for k, v in p.items():
                if isinstance(v, datetime):
                    p[k] = v.isoformat()
            prefs.append(p)
        return prefs

    async def upsert_preference(
        self,
        recruiter_id: str,
        company_id: str,
        preference_key: str,
        preference_value: str,
        context: Optional[dict] = None,
    ) -> bool:
        """Cria ou atualiza uma preferência do recrutador. Fail-closed.

        Returns True on success, raises on DB error (REGRA 4 — fail-loud).
        """
        self._require_company_id(company_id)
        if context is None:
            context = {}

        existing = await self.db.execute(
            text("""
                SELECT id, frequency FROM recruiter_preferences
                WHERE recruiter_id = :rid AND preference_key = :pkey
                LIMIT 1
            """),
            {"rid": recruiter_id, "pkey": preference_key},
        )
        row = existing.mappings().first()

        ctx_json = json.dumps(context) if isinstance(context, dict) else context

        if row:
            await self.db.execute(
                text("""
                    UPDATE recruiter_preferences
                    SET preference_value = :pval,
                        frequency = :freq,
                        last_used = NOW(),
                        context = :ctx
                    WHERE id = :pid
                """),
                {
                    "pval": preference_value,
                    "freq": (row["frequency"] or 0) + 1,
                    "ctx": ctx_json,
                    "pid": str(row["id"]),
                },
            )
        else:
            await self.db.execute(
                # RLS-EXEMPT: recruiter_preferences — user-scoped via user_id (recruiter_profiles join)
                text("""
                    INSERT INTO recruiter_preferences
                        (recruiter_id, preference_key, preference_value, frequency, context, last_used)
                    VALUES (:rid, :pkey, :pval, 1, :ctx, NOW())
                """),
                {
                    "rid": recruiter_id,
                    "pkey": preference_key,
                    "pval": preference_value,
                    "ctx": ctx_json,
                },
            )

        await self.db.commit()
        return True
