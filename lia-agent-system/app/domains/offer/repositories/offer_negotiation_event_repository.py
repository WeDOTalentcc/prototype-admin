"""OfferNegotiationEventRepository — ADR-001 canonical.

Toda query via repositório — sem SQL inline em services.
`_require_company_id` em todo método público (multi-tenancy fail-closed).

Aprendizado LGPD: MIN_SAMPLES = 10 gate (ADR-LGPD-001 Art. 12 §1).
"""
from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from libs.models.lia_models.offer_negotiation_event import OfferNegotiationEvent

logger = logging.getLogger(__name__)

_MIN_LEARNING_SAMPLES = 10


class OfferNegotiationEventRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    def _require_company_id(self, company_id: str) -> None:
        if not company_id:
            raise ValueError(
                "company_id obrigatório — ADR-001 multi-tenancy. "
                "Nunca chamar OfferNegotiationEventRepository sem company_id."
            )

    async def create(
        self,
        offer_id: UUID,
        company_id: str,
        event_type: str,
        actor: str,
        round_number: int = 0,
        notes: str | None = None,
        salary_proposed: float | None = None,
        salary_counter: float | None = None,
        benefits_snapshot: dict | None = None,
        fairness_snapshot: dict | None = None,
    ) -> OfferNegotiationEvent:
        self._require_company_id(company_id)

        from libs.models.lia_models.offer_negotiation_event import VALID_EVENT_TYPES, VALID_ACTORS
        if event_type not in VALID_EVENT_TYPES:
            raise ValueError(
                f"event_type inválido: {event_type!r}. "
                f"Válidos: {sorted(VALID_EVENT_TYPES)}"
            )
        if actor not in VALID_ACTORS:
            raise ValueError(
                f"actor inválido: {actor!r}. "
                f"Válidos: {sorted(VALID_ACTORS)}"
            )

        event = OfferNegotiationEvent(
            offer_id=offer_id,
            company_id=company_id,
            event_type=event_type,
            actor=actor,
            round_number=round_number,
            notes=notes,
            salary_proposed=salary_proposed,
            salary_counter=salary_counter,
            benefits_snapshot=benefits_snapshot or {},
            fairness_snapshot=fairness_snapshot or {"check": "not_provided"},
        )
        self._db.add(event)
        await self._db.flush()
        logger.debug(
            "[offer_events] created event=%s actor=%s offer_id=%s",
            event_type, actor, offer_id,
        )
        return event

    async def get_by_offer(self, offer_id: UUID) -> list[OfferNegotiationEvent]:
        result = await self._db.execute(
            select(OfferNegotiationEvent)
            .where(OfferNegotiationEvent.offer_id == offer_id)
            .order_by(OfferNegotiationEvent.created_at)
        )
        return list(result.scalars().all())

    async def get_learning_data(self, company_id: str, limit: int = 200) -> list[dict]:
        """Retorna dados anonimizados para learning loop.

        ADR-LGPD-001: agrega sem PII individual. Retorna lista vazia quando
        amostra < MIN_LEARNING_SAMPLES — não expõe dados de poucos candidatos.
        """
        self._require_company_id(company_id)

        result = await self._db.execute(
            select(
                OfferNegotiationEvent.event_type,
                OfferNegotiationEvent.round_number,
                OfferNegotiationEvent.salary_proposed,
                OfferNegotiationEvent.salary_counter,
                OfferNegotiationEvent.created_at,
            )
            .where(OfferNegotiationEvent.company_id == company_id)
            .order_by(OfferNegotiationEvent.created_at.desc())
            .limit(limit)
        )
        rows = [row._asdict() for row in result]

        if len(rows) < _MIN_LEARNING_SAMPLES:
            logger.debug(
                "[offer_events] learning data insuficiente: %d < %d (ADR-LGPD-001)",
                len(rows), _MIN_LEARNING_SAMPLES,
            )
            return []

        return rows
