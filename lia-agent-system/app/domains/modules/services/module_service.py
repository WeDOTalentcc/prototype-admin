import json
import logging
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.billing import (
    CompanyModule,
    ModuleStatus,
    ModuleTier,
    AVAILABLE_MODULES,
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
            stmt = select(CompanyModule).where(
                and_(
                    CompanyModule.company_id == company_id,
                    CompanyModule.module_name == module_name,
                )
            )
            result = await db.execute(stmt)
            mod = result.scalar_one_or_none()

            if mod:
                if mod.status in _EXPLICITLY_OFF:
                    return False
                return mod.is_accessible

            from app.shared.governance.feature_flag_service import feature_flag_service
            flag_key = f"module_{module_name}_enabled"
            return await feature_flag_service.is_enabled(db, flag_key, company_id)
        except Exception as e:
            self.logger.error(f"Error checking module {module_name} for {company_id}: {e}")
            return False

    async def get_module_status(
        self,
        db: AsyncSession,
        company_id: str,
        module_name: str,
    ) -> Optional[str]:
        stmt = select(CompanyModule).where(
            and_(
                CompanyModule.company_id == company_id,
                CompanyModule.module_name == module_name,
            )
        )
        result = await db.execute(stmt)
        mod = result.scalar_one_or_none()
        if not mod:
            return None
        if mod.expires_at and mod.expires_at < datetime.utcnow():
            return ModuleStatus.EXPIRED.value
        return mod.status

    async def get_company_modules(
        self,
        db: AsyncSession,
        company_id: str,
        include_catalog: bool = False,
    ) -> list[dict[str, Any]]:
        stmt = select(CompanyModule).where(CompanyModule.company_id == company_id)
        result = await db.execute(stmt)
        modules = result.scalars().all()

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

        stmt = select(CompanyModule).where(
            and_(
                CompanyModule.company_id == company_id,
                CompanyModule.module_name == module_name,
            )
        )
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            existing.status = status
            existing.tier = tier
            existing.activated_at = datetime.utcnow()
            existing.expires_at = expires_at
            if metadata:
                existing.metadata_json = json.dumps(metadata)
            mod = existing
        else:
            mod = CompanyModule(
                company_id=company_id,
                module_name=module_name,
                status=status,
                tier=tier,
                expires_at=expires_at,
                metadata_json=json.dumps(metadata) if metadata else "{}",
            )
            db.add(mod)

        await db.flush()
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

        stmt = select(CompanyModule).where(
            and_(
                CompanyModule.company_id == company_id,
                CompanyModule.module_name == module_name,
            )
        )
        result = await db.execute(stmt)
        mod = result.scalar_one_or_none()

        if not mod:
            return {"success": False, "error": f"Module {module_name} not found for company {company_id}"}

        if status is not None:
            mod.status = status
        if tier is not None:
            mod.tier = tier
        if expires_at is not None:
            mod.expires_at = expires_at

        await db.flush()
        self.logger.info(f"Module {module_name} updated for {company_id}")
        return {"success": True, "module": mod.to_dict()}

    async def deactivate_module(
        self,
        db: AsyncSession,
        company_id: str,
        module_name: str,
    ) -> dict[str, Any]:
        stmt = select(CompanyModule).where(
            and_(
                CompanyModule.company_id == company_id,
                CompanyModule.module_name == module_name,
            )
        )
        result = await db.execute(stmt)
        mod = result.scalar_one_or_none()

        if not mod:
            return {"success": False, "error": "Module not found for this company"}

        mod.status = ModuleStatus.DISABLED.value
        await db.flush()
        self.logger.info(f"Module {module_name} deactivated for {company_id}")
        return {"success": True, "module": mod.to_dict()}

    async def get_module_tier(
        self,
        db: AsyncSession,
        company_id: str,
        module_name: str,
    ) -> Optional[str]:
        stmt = select(CompanyModule).where(
            and_(
                CompanyModule.company_id == company_id,
                CompanyModule.module_name == module_name,
            )
        )
        result = await db.execute(stmt)
        mod = result.scalar_one_or_none()
        return mod.tier if mod else None

    async def seed_beta_modules(
        self,
        db: AsyncSession,
        company_id: str,
    ) -> list[dict[str, Any]]:
        created = []
        for name, info in AVAILABLE_MODULES.items():
            initial_status = info.get("initial_status", "beta")
            stmt = select(CompanyModule).where(
                and_(
                    CompanyModule.company_id == company_id,
                    CompanyModule.module_name == name,
                )
            )
            result = await db.execute(stmt)
            if result.scalar_one_or_none():
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
