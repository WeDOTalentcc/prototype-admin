"""
Rubric Evaluation Service - Structured rubrics for CV vs Job evaluation.

Based on Schmidt & Hunter (1998) meta-analysis and BARS methodology.
This service evaluates ONLY CV vs Job requirements match.
Big Five, WSI, and Cultural Fit require separate assessments.

Enhanced Features (v2.0):
- Evaluation caching to ensure consistency and reduce LLM costs
- Variation logging to detect LLM inconsistencies
- Calibration system with recruiter feedback
"""
import asyncio
import hashlib
import json
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Any


from app.schemas.rubric import (
    EvaluationLevelEnum,
    EvidenceType,
    JobRequirementCreate,
    LegacyScoreWrapper,
    RequirementEvaluation,
    RequirementPriorityEnum,
    RubricEvaluationResult,
)


class RubricEvaluationError(Exception):
    """LLM evaluation failed — cannot produce reliable score.

    Callers MUST handle this explicitly: either re-try or route the
    candidate to manual review.  Silently returning score=0 is the
    anti-pattern this exception replaces (F5a fail-loud).
    """

from app.domains.ai.services.llm import LLMService
from app.services.notification_service import NotificationChannel, NotificationService, NotificationType
from app.domains.analytics.services.sector_benchmark_service import sector_benchmark_service
from app.shared.compliance.fairness_guard import FairnessGuard

logger = logging.getLogger(__name__)
_fairness_guard = FairnessGuard()

CACHE_TTL_HOURS = int(os.getenv("RUBRIC_CACHE_TTL_HOURS", "168"))
VARIATION_THRESHOLD = float(os.getenv("RUBRIC_VARIATION_THRESHOLD", "10.0"))

import threading


class RubricEvaluationCache:
    """
    Thread-safe in-memory cache for rubric evaluations to ensure consistency.
    Uses hash of stable candidate fields + requirements as key.
    
    For production, replace with Redis implementation.
    """
    
    def __init__(self, ttl_hours: int = CACHE_TTL_HOURS):
        self._cache: dict[str, tuple[RubricEvaluationResult, datetime]] = {}
        self._ttl = timedelta(hours=ttl_hours)
        self._variation_log: list[dict[str, Any]] = []
        self._lock = threading.RLock()
    
    def _extract_stable_candidate_fields(self, candidate_data: dict[str, Any]) -> dict[str, Any]:
        """Extract only stable fields from candidate data for cache key generation."""
        stable_fields = [
            "id", "candidate_id", "name", "email",
            "current_title", "current_company", "years_of_experience",
            "seniority_level", "technical_skills", "skills", "soft_skills",
            "certifications", "languages", "education", "experience",
            "city", "state", "country", "cv_text", "cv_content"
        ]
        return {k: v for k, v in candidate_data.items() if k in stable_fields and v is not None}
    
    def _generate_cache_key(
        self, 
        candidate_data: dict[str, Any], 
        requirements: list[Any],
        job_id: str | None = None,
        calibration_version: int | None = None
    ) -> str:
        """Generate a unique hash key for candidate + requirements + job + calibration version."""
        stable_data = self._extract_stable_candidate_fields(candidate_data)
        candidate_str = json.dumps(stable_data, sort_keys=True, default=str)
        
        effective_job_id = job_id or candidate_data.get("job_id") or candidate_data.get("job_vacancy_id") or "no_job"
        
        cal_version = calibration_version if calibration_version is not None else 0
        
        requirements_str = json.dumps(
            [
                {
                    "req": r.requirement, 
                    "priority": r.priority.value,
                    "desc": getattr(r, 'description', '') or ''
                } 
                for r in requirements
            ],
            sort_keys=True
        )
        combined = f"job:{effective_job_id}|cal_v:{cal_version}|{candidate_str}|{requirements_str}"
        return hashlib.sha256(combined.encode()).hexdigest()[:32]
    
    def get(
        self, 
        candidate_data: dict[str, Any], 
        requirements: list[Any],
        calibration_version: int | None = None
    ) -> RubricEvaluationResult | None:
        """Get cached evaluation if exists and not expired. Thread-safe.
        
        Args:
            calibration_version: If provided, includes in cache key to invalidate on calibration changes
        """
        key = self._generate_cache_key(
            candidate_data, requirements, 
            calibration_version=calibration_version
        )
        
        with self._lock:
            if key in self._cache:
                result, cached_at = self._cache[key]
                if datetime.utcnow() - cached_at < self._ttl:
                    logger.info(f"Cache HIT for rubric evaluation (key={key[:8]}...)")
                    return result
                else:
                    del self._cache[key]
                    logger.info(f"Cache EXPIRED for rubric evaluation (key={key[:8]}...)")
        
        return None
    
    def set(
        self, 
        candidate_data: dict[str, Any], 
        requirements: list[Any],
        result: RubricEvaluationResult,
        calibration_version: int | None = None
    ) -> None:
        """Cache an evaluation result. Thread-safe.
        
        Args:
            calibration_version: If provided, includes in cache key for proper invalidation
        """
        key = self._generate_cache_key(
            candidate_data, requirements,
            calibration_version=calibration_version
        )
        with self._lock:
            self._cache[key] = (result, datetime.utcnow())
        logger.info(f"Cache SET for rubric evaluation (key={key[:8]}..., score={result.score})")
    
    def log_variation(
        self,
        candidate_id: str,
        job_id: str,
        old_score: float,
        new_score: float,
        variation: float
    ) -> None:
        """Log when a re-evaluation produces a different score. Thread-safe."""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "candidate_id": candidate_id,
            "job_id": job_id,
            "old_score": old_score,
            "new_score": new_score,
            "variation": variation,
            "exceeds_threshold": abs(variation) > VARIATION_THRESHOLD
        }
        with self._lock:
            self._variation_log.append(entry)
        
        if abs(variation) > VARIATION_THRESHOLD:
            logger.warning(
                f"⚠️ VARIATION ALERT: Score changed by {variation:.1f} points "
                f"(old={old_score:.1f}, new={new_score:.1f}) for "
                f"candidate={candidate_id}, job={job_id}"
            )
        else:
            logger.info(
                f"Score variation within threshold: {variation:.1f} points "
                f"for candidate={candidate_id}, job={job_id}"
            )
    
    def get_variation_log(self) -> list[dict[str, Any]]:
        """Get the variation log for analysis. Thread-safe."""
        with self._lock:
            return self._variation_log.copy()
    
    def clear_expired(self) -> int:
        """Clear expired cache entries and return count of cleared entries. Thread-safe."""
        now = datetime.utcnow()
        with self._lock:
            expired_keys = [
                key for key, (_, cached_at) in self._cache.items()
                if now - cached_at >= self._ttl
            ]
            for key in expired_keys:
                del self._cache[key]
        return len(expired_keys)


