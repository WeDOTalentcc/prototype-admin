"""
CVScreeningBatchService - Batch CV screening without agent overhead.

Extracted from TriagemCurricularAgent._handle_batch_screening() (Sprint 5).
Called directly by Celery tasks — no BaseAgent dependency.

Public API:
    run_batch(candidate_ids, job_id, company_id) -> dict
"""
import asyncio
import logging
from typing import Any
from uuid import UUID

from app.domains.cv_screening.repositories.screening_repository import ScreeningRepository
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.domains.cv_screening.services.rubric_evaluation_service import rubric_evaluation_service
from lia_models.candidate import Candidate
from lia_models.job_vacancy import JobVacancy
from lia_models.rubric import JobRequirement
from app.schemas.rubric import JobRequirementCreate, RequirementPriorityEnum
from app.shared.policy_middleware import get_policy_for_company

logger = logging.getLogger(__name__)

_WSI_TECHNICAL_WEIGHT_DEFAULT = 0.70
_WSI_BEHAVIORAL_WEIGHT_DEFAULT = 0.30
_SCORE_THRESHOLDS = {"auto_approve": 75, "review": 55}


def _normalize_priority(priority_value) -> RequirementPriorityEnum:
    if priority_value is None:
        return RequirementPriorityEnum.IMPORTANT
    if isinstance(priority_value, RequirementPriorityEnum):
        return priority_value
    if hasattr(priority_value, "value"):
        priority_value = priority_value.value
    if isinstance(priority_value, str):
        try:
            return RequirementPriorityEnum(priority_value.lower())
        except ValueError:
            return RequirementPriorityEnum.IMPORTANT
    return RequirementPriorityEnum.IMPORTANT


def _calculate_wsi_score(
    rubric_score: float,
    tech_weight: float = _WSI_TECHNICAL_WEIGHT_DEFAULT,
    behav_weight: float = _WSI_BEHAVIORAL_WEIGHT_DEFAULT,
) -> dict[str, Any]:
    technical_score = rubric_score
    behavioral_score = rubric_score * 0.85
    wsi_score = (technical_score * tech_weight) + (behavioral_score * behav_weight)
    wsi_normalized = wsi_score / 20

    if wsi_normalized >= 4.5:
        classification = "Excelente"
    elif wsi_normalized >= 4.0:
        classification = "Alto"
    elif wsi_normalized >= 3.0:
        classification = "Médio"
    elif wsi_normalized >= 2.0:
        classification = "Regular"
    else:
        classification = "Baixo"

    return {
        "wsi_score": round(wsi_normalized, 2),
        "technical_score": round(technical_score, 2),
        "behavioral_score": round(behavioral_score, 2),
        "classification": classification,
    }


def _determine_recommendation(score: float) -> str:
    if score >= _SCORE_THRESHOLDS["auto_approve"]:
        return "avançar"
    if score >= _SCORE_THRESHOLDS["review"]:
        return "revisao"
    return "rejeitar"


async def _load_calibration_weights(
    company_id: str, job_id: str, db: AsyncSession
) -> dict[str, float]:
    """Load CalibrationWeight for tenant. Falls back to defaults if none found."""
    try:
        from sqlalchemy import and_
        from lia_models.calibration import CalibrationWeight

        # ADR-001-EXEMPT: dynamic chained where() — base query reused with two different
        # job_id refinements (job-specific then null fallback). Sprint 6 follow-up to expose
        # via repo with two explicit list_by_company_for_job(job_id|None) calls.
        query = select(CalibrationWeight).where(
            and_(
                CalibrationWeight.company_id == company_id,
                CalibrationWeight.is_active == True,  # noqa: E712
            )
        )
        # Try job-specific first, then global
        result = await db.execute(query.where(CalibrationWeight.job_id == job_id))
        weights = result.scalars().all()
        if not weights:
            result = await db.execute(query.where(CalibrationWeight.job_id.is_(None)))
            weights = result.scalars().all()

        if weights:
            loaded = {w.dimension: w.adjusted_weight for w in weights}
            logger.info(
                "[CVScreeningBatch] Loaded %d calibration weights (company=%s, job=%s)",
                len(loaded), company_id, job_id,
            )
            return loaded
    except Exception as exc:
        logger.warning("[CVScreeningBatch] CalibrationWeight load failed: %s", exc)

    return {"technical": _WSI_TECHNICAL_WEIGHT_DEFAULT, "behavioral": _WSI_BEHAVIORAL_WEIGHT_DEFAULT}


