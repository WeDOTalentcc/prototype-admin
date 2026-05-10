import logging
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.billing import (
    CompanyModule,
    ModuleStatus,
    ModuleTier,
    AVAILABLE_MODULES,
)

from app.domains.modules.repositories.company_module_repository import (
    CompanyModuleRepository,
)

logger = logging.getLogger(__name__)

_EXPLICITLY_OFF = {ModuleStatus.DISABLED.value, ModuleStatus.EXPIRED.value}


class ModuleService:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    async def is_module_active(
        self,
        db: AsyncSession,
        company_id: str,
        module_name: str,
    ) -> bool:
        try:
            repo = CompanyModuleRepository(db)
            mod = await repo.get_by_company_and_name(company_id, module_name)

            if mod:
                if mod.status in _EXPLICITLY_OFF:
                    return False
                return mod.is_accessible

            from app.shared.governance.feature_flag_service import feature_flag_service
            flag_key = f"module_{module_name}_enabled"
            return await feature_flag_service.is_enabled(db, flag_key, company_id)
        except Exception as e:
            # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
            self.logger.error(f"Error checking module {module_name} for {company_id}: {e}")
            return False

    async def get_module_status(
        self,
        db: AsyncSession,
        company_id: str,
        module_name: str,
    ) -> Optional[str]:
        try:
            repo = CompanyModuleRepository(db)
            mod = await repo.get_by_company_and_name(company_id, module_name)
            if not mod:
                return None
            if mod.expires_at and mod.expires_at < datetime.utcnow():
                return ModuleStatus.EXPIRED.value
            return mod.status
        except Exception as e:
            # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
            self.logger.error(f"Error getting module status {module_name} for {company_id}: {e}")
            return None

    async def get_company_modules(
        self,
        db: AsyncSession,
        company_id: str,
        include_catalog: bool = False,
    ) -> list[dict[str, Any]]:
        repo = CompanyModuleRepository(db)
        modules = await repo.list_by_company(company_id)

        module_dict = {m.module_name: m for m in modules}

        items = []
        names = set(module_dict.keys())

        if include_catalog:
            names = names | set(AVAILABLE_MODULES.keys())

        for name in sorted(names):
            if name in module_dict:
                items.append(module_dict[name].to_dict())
            else:
                info = AVAILABLE_MODULES.get(name, {})
                items.append({
                    "id": None,
                    "company_id": company_id,
                    "module_name": name,
                    "label": info.get("label", name),
                    "description": info.get("description", ""),
                    "status": info.get("initial_status", "coming_soon"),
                    "tier": "free",
                    "activated_at": None,
                    "expires_at": None,
                    "metadata": {},
                    "created_at": None,
                    "updated_at": None,
                })

        return items

    async def activate_module(
        self,
        db: AsyncSession,
        company_id: str,
        module_name: str,
        status: str = ModuleStatus.BETA.value,
        tier: str = ModuleTier.FREE.value,
        expires_at: Optional[datetime] = None,
        metadata: Optional[dict] = None,
    ) -> dict[str, Any]:
        if module_name not in AVAILABLE_MODULES:
            return {"success": False, "error": f"Unknown module: {module_name}"}

        repo = CompanyModuleRepository(db)
        existing = await repo.get_by_company_and_name(company_id, module_name)

        if existing:
            existing.status = status
            existing.tier = tier
            existing.activated_at = datetime.utcnow()
            existing.expires_at = expires_at
            if metadata:
                existing.metadata_json = metadata
            mod = existing
        else:
            mod = CompanyModule(
                company_id=company_id,
                module_name=module_name,
                status=status,
                tier=tier,
                expires_at=expires_at,
                metadata_json=metadata or {},
            )
            await repo.add(mod)

        await db.flush()
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        self.logger.info(f"Module {module_name} activated for {company_id} (status={status}, tier={tier})")
        return {"success": True, "module": mod.to_dict()}

    async def update_module(
        self,
        db: AsyncSession,
        company_id: str,
        module_name: str,
        status: Optional[str] = None,
        tier: Optional[str] = None,
        expires_at: Optional[datetime] = None,
    ) -> dict[str, Any]:
        if module_name not in AVAILABLE_MODULES:
            return {"success": False, "error": f"Unknown module: {module_name}"}

        repo = CompanyModuleRepository(db)
        mod = await repo.get_by_company_and_name(company_id, module_name)

        if not mod:
            return {"success": False, "error": f"Module {module_name} not found for company {company_id}"}

        if status is not None:
            mod.status = status
        if tier is not None:
            mod.tier = tier
        if expires_at is not None:
            mod.expires_at = expires_at

        await db.flush()
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        self.logger.info(f"Module {module_name} updated for {company_id}")
        return {"success": True, "module": mod.to_dict()}

    async def deactivate_module(
        self,
        db: AsyncSession,
        company_id: str,
        module_name: str,
    ) -> dict[str, Any]:
        repo = CompanyModuleRepository(db)
        mod = await repo.get_by_company_and_name(company_id, module_name)

        if not mod:
            return {"success": False, "error": "Module not found for this company"}

        mod.status = ModuleStatus.DISABLED.value
        await db.flush()
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        self.logger.info(f"Module {module_name} deactivated for {company_id}")
        return {"success": True, "module": mod.to_dict()}

    async def get_module_tier(
        self,
        db: AsyncSession,
        company_id: str,
        module_name: str,
    ) -> Optional[str]:
        repo = CompanyModuleRepository(db)
        mod = await repo.get_by_company_and_name(company_id, module_name)
        return mod.tier if mod else None

    async def get_module_by_id(
        self,
        db: AsyncSession,
        module_id: str,
    ) -> Optional[CompanyModule]:
        repo = CompanyModuleRepository(db)
        return await repo.get_by_id(module_id)

    async def update_module_by_id(
        self,
        db: AsyncSession,
        module_id: str,
        status: Optional[str] = None,
        tier: Optional[str] = None,
        expires_at: Optional[datetime] = None,
    ) -> dict[str, Any]:
        mod = await self.get_module_by_id(db, module_id)
        if not mod:
            return {"success": False, "error": f"Module with id {module_id} not found"}

        if status is not None:
            mod.status = status
        if tier is not None:
            mod.tier = tier
        if expires_at is not None:
            mod.expires_at = expires_at

        await db.flush()
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        self.logger.info(f"Module {mod.module_name} (id={module_id}) updated")
        return {"success": True, "module": mod.to_dict()}

    async def get_billing_context(
        self,
        db: AsyncSession,
        company_id: str,
        module_name: str,
    ) -> Optional[dict[str, Any]]:
        from lia_models.billing import CreditAccount
        repo = CompanyModuleRepository(db)
        mod = await repo.get_by_company_and_name(company_id, module_name)
        if not mod:
            return None

        # ADR-001-EXEMPT: cross-domain CreditAccount read; credits domain has no
        # get_account_by_company helper yet (Sprint 6 follow-up to extend CreditsRepository).
        acct_stmt = select(CreditAccount).where(CreditAccount.company_id == company_id)
        acct_result = await db.execute(acct_stmt)
        acct = acct_result.scalar_one_or_none()

        return {
            "module": mod.to_dict(),
            "credit_account": acct.to_dict() if acct else None,
            "is_billable": mod.tier != ModuleTier.FREE.value and mod.status == ModuleStatus.ACTIVE.value,
        }

    async def seed_beta_modules(
        self,
        db: AsyncSession,
        company_id: str,
    ) -> list[dict[str, Any]]:
        created = []
        repo = CompanyModuleRepository(db)
        for name, info in AVAILABLE_MODULES.items():
            initial_status = info.get("initial_status", "beta")
            if await repo.get_by_company_and_name(company_id, name):
                continue

            mod = CompanyModule(
                company_id=company_id,
                module_name=name,
                status=initial_status,
                tier=ModuleTier.FREE.value,
            )
            db.add(mod)
            created.append(name)

        if created:
            await db.flush()
            self.logger.info(f"Seeded {len(created)} modules for {company_id}: {created}")
        return created


module_service = ModuleService()


def get_module_service() -> ModuleService:
    return module_service
