"""
Unified System Health Check for production readiness.
Checks DB connectivity, key subsystems, and returns structured status.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from datetime import datetime
import logging
import os

from app.core.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(tags=["system"])


@router.get("/health")
async def system_health(db: AsyncSession = Depends(get_db)):
    """
    Unified health check for deployment readiness/liveness probes.
    Returns 200 if healthy, 503 if critical components are down.
    """
    components = {}
    overall_healthy = True
    
    try:
        result = await db.execute(text("SELECT 1"))
        result.scalar()
        components["database"] = {"status": "healthy"}
    except Exception as e:
        components["database"] = {"status": "unhealthy", "error": str(e)}
        overall_healthy = False
    
    try:
        from app.middleware.rate_limiter import rate_limiter
        stats = rate_limiter.get_stats()
        components["rate_limiter"] = {"status": "healthy", "tracked_users": stats["tracked_users"]}
    except Exception as e:
        components["rate_limiter"] = {"status": "degraded", "error": str(e)}
    
    try:
        from app.shared.async_processing.enhanced_task_manager import EnhancedTaskManager
        manager = EnhancedTaskManager.get_instance()
        components["task_manager"] = {
            "status": "healthy",
            "persistence_enabled": manager.persistence_enabled
        }
    except Exception:
        components["task_manager"] = {"status": "unavailable"}
    
    try:
        from app.shared.channels.multi_channel_service import MultiChannelService
        svc = MultiChannelService.get_instance()
        available = [ch for ch in svc.get_available_channels() if ch.get("available")]
        components["multi_channel"] = {
            "status": "healthy",
            "available_channels": len(available)
        }
    except Exception:
        components["multi_channel"] = {"status": "unavailable"}
    
    external = {}
    external["anthropic"] = "configured" if os.getenv("ANTHROPIC_API_KEY") else "not_configured"
    external["openai"] = "configured" if os.getenv("OPENAI_API_KEY") else "not_configured"
    external["workos"] = "configured" if os.getenv("WORKOS_API_KEY") else "not_configured"
    components["external_services"] = external
    
    status_code = 200 if overall_healthy else 503
    
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "healthy" if overall_healthy else "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": os.getenv("APP_VERSION", "1.0.0"),
            "environment": os.getenv("APP_ENV", "development"),
            "components": components
        }
    )
