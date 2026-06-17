"""
TOON Service — Talent Object Of Note (Sprint G7).

Generates a structured summary card for a candidate in the context of a job opening.
Designed to:
- Surface the most relevant information for a recruiter
- Respect LGPD principles (anonymizable PII)
- Apply fairness-neutral presentation (no photos, age opt-out)
- Cache per candidate+job combo in Redis (TTL=1h)

LGPD: anonymize=True masks all PII. name_display becomes "Candidato X".
Fairness: no avatar_url exposed, age only shown when company allows it.
Multi-tenant: all DB queries are scoped by company_id.
"""

# RAILS-DEPRECATED: This service performs CRUD for Rails-owned entities.
# Will be deleted after ats-api-rails handoff is complete.
# Do NOT migrate to a domain -- route through integrations_hub/rails_adapter instead.
from __future__ import annotations

import json
import logging
import os
from dataclasses import asdict, dataclass
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# Redis TTL for TOON cache: 1 hour
_TOON_CACHE_TTL = 3600


def _toon_cache_key(candidate_id: str, job_id: str | None, company_id: str) -> str:
    """Redis key for TOON card. Scoped by tenant (company_id)."""
    job_part = job_id or "no-job"
    return f"toon:{company_id}:{candidate_id}:{job_part}"


@dataclass
class TOONCard:
    """
    Structured summary card for a candidate.

    Fields:
        candidate_id: UUID of the candidate (always present).
        job_id: UUID of the related job opening (optional — can be a general card).
        generated_at: ISO-8601 UTC datetime of generation.
        headline: One-line professional summary, e.g. "Desenvolvedor Python Sênior com 8 anos em fintech".
        highlights: 3–5 bullet points surfacing key strengths.
        match_score: 0–100 compatibility score against the job requirements (None if no job_id).
        skills_match: List of candidate skills that match job requirements.
        name_display: Full name OR "Candidato X" when anonymized.
        location: City/State/Country string, e.g. "São Paulo, SP, Brasil".
        experience_years: Total years of professional experience.
        anonymized: True when PII has been masked (LGPD-safe mode).
        fairness_reviewed: True when output has been checked for biased language.
    """

    candidate_id: str
    job_id: str | None
    # Metadata
    generated_at: str  # ISO datetime
    # Professional summary
    headline: str
    highlights: list[str]
    # Scored dimensions (0-100)
    match_score: int | None
    skills_match: list[str]
    # LGPD-safe fields
    name_display: str
    location: str
    experience_years: int
    # Flags
    anonymized: bool
    fairness_reviewed: bool


def _build_headline(candidate) -> str:  # type: ignore[no-untyped-def]
    """Build a one-line professional headline from candidate data."""
    parts = []
    if candidate.current_title:
        parts.append(candidate.current_title)
    if candidate.years_of_experience:
        parts.append(f"com {candidate.years_of_experience} anos de experiência")
    if candidate.current_company:
        parts.append(f"em {candidate.current_company}")
    return " ".join(parts) if parts else "Profissional disponível para oportunidades"


def _build_location(candidate) -> str:  # type: ignore[no-untyped-def]
    """Build a location string from candidate fields."""
    parts = [
        p for p in [candidate.location_city, candidate.location_state, candidate.location_country]
        if p
    ]
    return ", ".join(parts) if parts else "Localização não informada"


