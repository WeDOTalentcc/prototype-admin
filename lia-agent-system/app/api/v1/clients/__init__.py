"""
clients package — re-exports a single combined APIRouter.
"""
from fastapi import APIRouter

from .clients_crud import router as crud_router
from .clients_integrations import router as integrations_router
from .clients_automations import router as automations_router
from .clients_hubspot import router as hubspot_router
from .clients_setup import router as setup_router
from .clients_dashboard import router as dashboard_router

router = APIRouter()
router.include_router(dashboard_router)
router.include_router(crud_router)
router.include_router(integrations_router)
router.include_router(automations_router)
router.include_router(hubspot_router)
router.include_router(setup_router)

__all__ = ["router"]
