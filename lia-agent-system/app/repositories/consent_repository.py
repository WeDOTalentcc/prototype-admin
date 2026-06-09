"""
Repository for Consent domain.

Encapsulates all database access for:
- ConsentVersion
- ConsentEvent
"""
from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.observability import ConsentEvent, ConsentVersion


class ConsentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------ #
    # ConsentVersion                                                       #
    # ------------------------------------------------------------------ #

    async def list_versions(
        self,
        company_uuid: UUID,
        consent_type=None,
        is_current=None,
        limit: int = 50,
        offset: int = 0,
    ):
        conditions = [ConsentVersion.company_id == company_uuid]
        if consent_type is not None:
            conditions.append(ConsentVersion.consent_type == consent_type)
        if is_current is not None:
            conditions.append(ConsentVersion.is_current == is_current)

        # TENANT-EXEMPT: dynamic builder — conditions[0] is ConsentVersion.company_id == company_uuid (L33 above); AST sensor cannot trace dynamic conditions list
        query = (
            select(ConsentVersion)
            .where(and_(*conditions))
            .order_by(desc(ConsentVersion.created_at))
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(query)
        versions = result.scalars().all()

        count_query = select(func.count(ConsentVersion.id)).where(and_(*conditions))
        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0

        return versions, total

    async def get_version(self, version_uuid: UUID, company_uuid: UUID):
        query = select(ConsentVersion).where(
            and_(
                ConsentVersion.id == version_uuid,
                ConsentVersion.company_id == company_uuid,
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_active_version(self, company_uuid: UUID, consent_type: str):
        query = select(ConsentVersion).where(
            and_(
                ConsentVersion.company_id == company_uuid,
                ConsentVersion.consent_type == consent_type,
                ConsentVersion.is_current,
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_current_versions_of_type(
        self, company_uuid: UUID, consent_type: str
    ):
        """Return all current versions for a given type (used before creating a new one)."""
        query = select(ConsentVersion).where(
            and_(
                ConsentVersion.company_id == company_uuid,
                ConsentVersion.consent_type == consent_type,
                ConsentVersion.is_current,
            )
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def create_version(
        self,
        company_uuid: UUID,
        consent_type: str,
        version: str,
        title: str,
        content_html: str,
        content_text: str,
        content_hash: str,
        effective_from: datetime,
        requires_explicit_consent: bool,
        renewal_period_days=None,
    ) -> ConsentVersion:
        obj = ConsentVersion(
            company_id=company_uuid,
            consent_type=consent_type,
            version=version,
            title=title,
            content_html=content_html,
            content_text=content_text,
            hash=content_hash,
            effective_from=effective_from,
            is_current=True,
            requires_explicit_consent=requires_explicit_consent,
            renewal_period_days=renewal_period_days,
        )
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def update_version(self, version_obj: ConsentVersion, data: dict) -> ConsentVersion:
        for key, value in data.items():
            setattr(version_obj, key, value)
        await self.db.commit()
        await self.db.refresh(version_obj)
        return version_obj

    async def get_distinct_consent_types(self, company_uuid: UUID):
        query = (
            select(ConsentVersion.consent_type)
            .where(ConsentVersion.company_id == company_uuid)
            .distinct()
        )
        result = await self.db.execute(query)
        return [row[0] for row in result.fetchall()]

    async def get_version_ids_for_type(self, company_uuid: UUID, consent_type: str):
        query = select(ConsentVersion.id).where(
            and_(
                ConsentVersion.company_id == company_uuid,
                ConsentVersion.consent_type == consent_type,
            )
        )
        result = await self.db.execute(query)
        return [row[0] for row in result.fetchall()]

    async def get_versions_by_ids(
        self,
        version_ids: list,
        company_uuid: UUID | None = None,
    ):
        """Lookup ConsentVersion por lista de ids.

        Sprint B.1 tail (2026-05-22): company_uuid RECOMENDADO (defense-in-depth).
        Quando passado, re-valida no read (version_ids vem de query upstream
        tenant-gated — ainda assim defense-in-depth canonical).
        """
        # TENANT-EXEMPT: defense-in-depth — version_ids ja eh derivado de tenant-gated query; company_uuid opcional pra re-validacao
        if company_uuid is not None:
            query = select(ConsentVersion).where(
                ConsentVersion.id.in_(version_ids),
                ConsentVersion.company_id == company_uuid,
            )
        else:
            # TENANT-EXEMPT: backwards-compat — version_ids ja tenant-gated upstream
            query = select(ConsentVersion).where(ConsentVersion.id.in_(version_ids))
        result = await self.db.execute(query)
        return {v.id: v for v in result.scalars().all()}

    # ------------------------------------------------------------------ #
    # ConsentEvent                                                         #
    # ------------------------------------------------------------------ #

    async def list_events(
        self,
        company_uuid: UUID,
        consent_version_id=None,
        subject_email=None,
        event_type=None,
        date_from=None,
        date_to=None,
        limit: int = 50,
        offset: int = 0,
    ):
        conditions = [ConsentEvent.company_id == company_uuid]
        if consent_version_id is not None:
            conditions.append(ConsentEvent.consent_version_id == consent_version_id)
        if subject_email is not None:
            conditions.append(ConsentEvent.subject_email == subject_email)
        if event_type is not None:
            conditions.append(ConsentEvent.event_type == event_type)
        if date_from is not None:
            conditions.append(ConsentEvent.created_at >= date_from)
        if date_to is not None:
            conditions.append(ConsentEvent.created_at <= date_to)

        # TENANT-EXEMPT: dynamic builder — conditions[0] is ConsentEvent.company_id == company_uuid (L165 above); AST sensor cannot trace dynamic conditions list
        query = (
            select(ConsentEvent)
            .where(and_(*conditions))
            .order_by(desc(ConsentEvent.created_at))
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(query)
        events = result.scalars().all()

        count_query = select(func.count(ConsentEvent.id)).where(and_(*conditions))
        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0

        return events, total

    async def get_subject_events(self, company_uuid: UUID, subject_identifier: str):
        query = (
            select(ConsentEvent)
            .where(
                and_(
                    ConsentEvent.company_id == company_uuid,
                    ConsentEvent.subject_identifier == subject_identifier,
                )
            )
            .order_by(desc(ConsentEvent.created_at))
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_last_granted_event(
        self,
        company_uuid: UUID,
        version_uuid: UUID,
        subject_identifier: str,
    ):
        query = (
            select(ConsentEvent)
            .where(
                and_(
                    ConsentEvent.company_id == company_uuid,
                    ConsentEvent.consent_version_id == version_uuid,
                    ConsentEvent.subject_identifier == subject_identifier,
                    ConsentEvent.event_type == "granted",
                    ConsentEvent.consent_given,
                )
            )
            .order_by(desc(ConsentEvent.created_at))
            .limit(1)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_event(
        self,
        company_uuid: UUID,
        consent_version_id: UUID,
        subject_email: str,
        subject_identifier: str,
        event_type: str,
        consent_given: bool,
        ip_address=None,
        user_agent=None,
        device_info=None,
        channel: str = "",
        proof_hash: str = "",
        expires_at=None,
    ) -> ConsentEvent:
        obj = ConsentEvent(
            company_id=company_uuid,
            consent_version_id=consent_version_id,
            subject_email=subject_email,
            subject_identifier=subject_identifier,
            event_type=event_type,
            consent_given=consent_given,
            ip_address=ip_address,
            user_agent=user_agent,
            device_info=device_info if device_info is not None else {},
            channel=channel,
            proof_hash=proof_hash,
            expires_at=expires_at,
        )
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    # ------------------------------------------------------------------ #
    # Stats aggregations                                                   #
    # ------------------------------------------------------------------ #

    async def count_versions(self, company_uuid: UUID) -> int:
        query = select(func.count(ConsentVersion.id)).where(
            ConsentVersion.company_id == company_uuid
        )
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def count_events(self, company_uuid: UUID) -> int:
        query = select(func.count(ConsentEvent.id)).where(
            ConsentEvent.company_id == company_uuid
        )
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def count_distinct_subjects(self, company_uuid: UUID) -> int:
        query = select(
            func.count(func.distinct(ConsentEvent.subject_identifier))
        ).where(ConsentEvent.company_id == company_uuid)
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def count_granted(self, company_uuid: UUID) -> int:
        query = select(func.count(ConsentEvent.id)).where(
            and_(
                ConsentEvent.company_id == company_uuid,
                ConsentEvent.event_type == "granted",
                ConsentEvent.consent_given,
            )
        )
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def count_revoked(self, company_uuid: UUID) -> int:
        query = select(func.count(ConsentEvent.id)).where(
            and_(
                ConsentEvent.company_id == company_uuid,
                ConsentEvent.event_type == "revoked",
            )
        )
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def count_expired(self, company_uuid: UUID, now: datetime) -> int:
        query = select(func.count(ConsentEvent.id)).where(
            and_(
                ConsentEvent.company_id == company_uuid,
                ConsentEvent.event_type == "granted",
                ConsentEvent.expires_at.isnot(None),
                ConsentEvent.expires_at < now,
            )
        )
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def count_granted_for_versions(self, version_ids: list) -> int:
        query = select(func.count(ConsentEvent.id)).where(
            and_(
                ConsentEvent.consent_version_id.in_(version_ids),
                ConsentEvent.event_type == "granted",
                ConsentEvent.consent_given,
            )
        )
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def count_revoked_for_versions(self, version_ids: list) -> int:
        query = select(func.count(ConsentEvent.id)).where(
            and_(
                ConsentEvent.consent_version_id.in_(version_ids),
                ConsentEvent.event_type == "revoked",
            )
        )
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def count_expired_for_versions(self, version_ids: list, now: datetime) -> int:
        query = select(func.count(ConsentEvent.id)).where(
            and_(
                ConsentEvent.consent_version_id.in_(version_ids),
                ConsentEvent.event_type == "granted",
                ConsentEvent.expires_at.isnot(None),
                ConsentEvent.expires_at < now,
            )
        )
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def get_events_by_channel(self, company_uuid: UUID):
        query = (
            select(ConsentEvent.channel, func.count(ConsentEvent.id))
            .where(ConsentEvent.company_id == company_uuid)
            .group_by(ConsentEvent.channel)
        )
        result = await self.db.execute(query)
        return {row[0]: row[1] for row in result.fetchall()}

    async def rollback(self):
        await self.db.rollback()
