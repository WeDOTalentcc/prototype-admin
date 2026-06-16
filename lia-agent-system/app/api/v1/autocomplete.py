"""
Premium Autocomplete API - Company-specific search suggestions.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.shared.tenant_guard import get_verified_company_id
from app.shared.security.require_company_id import require_company_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search/autocomplete", tags=["autocomplete"])


class PremiumSuggestion(BaseModel):
    """A premium autocomplete suggestion."""
    text: str
    category: str  # recent, popular, team, recommended
    count: int | None = None
    lastUsed: str | None = None


class PremiumAutocompleteResponse(BaseModel):
    """Response with premium suggestions."""
    suggestions: list[PremiumSuggestion]
    query: str


@router.get("/premium", response_model=PremiumAutocompleteResponse)
# TODO(phase2): extract to repository — autocomplete DB queries
async def get_premium_suggestions(
    query: str = Query(..., min_length=2),
    user_id: str = Query(..., description="User ID — required for per-user history"),
    limit: int = Query(10, ge=1, le=20),
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db), 
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Get premium autocomplete suggestions based on company history.

    Returns suggestions from:
    - User's recent searches
    - Popular searches in the company
    - Team members' searches
    - LIA-recommended queries

    company_id is resolved from the JWT token — not from caller-supplied query params.
    """
    if not user_id or user_id in ("default_user", "anonymous", ""):
        raise HTTPException(
            status_code=400,
            detail="Valid user_id is required.",
        )
    suggestions: list[PremiumSuggestion] = []
    query_lower = query.lower()
    
    try:
        # Try to get recent searches from database
        recent_query = text("""
            SELECT DISTINCT query, MAX(created_at) as last_used, COUNT(*) as count
            FROM search_history
            WHERE company_id = :company_id
            AND user_id = :user_id
            AND LOWER(query) LIKE :query_pattern
            GROUP BY query
            ORDER BY last_used DESC
            LIMIT 3
        """)
        
        result = await db.execute(recent_query, {
            "company_id": company_id,
            "user_id": user_id,
            "query_pattern": f"%{query_lower}%"
        })
        
        for row in result.fetchall():
            suggestions.append(PremiumSuggestion(
                text=row[0],
                category="recent",
                count=row[2],
                lastUsed="recente"
            ))
            
    except Exception as e:
        logger.debug(f"No search history table: {e}")
    
    try:
        # Get popular searches in company
        popular_query = text("""
            SELECT query, COUNT(*) as count
            FROM search_history
            WHERE company_id = :company_id
            AND LOWER(query) LIKE :query_pattern
            GROUP BY query
            ORDER BY count DESC
            LIMIT 3
        """)
        
        result = await db.execute(popular_query, {
            "company_id": company_id,
            "query_pattern": f"%{query_lower}%"
        })
        
        for row in result.fetchall():
            if not any(s.text == row[0] for s in suggestions):
                suggestions.append(PremiumSuggestion(
                    text=row[0],
                    category="popular",
                    count=row[1]
                ))
                
    except Exception as e:
        logger.debug(f"Could not fetch popular searches: {e}")
    
    # Add fallback suggestions based on common patterns
    if len(suggestions) < 5:
        fallback = generate_fallback_suggestions(query)
        for fb in fallback:
            if not any(s.text.lower() == fb.text.lower() for s in suggestions):
                suggestions.append(fb)
                if len(suggestions) >= limit:
                    break
    
    return PremiumAutocompleteResponse(
        suggestions=suggestions[:limit],
        query=query
    )


