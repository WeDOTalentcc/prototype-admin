"""SuggestionClickRepository — P1-3 Fase 2 + Fase 3 foundation.

ADR-001 compliant: services NÃO fazem SQL inline; tudo via repo canonical.
Multi-tenancy fail-closed: company_id obrigatório em todo método.
"""
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.suggestion_click_event import SuggestionClickEvent


class SuggestionClickRepository:
    """Repository pra SuggestionClickEvent — append-only logging + aggregates."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ── P1-3 Fase 2: logging ─────────────────────────────────────────────

    async def record_click(
        self,
        *,
        company_id: str,
        user_id: str,
        suggestion_id: str,
        suggestion_text: str,
        suggestion_source: str,
        page_context: str | None = None,
        chat_mode: str | None = None,
        click_metadata: dict[str, Any] | None = None,
    ) -> SuggestionClickEvent:
        """Append-only insert. NÃO atualiza records existentes.

        Multi-tenancy: company_id obrigatório (caller responsável de extrair
        do JWT via require_company_id).
        """
        event = SuggestionClickEvent(
            company_id=company_id,
            user_id=user_id,
            suggestion_id=suggestion_id,
            suggestion_text=suggestion_text[:500],  # defense-in-depth (DB limit é 500)
            suggestion_source=suggestion_source,
            page_context=page_context,
            chat_mode=chat_mode,
            click_metadata=click_metadata or {},
        )
        self.db.add(event)
        await self.db.commit()
        await self.db.refresh(event)
        return event

    # ── P1-3 Fase 3 foundation: aggregates ───────────────────────────────

    async def get_top_suggestions_for_company(
        self,
        *,
        company_id: str,
        page_context: str | None = None,
        days: int = 7,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Retorna top sugestões mais clicadas pela tenant nas últimas N dias.

        FASE 3 FOUNDATION ONLY — query helper canonical pronto, MAS ainda
        não wired no /lia/suggestions endpoint. Aplicar ranqueamento exige
        ~1 semana de tráfego pra calibrar threshold de cold-start (Bayesian
        smoothing). Quando tráfego acumular, /lia/suggestions vai chamar
        este método pra reordenar cards baseado em popularity.

        Args:
            company_id: tenant UUID (multi-tenancy fail-closed)
            page_context: filtra por contexto de página (None = todas)
            days: janela retroativa (default 7d)
            limit: top N sugestões (default 10)

        Returns:
            [{"suggestion_id", "suggestion_source", "click_count", "last_clicked_at"}]
            ordenado por click_count DESC.
        """
        since = datetime.utcnow() - timedelta(days=days)

        conditions = [
            SuggestionClickEvent.company_id == company_id,
            SuggestionClickEvent.created_at >= since,
        ]
        if page_context:
            conditions.append(SuggestionClickEvent.page_context == page_context)

        stmt = (
            select(
                SuggestionClickEvent.suggestion_id,
                SuggestionClickEvent.suggestion_source,
                func.count(SuggestionClickEvent.id).label("click_count"),
                func.max(SuggestionClickEvent.created_at).label("last_clicked_at"),
            )
            .where(*conditions)
            .group_by(
                SuggestionClickEvent.suggestion_id,
                SuggestionClickEvent.suggestion_source,
            )
            .order_by(desc("click_count"))
            .limit(limit)
        )

        result = await self.db.execute(stmt)
        rows = result.all()

        return [
            {
                "suggestion_id": r.suggestion_id,
                "suggestion_source": r.suggestion_source,
                "click_count": int(r.click_count),
                "last_clicked_at": r.last_clicked_at.isoformat() if r.last_clicked_at else None,
            }
            for r in rows
        ]

    async def count_clicks_for_user(
        self,
        *,
        company_id: str,
        user_id: str,
        days: int = 7,
    ) -> int:
        """Conta total de cliques de um usuário (rate limit + analytics)."""
        since = datetime.utcnow() - timedelta(days=days)
        stmt = (
            select(func.count(SuggestionClickEvent.id))
            .where(
                SuggestionClickEvent.company_id == company_id,
                SuggestionClickEvent.user_id == user_id,
                SuggestionClickEvent.created_at >= since,
            )
        )
        result = await self.db.execute(stmt)
        return int(result.scalar() or 0)
