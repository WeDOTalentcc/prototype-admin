"""WebhookRepository — DB access for Webhook and WebhookLog records.

Extracted from app/domains/communication/services/webhook_service.py per ADR-001.
All queries scoped by company_id (multi-tenancy invariant).

P1-W3-04 (2026-05-24): secret field em plaintext (WT-2022 TODO migrado aqui).
Adicionados create_webhook() e get_with_decrypted_secret() que fazem
encrypt/decrypt via app.shared.encryption canonical (Fernet, FIELD_ENCRYPTION_KEY).
ATENÇÃO: dados existentes no DB estão em plaintext — para decriptá-los, checar
se ciphertext decodifica; fallback para safe_decrypt_value() retorna None (não
expõe dado errado). Migration de backfill deve ser criada em sprint separada
(alembic/versions/<n>_backfill_webhook_secret_encrypted.py).
"""
from __future__ import annotations

import logging

from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.webhook import Webhook, WebhookLog

logger = logging.getLogger(__name__)


class WebhookRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id_and_company(
        self,
        *,
        webhook_id: str,
        company_id: str,
    ) -> Webhook | None:
        if not company_id:
            raise ValueError("company_id is required (multi-tenancy invariant)")
        result = await self.db.execute(
            select(Webhook).where(
                and_(
                    Webhook.id == webhook_id,
                    Webhook.company_id == company_id,
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_for_company(
        self,
        *,
        company_id: str,
        is_active: bool | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Webhook]:
        if not company_id:
            raise ValueError("company_id is required (multi-tenancy invariant)")
        conditions = [Webhook.company_id == company_id]
        if is_active is not None:
            conditions.append(Webhook.is_active == is_active)
        # TENANT-EXEMPT: dynamic builder — conditions seeded with
        # Webhook.company_id == company_id above. Sensor cannot trace company_id
        # through and_(*conditions) spread.
        result = await self.db.execute(
            select(Webhook)
            .where(and_(*conditions))
            .order_by(desc(Webhook.created_at))
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars())

    async def list_active_for_company(
        self,
        *,
        company_id: str,
    ) -> list[Webhook]:
        if not company_id:
            raise ValueError("company_id is required (multi-tenancy invariant)")
        result = await self.db.execute(
            select(Webhook).where(
                and_(
                    Webhook.company_id == company_id,
                    Webhook.is_active,
                )
            )
        )
        return list(result.scalars())

    async def create_webhook(
        self,
        *,
        company_id: str,
        name: str,
        url: str,
        events: list[str],
        secret: str,
        created_by: str,
        is_active: bool = True,
    ) -> Webhook:
        """Create a new Webhook with Fernet-encrypted secret (P1-W3-04).

        ALWAYS use this method instead of creating Webhook() directly so the
        secret is encrypted at rest. The plaintext secret is never stored.

        Args:
            secret: Plaintext HMAC secret (auto-generated upstream via
                ``secrets.token_urlsafe(32)``). Encrypted via
                ``app.shared.encryption.encrypt_value`` before INSERT.

        Returns:
            Persisted Webhook ORM row. ``.secret`` field contains ciphertext.
            Use ``get_with_decrypted_secret()`` to obtain plaintext for signing.
        """
        if not company_id:
            raise ValueError("company_id is required (multi-tenancy invariant)")
        from app.shared.encryption import encrypt_value

        encrypted_secret = encrypt_value(secret)
        webhook = Webhook(
            company_id=company_id,
            name=name,
            url=url,
            events=events,
            secret=encrypted_secret,  # Fernet ciphertext at rest
            created_by=created_by,
            is_active=is_active,
        )
        self.db.add(webhook)
        await self.db.commit()
        await self.db.refresh(webhook)
        return webhook

    async def get_with_decrypted_secret(
        self,
        *,
        webhook_id: str,
        company_id: str,
    ) -> tuple[Webhook, str | None]:
        """Return (webhook, decrypted_secret) for HMAC signing (P1-W3-04).

        Handles legacy rows where ``secret`` is still plaintext by using
        ``safe_decrypt_value()`` — returns None if decryption fails (caller
        must treat None as "no secret configured").

        NOTE: After backfill migration is complete, replace safe_decrypt_value
        with decrypt_value (fail-loud) since all rows will be encrypted.
        """
        if not company_id:
            raise ValueError("company_id is required (multi-tenancy invariant)")
        from app.shared.encryption import safe_decrypt_value

        webhook = await self.get_by_id_and_company(
            webhook_id=webhook_id,
            company_id=company_id,
        )
        if webhook is None:
            return webhook, None
        decrypted = safe_decrypt_value(webhook.secret)
        if decrypted is None:
            # Legacy row: safe_decrypt_value returned None (plaintext or corrupt).
            # Log so observability picks up drift; do NOT expose the raw ciphertext.
            logger.warning(
                "[WebhookRepository] P1-W3-04: falha ao decriptar secret webhook_id=%s "
                "— row pode ser legacy plaintext. Execute backfill migration.",
                webhook_id,
            )
        return webhook, decrypted

    async def list_logs_for_webhook(
        self,
        *,
        webhook_id: str,
        company_id: str,
        status_filter: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[WebhookLog]:
        if not company_id:
            raise ValueError("company_id is required (multi-tenancy invariant)")
        conditions = [
            WebhookLog.webhook_id == webhook_id,
            WebhookLog.company_id == company_id,
        ]
        if status_filter:
            conditions.append(WebhookLog.status == status_filter)
        # TENANT-EXEMPT: dynamic builder — conditions seeded with
        # WebhookLog.company_id == company_id above. Sensor cannot trace
        # company_id through and_(*conditions) spread.
        result = await self.db.execute(
            select(WebhookLog)
            .where(and_(*conditions))
            .order_by(desc(WebhookLog.triggered_at))
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars())