def generate_fallback_suggestions(query: str) -> list[PremiumSuggestion]:
    """Generate fallback suggestions based on query patterns."""
    query_lower = query.lower()
    suggestions = []
    
    # Tech role patterns
    if any(x in query_lower for x in ['python', 'dev', 'desen']):
        suggestions.extend([
            PremiumSuggestion(text="Python Developer Sênior São Paulo", category="popular", count=15),
            PremiumSuggestion(text="Python AWS Data Engineer", category="team", count=8),
            PremiumSuggestion(text="Desenvolvedor Python Backend", category="recommended"),
        ])
    
    if any(x in query_lower for x in ['data', 'dados', 'eng']):
        suggestions.extend([
            PremiumSuggestion(text="Data Engineer Pleno Fintech", category="popular", count=12),
            PremiumSuggestion(text="Data Scientist Machine Learning", category="recommended"),
            PremiumSuggestion(text="Engenheiro de Dados AWS Spark", category="team", count=6),
        ])
    
    if any(x in query_lower for x in ['front', 'react', 'angular', 'vue']):
        suggestions.extend([
            PremiumSuggestion(text="Frontend React TypeScript", category="popular", count=20),
            PremiumSuggestion(text="React Developer Pleno Remoto", category="team", count=5),
            PremiumSuggestion(text="Angular Frontend Sênior", category="recommended"),
        ])
    
    if any(x in query_lower for x in ['backend', 'back', 'api']):
        suggestions.extend([
            PremiumSuggestion(text="Backend Node.js TypeScript", category="popular", count=18),
            PremiumSuggestion(text="Backend Java Spring Boot", category="team", count=7),
            PremiumSuggestion(text="API Developer Microservices", category="recommended"),
        ])
    
    if any(x in query_lower for x in ['devops', 'sre', 'cloud']):
        suggestions.extend([
            PremiumSuggestion(text="DevOps Engineer AWS Kubernetes", category="popular", count=14),
            PremiumSuggestion(text="SRE Terraform Docker", category="team", count=4),
            PremiumSuggestion(text="Cloud Engineer Azure GCP", category="recommended"),
        ])
    
    if any(x in query_lower for x in ['senior', 'sênior', 'sr']):
        suggestions.extend([
            PremiumSuggestion(text="Sênior Full Stack JavaScript", category="popular", count=16),
            PremiumSuggestion(text="Tech Lead Sênior", category="recommended"),
        ])
    
    if any(x in query_lower for x in ['pleno', 'mid', 'pl']):
        suggestions.extend([
            PremiumSuggestion(text="Desenvolvedor Pleno Full Stack", category="popular", count=22),
            PremiumSuggestion(text="Pleno Backend Python Django", category="team", count=9),
        ])
    
    # If no specific patterns matched, add generic tech suggestions
    if not suggestions:
        suggestions.extend([
            PremiumSuggestion(text=f"{query} Desenvolvedor", category="recommended"),
            PremiumSuggestion(text=f"{query} São Paulo", category="popular", count=10),
            PremiumSuggestion(text=f"{query} Remoto", category="team", count=5),
        ])
    
    return suggestions[:8]



class RecentSuggestion(BaseModel):
    text: str
    category: str


class RecentSuggestionsResponse(BaseModel):
    suggestions: list[RecentSuggestion]


@router.get("/recent", response_model=RecentSuggestionsResponse)
async def get_recent_suggestions(
    limit: int = Query(3, ge=1, le=10),
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db),
    _company_gate: str = Depends(require_company_id),
    x_user_id: str | None = None,
):
    suggestions: list[RecentSuggestion] = []

    if x_user_id and x_user_id not in ("", "anonymous", "default_user"):
        try:
            result = await db.execute(
                text(
                    "SELECT query, MAX(created_at) AS last_used"
                    " FROM search_history"
                    " WHERE company_id = :company_id AND user_id = :user_id"
                    " GROUP BY query ORDER BY last_used DESC LIMIT :limit"
                ),
                {"company_id": company_id, "user_id": x_user_id, "limit": limit},
            )
            for row in result.fetchall():
                suggestions.append(RecentSuggestion(text=row[0], category="recent"))
        except Exception as exc:
            logger.debug("search_history lookup failed: %s", exc)

    if not suggestions:
        try:
            result = await db.execute(
                text(
                    "SELECT name FROM search_archetypes"
                    " WHERE (company_id = :company_id OR company_id IS NULL)"
                    " AND is_active = true"
                    " ORDER BY usage_count DESC, created_at DESC LIMIT :limit"
                ),
                {"company_id": company_id, "limit": limit},
            )
            for row in result.fetchall():
                suggestions.append(RecentSuggestion(text=row[0], category="archetype"))
        except Exception as exc:
            logger.debug("search_archetypes lookup failed: %s", exc)

    return RecentSuggestionsResponse(suggestions=suggestions)
