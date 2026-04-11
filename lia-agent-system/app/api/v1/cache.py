"""
Cache management endpoints for manual cache invalidation.

Provides endpoints for administrators to manually invalidate cached data
when needed for testing, debugging, or emergency cache clearing.
"""
import logging

from fastapi import APIRouter, HTTPException

from app.domains.job_management.services.jd_template_cache_service import jd_template_cache_service
from app.shared.services.embedding_cache_service import embedding_cache

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cache", tags=["cache"])


@router.delete("/jd/{company_id}", response_model=None)
async def invalidate_jd_cache(company_id: str):
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
    except Exception as e:
        logger.error(f"[CACHE INVALIDATION] Error invalidating JD cache for company={company_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error invalidating JD cache: {str(e)}"
        )


@router.get("/jd/metrics", response_model=None)
async def get_jd_cache_metrics():
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
    except Exception as e:
        logger.error(f"[CACHE METRICS] Error retrieving metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving cache metrics: {str(e)}"
        )


@router.post("/jd/reset-metrics", response_model=None)
async def reset_jd_cache_metrics():
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
    except Exception as e:
        logger.error(f"[CACHE METRICS] Error resetting metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error resetting cache metrics: {str(e)}"
        )


@router.get("/embeddings/stats", response_model=None)
async def get_embedding_cache_stats():
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
    except Exception as e:
        logger.error(f"[EMBEDDING CACHE] Error retrieving stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving embedding cache stats: {str(e)}"
        )


@router.post("/embeddings/clear", response_model=None)
async def clear_embedding_cache():
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
    except Exception as e:
        logger.error(f"[EMBEDDING CACHE] Error clearing cache: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error clearing embedding cache: {str(e)}"
        )
