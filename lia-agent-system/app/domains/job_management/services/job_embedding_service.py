"""
Job Embedding Service - Manages embeddings for semantic job search.

Enables:
- Generating embeddings for new job vacancies
- Finding semantically similar jobs
- Fast Track suggestions based on similar past jobs
- Pattern discovery across departments
"""
import logging
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import text, select, and_  # noqa: F401 — select/and_ needed by batch_process_jobs and for test patching

from app.core.database import AsyncSessionLocal
from app.domains.job_management.repositories.job_embedding_repository import JobEmbeddingRepository
from lia_models.job_pattern import EMBEDDING_DIMENSION, JobEmbedding
from app.shared.intelligence.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class JobEmbeddingService:
    """
    Service for managing job embeddings and semantic search.
    
    Features:
    - Generate embeddings for job vacancies
    - Semantic similarity search
    - Batch processing for existing jobs
    - Template discovery
    """
    
    def __init__(self):
        self._embedding_service = None
    
    @property
    def embedding_service(self) -> EmbeddingService:
        """Get embedding service instance."""
        if not self._embedding_service:
            self._embedding_service = EmbeddingService()
        return self._embedding_service
    
    async def generate_job_embedding(
        self,
        job_title: str,
        department: str = None,
        seniority: str = None,
        location: str = None,
        skills: list[str] = None,
        behavioral: list[str] = None,
        description: str = None,
        company_id: str | None = None,
    ) -> list[float]:
        """
        Generate embedding vector for a job.

        Returns:
            Embedding vector (dimensions depend on provider).
        """
        embedding_text = JobEmbedding.create_embedding_text(
            job_title=job_title,
            department=department,
            seniority=seniority,
            location=location,
            skills=skills or [],
            behavioral=behavioral or [],
            description=description
        )

        try:
            embedding = await self.embedding_service.generate_embedding(embedding_text, company_id=company_id)
            return embedding
        except Exception as e:
            logger.error(f"Error generating job embedding: {e}")
            return [0.0] * EMBEDDING_DIMENSION

    async def generate_job_embedding_with_metadata(
        self,
        job_title: str,
        department: str = None,
        seniority: str = None,
        location: str = None,
        skills: list[str] = None,
        behavioral: list[str] = None,
        description: str = None,
        company_id: str | None = None,
    ) -> tuple:
        """
        Generate embedding vector for a job and return (vector, provider, model).

        Returns:
            Tuple of (embedding vector, provider_name, model_name).
        """
        embedding_text = JobEmbedding.create_embedding_text(
            job_title=job_title,
            department=department,
            seniority=seniority,
            location=location,
            skills=skills or [],
            behavioral=behavioral or [],
            description=description
        )

        try:
            return await self.embedding_service.generate_embedding_with_metadata(embedding_text, company_id=company_id)
        except Exception as e:
            logger.error(f"Error generating job embedding with metadata: {e}")
            return [0.0] * EMBEDDING_DIMENSION, "unknown", "unknown"
    
    async def create_or_update_job_embedding(
        self,
        company_id: str,
        job_id: str,
        job_title: str,
        department: str = None,
        seniority: str = None,
        location: str = None,
        work_model: str = None,
        skills: list[str] = None,
        behavioral: list[str] = None,
        description: str = None,
        outcome_status: str = None,
        time_to_fill_days: int = None,
        is_template: bool = False,
        draft_id: str = None
    ) -> dict[str, Any]:
        """
        Create or update embedding for a job vacancy.
        
        Returns:
            Dict with embedding info and status
        """
        embedding_text = JobEmbedding.create_embedding_text(
            job_title=job_title,
            department=department,
            seniority=seniority,
            location=location,
            skills=skills or [],
            behavioral=behavioral or [],
            description=description
        )
        
        try:
            embedding, emb_provider, emb_model = await self.generate_job_embedding_with_metadata(
                job_title=job_title,
                department=department,
                seniority=seniority,
                location=location,
                skills=skills,
                behavioral=behavioral,
                description=description,
                company_id=company_id,
            )

            async with AsyncSessionLocal() as session:
                job_embedding = await JobEmbeddingRepository(session).get_by_job_id(UUID(job_id))

                normalized_title = self._normalize_title(job_title)

                if job_embedding:
                    job_embedding.job_title = job_title
                    job_embedding.job_title_normalized = normalized_title
                    job_embedding.department = department
                    job_embedding.seniority = seniority
                    job_embedding.location = location
                    job_embedding.work_model = work_model
                    job_embedding.skills = skills or []
                    job_embedding.behavioral_competencies = behavioral or []
                    job_embedding.embedding = embedding
                    job_embedding.embedding_text = embedding_text
                    job_embedding.embedding_provider = emb_provider
                    job_embedding.embedding_model = emb_model
                    job_embedding.outcome_status = outcome_status
                    job_embedding.time_to_fill_days = time_to_fill_days
                    job_embedding.is_template = is_template
                    job_embedding.updated_at = datetime.utcnow()
                    action = "updated"
                else:
                    job_embedding = JobEmbedding(
                        company_id=UUID(company_id),
                        job_id=UUID(job_id),
                        draft_id=UUID(draft_id) if draft_id else None,
                        job_title=job_title,
                        job_title_normalized=normalized_title,
                        department=department,
                        seniority=seniority,
                        location=location,
                        work_model=work_model,
                        skills=skills or [],
                        behavioral_competencies=behavioral or [],
                        embedding=embedding,
                        embedding_text=embedding_text,
                        embedding_provider=emb_provider,
                        embedding_model=emb_model,
                        outcome_status=outcome_status,
                        time_to_fill_days=time_to_fill_days,
                        is_template=is_template
                    )
                    session.add(job_embedding)
                    action = "created"

                await session.commit()
                await session.refresh(job_embedding)

                return {
                    "success": True,
                    "job_id": str(job_embedding.job_id),
                    "embedding_id": str(job_embedding.id),
                    "embedding_provider": emb_provider,
                    "embedding_model": emb_model,
                    "action": action,
                }

        except Exception as e:
            # rollback handled automatically by `async with AsyncSessionLocal()`
            logger.error(f"Error creating/updating job embedding: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def find_similar_jobs(
        self,
        company_id: str,
        job_title: str,
        department: str = None,
        seniority: str = None,
        location: str = None,
        skills: list[str] = None,
        behavioral: list[str] = None,
        description: str = None,
        limit: int = 5,
        min_similarity: float = 0.5,
        exclude_job_ids: list[str] = None
    ) -> list[dict[str, Any]]:
        """
        Find semantically similar jobs using vector similarity.
        
        Args:
            company_id: Company ID
            job_title: Job title to match
            department: Optional department filter
            seniority: Optional seniority filter
            limit: Maximum results to return
            min_similarity: Minimum similarity threshold (0-1)
            exclude_job_ids: Job IDs to exclude from results
            
        Returns:
            List of similar jobs with similarity scores
        """
        try:
            query_embedding, query_provider, query_model = (
                await self.generate_job_embedding_with_metadata(
                    job_title=job_title,
                    department=department,
                    seniority=seniority,
                    location=location,
                    skills=skills,
                    behavioral=behavioral,
                    description=description
                )
            )

            if all(v == 0.0 for v in query_embedding):
                logger.warning("Empty embedding generated, falling back to text search")
                return await self._fallback_text_search(
                    company_id, job_title, department, seniority, limit
                )

            async with AsyncSessionLocal() as session:
                similarity_sql = text("""
                    WITH provider_candidates AS (
                        SELECT
                            id, job_id, job_title, department, seniority, location,
                            work_model, skills, behavioral_competencies,
                            outcome_status, time_to_fill_days, is_template,
                            metadata_json, embedding_provider, embedding_model,
                            embedding
                        FROM job_embeddings
                        WHERE company_id = :company_id
                            AND is_active = true
                            AND embedding IS NOT NULL
                            AND embedding_provider = :provider
                            AND embedding_model = :model
                    )
                    SELECT
                        id, job_id, job_title, department, seniority, location,
                        work_model, skills, behavioral_competencies,
                        outcome_status, time_to_fill_days, is_template,
                        metadata_json, embedding_provider, embedding_model,
                        1 - (embedding <=> :query_embedding::vector) as base_similarity,
                        COALESCE(
                            (metadata_json->'outcome_data'->>'success_weight')::float,
                            (metadata_json->'fast_track_stats'->>'success_weight')::float,
                            1.0
                        ) as success_weight,
                        (1 - (embedding <=> :query_embedding::vector)) *
                        COALESCE(
                            (metadata_json->'outcome_data'->>'success_weight')::float,
                            (metadata_json->'fast_track_stats'->>'success_weight')::float,
                            1.0
                        ) as similarity
                    FROM provider_candidates
                    WHERE 1 - (embedding <=> :query_embedding::vector) >= :min_similarity
                    ORDER BY similarity DESC
                    LIMIT :limit
                """)

                result = await session.execute(
                    similarity_sql,
                    {
                        "query_embedding": str(query_embedding),
                        "company_id": str(company_id),
                        "provider": query_provider,
                        "model": query_model,
                        "min_similarity": min_similarity,
                        "limit": limit + len(exclude_job_ids or [])
                    }
                )
                
                rows = result.fetchall()
                
                similar_jobs = []
                exclude_set = set(exclude_job_ids or [])
                
                for row in rows:
                    job_id_str = str(row.job_id)
                    if job_id_str in exclude_set:
                        continue
                    
                    success_weight = float(row.success_weight) if hasattr(row, 'success_weight') else 1.0
                    is_boosted = success_weight > 1.0
                    
                    similar_jobs.append({
                        "job_id": job_id_str,
                        "job_title": row.job_title,
                        "department": row.department,
                        "seniority": row.seniority,
                        "location": row.location,
                        "work_model": row.work_model,
                        "skills": row.skills or [],
                        "behavioral_competencies": row.behavioral_competencies or [],
                        "outcome_status": row.outcome_status,
                        "time_to_fill_days": row.time_to_fill_days,
                        "is_template": row.is_template,
                        "similarity": round(float(row.similarity), 3),
                        "base_similarity": round(float(row.base_similarity), 3) if hasattr(row, 'base_similarity') else None,
                        "success_weight": round(success_weight, 2),
                        "is_boosted": is_boosted
                    })
                    
                    if len(similar_jobs) >= limit:
                        break
                
                return similar_jobs
                
        except Exception as e:
            logger.error(f"Error finding similar jobs: {e}")
            return await self._fallback_text_search(
                company_id, job_title, department, seniority, limit
            )
    
    async def _fallback_text_search(
        self,
        company_id: str,
        job_title: str,
        department: str = None,
        seniority: str = None,
        limit: int = 5
    ) -> list[dict[str, Any]]:
        """Fallback to text-based search when embeddings fail."""
        try:
            async with AsyncSessionLocal() as session:
                normalized = self._normalize_title(job_title)
                jobs = await JobEmbeddingRepository(session).text_search_active(
                    company_id=UUID(company_id),
                    normalized_title=normalized,
                    department=department,
                    limit=limit,
                )
                
                return [
                    {
                        **job.to_dict(),
                        "similarity": 0.5
                    }
                    for job in jobs
                ]
                
        except Exception as e:
            logger.error(f"Fallback text search failed: {e}")
            return []
    
    async def get_fast_track_suggestions(
        self,
        company_id: str,
        job_title: str,
        department: str = None,
        limit: int = 3
    ) -> list[dict[str, Any]]:
        """
        Get Fast Track suggestions for quick job creation.
        
        Returns jobs with high success rates that are semantically similar.
        """
        similar = await self.find_similar_jobs(
            company_id=company_id,
            job_title=job_title,
            department=department,
            limit=limit * 2,
            min_similarity=0.6
        )
        
        suggestions = []
        for job in similar:
            if job.get("outcome_status") == "filled":
                suggestions.append({
                    **job,
                    "recommendation": "Fast Track - Similar job filled successfully",
                    "time_saved_estimate": "80%"
                })
            elif job.get("is_template"):
                suggestions.append({
                    **job,
                    "recommendation": "Template - Pre-configured job template",
                    "time_saved_estimate": "70%"
                })
            else:
                suggestions.append({
                    **job,
                    "recommendation": "Similar job - Can be used as starting point",
                    "time_saved_estimate": "50%"
                })
            
            if len(suggestions) >= limit:
                break
        
        return suggestions
    
    async def batch_process_jobs(
        self,
        company_id: str,
        job_ids: list[str] = None,
        limit: int = 100
    ) -> dict[str, Any]:
        """
        Process embeddings for multiple jobs in batch.
        
        Args:
            company_id: Company ID
            job_ids: Specific job IDs to process (optional)
            limit: Maximum jobs to process
            
        Returns:
            Processing stats
        """
        processed = 0
        errors = 0
        
        try:
            async with AsyncSessionLocal() as session:
                jobs = await JobEmbeddingRepository(session).list_missing_embeddings(
                    company_id=UUID(company_id),
                    job_ids=[UUID(jid) for jid in job_ids] if job_ids else None,
                    limit=limit,
                )
                
                for job in jobs:
                    try:
                        embedding, emb_provider, emb_model = (
                            await self.generate_job_embedding_with_metadata(
                                job_title=job.job_title,
                                department=job.department,
                                seniority=job.seniority,
                                location=job.location,
                                skills=job.skills,
                                behavioral=job.behavioral_competencies,
                                description=job.description_summary
                            )
                        )

                        job.embedding = embedding
                        job.embedding_text = JobEmbedding.create_embedding_text(
                            job_title=job.job_title,
                            department=job.department,
                            seniority=job.seniority,
                            location=job.location,
                            skills=job.skills,
                            behavioral=job.behavioral_competencies
                        )
                        job.embedding_provider = emb_provider
                        job.embedding_model = emb_model
                        job.updated_at = datetime.utcnow()
                        processed += 1

                    except Exception as e:
                        logger.error(f"Error processing job {job.job_id}: {e}")
                        errors += 1
                
                await session.commit()
                
        except Exception as e:
            # rollback handled automatically by `async with AsyncSessionLocal()`
            logger.error(f"Batch processing error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
        
        return {
            "success": True,
            "processed": processed,
            "errors": errors,
            "total": processed + errors
        }
    
    async def get_embedding_stats(self, company_id: str) -> dict[str, Any]:
        """Get statistics about job embeddings for a company."""
        try:
            async with AsyncSessionLocal() as session:
                stats = await JobEmbeddingRepository(session).stats(UUID(company_id))

                return {
                    "total_jobs": stats["total_jobs"],
                    "with_embeddings": stats["with_embeddings"],
                    "templates": stats["templates"],
                    "coverage_percent": round(
                        (stats["with_embeddings"] or 0) / max(stats["total_jobs"] or 1, 1) * 100, 1
                    )
                }
                
        except Exception as e:
            logger.error(f"Error getting embedding stats: {e}")
            return {
                "total_jobs": 0,
                "with_embeddings": 0,
                "templates": 0,
                "coverage_percent": 0
            }
    
    def _normalize_title(self, title: str) -> str:
        """Normalize job title for matching."""
        if not title:
            return ""
        
        import re
        normalized = title.lower().strip()
        normalized = re.sub(r'\s+', ' ', normalized)
        normalized = re.sub(r'(sr\.?|senior)\s+', 'senior ', normalized)
        normalized = re.sub(r'(jr\.?|junior)\s+', 'junior ', normalized)
        
        return normalized
    
    async def get_full_job_data(
        self,
        company_id: str,
        job_id: str
    ) -> dict[str, Any] | None:
        """
        Get complete job data for Fast Track copy.
        
        Fetches all fields needed for Fast Track:
        - Basic info (title, department, location, etc.)
        - Skills and behavioral competencies
        - Salary and benefits
        - Description and responsibilities
        - WSI/screening questions
        """
        from lia_models.job_vacancy import JobVacancy
        
        try:
            async with AsyncSessionLocal() as session:
                job = await JobEmbeddingRepository(session).get_vacancy_for_embedding(
                    UUID(job_id), company_id
                )
                
                if not job:
                    return None
                
                technical_skills = []
                if job.technical_requirements:
                    for req in job.technical_requirements:
                        if isinstance(req, dict):
                            technical_skills.append(req.get("technology", req.get("name", "")))
                        else:
                            technical_skills.append(str(req))
                
                if job.requirements and not technical_skills:
                    technical_skills = list(job.requirements) if job.requirements else []
                
                behavioral = []
                if job.behavioral_competencies:
                    for comp in job.behavioral_competencies:
                        if isinstance(comp, dict):
                            behavioral.append({
                                "name": comp.get("competency", comp.get("name", "")),
                                "weight": comp.get("weight", 3),
                                "justification": comp.get("justification", "")
                            })
                        else:
                            behavioral.append({"name": str(comp), "weight": 3})
                
                salary_min = None
                salary_max = None
                if job.salary_range:
                    salary_min = job.salary_range.get("min")
                    salary_max = job.salary_range.get("max")
                
                benefits = []
                if job.benefits:
                    for i, b in enumerate(job.benefits):
                        benefits.append({
                            "id": str(i + 1),
                            "name": b,
                            "enabled": True
                        })
                
                wsi_questions = []
                if job.screening_questions:
                    for q in job.screening_questions:
                        if isinstance(q, dict):
                            wsi_questions.append({
                                "id": q.get("id", str(uuid4())),
                                "question": q.get("question", ""),
                                "type": q.get("type", "open"),
                                "required": q.get("required", True),
                                "options": q.get("options"),
                                "competency_validated": q.get("competency_validated")
                            })
                
                return {
                    "job_id": str(job.id),
                    "job_title": job.title,
                    "department": job.department,
                    "seniority": job.seniority_level,
                    "location": job.location,
                    "work_model": job.work_model,
                    "employment_type": job.employment_type,
                    "description": job.description,
                    "technical_skills": technical_skills,
                    "behavioral_competencies": behavioral,
                    "salary_min": salary_min,
                    "salary_max": salary_max,
                    "benefits": benefits,
                    "wsi_questions": wsi_questions,
                    "manager": job.manager,
                    "manager_email": job.manager_email,
                    "is_affirmative": job.is_affirmative,
                    "affirmative_criteria_primary": job.affirmative_criteria_primary,
                    "affirmative_criteria_secondary": job.affirmative_criteria_secondary,
                    "languages": job.languages or [],
                    "interview_stages": job.interview_stages or [],
                    "created_at": job.created_at.isoformat() if job.created_at else None,
                    "status": job.status
                }
                
        except Exception as e:
            logger.error(f"Error getting full job data: {e}")
            return None
    
    async def get_fast_track_full_suggestions(
        self,
        company_id: str,
        job_title: str,
        department: str = None,
        limit: int = 3
    ) -> list[dict[str, Any]]:
        """
        Get Fast Track suggestions with complete job data.
        
        Returns suggestions enriched with all fields needed for copy.
        """
        suggestions = await self.get_fast_track_suggestions(
            company_id=company_id,
            job_title=job_title,
            department=department,
            limit=limit
        )
        
        enriched = []
        for suggestion in suggestions:
            job_id = suggestion.get("job_id")
            if job_id:
                full_data = await self.get_full_job_data(company_id, job_id)
                if full_data:
                    enriched.append({
                        **suggestion,
                        **full_data,
                        "similarity_score": suggestion.get("similarity", 0.7)
                    })
                else:
                    enriched.append({
                        **suggestion,
                        "similarity_score": suggestion.get("similarity", 0.7)
                    })
            else:
                enriched.append(suggestion)
        
        return enriched
    
    async def record_fast_track_usage(
        self,
        company_id: str,
        source_job_id: str,
        new_job_id: str,
        modified_fields: list[str],
        was_published: bool
    ) -> dict[str, Any]:
        """
        Record when Fast Track is used to create a new job.
        
        This data is used to:
        - Track Fast Track adoption
        - Identify commonly modified fields (improve copy quality)
        - Measure Fast Track success rate
        
        Args:
            company_id: Company ID
            source_job_id: ID of the job that was used as template
            new_job_id: ID of the newly created job
            modified_fields: List of fields that were modified after Fast Track copy
            was_published: Whether the job was successfully published
            
        Returns:
            Success status and tracking info
        """
        try:
            async with AsyncSessionLocal() as session:
                source = await JobEmbeddingRepository(session).get_by_company_and_job(
                    company_id, source_job_id
                )
                
                if source:
                    current_metadata = source.metadata_json or {}
                    fast_track_stats = current_metadata.get("fast_track_stats", {
                        "times_used_as_template": 0,
                        "modifications_histogram": {},
                        "successful_publishes": 0
                    })
                    
                    fast_track_stats["times_used_as_template"] += 1
                    if was_published:
                        fast_track_stats["successful_publishes"] += 1
                    
                    for field in modified_fields:
                        current_count = fast_track_stats["modifications_histogram"].get(field, 0)
                        fast_track_stats["modifications_histogram"][field] = current_count + 1
                    
                    current_metadata["fast_track_stats"] = fast_track_stats
                    source.metadata_json = current_metadata
                    await session.commit()
                    
                    logger.info(f"Recorded Fast Track usage: {source_job_id} -> {new_job_id}")
                    return {
                        "success": True,
                        "source_job_id": source_job_id,
                        "new_job_id": new_job_id,
                        "times_used": fast_track_stats["times_used_as_template"]
                    }
                
                return {"success": True, "message": "Source job not found in embeddings"}
                
        except Exception as e:
            # rollback handled automatically by `async with AsyncSessionLocal()`
            logger.error(f"Error recording Fast Track usage: {e}")
            return {"success": False, "error": str(e)}
    
    async def update_embedding_from_outcome(
        self,
        company_id: str,
        job_id: str,
        outcome_status: str,
        time_to_fill_days: int = None,
        hire_quality_score: float = None
    ) -> dict[str, Any]:
        """
        Update job embedding metadata based on outcome.
        
        Positive outcomes (filled, hired) boost the job's weight in suggestions.
        Negative outcomes (cancelled, expired) reduce weight.
        
        Args:
            company_id: Company ID
            job_id: Job ID
            outcome_status: Outcome (filled, hired, cancelled, expired)
            time_to_fill_days: Days to fill the position
            hire_quality_score: Quality score of the hire (0-100)
            
        Returns:
            Success status and updated metadata
        """
        try:
            async with AsyncSessionLocal() as session:
                embedding = await JobEmbeddingRepository(session).get_by_company_and_job(
                    company_id, job_id
                )
                
                if embedding:
                    embedding.outcome_status = outcome_status
                    if time_to_fill_days:
                        embedding.time_to_fill_days = time_to_fill_days
                    
                    current_metadata = embedding.metadata_json or {}
                    outcome_data = current_metadata.get("outcome_data", {})
                    
                    outcome_data["status"] = outcome_status
                    outcome_data["recorded_at"] = datetime.utcnow().isoformat()
                    
                    if time_to_fill_days:
                        outcome_data["time_to_fill_days"] = time_to_fill_days
                    if hire_quality_score is not None:
                        outcome_data["hire_quality_score"] = hire_quality_score
                    
                    success_weight = 1.0
                    if outcome_status in ["filled", "hired"]:
                        success_weight = 1.2
                        if hire_quality_score and hire_quality_score >= 80:
                            success_weight = 1.5
                    elif outcome_status in ["cancelled", "expired"]:
                        success_weight = 0.8
                    
                    outcome_data["success_weight"] = success_weight
                    current_metadata["outcome_data"] = outcome_data
                    embedding.metadata_json = current_metadata
                    
                    await session.commit()
                    
                    logger.info(f"Updated embedding outcome for job {job_id}: {outcome_status}")
                    return {
                        "success": True,
                        "job_id": job_id,
                        "outcome_status": outcome_status,
                        "success_weight": success_weight
                    }
                
                return {"success": False, "error": "Job embedding not found"}
                
        except Exception as e:
            # rollback handled automatically by `async with AsyncSessionLocal()`
            logger.error(f"Error updating embedding outcome: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_fast_track_insights(
        self,
        company_id: str,
        limit: int = 10
    ) -> dict[str, Any]:
        """
        Get insights about Fast Track usage for a company.
        
        Returns:
        - Most used templates
        - Most commonly modified fields
        - Success rate
        - Time savings estimate
        """
        try:
            async with AsyncSessionLocal() as session:
                embeddings = await JobEmbeddingRepository(session).list_with_metadata(
                    company_id, limit=100
                )
                
                total_uses = 0
                total_publishes = 0
                modifications_total = {}
                top_templates = []
                
                for emb in embeddings:
                    meta = emb.metadata_json or {}
                    stats = meta.get("fast_track_stats", {})
                    
                    uses = stats.get("times_used_as_template", 0)
                    if uses > 0:
                        total_uses += uses
                        total_publishes += stats.get("successful_publishes", 0)
                        
                        for field, count in stats.get("modifications_histogram", {}).items():
                            modifications_total[field] = modifications_total.get(field, 0) + count
                        
                        top_templates.append({
                            "job_id": emb.job_id,
                            "job_title": emb.job_title,
                            "times_used": uses,
                            "success_rate": stats.get("successful_publishes", 0) / uses if uses > 0 else 0
                        })
                
                top_templates.sort(key=lambda x: x["times_used"], reverse=True)
                
                sorted_modifications = sorted(
                    modifications_total.items(), 
                    key=lambda x: x[1], 
                    reverse=True
                )
                
                time_saved_minutes = total_uses * 12
                
                return {
                    "success": True,
                    "total_fast_track_uses": total_uses,
                    "successful_publishes": total_publishes,
                    "success_rate": total_publishes / total_uses if total_uses > 0 else 0,
                    "estimated_time_saved_minutes": time_saved_minutes,
                    "top_templates": top_templates[:limit],
                    "most_modified_fields": [
                        {"field": field, "count": count} 
                        for field, count in sorted_modifications[:10]
                    ],
                    "improvement_suggestions": self._generate_improvement_suggestions(sorted_modifications)
                }
                
        except Exception as e:
            logger.error(f"Error getting Fast Track insights: {e}")
            return {"success": False, "error": str(e)}
    
    def _generate_improvement_suggestions(
        self,
        modifications: list[tuple]
    ) -> list[str]:
        """Generate suggestions based on modification patterns."""
        suggestions = []
        
        for field, count in modifications[:5]:
            if count >= 5:
                if field == "gestor":
                    suggestions.append(
                        "O campo 'Gestor' é frequentemente modificado. "
                        "Considere perguntar explicitamente no início do Fast Track."
                    )
                elif field == "localidade":
                    suggestions.append(
                        "O campo 'Localidade' é frequentemente modificado. "
                        "Verifique se as localizações padrão estão atualizadas."
                    )
                elif field == "salary_min" or field == "salary_max":
                    suggestions.append(
                        "Os valores de salário são frequentemente ajustados. "
                        "Considere atualizar as faixas salariais baseado no mercado."
                    )
                elif field == "skills" or field == "technical_skills":
                    suggestions.append(
                        "As skills técnicas são frequentemente modificadas. "
                        "O catálogo de skills pode precisar de atualização."
                    )
        
        return suggestions


job_embedding_service = JobEmbeddingService()