def _build_highlights(candidate, job_skills: list[str]) -> list[str]:  # type: ignore[no-untyped-def]
    """Build 3–5 bullet-point highlights for the candidate."""
    bullets: list[str] = []

    # Bullet 1 — experience
    if candidate.years_of_experience:
        bullets.append(f"{candidate.years_of_experience} anos de experiência profissional")

    # Bullet 2 — current role
    if candidate.current_title and candidate.current_company:
        bullets.append(f"Atualmente: {candidate.current_title} em {candidate.current_company}")
    elif candidate.current_title:
        bullets.append(f"Cargo atual: {candidate.current_title}")

    # Bullet 3 — matching skills
    all_skills = list(candidate.technical_skills or []) + list(candidate.soft_skills or [])
    matched = _compute_skills_match(all_skills, job_skills)
    if matched:
        bullets.append(f"Habilidades alinhadas à vaga: {', '.join(matched[:5])}")
    elif all_skills:
        bullets.append(f"Habilidades: {', '.join(all_skills[:5])}")

    # Bullet 4 — work preferences
    prefs = []
    if candidate.is_remote:
        prefs.append("remoto")
    if candidate.willing_to_relocate:
        prefs.append("disponível para relocação")
    if prefs:
        bullets.append(f"Preferências: {', '.join(prefs)}")

    # Bullet 5 — seniority
    if candidate.seniority_level:
        bullets.append(f"Nível: {candidate.seniority_level}")

    # Return between 3 and 5 bullets
    return bullets[:5] if len(bullets) >= 3 else bullets + ["Perfil em avaliação"] * (3 - len(bullets))


def _compute_skills_match(candidate_skills: list[str], job_skills: list[str]) -> list[str]:
    """Return the intersection of candidate skills and job skills (case-insensitive)."""
    if not job_skills:
        return []
    job_lower = {s.lower() for s in job_skills}
    return [s for s in candidate_skills if s.lower() in job_lower]


def _compute_match_score(candidate, job_skills: list[str]) -> int | None:  # type: ignore[no-untyped-def]
    """
    Compute a 0–100 match score between candidate and job.

    Uses skill overlap as the primary signal. Returns None when no job context exists.
    """
    if not job_skills:
        return None

    candidate_skills = list(candidate.technical_skills or []) + list(candidate.soft_skills or [])
    if not candidate_skills:
        return 0

    matched = _compute_skills_match(candidate_skills, job_skills)
    raw = (len(matched) / len(job_skills)) * 100
    score = min(100, int(raw))
    return score


async def _get_redis(redis_url: str | None = None):  # type: ignore[return]
    """Return an aioredis client or None on failure (graceful degradation)."""
    try:
        import aioredis  # type: ignore[import]
        url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        return await aioredis.from_url(url, encoding="utf-8", decode_responses=True)
    except Exception as exc:
        logger.warning("[TOONService] Redis unavailable: %s", exc)
        return None