class CalibrationFeedback:
    """
    Thread-safe system for collecting and applying recruiter feedback on rubric evaluations.
    Enables calibration loop to improve evaluation accuracy.
    
    Uses proper averaging with count tracking for statistical accuracy.
    Tracks version per job to enable cache invalidation when calibration changes.
    """
    
    def __init__(self):
        self._feedback_log: list[dict[str, Any]] = []
        self._calibration_adjustments: dict[str, dict[str, Any]] = {}
        self._lock = threading.RLock()
        self._redis_client = None  # lazy — fail-open se Redis ausente

    def _get_redis(self):
        """Lazy Redis client (sync). Retorna None se Redis indisponível (fail-open)."""
        if self._redis_client is not None:
            return self._redis_client
        try:
            import redis as _redis_lib  # noqa: PLC0415
            redis_url = os.environ.get("REDIS_URL")
            if not redis_url:
                try:
                    from app.core.config import settings as _s  # noqa: PLC0415
                    redis_url = getattr(_s, "REDIS_URL", None)
                except Exception:
                    pass
            if redis_url:
                self._redis_client = _redis_lib.from_url(
                    redis_url, decode_responses=True, socket_timeout=1
                )
        except Exception:
            pass
        return self._redis_client
    
    def get_calibration_version(self, job_id: str) -> int:
        """Get the calibration version for a job (incremented on each feedback).
        Lê Redis primeiro para sobreviver restarts (fail-open).
        """
        key = f"job:{job_id}"
        redis_key = f"calibration_adjustment:{job_id}"
        try:
            r = self._get_redis()
            if r:
                v = r.hget(redis_key, "version")
                if v is not None:
                    return int(float(v))
        except Exception:
            pass
        with self._lock:
            data = self._calibration_adjustments.get(key)
            return data.get("version", 0) if data else 0
    
    def record_feedback(
        self,
        evaluation_id: str,
        candidate_id: str,
        job_id: str,
        original_score: float,
        recruiter_adjusted_score: float | None,
        recruiter_decision: str,
        feedback_notes: str | None = None
    ) -> None:
        """
        Record recruiter feedback on an evaluation. Thread-safe.
        
        Args:
            evaluation_id: Unique ID of the evaluation
            candidate_id: Candidate being evaluated
            job_id: Job vacancy ID
            original_score: Score from LLM evaluation
            recruiter_adjusted_score: Score recruiter would give (optional)
            recruiter_decision: approved, rejected, needs_review
            feedback_notes: Optional notes from recruiter
        """
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "evaluation_id": evaluation_id,
            "candidate_id": candidate_id,
            "job_id": job_id,
            "original_score": original_score,
            "recruiter_adjusted_score": recruiter_adjusted_score,
            "recruiter_decision": recruiter_decision,
            "feedback_notes": feedback_notes,
            "score_delta": (
                recruiter_adjusted_score - original_score 
                if recruiter_adjusted_score is not None else None
            )
        }
        
        with self._lock:
            self._feedback_log.append(entry)
        
        logger.info(
            f"Calibration feedback recorded: candidate={candidate_id}, "
            f"original={original_score:.1f}, adjusted={recruiter_adjusted_score}, "
            f"decision={recruiter_decision}"
        )
        
        if recruiter_adjusted_score is not None:
            self._update_calibration_adjustments(job_id, original_score, recruiter_adjusted_score)
    
    def _update_calibration_adjustments(
        self,
        job_id: str,
        original: float,
        adjusted: float,
    ) -> None:
        """Update running calibration adjustment for a job using proper averaging.
        Persiste no Redis para sobreviver restarts (fail-open).
        """
        key = f"job:{job_id}"
        redis_key = f"calibration_adjustment:{job_id}"
        delta = adjusted - original

        with self._lock:
            if key not in self._calibration_adjustments:
                self._calibration_adjustments[key] = {"sum": delta, "count": 1, "avg": delta, "version": 1}
            else:
                data = self._calibration_adjustments[key]
                data["sum"] += delta
                data["count"] += 1
                data["avg"] = data["sum"] / data["count"]
                data["version"] = data.get("version", 0) + 1
            snapshot = dict(self._calibration_adjustments[key])

        # persist to Redis (fail-open — indisponível não bloqueia o feedback)
        try:
            r = self._get_redis()
            if r:
                r.hset(redis_key, mapping={k: str(v) for k, v in snapshot.items()})
                r.expire(redis_key, _CALIBRATION_REDIS_TTL)
        except Exception as _redis_err:
            logger.debug("[CalibrationFeedback] Redis write failed (fail-open): %s", _redis_err)

    def get_calibration_adjustment(self, job_id: str) -> float:
        """Get the calibration adjustment for a job based on feedback.
        Lê Redis primeiro (sobrevive restarts), fallback in-memory (fail-open).
        """
        key = f"job:{job_id}"
        redis_key = f"calibration_adjustment:{job_id}"

        try:
            r = self._get_redis()
            if r:
                raw = r.hgetall(redis_key)
                if raw and "avg" in raw:
                    avg = float(raw["avg"])
                    with self._lock:
                        if key not in self._calibration_adjustments:
                            self._calibration_adjustments[key] = {
                                "sum": float(raw.get("sum", avg)),
                                "count": int(float(raw.get("count", 1))),
                                "avg": avg,
                                "version": int(float(raw.get("version", 1))),
                            }
                    return avg
        except Exception as _redis_err:
            logger.debug("[CalibrationFeedback] Redis read failed (fallback in-memory): %s", _redis_err)

        with self._lock:
            data = self._calibration_adjustments.get(key)
            return data["avg"] if data else 0.0

    def get_feedback_stats(self, job_id: str | None = None) -> dict[str, Any]:
        """Get statistics about feedback for analysis. Thread-safe."""
        with self._lock:
            filtered = self._feedback_log.copy()
        
        if job_id:
            filtered = [f for f in filtered if f["job_id"] == job_id]
        
        if not filtered:
            return {"total_feedback": 0, "avg_delta": 0.0, "decision_distribution": {}}
        
        deltas = [f["score_delta"] for f in filtered if f["score_delta"] is not None]
        decisions = [f["recruiter_decision"] for f in filtered]
        
        with self._lock:
            calibration_data = self._calibration_adjustments.copy()
        
        return {
            "total_feedback": len(filtered),
            "avg_delta": sum(deltas) / len(deltas) if deltas else 0.0,
            "max_delta": max(deltas) if deltas else 0.0,
            "min_delta": min(deltas) if deltas else 0.0,
            "decision_distribution": {
                decision: decisions.count(decision) 
                for decision in set(decisions)
            },
            "calibration_adjustments": calibration_data
        }