async def _get_candidate_data(candidate_id: str, db: AsyncSession) -> dict[str, Any] | None:
    try:
        candidate = await ScreeningRepository(db).get_candidate_by_uuid_string(candidate_id)
        if not candidate:
            return None
        return {
            "id": str(candidate.id),
            "name": candidate.name,
            "email": candidate.email,
            "current_title": candidate.current_title,
            "current_company": candidate.current_company,
            "years_of_experience": candidate.years_of_experience,
            "seniority_level": candidate.seniority_level,
            "technical_skills": candidate.technical_skills or [],
            "soft_skills": candidate.soft_skills or [],
            "certifications": candidate.certifications or [],
            "languages": candidate.languages or {},
            "location_city": candidate.location_city,
            "location_state": candidate.location_state,
            "location_country": candidate.location_country,
            "is_remote": getattr(candidate, "is_remote", False),
            "work_history": getattr(candidate, "work_history", []) or [],
            "education": getattr(candidate, "education", []) or [],
            "resume_text": getattr(candidate, "resume_text", None),
            "self_introduction": candidate.self_introduction,
            "salary_expectation_clt": getattr(candidate, "salary_expectation_clt", None),
            "salary_expectation_pj": getattr(candidate, "salary_expectation_pj", None),
            "salary_expectation_freelance": getattr(candidate, "salary_expectation_freelance", None),
        }
    except Exception as e:
        logger.error(f"Error fetching candidate {candidate_id}: {e}")
        return None


async def _get_job_requirements(job_id: str, db: AsyncSession) -> list[JobRequirementCreate]:
    try:
        db_requirements = await ScreeningRepository(db).list_requirements_by_vacancy_uuid_string(job_id)
        return [
            JobRequirementCreate(
                requirement=req.requirement,
                description=req.description,
                priority=_normalize_priority(req.priority),
                category=req.category,
            )
            for req in db_requirements
        ]
    except Exception as e:
        logger.error(f"Error fetching job requirements for {job_id}: {e}")
        return []


async def _get_job_title(job_id: str, db: AsyncSession) -> str:
    try:
        job = await ScreeningRepository(db).get_job_vacancy_by_uuid_string(job_id)
        return job.title if job else "Vaga"
    except Exception as e:
        logger.error(f"Error fetching job info for {job_id}: {e}")
        return "Vaga"


async def _get_job_salary_range(job_id: str, db: AsyncSession) -> dict[str, Any] | None:
    try:
        job = await ScreeningRepository(db).get_job_vacancy_by_uuid_string(job_id)
        return job.salary_range if job else None
    except Exception as e:
        logger.error(f"Error fetching salary range for job {job_id}: {e}")
        return None


def _check_salary_compatibility(
    candidate: dict[str, Any],
    salary_range: dict[str, Any] | None,
    tolerance_percent: int,
) -> bool:
    """
    Returns True if candidate is salary-compatible with the job or if data is missing.

    Candidate is incompatible only when:
    - salary_range has a valid max
    - candidate has at least one salary expectation field
    - candidate's lowest expectation exceeds max * (1 + tolerance/100)
    """
    if not salary_range:
        return True

    max_salary = salary_range.get("max")
    if not max_salary or max_salary <= 0:
        return True

    expectations = [
        v for v in [
            candidate.get("salary_expectation_clt"),
            candidate.get("salary_expectation_pj"),
            candidate.get("salary_expectation_freelance"),
        ]
        if v is not None and v > 0
    ]
    if not expectations:
        return True

    tolerance_factor = 1 + (tolerance_percent / 100)
    ceiling = max_salary * tolerance_factor
    return min(expectations) <= ceiling


async def _apply_fairness_gate(
    score: float,
    company_id: str,
    domain: str = "screening",
) -> tuple:
    """Verifica FairnessPolicyService.allows_automated() antes de aprovar automaticamente.

    Returns:
        (status, reason) where status in {"Aprovado", "Revisao", "Reprovado"}
        reason = None se aprovado; str com motivo se foi para revisao por fairness gate
    """
    if score >= _SCORE_THRESHOLDS["auto_approve"]:
        default_status = "Aprovado"
    elif score >= _SCORE_THRESHOLDS["review"]:
        default_status = "Revisão"
    else:
        default_status = "Reprovado"

    if default_status != "Aprovado":
        return default_status, None

    try:
        from app.shared.compliance.fairness_policy_service import _get_fairness_service
        from app.core.database import AsyncSessionLocal as _ASL

        confidence = score / 100.0

        async with _ASL() as _db:
            svc = _get_fairness_service()
            effective_policy = await svc.load_effective_policy(
                tenant_id=company_id,
                domain=domain,
                db=_db,
            )
            allowed, reason = await svc.allows_automated(
                decision_type="screening_score",
                confidence=confidence,
                effective_policy=effective_policy,
                tenant_id=company_id,
                domain=domain,
                db=_db,
            )

        if not allowed:
            logger.info(
                "[CVScreeningBatch] FairnessGate override: score=%.1f blocked -- %s",
                score, reason,
            )
            return "Revisão", reason

        return "Aprovado", None

    except Exception as exc:
        logger.warning(
            "[CVScreeningBatch] FairnessGate unavailable (fail-open): %s", exc
        )
        return default_status, None