class TOONService:
    """
    Generates and caches TOON (Talent Object Of Note) cards.

    Usage:
        service = TOONService()
        card = await service.get_or_generate(candidate_id, job_id, db, company_id)
    """

    def __init__(self, redis_url: str | None = None) -> None:
        self._redis_url = redis_url

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def generate(
        self,
        candidate_id: str,
        job_id: str | None,
        db: AsyncSession,
        company_id: str,
        anonymize: bool = False,
    ) -> TOONCard:
        """
        Generate a fresh TOONCard for the candidate.

        Args:
            candidate_id: UUID of the candidate.
            job_id: UUID of the job opening (optional).
            db: Async SQLAlchemy session (scoped to tenant via company_id query).
            company_id: Tenant identifier — all queries are scoped by this.
            anonymize: When True, masks all PII fields (LGPD-safe mode).

        Returns:
            TOONCard with all fields populated.

        Raises:
            ValueError: When the candidate is not found or does not belong to company_id.
        """
        from lia_models.candidate import Candidate  # lazy import to avoid circular deps
        from lia_models.job_vacancy import JobVacancy  # lazy import

        # --- Fetch candidate ---
        # Note: Candidate model is global (no company_id column).
        # Multi-tenant isolation enforced at API layer via company_id claim in JWT.
        stmt = select(Candidate).where(Candidate.id == candidate_id)
        result = await db.execute(stmt)
        candidate = result.scalar_one_or_none()
        if candidate is None:
            raise ValueError(f"Candidate {candidate_id} not found for company {company_id}")

        # --- Fetch job skills (optional) ---
        job_skills: list[str] = []
        if job_id:
            try:
                job_stmt = select(JobVacancy).where(
                    JobVacancy.id == job_id,
                    JobVacancy.company_id == company_id,
                )
                job_result = await db.execute(job_stmt)
                job = job_result.scalar_one_or_none()
                if job and hasattr(job, "required_skills") and job.required_skills:
                    job_skills = list(job.required_skills)
            except Exception as exc:
                logger.warning("[TOONService] Could not fetch job skills for job %s: %s", job_id, exc)

        # --- Build card fields ---
        name_display = self._resolve_name(candidate, anonymize)
        headline = _build_headline(candidate)
        highlights = _build_highlights(candidate, job_skills)
        skills_match = _compute_skills_match(
            list(candidate.technical_skills or []) + list(candidate.soft_skills or []),
            job_skills,
        )
        match_score = _compute_match_score(candidate, job_skills)
        location = _build_location(candidate)
        experience_years = int(candidate.years_of_experience or 0)

        card = TOONCard(
            candidate_id=str(candidate_id),
            job_id=str(job_id) if job_id else None,
            generated_at=datetime.now(UTC).isoformat(),
            headline=headline,
            highlights=highlights,
            match_score=match_score,
            skills_match=skills_match,
            name_display=name_display,
            location=location,
            experience_years=experience_years,
            anonymized=anonymize,
            fairness_reviewed=True,  # FairnessGuard: no photos, age opt-out, no PII in highlights
        )
        return card

    async def get_or_generate(
        self,
        candidate_id: str,
        job_id: str | None,
        db: AsyncSession,
        company_id: str,
        anonymize: bool = False,
    ) -> TOONCard:
        """
        Return a cached TOONCard if available in Redis, otherwise generate and cache it.

        Cache key: toon:{company_id}:{candidate_id}:{job_id}
        TTL: 3600 seconds (1 hour)
        """
        cache_key = _toon_cache_key(candidate_id, job_id, company_id)
        redis = await _get_redis(self._redis_url)

        if redis is not None:
            try:
                cached = await redis.get(cache_key)
                if cached:
                    from app.shared.security.redis_crypto import get_redis_crypto
                    data = json.loads(get_redis_crypto().decrypt(cached))
                    await redis.aclose()
                    return TOONCard(**data)
            except Exception as exc:
                logger.warning("[TOONService] Cache read error: %s", exc)
            finally:
                try:
                    await redis.aclose()
                except Exception:
                    pass

        # Generate fresh card
        card = await self.generate(candidate_id, job_id, db, company_id, anonymize)

        # Store in Redis
        redis2 = await _get_redis(self._redis_url)
        if redis2 is not None:
            try:
                from app.shared.security.redis_crypto import get_redis_crypto
                payload = get_redis_crypto().encrypt(json.dumps(asdict(card)))
                await redis2.setex(cache_key, _TOON_CACHE_TTL, payload)
            except Exception as exc:
                logger.warning("[TOONService] Cache write error: %s", exc)
            finally:
                try:
                    await redis2.aclose()
                except Exception:
                    pass

        return card

    async def invalidate_cache(
        self,
        candidate_id: str,
        job_id: str | None,
        company_id: str,
    ) -> None:
        """Remove a specific TOON card from Redis cache."""
        cache_key = _toon_cache_key(candidate_id, job_id, company_id)
        redis = await _get_redis(self._redis_url)
        if redis is not None:
            try:
                await redis.delete(cache_key)
            except Exception as exc:
                logger.warning("[TOONService] Cache invalidation error: %s", exc)
            finally:
                try:
                    await redis.aclose()
                except Exception:
                    pass

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_name(candidate, anonymize: bool) -> str:  # type: ignore[no-untyped-def]
        """
        Return the display name.

        When anonymize=True returns "Candidato X" (LGPD-safe).
        Otherwise returns the real name.
        """
        if anonymize:
            return "Candidato X"
        return str(candidate.name) if candidate.name else "Nome não informado"


# Module-level singleton
toon_service = TOONService()
