"""
clients package — re-exports a single combined APIRouter.

Sub-module routes are appended directly to avoid FastAPI empty-prefix/path conflict.
NOTE: routes.py must register this router with prefix="/api/v1/clients".
"""
from fastapi import APIRouter

from .clients_dashboard import router as dashboard_router
from .clients_crud import router as crud_router
from .clients_integrations import router as integrations_router
from .clients_automations import router as automations_router
from .clients_hubspot import router as hubspot_router
from .clients_setup import router as setup_router

router = APIRouter()

for _sub in (dashboard_router, crud_router, integrations_router, automations_router, hubspot_router, setup_router):
    router.routes.extend(_sub.routes)

__all__ = ["router"]