async def run_batch(
    candidate_ids: list[str],
    job_id: str,
    company_id: str,
    max_concurrent: int = 5,
) -> dict[str, Any]:
    """
    Screen a batch of candidates against a job, in parallel.

    Returns:
        {
            "processed": int,
            "approved": int,
            "rejected": int,
            "review": int,
            "ranking": list[dict],
        }
    """
    async with AsyncSessionLocal() as db:
        requirements = await _get_job_requirements(job_id, db)
        if not requirements:
            logger.warning(f"No requirements found for job {job_id} — batch aborted")
            return {"processed": 0, "approved": 0, "rejected": 0, "review": 0, "ranking": []}

        job_title = await _get_job_title(job_id, db)

        # Load salary filter policy
        policy = await get_policy_for_company(company_id, db)
        screening_rules = policy.get("screening_rules", {})
        from app.shared.policy_helper import coerce_bool, coerce_int
        salary_filter_enabled: bool = coerce_bool(screening_rules.get("salary_expectation_filter", False))
        salary_tolerance: int = coerce_int(screening_rules.get("salary_tolerance_percent", 15), 15)
        job_salary_range = await _get_job_salary_range(job_id, db) if salary_filter_enabled else None

        # Load CalibrationWeight for this tenant (item 12.3)
        calibration_weights = await _load_calibration_weights(company_id, job_id, db)

        candidates_data: list[dict[str, Any]] = []
        salary_excluded: list[str] = []
        for cid in candidate_ids:
            cdata = await _get_candidate_data(str(cid), db)
            if not cdata:
                continue
            if salary_filter_enabled and not _check_salary_compatibility(
                cdata, job_salary_range, salary_tolerance
            ):
                logger.info(
                    f"[salary_filter] Candidate excluded — expectation exceeds "
                    f"job max with {salary_tolerance}% tolerance (job={job_id})"
                )
                salary_excluded.append(cid)
            else:
                candidates_data.append(cdata)

    if not candidates_data:
        logger.warning(f"No valid candidates found for job {job_id} (salary_excluded={len(salary_excluded)})")
        return {"processed": 0, "approved": 0, "rejected": 0, "review": 0, "ranking": [], "salary_excluded": len(salary_excluded)}

    semaphore = asyncio.Semaphore(max_concurrent)

    tech_w = calibration_weights.get("technical", _WSI_TECHNICAL_WEIGHT_DEFAULT)
    behav_w = calibration_weights.get("behavioral", _WSI_BEHAVIORAL_WEIGHT_DEFAULT)

    async def _evaluate(candidate: dict[str, Any]) -> dict[str, Any]:
        async with semaphore:
            try:
                result = await rubric_evaluation_service.evaluate_candidate(
                    candidate_data=candidate,
                    requirements=requirements,
                )
                wsi = _calculate_wsi_score(result.score, tech_weight=tech_w, behav_weight=behav_w)
                return {
                    "candidate_id": candidate.get("id"),
                    "candidate_name": candidate.get("name", "Candidato"),
                    "rubric_score": result.score,
                    "wsi_score": wsi["wsi_score"],
                    "classification": wsi["classification"],
                    "recommendation": _determine_recommendation(result.score),
                    "strengths": result.strengths[:3],
                    "concerns": result.concerns[:3],
                    "success": True,
                }
            except Exception as e:
                logger.error(f"Failed to evaluate candidate {candidate.get('id')}: {e}")
                return {
                    "candidate_id": candidate.get("id"),
                    "candidate_name": candidate.get("name", "Candidato"),
                    "error": str(e),
                    "success": False,
                }

    logger.info(f"[CVScreeningBatchService] Starting batch: {len(candidates_data)} candidates, job={job_id}")
    raw_results = await asyncio.gather(*[_evaluate(c) for c in candidates_data], return_exceptions=True)

    successful, failed = [], []
    for r in raw_results:
        if isinstance(r, Exception):
            failed.append({"error": str(r), "success": False})
        elif r.get("success"):
            successful.append(r)
        else:
            failed.append(r)

    ranking = sorted(successful, key=lambda x: x.get("rubric_score", 0), reverse=True)
    for i, item in enumerate(ranking, 1):
        item["rank"] = i
        score = item["rubric_score"]
        if score >= _SCORE_THRESHOLDS["auto_approve"]:
            item["status"], _gate_reason = await _apply_fairness_gate(score, company_id)
            if _gate_reason:
                item["fairness_gate_reason"] = _gate_reason
        elif score >= _SCORE_THRESHOLDS["review"]:
            item["status"] = "Revisão"
        else:
            item["status"] = "Reprovado"

    approved = sum(1 for r in ranking if r.get("status") == "Aprovado")
    review = sum(1 for r in ranking if r.get("status") == "Revisão")
    rejected = sum(1 for r in ranking if r.get("status") == "Reprovado")

    logger.info(
        f"[CVScreeningBatchService] Done: {len(successful)} ok, {len(failed)} failed "
        f"— approved={approved}, review={review}, rejected={rejected}, salary_excluded={len(salary_excluded)}"
    )

    return {
        "processed": len(successful),
        "approved": approved,
        "rejected": rejected,
        "review": review,
        "ranking": ranking,
        "job_id": job_id,
        "job_title": job_title,
        "total_candidates": len(candidate_ids),
        "failed": len(failed),
        "salary_excluded": len(salary_excluded),
    }
