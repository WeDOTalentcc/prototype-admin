"""
Cache management endpoints for manual cache invalidation.

Provides endpoints for administrators to manually invalidate cached data
when needed for testing, debugging, or emergency cache clearing.
"""
import logging

from fastapi import APIRouter, HTTPException

from app.domains.job_management.services.jd_template_cache_service import jd_template_cache_service
from app.shared.services.embedding_cache_service import embedding_cache
from fastapi import Depends
from app.shared.security.require_company_id import require_company_id, require_company_id_strict_match
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, reorder_collection_before_item

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cache", tags=["cache"])


@router.delete("/jd/{company_id}", response_model=None)
async def invalidate_jd_cache(company_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)], _company_gate: str = Depends(require_company_id_strict_match("path.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Manually invalidate JD template cache for a company.
    
    This endpoint clears all cached job description extractions for the specified company.
    Useful for:
    - Testing and debugging
    - Force refreshing cached data
    - Emergency cache clearing
    
    Args:
        company_id: The company identifier
    
    Returns:
        Dictionary with invalidation status and count of cleared entries
    
    Example:
        DELETE /api/v1/cache/jd/comp_123
    """
    if not company_id or not company_id.strip():
        raise HTTPException(status_code=400, detail="Company ID is required")
    
    try:
        count = await jd_template_cache_service.invalidate(company_id)
        
        logger.info(f"[CACHE INVALIDATION] JD cache invalidated for company={company_id}, count={count}")
        
        return {
            "success": True,
            "message": f"JD cache invalidated for company {company_id}",
            "company_id": company_id,
            "entries_cleared": count,
            "cache_service": "jd_template_cache"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[CACHE INVALIDATION] Error invalidating JD cache for company={company_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


@router.get("/jd/metrics", response_model=None)
async def get_jd_cache_metrics(company_id: str = Depends(require_company_id)):
    # multi-tenancy: public endpoint (metrics) — no tenant data
    """
    Get JD template cache performance metrics.
    
    Returns cache statistics including:
    - Hit count
    - Miss count
    - Hit rate percentage
    - Cache size
    - Backend type (Redis or in-memory)
    
    Example:
        GET /api/v1/cache/jd/metrics
    """
    try:
        metrics = jd_template_cache_service.get_metrics()
        
        return {
            "success": True,
            "service": "jd_template_cache",
            "metrics": metrics
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[CACHE METRICS] Error retrieving metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


@router.post("/jd/reset-metrics", response_model=None)
async def reset_jd_cache_metrics(company_id: str = Depends(require_company_id)):
    # multi-tenancy: public endpoint (metrics) — no tenant data
    """
    Reset JD template cache performance metrics.
    
    Resets hit/miss counters to zero. Useful for starting a fresh metrics collection.
    
    Example:
        POST /api/v1/cache/jd/reset-metrics
    """
    try:
        jd_template_cache_service.reset_metrics()
        
        logger.info("[CACHE METRICS] JD cache metrics reset")
        
        return {
            "success": True,
            "message": "JD cache metrics reset",
            "service": "jd_template_cache"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[CACHE METRICS] Error resetting metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


@router.get("/embeddings/stats", response_model=None)
async def get_embedding_cache_stats(company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Get embedding cache statistics.
    
    Returns cache statistics including:
    - Number of cached embeddings
    - Warm-up status
    - Memory usage
    
    Example:
        GET /api/v1/cache/embeddings/stats
    """
    try:
        stats = embedding_cache.get_stats()
        
        return {
            "success": True,
            "service": "embedding_cache",
            "stats": stats
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[EMBEDDING CACHE] Error retrieving stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


@router.post("/embeddings/clear", response_model=None)
async def clear_embedding_cache(company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Clear embedding cache.
    
    Clears all cached embeddings and resets warm-up status.
    
    Example:
        POST /api/v1/cache/embeddings/clear
    """
    try:
        embedding_cache.clear()
        
        logger.info("[EMBEDDING CACHE] Cache cleared")
        
        return {
            "success": True,
            "message": "Embedding cache cleared",
            "service": "embedding_cache"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[EMBEDDING CACHE] Error clearing cache: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )

reorder_collection_before_item(router)