evaluation_cache = RubricEvaluationCache()
calibration_feedback = CalibrationFeedback()
_CALIBRATION_REDIS_TTL = 30 * 24 * 3600  # 30 dias — sobrevive um mês de histórico


RUBRIC_EVALUATION_PROMPT = """You are an expert HR analyst evaluating a candidate's CV against specific job requirements.

## Your Task
Evaluate each requirement using the BARS (Behaviorally Anchored Rating Scale) methodology.

## CRITICAL RULES - DO NOT INFER
- DO NOT infer experience without EXPLICIT evidence in the CV
- If the candidate worked at a tech company, DO NOT assume they know programming
- If the candidate is a "Project Manager", DO NOT assume Agile/Scrum experience
- Each competency must have DIRECT, EXPLICIT evidence in the CV to be rated "meets" or "exceeds"
- When in doubt between two levels, ALWAYS choose the LOWER level
- If your analysis uses words like "probably", "suggests", "may have", "indicates" - classify as INFERRED evidence

## Evaluation Levels
- EXCEEDS (100 pts): Exceptional evidence with measurable results. Experience >50% above requirement. MUST have explicit, quantified evidence.
- MEETS (75 pts): Clearly and directly demonstrates the competency/experience. Specific examples present.
- PARTIAL (40 pts): Related but indirect evidence, or experience below requirement. May be implicit.
- MISSING (0 pts): No evidence found in the CV. Do NOT guess or assume.

## Evidence Types (MANDATORY for each requirement)
- EXPLICIT: Direct statement in CV (e.g., "5 years of Python", "Led team of 8")
- IMPLICIT: Reasonably derived from context (e.g., "Senior Developer at Google" implies coding skills)
- INFERRED: Weak connection, assumption-based (e.g., "worked in tech" → "may know Python")

## CV Content
{cv_content}

## Job Requirements to Evaluate
{requirements}

{criteria_examples}

## Instructions
For EACH requirement, provide:
1. The exact requirement text
2. The evaluation level (EXCEEDS, MEETS, PARTIAL, or MISSING)
3. The evidence type (EXPLICIT, IMPLICIT, or INFERRED)
4. A confidence score from 0.0 to 1.0 for your assessment
5. A specific quote or evidence from the CV that supports your evaluation
6. Brief reasoning for your evaluation

## Output Format (JSON)
Return a valid JSON object with this structure:
{{
    "evaluations": [
        {{
            "requirement": "requirement text",
            "priority": "essential|important|nice_to_have",
            "level": "exceeds|meets|partial|missing",
            "evidence_type": "explicit|implicit|inferred",
            "confidence": 0.85,
            "evidence": "Specific quote from CV...",
            "reasoning": "Brief explanation..."
        }}
    ],
    "strengths": ["strength 1", "strength 2"],
    "concerns": ["concern 1", "concern 2"],
    "overall_reasoning": "Overall assessment of candidate fit..."
}}

REMEMBER: Be precise. Cite specific evidence. If no evidence exists, say "No evidence found in CV" and use level "missing" with evidence_type "explicit" (explicit absence). Never fabricate or assume qualifications.
"""


def get_recommendation(score: float) -> str:
    """Get recommendation level based on score."""
    if score >= 85:
        return "Altamente Recomendado"
    elif score >= 70:
        return "Recomendado"
    elif score >= 55:
        return "Potencial"
    elif score >= 40:
        return "Baixo Match"
    else:
        return "Não Recomendado"


