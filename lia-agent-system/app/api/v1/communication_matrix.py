"""
Communication Matrix API Endpoints.

Provides endpoints for:
- Listing all matrix entries (with module filter)
- Listing available modules
- Getting a specific entry
- Updating entry configuration
- Resetting to platform defaults (seed data)
"""
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user_or_demo
from app.auth.models import User
from app.core.database import get_db
from app.models.communication_matrix import (
    DEFAULT_MATRIX_ENTRIES,
    MODULE_LABELS,
    ChannelType,
    CommunicationMatrixEntry,
    ModuleType,
    RecipientType,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/communication-matrix", tags=["communication-matrix"])


class UpdateMatrixEntryRequest(BaseModel):
    """Request model for updating a matrix entry."""
    channels: list[str] | None = Field(None, description="List of channels to use")
    is_automatic: bool | None = Field(None, description="Whether this is sent automatically")
    template_id: str | None = Field(None, description="Reference to template")
    requires_approval: bool | None = Field(None, description="Whether approval is required")
    is_active: bool | None = Field(None, description="Whether this communication is enabled")


class ResetMatrixRequest(BaseModel):
    """Request model for resetting matrix to defaults."""
    confirm: bool = Field(..., description="Must be true to confirm reset")


@router.get("", summary="List communication matrix entries")
async def list_matrix_entries(
    module: str | None = Query(None, description="Filter by module type"),
    is_active: bool | None = Query(None, description="Filter by active status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
):
    company_id = current_user.company_id
    """
    List all communication matrix entries.
    
    Can be filtered by module and active status.
    Returns entries for the specified company or platform defaults if no company_id.
    """
    try:
        query = select(CommunicationMatrixEntry)
        
        if company_id:
            query = query.where(CommunicationMatrixEntry.company_id == company_id)
        else:
            query = query.where(CommunicationMatrixEntry.company_id.is_(None))
        
        if module:
            query = query.where(CommunicationMatrixEntry.module == module)
        
        if is_active is not None:
            query = query.where(CommunicationMatrixEntry.is_active == is_active)
        
        query = query.order_by(
            CommunicationMatrixEntry.module,
            CommunicationMatrixEntry.display_order
        )
        
        result = await db.execute(query)
        entries = result.scalars().all()
        
        entries_by_module: dict[str, list[dict]] = {}
        for entry in entries:
            entry_dict = entry.to_dict()
            module_key = entry.module
            if module_key not in entries_by_module:
                entries_by_module[module_key] = []
            entries_by_module[module_key].append(entry_dict)
        
        modules_data = []
        for mod_key, mod_entries in entries_by_module.items():
            mod_info = MODULE_LABELS.get(mod_key, {"label": mod_key, "description": "", "icon": "folder"})
            modules_data.append({
                "module": mod_key,
                "label": mod_info["label"],
                "description": mod_info["description"],
                "icon": mod_info["icon"],
                "entries": mod_entries,
                "total_entries": len(mod_entries),
                "active_entries": sum(1 for e in mod_entries if e["is_active"]),
            })
        
        logger.info(f"📋 Listed {len(entries)} matrix entries across {len(modules_data)} modules")
        
        return {
            "success": True,
            "data": {
                "modules": modules_data,
                "total_entries": len(entries),
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error listing matrix entries: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list matrix entries: {str(e)}"
        )


@router.get("/modules", summary="List available modules")
async def list_modules():
    """
    List all available modules with their labels and descriptions.
    """
    try:
        modules = []
        for mod_type in ModuleType:
            mod_info = MODULE_LABELS.get(mod_type.value, {})
            modules.append({
                "id": mod_type.value,
                "label": mod_info.get("label", mod_type.value),
                "description": mod_info.get("description", ""),
                "icon": mod_info.get("icon", "folder"),
            })
        
        return {
            "success": True,
            "data": {
                "modules": modules,
                "recipient_types": [r.value for r in RecipientType],
                "channel_types": [c.value for c in ChannelType],
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error listing modules: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list modules: {str(e)}"
        )


@router.get("/{entry_id}", summary="Get specific matrix entry")
async def get_matrix_entry(
    entry_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
):
    """
    Get a specific communication matrix entry by ID.
    """
    try:
        try:
            uuid_id = UUID(entry_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid entry ID format"
            )
        
        query = select(CommunicationMatrixEntry).where(
            CommunicationMatrixEntry.id == uuid_id
        )
        result = await db.execute(query)
        entry = result.scalar_one_or_none()
        
        if not entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Matrix entry not found"
            )
        
        return {
            "success": True,
            "data": entry.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting matrix entry: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get matrix entry: {str(e)}"
        )


@router.put("/{entry_id}", summary="Update matrix entry")
async def update_matrix_entry(
    entry_id: str,
    data: UpdateMatrixEntryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
):
    """
    Update a communication matrix entry.
    
    Can update:
    - channels: List of communication channels
    - is_automatic: Whether this is sent automatically
    - template_id: Reference to email/message template
    - requires_approval: Whether approval is required
    - is_active: Whether this communication is enabled
    """
    try:
        try:
            uuid_id = UUID(entry_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid entry ID format"
            )
        
        query = select(CommunicationMatrixEntry).where(
            CommunicationMatrixEntry.id == uuid_id
        )
        result = await db.execute(query)
        entry = result.scalar_one_or_none()
        
        if not entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Matrix entry not found"
            )
        
        if data.channels is not None:
            valid_channels = [c.value for c in ChannelType]
            for channel in data.channels:
                if channel not in valid_channels:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid channel: {channel}. Valid channels: {valid_channels}"
                    )
            entry.channels = data.channels
        
        if data.is_automatic is not None:
            entry.is_automatic = data.is_automatic
        
        if data.template_id is not None:
            entry.template_id = data.template_id if data.template_id else None
        
        if data.requires_approval is not None:
            entry.requires_approval = data.requires_approval
        
        if data.is_active is not None:
            entry.is_active = data.is_active
        
        await db.commit()
        await db.refresh(entry)
        
        logger.info(f"✅ Updated matrix entry: {entry.trigger_name} (ID: {entry.id})")
        
        return {
            "success": True,
            "message": "Entrada da matriz atualizada com sucesso",
            "data": entry.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating matrix entry: {str(e)}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update matrix entry: {str(e)}"
        )


@router.post("/reset", summary="Reset matrix to platform defaults")
async def reset_matrix_to_defaults(
    data: ResetMatrixRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
):
    company_id = current_user.company_id
    """
    Reset the communication matrix to platform defaults.
    
    This will:
    1. Delete all existing entries for the specified company_id (or platform defaults)
    2. Re-create all entries from the default seed data
    
    Requires confirm=true to execute.
    """
    try:
        if not data.confirm:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Confirmation required. Set confirm=true to reset."
            )
        
        if company_id:
            delete_query = delete(CommunicationMatrixEntry).where(
                CommunicationMatrixEntry.company_id == company_id
            )
        else:
            delete_query = delete(CommunicationMatrixEntry).where(
                CommunicationMatrixEntry.company_id.is_(None)
            )
        
        await db.execute(delete_query)
        
        created_count = 0
        for entry_data in DEFAULT_MATRIX_ENTRIES:
            entry = CommunicationMatrixEntry(
                company_id=company_id,
                module=entry_data["module"],
                trigger_name=entry_data["trigger_name"],
                trigger_description=entry_data["trigger_description"],
                recipient_type=entry_data["recipient_type"],
                channels=entry_data["channels"],
                is_automatic=entry_data["is_automatic"],
                template_id=entry_data["template_id"],
                requires_approval=entry_data["requires_approval"],
                is_active=entry_data.get("is_active", True),
                display_order=entry_data["display_order"],
            )
            db.add(entry)
            created_count += 1
        
        await db.commit()
        
        logger.info(f"🔄 Reset matrix: deleted and recreated {created_count} entries for company_id={company_id}")
        
        return {
            "success": True,
            "message": f"Matriz de comunicação resetada com sucesso. {created_count} entradas criadas.",
            "data": {
                "entries_created": created_count,
                "company_id": company_id,
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error resetting matrix: {str(e)}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset matrix: {str(e)}"
        )


@router.post("/seed", summary="Seed default matrix entries (if empty)")
async def seed_matrix_entries(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
):
    company_id = current_user.company_id
    """
    Seed the communication matrix with default entries if it's empty.
    
    Unlike reset, this will only add entries if none exist.
    """
    try:
        if company_id:
            count_query = select(CommunicationMatrixEntry).where(
                CommunicationMatrixEntry.company_id == company_id
            )
        else:
            count_query = select(CommunicationMatrixEntry).where(
                CommunicationMatrixEntry.company_id.is_(None)
            )
        
        result = await db.execute(count_query)
        existing_entries = result.scalars().all()
        
        if len(existing_entries) > 0:
            return {
                "success": True,
                "message": f"Matriz já possui {len(existing_entries)} entradas. Use /reset para recriá-las.",
                "data": {
                    "entries_existing": len(existing_entries),
                    "entries_created": 0,
                }
            }
        
        created_count = 0
        for entry_data in DEFAULT_MATRIX_ENTRIES:
            entry = CommunicationMatrixEntry(
                company_id=company_id,
                module=entry_data["module"],
                trigger_name=entry_data["trigger_name"],
                trigger_description=entry_data["trigger_description"],
                recipient_type=entry_data["recipient_type"],
                channels=entry_data["channels"],
                is_automatic=entry_data["is_automatic"],
                template_id=entry_data["template_id"],
                requires_approval=entry_data["requires_approval"],
                is_active=entry_data.get("is_active", True),
                display_order=entry_data["display_order"],
            )
            db.add(entry)
            created_count += 1
        
        await db.commit()
        
        logger.info(f"🌱 Seeded matrix with {created_count} entries for company_id={company_id}")
        
        return {
            "success": True,
            "message": f"Matriz de comunicação populada com sucesso. {created_count} entradas criadas.",
            "data": {
                "entries_created": created_count,
                "company_id": company_id,
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error seeding matrix: {str(e)}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to seed matrix: {str(e)}"
        )


@router.post("/copy-to-company", summary="Copy platform defaults to a company")
async def copy_defaults_to_company(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo)
):
    company_id = current_user.company_id
    """
    Copy platform default matrix entries to a specific company.
    
    This allows companies to have their own customizable copy of the communication matrix.
    """
    try:
        check_query = select(CommunicationMatrixEntry).where(
            CommunicationMatrixEntry.company_id == company_id
        )
        result = await db.execute(check_query)
        existing = result.scalars().all()
        
        if len(existing) > 0:
            return {
                "success": False,
                "message": f"Empresa já possui {len(existing)} entradas. Use /reset para recriá-las.",
                "data": {
                    "entries_existing": len(existing),
                }
            }
        
        created_count = 0
        for entry_data in DEFAULT_MATRIX_ENTRIES:
            entry = CommunicationMatrixEntry(
                company_id=company_id,
                module=entry_data["module"],
                trigger_name=entry_data["trigger_name"],
                trigger_description=entry_data["trigger_description"],
                recipient_type=entry_data["recipient_type"],
                channels=entry_data["channels"],
                is_automatic=entry_data["is_automatic"],
                template_id=entry_data["template_id"],
                requires_approval=entry_data["requires_approval"],
                is_active=entry_data.get("is_active", True),
                display_order=entry_data["display_order"],
            )
            db.add(entry)
            created_count += 1
        
        await db.commit()
        
        logger.info(f"📋 Copied {created_count} default entries to company {company_id}")
        
        return {
            "success": True,
            "message": f"Matriz copiada com sucesso para a empresa. {created_count} entradas criadas.",
            "data": {
                "entries_created": created_count,
                "company_id": company_id,
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error copying matrix to company: {str(e)}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to copy matrix to company: {str(e)}"
        )