class RubricEvaluationService:
    """
    Service for evaluating candidates against job requirements using structured rubrics.
    
    Uses Claude AI for semantic analysis of CV content against requirements.
    """
    
    VAGUE_LANGUAGE_INDICATORS = [
        "pode ter", "indica que", "sugere", "provavelmente",
        "possivelmente", "talvez", "parece que", "aparentemente",
        "possibly", "probably", "suggests", "indicates", "may have",
        "might have", "could have", "seems to", "appears to",
        "likely", "presumably", "it seems", "one could infer",
    ]

    def __init__(self, llm_service: LLMService | None = None):
        self.llm_service = llm_service or LLMService()
    
    def _format_requirements_for_prompt(self, requirements: list[JobRequirementCreate]) -> str:
        """Format requirements for the LLM prompt."""
        lines = []
        for i, req in enumerate(requirements, 1):
            priority_label = {
                RequirementPriorityEnum.ESSENTIAL: "ESSENTIAL (3x weight)",
                RequirementPriorityEnum.IMPORTANT: "IMPORTANT (2x weight)",
                RequirementPriorityEnum.NICE_TO_HAVE: "NICE TO HAVE (1x weight)",
            }.get(req.priority, "IMPORTANT")
            
            lines.append(f"{i}. [{priority_label}] {req.requirement}")
            if req.description:
                lines.append(f"   Description: {req.description}")
        
        return "\n".join(lines)
    
    def _extract_cv_content(self, candidate_data: dict[str, Any]) -> str:
        """Extract relevant CV content from candidate data."""
        parts = []
        
        if candidate_data.get("current_title"):
            parts.append(f"Current Title: {candidate_data['current_title']}")
        
        if candidate_data.get("current_company"):
            parts.append(f"Current Company: {candidate_data['current_company']}")
        
        if candidate_data.get("years_of_experience"):
            parts.append(f"Years of Experience: {candidate_data['years_of_experience']}")
        
        if candidate_data.get("seniority_level"):
            parts.append(f"Seniority: {candidate_data['seniority_level']}")
        
        skills = candidate_data.get("technical_skills") or candidate_data.get("skills", [])
        if skills:
            parts.append(f"Technical Skills: {', '.join(skills)}")
        
        soft_skills = candidate_data.get("soft_skills", [])
        if soft_skills:
            parts.append(f"Soft Skills: {', '.join(soft_skills)}")
        
        certifications = candidate_data.get("certifications", [])
        if certifications:
            parts.append(f"Certifications: {', '.join(certifications)}")
        
        languages = candidate_data.get("languages", {})
        if languages:
            lang_list = [f"{k}: {v}" for k, v in languages.items()]
            parts.append(f"Languages: {', '.join(lang_list)}")
        
        location = []
        if candidate_data.get("location_city"):
            location.append(candidate_data["location_city"])
        if candidate_data.get("location_state"):
            location.append(candidate_data["location_state"])
        if candidate_data.get("location_country"):
            location.append(candidate_data["location_country"])
        if location:
            parts.append(f"Location: {', '.join(location)}")
        
        if candidate_data.get("is_remote"):
            parts.append("Available for remote work: Yes")
        
        education = candidate_data.get("education", [])
        if education:
            parts.append("\n--- Education ---")
            for edu in education[:5]:
                if isinstance(edu, dict):
                    edu_line = edu.get("degree", "") + " - " + edu.get("institution", "")
                    if edu.get("field_of_study"):
                        edu_line += f" ({edu['field_of_study']})"
                    parts.append(edu_line)
                else:
                    parts.append(str(edu))
        
        work_history = candidate_data.get("work_history", [])
        if work_history:
            parts.append("\n--- Work Experience ---")
            for exp in work_history[:10]:
                if isinstance(exp, dict):
                    exp_line = f"• {exp.get('title', 'N/A')} at {exp.get('company_name', 'N/A')}"
                    if exp.get("start_date") or exp.get("end_date"):
                        exp_line += f" ({exp.get('start_date', '')} - {exp.get('end_date', 'Present')})"
                    parts.append(exp_line)
                    if exp.get("description"):
                        parts.append(f"  {exp['description'][:500]}")
                    if exp.get("technologies"):
                        parts.append(f"  Technologies: {', '.join(exp['technologies'][:10])}")
        
        if candidate_data.get("resume_text"):
            parts.append("\n--- Resume Text ---")
            parts.append(candidate_data["resume_text"][:5000])
        
        if candidate_data.get("self_introduction"):
            parts.append("\n--- Self Introduction ---")
            parts.append(candidate_data["self_introduction"][:1000])
        
        return "\n".join(parts)

    async def _format_criteria_examples(self, requirements: list[JobRequirementCreate]) -> str:
        """Format evaluation criteria examples for prompt injection."""
        try:
            from app.core.database import AsyncSessionLocal
            from app.domains.cv_screening.services.evaluation_criteria_service import evaluation_criteria_service

            async with AsyncSessionLocal() as db:
                req_texts = [r.requirement for r in requirements]
                matches = await evaluation_criteria_service.get_criteria_for_requirements(db, req_texts)

                if not matches:
                    return ""

                lines = ["## Evidence Examples for Requirements"]
                for match in matches:
                    matched_criteria = match.get("matched_criteria", [])
                    if not matched_criteria:
                        continue
                    criteria = matched_criteria[0]
                    lines.append(f"\n### {match['requirement']}")
                    if criteria.positive_evidences:
                        lines.append("Strong evidence examples:")
                        for ev in criteria.positive_evidences[:3]:
                            lines.append(f"  ✓ {ev}")
                    if criteria.negative_evidences:
                        lines.append("Weak/insufficient evidence examples:")
                        for ev in criteria.negative_evidences[:3]:
                            lines.append(f"  ✗ {ev}")

                return "\n".join(lines)
        except Exception as e:
            logger.warning(f"Failed to load criteria examples: {e}")
            return ""

    def _detect_vague_language(self, evidence: str) -> bool:
        """Check evidence text for vague language indicators."""
        evidence_lower = evidence.lower()
        return any(indicator in evidence_lower for indicator in self.VAGUE_LANGUAGE_INDICATORS)

    def _detect_anomalies(self, evaluations: list[RequirementEvaluation], candidate_data: dict[str, Any]) -> list[str]:
        """Check for logical inconsistencies in evaluations."""
        anomalies = []
        skills = candidate_data.get("technical_skills") or candidate_data.get("skills", [])
        skills_count = len(skills) if isinstance(skills, list) else 0

        exceeds_count = sum(1 for e in evaluations if e.level == EvaluationLevelEnum.EXCEEDS)
        total_reqs = len(evaluations)

        if skills_count < 3 and exceeds_count > 3:
            anomalies.append(f"ANOMALY: {exceeds_count} exceeds ratings with only {skills_count} skills listed")

        if total_reqs > 0 and exceeds_count / total_reqs > 0.8:
            anomalies.append(f"ANOMALY: {exceeds_count}/{total_reqs} requirements rated exceeds (>80%)")

        inferred_meets = sum(
            1 for e in evaluations
            if e.level in [EvaluationLevelEnum.EXCEEDS, EvaluationLevelEnum.MEETS]
            and e.evidence_type == EvidenceType.INFERRED
        )
        if inferred_meets > 0:
            anomalies.append(f"ANOMALY: {inferred_meets} meets/exceeds ratings based on inferred evidence")

        yrs = candidate_data.get("years_of_experience")
        if yrs is not None and yrs < 2 and exceeds_count > 2:
            anomalies.append(f"ANOMALY: {exceeds_count} exceeds with only {yrs} years experience")

        return anomalies

    def _check_essential_exclusion(self, evaluations: list[RequirementEvaluation]) -> tuple[bool, list[str]]:
        """Check if candidate should be auto-excluded based on essential requirements."""
        exclusion_reasons = []

        essential_evals = [e for e in evaluations if e.priority == RequirementPriorityEnum.ESSENTIAL]

        for e in essential_evals:
            if e.level == EvaluationLevelEnum.MISSING:
                exclusion_reasons.append(
                    f"Requisito essencial não atendido: {e.requirement[:80]}"
                )
            elif e.evidence_type != EvidenceType.EXPLICIT and e.level in [EvaluationLevelEnum.PARTIAL, EvaluationLevelEnum.MEETS, EvaluationLevelEnum.EXCEEDS]:
                exclusion_reasons.append(
                    f"Requisito essencial com evidência {e.evidence_type.value} (requer explícita): {e.requirement[:80]}"
                )

        return len(exclusion_reasons) > 0, exclusion_reasons

    def _parse_llm_response(
        self, 
        response: str, 
        requirements: list[JobRequirementCreate]
    ) -> tuple[list[RequirementEvaluation], list[str], list[str], str]:
        """Parse LLM response into structured evaluation data."""
        try:
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            
            data = json.loads(response.strip())
            
            evaluations = []
            {req.requirement.lower(): req for req in requirements}
            
            for eval_data in data.get("evaluations", []):
                req_text = eval_data.get("requirement", "")
                priority_str = eval_data.get("priority", "important")
                level_str = eval_data.get("level", "missing").lower()
                evidence = eval_data.get("evidence", "No evidence found")
                reasoning = eval_data.get("reasoning", "")
                
                try:
                    priority = RequirementPriorityEnum(priority_str)
                except ValueError:
                    priority = RequirementPriorityEnum.IMPORTANT
                
                level_map = {
                    "exceeds": EvaluationLevelEnum.EXCEEDS,
                    "meets": EvaluationLevelEnum.MEETS,
                    "partial": EvaluationLevelEnum.PARTIAL,
                    "missing": EvaluationLevelEnum.MISSING,
                }
                level = level_map.get(level_str, EvaluationLevelEnum.MISSING)
                
                points_map = {
                    EvaluationLevelEnum.EXCEEDS: 100,
                    EvaluationLevelEnum.MEETS: 75,
                    EvaluationLevelEnum.PARTIAL: 40,
                    EvaluationLevelEnum.MISSING: 0,
                }
                points = points_map[level]
                
                multiplier_map = {
                    RequirementPriorityEnum.ESSENTIAL: 3,
                    RequirementPriorityEnum.IMPORTANT: 2,
                    RequirementPriorityEnum.NICE_TO_HAVE: 1,
                }
                multiplier = multiplier_map[priority]

                evidence_type_str = eval_data.get("evidence_type", "explicit").lower()
                evidence_type_map = {
                    "explicit": EvidenceType.EXPLICIT,
                    "implicit": EvidenceType.IMPLICIT,
                    "inferred": EvidenceType.INFERRED,
                }
                evidence_type = evidence_type_map.get(evidence_type_str, EvidenceType.INFERRED)

                confidence = float(eval_data.get("confidence", 1.0))
                confidence = max(0.0, min(1.0, confidence))

                vague_detected = self._detect_vague_language(evidence)
                if vague_detected and evidence_type != EvidenceType.INFERRED:
                    evidence_type = EvidenceType.INFERRED
                    confidence = min(confidence, 0.3)

                evaluations.append(RequirementEvaluation(
                    requirement=req_text,
                    priority=priority,
                    level=level,
                    evidence_type=evidence_type,
                    confidence=confidence,
                    points=points,
                    multiplier=multiplier,
                    weighted_points=points * multiplier,
                    max_weighted_points=100 * multiplier,
                    evidence=evidence,
                    reasoning=reasoning,
                    vague_language_detected=vague_detected,
                ))
            
            strengths = data.get("strengths", [])
            concerns = data.get("concerns", [])
            overall_reasoning = data.get("overall_reasoning", "")
            
            return evaluations, strengths, concerns, overall_reasoning
            
        except json.JSONDecodeError as e:
            logger.error("[RubricEval] Failed to parse LLM response as JSON: %s", e, exc_info=True)
            raise RubricEvaluationError(
                f"LLM response is not valid JSON: {e}"
            ) from e
        except Exception as e:
            logger.error("[RubricEval] Error parsing LLM response: %s", e, exc_info=True)
            raise RubricEvaluationError(
                f"LLM evaluation parse failed: {e}"
            ) from e
    
    def _fallback_evaluation(
        self, 
        requirements: list[JobRequirementCreate]
    ) -> tuple[list[RequirementEvaluation], list[str], list[str], str]:
        """Generate fallback evaluation when LLM fails."""
        evaluations = []
        
        for req in requirements:
            multiplier = {
                RequirementPriorityEnum.ESSENTIAL: 3,
                RequirementPriorityEnum.IMPORTANT: 2,
                RequirementPriorityEnum.NICE_TO_HAVE: 1,
            }.get(req.priority, 2)
            
            evaluations.append(RequirementEvaluation(
                requirement=req.requirement,
                priority=req.priority,
                level=EvaluationLevelEnum.PARTIAL,
                evidence_type=EvidenceType.INFERRED,
                confidence=0.0,
                points=40,
                multiplier=multiplier,
                weighted_points=40 * multiplier,
                max_weighted_points=100 * multiplier,
                evidence="Unable to evaluate - LLM analysis failed",
                reasoning="Fallback evaluation due to processing error",
                vague_language_detected=False,
            ))
        
        return (
            evaluations,
            [],
            ["Automated evaluation failed - manual review recommended"],
            "Evaluation could not be completed automatically. Please review manually."
        )
    
    EVIDENCE_WEIGHTS = {
        EvidenceType.EXPLICIT: 1.0,
        EvidenceType.IMPLICIT: 0.7,
        EvidenceType.INFERRED: 0.3,
    }

    def _calculate_score(self, evaluations: list[RequirementEvaluation]) -> tuple[float, float, float, float]:
        """Calculate the rubric score from evaluations using André's methodology.
        
        André's Formula:
          adjusted_score_i = points_i × evidence_weight_i
          total = Σ(adjusted_score_i × multiplier_i) / Σ(100 × multiplier_i) × 100
          
        Returns:
            Tuple of (final_score, total_weighted, max_possible, raw_score_before_adjustments)
            - final_score: After cap 99 + floor (integer rounding)
            - raw_score: Before cap/floor (for transparency)
        """
        if not evaluations:
            return 0.0, 0.0, 0.0, 0.0
        
        total_adjusted_weighted = 0.0
        max_possible = 0.0
        
        for e in evaluations:
            evidence_weight = self.EVIDENCE_WEIGHTS.get(e.evidence_type, 0.3)
            adjusted_points = e.points * evidence_weight
            total_adjusted_weighted += adjusted_points * e.multiplier
            max_possible += 100 * e.multiplier
        
        if max_possible == 0:
            return 0.0, total_adjusted_weighted, max_possible, 0.0
        
        raw_score = (total_adjusted_weighted / max_possible) * 100
        
        capped_score = min(99.0, raw_score)
        
        final_score = float(round(capped_score))
        final_score = max(0.0, final_score)
        
        return final_score, total_adjusted_weighted, max_possible, raw_score
    
    async def _call_llm_with_retry(
        self,
        prompt: str,
        max_retries: int = 3,
        initial_delay: float = 1.0,
    ) -> str | None:
        """
        Call LLM with retry logic and fallback to different providers.
        
        Attempts:
        1. Claude (up to max_retries times with exponential backoff)
        2. Gemini as fallback
        3. Returns None if all fail (caller should use fallback evaluation)
        """
        providers = ["claude", "gemini"]
        last_error = None
        
        for provider in providers:
            delay = initial_delay
            
            for attempt in range(max_retries):
                try:
                    logger.info(f"LLM call attempt {attempt + 1}/{max_retries} with {provider}")
                    response = await self.llm_service.generate(prompt, provider=provider)
                    
                    if response and response.strip():
                        logger.info(f"LLM call successful with {provider}")
                        return response
                    else:
                        logger.warning(f"Empty response from {provider}, retrying...")
                        
                except Exception as e:
                    last_error = e
                    logger.warning(
                        f"LLM call failed (attempt {attempt + 1}/{max_retries}, provider={provider}): {e}"
                    )
                    
                    if attempt < max_retries - 1:
                        await asyncio.sleep(delay)
                        delay *= 2
            
            logger.warning(f"All retries exhausted for {provider}, trying next provider...")
        
        logger.error(f"All LLM providers failed. Last error: {last_error}")
        return None

    async def evaluate_candidate(
        self,
        candidate_data: dict[str, Any],
        requirements: list[JobRequirementCreate],
        use_cache: bool = True,
        force_refresh: bool = False,
    ) -> RubricEvaluationResult:
        """
        Evaluate a candidate against job requirements using structured rubrics.
        
        Args:
            candidate_data: Dictionary with candidate information (from CV/profile)
            requirements: List of job requirements with priorities
            use_cache: Whether to use cached results (default True)
            force_refresh: Force re-evaluation even if cached (default False)
        
        Returns:
            RubricEvaluationResult with score, evaluations, and reasoning
        
        Enhanced Features:
            - Caching: Returns cached result if available (reduces LLM costs)
            - Variation logging: Logs score differences when force_refresh is used
            - Fallback: Returns basic evaluation if all LLM providers fail
        """
        if not requirements:
            return RubricEvaluationResult(
                score=0.0,
                raw_score=0.0,
                total_weighted_points=0.0,
                max_possible_points=0.0,
                evaluations=[],
                strengths=[],
                concerns=["No requirements provided for evaluation"],
                reasoning="Cannot evaluate without job requirements.",
                recommendation="Não Recomendado",
            )
        
        job_id = candidate_data.get("job_id") or candidate_data.get("job_vacancy_id")
        calibration_version = calibration_feedback.get_calibration_version(str(job_id)) if job_id else 0
        
        cached_result = None
        if use_cache and not force_refresh:
            cached_result = evaluation_cache.get(
                candidate_data, requirements, 
                calibration_version=calibration_version
            )
            if cached_result:
                return cached_result
        
        if force_refresh and use_cache:
            cached_result = evaluation_cache.get(
                candidate_data, requirements,
                calibration_version=calibration_version
            )
        
        cv_content = self._extract_cv_content(candidate_data)
        requirements_text = self._format_requirements_for_prompt(requirements)

        # SEG-3B: data minimization — remove PII/quasi-identifiers before LLM call (LGPD Art. 12)
        from app.shared.pii_masking import strip_pii_for_llm_prompt
        cv_content = strip_pii_for_llm_prompt(cv_content)

        criteria_examples = await self._format_criteria_examples(requirements)

        prompt = RUBRIC_EVALUATION_PROMPT.format(
            cv_content=cv_content,
            requirements=requirements_text,
            criteria_examples=criteria_examples,
        )

        # D.3 — Crença #11: Anti-sycophancy — enriquecer prompt com benchmark setorial
        _benchmark_ctx = sector_benchmark_service.get_benchmark_context(
            area=str(candidate_data.get("area", "")),
            seniority=str(candidate_data.get("seniority", "")),
        )
        if _benchmark_ctx:
            prompt = prompt + f"\n\n## Benchmark Setorial (anti-sycophancy)\n{_benchmark_ctx}"

        _llm_call_start = time.monotonic()
        response = await self._call_llm_with_retry(prompt)
        _llm_latency_ms = (time.monotonic() - _llm_call_start) * 1000

        if response:
            evaluations, strengths, concerns, reasoning = self._parse_llm_response(
                response, requirements
            )
        else:
            logger.error("All LLM attempts failed, using fallback evaluation")
            evaluations, strengths, concerns, reasoning = self._fallback_evaluation(requirements)

        candidate_id_str = str(candidate_data.get("id", candidate_data.get("candidate_id", "unknown")))
        anomaly_flags = self._detect_anomalies(evaluations, candidate_data)
        if anomaly_flags:
            logger.warning(f"⚠️ Anomalies detected for candidate {candidate_id_str}: {anomaly_flags}")

        auto_excluded, exclusion_reasons = self._check_essential_exclusion(evaluations)
        if auto_excluded:
            logger.info(f"🚫 Candidate {candidate_id_str} auto-excluded: {exclusion_reasons}")

        final_score, total_weighted, max_possible, raw_score_before = self._calculate_score(evaluations)
        
        calibration_adjustment = 0.0
        if job_id:
            calibration_adjustment = calibration_feedback.get_calibration_adjustment(str(job_id))
        
        calibrated_score = min(99.0, max(0.0, final_score + calibration_adjustment))
        calibrated_score = float(round(calibrated_score))
        
        if auto_excluded:
            calibrated_score = 0.0
        
        recommendation = get_recommendation(calibrated_score)
        
        methodology_notes = []
        if abs(raw_score_before - calibrated_score) > 0.5:
            methodology_notes.append(
                f"Score bruto: {raw_score_before:.1f} → ajustado: {calibrated_score:.0f} "
                f"(evidence weights + cap 99 + floor)"
            )
        
        calibration_applied = abs(calibration_adjustment) > 0.01
        if calibration_applied:
            methodology_notes.append(
                f"Calibração: {calibration_adjustment:+.1f} pts "
                f"({calibration_feedback.get_feedback_stats(str(job_id)).get('total_feedback', 0)} feedbacks)"
            )
        
        if auto_excluded:
            methodology_notes.append(
                f"Auto-exclusão: {'; '.join(exclusion_reasons[:3])}"
            )
        
        reasoning_final = reasoning
        if methodology_notes:
            reasoning_final = f"{reasoning}\n\n[André Methodology: {' | '.join(methodology_notes)}]"

        # FairnessGuard — verificar texto gerado pelo LLM antes de retornar ao recrutador
        _fairness_warnings: list = []
        _guard_result = _fairness_guard.check(reasoning_final)
        _candidate_id_log = candidate_data.get("id", candidate_data.get("candidate_id", "unknown"))
        if _guard_result.is_blocked:
            logger.warning(
                "FairnessGuard bloqueou reasoning em evaluate_candidate: candidate=%s category=%s terms=%s",
                _candidate_id_log, _guard_result.category, _guard_result.blocked_terms,
            )
            reasoning_final = "[Avaliação sob revisão — conteúdo sinalizado pelo FairnessGuard para análise de possível viés discriminatório.]"
        else:
            _fairness_warnings.extend(_fairness_guard.check_implicit_bias(reasoning_final))
        # Verificar strengths e concerns (soft warning apenas)
        for _text in (strengths + concerns):
            _fairness_warnings.extend(_fairness_guard.check_implicit_bias(_text))

        # C.2 — Crença #9: log estruturado de consumo de tokens para observabilidade
        _company_id_log = str(candidate_data.get("company_id", ""))
        if _company_id_log:
            _estimated_input_tokens = len(prompt) // 4
            _estimated_output_tokens = len(response) // 4 if response else 0
            logger.info(
                "token_usage company_id=%s candidate=%s agent=rubric_evaluation model=claude "
                "input_tokens_est=%d output_tokens_est=%d latency_ms=%.0f",
                _company_id_log, _candidate_id_log,
                _estimated_input_tokens, _estimated_output_tokens, _llm_latency_ms,
            )

        # C.3 — FairnessGuard Camada 3: check_with_layer3 seletivo (ACH-026)
        # Executa quando Camadas 1+2 não bloquearam e texto é longo o suficiente.
        # check_with_layer3 usa Haiku (custo baixo), cache Redis 1h e action_type gating.
        if not _guard_result.is_blocked and len(reasoning_final) > 200:
            try:
                _l3_result = await _fairness_guard.check_with_layer3(
                    reasoning_final, action_type="wsi_score"
                )
                if _l3_result.soft_warnings:
                    _fairness_warnings.extend(_l3_result.soft_warnings)
                    logger.info(
                        "FairnessGuard Camada 3: %d avisos semânticos para candidate=%s",
                        len(_l3_result.soft_warnings), _candidate_id_log,
                    )
                if _l3_result.is_blocked:
                    logger.warning(
                        "FairnessGuard Camada 3 bloqueou reasoning: candidate=%s category=%s",
                        _candidate_id_log, _l3_result.category,
                    )
                    reasoning_final = (
                        "[Avaliação sob revisão — conteúdo sinalizado pela "
                        "Camada 3 do FairnessGuard para análise de possível viés discriminatório.]"
                    )
            except Exception as _l3_exc:
                logger.debug("FairnessGuard Camada 3 indisponível: %s", _l3_exc)

        result = RubricEvaluationResult(
            score=calibrated_score,
            raw_score=round(raw_score_before, 2),
            total_weighted_points=total_weighted,
            max_possible_points=max_possible,
            evaluations=evaluations,
            strengths=strengths,
            concerns=concerns,
            reasoning=reasoning_final,
            recommendation=recommendation,
            anomaly_flags=anomaly_flags,
            auto_excluded=auto_excluded,
            exclusion_reasons=exclusion_reasons,
            scoring_methodology="andre_v1",
            fairness_warnings=_fairness_warnings,
        )
        
        if use_cache:
            evaluation_cache.set(
                candidate_data, requirements, result,
                calibration_version=calibration_version
            )
        
        if force_refresh and cached_result:
            variation = result.score - cached_result.score
            candidate_id = candidate_data.get("id", candidate_data.get("candidate_id", "unknown"))
            log_job_id = str(job_id) if job_id else "unknown"
            evaluation_cache.log_variation(
                candidate_id=str(candidate_id),
                job_id=log_job_id,
                old_score=cached_result.score,
                new_score=result.score,
                variation=variation
            )
        
        return result
    
    async def batch_evaluate(
        self,
        candidates: list[dict[str, Any]],
        requirements: list[JobRequirementCreate],
        sort_by_score: bool = True,
    ) -> list[tuple[dict[str, Any], RubricEvaluationResult]]:
        """
        Evaluate multiple candidates against the same job requirements.
        
        Args:
            candidates: List of candidate data dictionaries
            requirements: Job requirements to evaluate against
            sort_by_score: Whether to sort results by score descending
        
        Returns:
            List of tuples (candidate_data, RubricEvaluationResult)
        """
        results = []
        
        for candidate in candidates:
            try:
                result = await self.evaluate_candidate(candidate, requirements)
                results.append((candidate, result))
            except RubricEvaluationError as e:
                logger.error(
                    "[RubricEval] Candidate evaluation FAILED (no score produced): %s",
                    e, exc_info=True,
                )
                results.append((candidate, None))
            except Exception as e:
                logger.error("[RubricEval] Unexpected error evaluating candidate: %s", e, exc_info=True)
                raise
        
        if sort_by_score:
            results.sort(key=lambda x: x[1].score if x[1] is not None else -1, reverse=True)
        
        return results
    
    def to_legacy_format(self, result: RubricEvaluationResult) -> LegacyScoreWrapper:
        """
        Convert RubricEvaluationResult to legacy LIA Score format.
        Maintains backward compatibility during transition.
        """
        return LegacyScoreWrapper.from_rubric_result(result)
    
    def _get_score_label(self, score: float) -> str:
        """Get human-readable score label based on score value."""
        if score >= 85:
            return "Altamente Recomendado"
        elif score >= 70:
            return "Forte"
        elif score >= 55:
            return "Médio"
        elif score >= 40:
            return "Fraco"
        else:
            return "Baixo Match"
    
    def _get_recommendation_action(self, score: float) -> str:
        """Get recommended action based on score value."""
        if score >= 85:
            return "interview"
        elif score >= 70:
            return "interview"
        elif score >= 55:
            return "review"
        else:
            return "reject"
    
    async def evaluate_and_create_activity(
        self,
        candidate_id: str,
        candidate_name: str,
        candidate_data: dict[str, Any],
        job_id: str,
        job_title: str,
        job_code: str | None,
        requirements: list[JobRequirementCreate],
        company_id: str,
        created_by: str | None = None,
        db=None,
    ) -> RubricEvaluationResult | None:
        """
        Evaluate a candidate against job requirements and create an activity feed entry.

        This method combines evaluation and activity creation in a single workflow.
        If evaluation fails, logs the error but does not raise an exception.

        Args:
            candidate_id: ID of the candidate being evaluated
            candidate_name: Name of the candidate
            candidate_data: Dictionary with candidate CV/profile information
            job_id: ID of the job vacancy
            job_title: Title of the job vacancy
            job_code: Optional job code/reference
            requirements: List of job requirements with priorities
            company_id: Company ID for multi-tenant isolation
            created_by: Optional ID of who triggered the evaluation
            db: AsyncSession opcional para verificação de consentimento granular (D5).

        Returns:
            RubricEvaluationResult if successful, None if evaluation failed
        """
        from app.domains.analytics.services.activity_service import activity_service

        # D5-G2 — Verificação de consentimento granular ai_screening (LGPD Art. 7)
        # Fail-open: se serviço indisponível ou db=None, avaliação prossegue normalmente.
        if db is not None:
            try:
                from app.shared.services.granular_consent_service import GranularConsentService
                _consent_svc = GranularConsentService(db)
                _has_consent = await _consent_svc.check_purpose(
                    candidate_id, company_id, "ai_screening"
                )
                if not _has_consent:
                    logger.warning(
                        "[RubricEval] Candidato %s não consentiu com ai_screening "
                        "(company=%s) — avaliação bloqueada (D5)",
                        candidate_id, company_id,
                    )
                    return None
            except Exception as _exc:
                logger.debug(
                    "[RubricEval] consent check falhou (fail-open): %s", _exc
                )
                # fail-open: continua avaliação normalmente

        try:
            result = await self.evaluate_candidate(candidate_data, requirements)
            
            score_label = self._get_score_label(result.score)
            recommendation = self._get_recommendation_action(result.score)
            
            evaluations_data = []
            for e in result.evaluations:
                evaluations_data.append({
                    "requirement": e.requirement,
                    "priority": e.priority.value if hasattr(e.priority, 'value') else str(e.priority),
                    "level": e.level.value if hasattr(e.level, 'value') else str(e.level),
                    "points": e.points,
                    "weighted_points": e.weighted_points,
                    "evidence": e.evidence,
                    "reasoning": e.reasoning,
                })
            
            try:
                activity_service.db = None
                activity_service.company_id = company_id
                
                await activity_service.create_rubric_evaluation_activity(
                    candidate_id=candidate_id,
                    candidate_name=candidate_name,
                    job_id=job_id,
                    job_title=job_title,
                    job_code=job_code,
                    score=result.score,
                    score_label=score_label,
                    evaluations=evaluations_data,
                    summary=result.reasoning,
                    recommendation=recommendation,
                    strengths=result.strengths,
                    concerns=result.concerns,
                    created_by=created_by,
                )
                
                try:
                    notification_service = NotificationService()
                    
                    notification_title = f"Análise CV Concluída - {candidate_name}"
                    notification_message = (
                        f"Score: {result.score:.0f}% ({score_label})\n"
                        f"Recomendação: {result.recommendation}\n"
                        f"Vaga: {job_title}"
                    )
                    if job_code:
                        notification_message += f" ({job_code})"
                    
                    notification_message += "\n\nCandidato pendente de aprovação para agendamento de entrevista."
                    
                    action_url = f"/funil-de-talentos/candidato/{candidate_id}?job={job_id}"
                    
                    target_user_id = created_by or "recruiter"
                    
                    await notification_service.create_notification(
                        user_id=target_user_id,
                        title=notification_title,
                        message=notification_message,
                        notification_type=NotificationType.ACTION_REQUIRED,
                        category="proactive_recommendation",
                        source_agent="rubric_evaluation",
                        source_trigger="cv_analysis_completed",
                        related_job_id=job_id,
                        related_candidate_id=candidate_id,
                        action_url=action_url,
                        action_label="Ver Análise Completa",
                        channels=[NotificationChannel.BELL.value, NotificationChannel.TEAMS.value],
                        metadata={
                            "candidate_name": candidate_name,
                            "job_title": job_title,
                            "job_code": job_code,
                            "score": result.score,
                            "score_label": score_label,
                            "recommendation": result.recommendation,
                            "strengths": result.strengths[:3] if result.strengths else [],
                            "concerns": result.concerns[:3] if result.concerns else [],
                        }
                    )
                    
                    logger.info(
                        f"🔔 Notification sent for rubric evaluation: "
                        f"candidate={candidate_name}, score={result.score:.1f}%"
                    )
                    
                except Exception as notif_err:
                    logger.warning(
                        f"⚠️ Rubric evaluation succeeded but notification creation failed: {notif_err}"
                    )
                
                logger.info(
                    f"✅ Rubric evaluation completed and activity created: "
                    f"candidate={candidate_id}, job={job_id}, score={result.score:.1f}%"
                )
                
            except Exception as activity_err:
                logger.warning(
                    f"⚠️ Rubric evaluation succeeded but activity creation failed: {activity_err}"
                )
            
            return result
            
        except Exception as e:
            logger.error(
                f"❌ Rubric evaluation failed for candidate={candidate_id}, job={job_id}: {e}",
                exc_info=True
            )
            return None
    
    def record_calibration_feedback(
        self,
        evaluation_id: str,
        candidate_id: str,
        job_id: str,
        original_score: float,
        recruiter_adjusted_score: float | None = None,
        recruiter_decision: str = "needs_review",
        feedback_notes: str | None = None
    ) -> None:
        """
        Record recruiter feedback for calibration.
        
        Args:
            evaluation_id: Unique ID of the evaluation
            candidate_id: Candidate being evaluated
            job_id: Job vacancy ID
            original_score: Score from automated evaluation
            recruiter_adjusted_score: Score recruiter would give (optional)
            recruiter_decision: approved, rejected, needs_review
            feedback_notes: Optional notes from recruiter
        """
        calibration_feedback.record_feedback(
            evaluation_id=evaluation_id,
            candidate_id=candidate_id,
            job_id=job_id,
            original_score=original_score,
            recruiter_adjusted_score=recruiter_adjusted_score,
            recruiter_decision=recruiter_decision,
            feedback_notes=feedback_notes
        )
    
    def get_calibration_stats(self, job_id: str | None = None) -> dict[str, Any]:
        """Get calibration statistics for analysis."""
        return calibration_feedback.get_feedback_stats(job_id)
    
    def get_variation_log(self) -> list[dict[str, Any]]:
        """Get the log of score variations for analysis."""
        return evaluation_cache.get_variation_log()
    
    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        return {
            "cached_evaluations": len(evaluation_cache._cache),
            "variation_entries": len(evaluation_cache._variation_log),
            "ttl_hours": CACHE_TTL_HOURS,
            "variation_threshold": VARIATION_THRESHOLD
        }
    
    def clear_cache(self) -> int:
        """Clear expired cache entries and return count."""
        return evaluation_cache.clear_expired()

    async def evaluate_candidate_cv(
        self,
        cv_content: str,
        requirements: list[JobRequirementCreate],
        job_id: str | None = None,
    ) -> RubricEvaluationResult:
        """
        Evaluate raw CV text against job requirements.

        Convenience wrapper over evaluate_candidate() for callers that have
        cv_content as a string rather than a full candidate data dict (e.g.
        conversation_manager.py).  FairnessGuard is applied via the underlying
        evaluate_candidate() call.

        Args:
            cv_content: Raw text extracted from the candidate CV.
            requirements: Job requirements to evaluate against.
            job_id: Optional job vacancy ID (used for calibration).

        Returns:
            RubricEvaluationResult with score, evaluations, reasoning and
            fairness_warnings populated by FairnessGuard.
        """
        candidate_data: dict[str, Any] = {"cv_content": cv_content}
        if job_id:
            candidate_data["job_id"] = job_id
        return await self.evaluate_candidate(candidate_data, requirements, use_cache=False)


rubric_evaluation_service = RubricEvaluationService()


def get_rubric_evaluation_service() -> RubricEvaluationService:
    return rubric_evaluation_service
