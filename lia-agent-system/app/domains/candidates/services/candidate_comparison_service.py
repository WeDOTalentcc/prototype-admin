"""
Candidate Comparison Service - Compare candidates for job vacancies.

This service compares candidates using scenario-based weights:
- Scenario A: Screened candidates (all have WSI) - Rubricas 40%, WSI 25%, Big Five 15%, Pre-req 10%, Historico 10%
- Scenario B: Non-screened candidates (CV only) - Rubricas 60%, Pre-req 25%, Historico 15%
- Scenario C: General comparison without job - Historico 50%, Completude 30%, Recency 20%
"""
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, StrEnum
from typing import Any, Literal

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.cv_screening.services.score_normalization_service import score_normalization_service
from app.domains.cv_screening.services.seniority_utils import normalize_seniority
from lia_models.candidate import Candidate, VacancyCandidate
from lia_models.job_vacancy import JobVacancy
from lia_models.voice_screening import VoiceScreeningAnalysis, VoiceScreeningCall
from app.domains.ai.services.llm import llm_service

logger = logging.getLogger(__name__)


class ComparisonScenario(StrEnum):
    """Comparison scenario types based on available data."""
    SCENARIO_A = "scenario_a"  # All candidates screened (WSI completed)
    SCENARIO_B = "scenario_b"  # Non-screened candidates (CV only)
    SCENARIO_C = "scenario_c"  # General comparison without job context


@dataclass
class ScenarioWeights:
    """Weight configuration for each comparison scenario."""
    rubricas: float = 0.0
    wsi: float = 0.0
    big_five: float = 0.0
    pre_requisitos: float = 0.0
    historico: float = 0.0
    completude: float = 0.0
    recency: float = 0.0
    
    @classmethod
    def for_scenario_a(cls) -> "ScenarioWeights":
        """Scenario A: Screened candidates with WSI."""
        return cls(
            rubricas=0.40,
            wsi=0.25,
            big_five=0.15,
            pre_requisitos=0.10,
            historico=0.10
        )
    
    @classmethod
    def for_scenario_b(cls) -> "ScenarioWeights":
        """Scenario B: Non-screened candidates (CV only)."""
        return cls(
            rubricas=0.60,
            pre_requisitos=0.25,
            historico=0.15
        )
    
    @classmethod
    def for_scenario_c(cls) -> "ScenarioWeights":
        """Scenario C: General comparison without job context."""
        return cls(
            historico=0.50,
            completude=0.30,
            recency=0.20
        )
    
    def to_dict(self) -> dict[str, float]:
        """Convert weights to dictionary with non-zero values only."""
        weights = {
            "rubricas": self.rubricas,
            "wsi": self.wsi,
            "big_five": self.big_five,
            "pre_requisitos": self.pre_requisitos,
            "historico": self.historico,
            "completude": self.completude,
            "recency": self.recency,
        }
        return {k: v for k, v in weights.items() if v > 0}


@dataclass
class DimensionScore:
    """Score for a single dimension."""
    dimension: str
    score: float
    weight: float
    weighted_score: float
    details: str | None = None


@dataclass
class CandidateComparisonResult:
    """Result of comparing candidates."""
    comparison_id: str
    winner: str | None
    winner_name: str | None
    confidence: float
    scenario: ComparisonScenario
    scenario_description: str
    methodology_used: list[str]
    data_completeness: dict[str, dict[str, bool]]
    weights_used: dict[str, float]
    dimension_comparison: dict[str, dict[str, Any]]
    candidate_scores: dict[str, float]
    analysis: str
    scenarios_recommendation: list[dict[str, Any]]
    generated_at: str
    
    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "comparison_id": self.comparison_id,
            "winner": self.winner,
            "winner_name": self.winner_name,
            "confidence": round(self.confidence, 2),
            "scenario": self.scenario.value,
            "scenario_description": self.scenario_description,
            "methodology_used": self.methodology_used,
            "data_completeness": self.data_completeness,
            "weights_used": self.weights_used,
            "dimension_comparison": self.dimension_comparison,
            "candidate_scores": {k: round(v, 2) for k, v in self.candidate_scores.items()},
            "analysis": self.analysis,
            "scenarios_recommendation": self.scenarios_recommendation,
            "generated_at": self.generated_at,
        }


class CandidateComparisonService:
    """
    Service for comparing candidates based on scenario-specific weights.
    
    Scenarios:
    - A: All candidates have WSI (voice screening) data
    - B: Candidates have CV data but no WSI
    - C: General comparison without specific job vacancy
    """
    
    async def compare_candidates(
        self,
        db: AsyncSession,
        candidate_ids: list[str],
        job_id: str | None = None,
        force_scenario: Literal["A", "B", "C"] | None = None
    ) -> dict[str, Any]:
        """
        Compare multiple candidates and determine the best fit.
        
        Args:
            db: Database session
            candidate_ids: List of candidate IDs to compare
            job_id: Optional job vacancy ID for context
            force_scenario: Force a specific scenario (A, B, or C)
            
        Returns:
            Comparison result with winner, confidence, and detailed analysis
        """
        if len(candidate_ids) < 2:
            raise ValueError("At least 2 candidates are required for comparison")
        
        candidates = await self._get_candidates(db, candidate_ids)
        if len(candidates) < 2:
            raise ValueError("Could not find enough candidates for comparison")
        
        job = None
        if job_id:
            job = await self._get_job(db, job_id)
        
        wsi_data = {}
        vacancy_candidates = {}
        if job_id:
            for candidate in candidates:
                vc = await self._get_vacancy_candidate(db, str(candidate.id), job_id)
                if vc:
                    vacancy_candidates[str(candidate.id)] = vc
                
                wsi = await self._get_wsi_data(
                    db, 
                    str(candidate.id), 
                    job,
                    vacancy_candidates.get(str(candidate.id))
                )
                if wsi:
                    wsi_data[str(candidate.id)] = wsi
        
        if job_id and len(wsi_data) >= 2:
            wsi_data = await self._apply_score_normalization(db, job_id, wsi_data)
        
        scenario = await self._detect_scenario(
            candidates=candidates,
            job=job,
            wsi_data=wsi_data,
            vacancy_candidates=vacancy_candidates,
            force_scenario=force_scenario
        )
        
        weights = self._get_weights_for_scenario(scenario)
        
        dimension_scores = await self._calculate_dimension_scores(
            candidates=candidates,
            job=job,
            wsi_data=wsi_data,
            scenario=scenario,
            weights=weights
        )
        
        candidate_totals = self._calculate_total_scores(dimension_scores)
        
        llm_analysis = await self._generate_llm_analysis(
            candidates=candidates,
            job=job,
            wsi_data=wsi_data,
            scenario=scenario,
            dimension_scores=dimension_scores,
            candidate_totals=candidate_totals
        )
        
        winner_id, confidence = self._determine_winner(candidate_totals)
        winner_name = None
        for candidate in candidates:
            if str(candidate.id) == winner_id:
                winner_name = str(candidate.name) if candidate.name else None
                break
        
        comparison_id = f"comp_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{len(candidates)}"
        
        methodology_used = self._get_methodology_for_scenario(scenario)
        
        data_completeness = self._build_data_completeness(
            candidates=candidates,
            wsi_data=wsi_data
        )
        
        result = CandidateComparisonResult(
            comparison_id=comparison_id,
            winner=winner_id,
            winner_name=winner_name,
            confidence=confidence,
            scenario=scenario,
            scenario_description=self._get_scenario_description(scenario),
            methodology_used=methodology_used,
            data_completeness=data_completeness,
            weights_used=weights.to_dict(),
            dimension_comparison=dimension_scores,
            candidate_scores=candidate_totals,
            analysis=llm_analysis.get("analysis", ""),
            scenarios_recommendation=llm_analysis.get("recommendations", []),
            generated_at=datetime.utcnow().isoformat()
        )
        
        logger.info(
            f"Comparison completed: {len(candidates)} candidates, "
            f"scenario={scenario.value}, winner={winner_id}, confidence={confidence:.2f}"
        )
        
        return result.to_dict()
    
    async def _get_candidates(
        self,
        db: AsyncSession,
        candidate_ids: list[str]
    ) -> list[Candidate]:
        """Fetch candidates by IDs."""
        from app.domains.candidates.repositories.candidate_repository import (
            CandidateRepository,
        )
        repo = CandidateRepository(db)
        return await repo.list_by_ids(candidate_ids)

    async def _get_job(
        self,
        db: AsyncSession,
        job_id: str
    ) -> JobVacancy | None:
        """Fetch job vacancy by ID."""
        from app.domains.job_management.repositories.job_vacancy_crud_repository import (
            JobVacancyCRUDRepository,
        )
        repo = JobVacancyCRUDRepository(db)
        return await repo.get_vacancy_by_id(job_id)

    async def _get_vacancy_candidate(
        self,
        db: AsyncSession,
        candidate_id: str,
        vacancy_id: str
    ) -> VacancyCandidate | None:
        """Get VacancyCandidate record if exists."""
        from app.domains.candidates.repositories.vacancy_candidate_repository import (
            VacancyCandidateRepository,
        )
        repo = VacancyCandidateRepository(db)
        import uuid
        try:
            vacancy_uuid = uuid.UUID(str(vacancy_id))
        except (ValueError, TypeError):
            return None
        return await repo.get_by_vacancy_and_candidate(vacancy_uuid, candidate_id)
    
    async def _get_wsi_data(
        self, 
        db: AsyncSession, 
        candidate_id: str,
        job: JobVacancy | None = None,
        vacancy_candidate: VacancyCandidate | None = None
    ) -> dict[str, Any] | None:
        """
        Get WSI data for a candidate, prioritizing job-scoped data.
        
        Priority order:
        1. VacancyCandidate.wsi_score (if wsi_completed=True) - most reliable, job-scoped
        2. VoiceScreeningCall with matching job_title - fallback
        3. Most recent VoiceScreeningCall - last resort fallback
        
        Args:
            db: Database session
            candidate_id: The candidate's ID
            job: Optional job vacancy to scope the WSI search
            vacancy_candidate: Optional VacancyCandidate with job-scoped WSI data
            
        Returns:
            Dict with WSI data or None if not found
        """
        if vacancy_candidate and getattr(vacancy_candidate, 'wsi_completed', False):
            wsi_score = getattr(vacancy_candidate, 'wsi_score', None)
            if wsi_score is not None:
                logger.info(f"Using VacancyCandidate WSI for candidate {candidate_id}: score={wsi_score}")
                return {
                    "overall_score": wsi_score,
                    "source": "vacancy_candidate",
                    "job_scoped": True,
                    "tech_score": getattr(vacancy_candidate, 'wsi_tech_score', None),
                    "comm_score": getattr(vacancy_candidate, 'wsi_comm_score', None),
                    "fit_score": getattr(vacancy_candidate, 'wsi_fit_score', None),
                    "recommendation": getattr(vacancy_candidate, 'wsi_recommendation', None),
                    "key_strengths": getattr(vacancy_candidate, 'wsi_strengths', []) or [],
                    "key_concerns": getattr(vacancy_candidate, 'wsi_concerns', []) or [],
                    "summary": getattr(vacancy_candidate, 'wsi_summary', None),
                }
        
        # ADR-001-EXEMPT: legacy VoiceScreeningCall+VoiceScreeningAnalysis JOIN
        # with conditional ilike on job.title — fallback path only used when
        # VacancyCandidate.wsi_completed=False. WsiRepository is the canonical
        # path (handled higher up). These legacy tables have no dedicated repo
        # and only two callers (this file + analytics/candidate_report_service).
        base_query = (
            select(VoiceScreeningCall, VoiceScreeningAnalysis)
            .join(
                VoiceScreeningAnalysis,
                VoiceScreeningCall.id == VoiceScreeningAnalysis.screening_call_id,
                isouter=True
            )
            .where(VoiceScreeningCall.candidate_id == candidate_id)
            .where(VoiceScreeningCall.call_status == "completed")
        )
        
        if job and job.title:
            job_scoped_query = base_query.where(
                VoiceScreeningCall.job_title.ilike(f"%{job.title}%")
            ).order_by(VoiceScreeningCall.created_at.desc())
            
            result = await db.execute(job_scoped_query.limit(1))
            row = result.first()
            
            if row:
                logger.debug(
                    f"Found job-scoped WSI for candidate {candidate_id}, "
                    f"job title: {job.title}"
                )
                wsi_result = self._parse_wsi_result(row)
                if wsi_result:
                    wsi_result["source"] = "voice_screening_call"
                    wsi_result["job_scoped"] = True
                return wsi_result
            
            logger.debug(
                f"No job-scoped WSI found for candidate {candidate_id}, "
                f"job title: {job.title}. Falling back to most recent WSI."
            )
        
        fallback_query = base_query.order_by(VoiceScreeningCall.created_at.desc())
        result = await db.execute(fallback_query.limit(1))
        row = result.first()
        
        wsi_result = self._parse_wsi_result(row) if row else None
        if wsi_result:
            wsi_result["source"] = "voice_screening_call"
            wsi_result["job_scoped"] = False
        return wsi_result
    
    def _parse_wsi_result(
        self, 
        row: tuple | None
    ) -> dict[str, Any] | None:
        """
        Parse a WSI query result row into a structured dictionary.
        
        Args:
            row: Tuple of (VoiceScreeningCall, VoiceScreeningAnalysis) or None
            
        Returns:
            Dict with WSI data or None if row is invalid
        """
        if not row:
            return None
        
        call, analysis = row
        
        if not analysis:
            return None
        
        return {
            "call_id": str(call.id),
            "job_title": call.job_title,
            "overall_score": analysis.overall_score,
            "tech_score": analysis.tech_score,
            "comm_score": analysis.comm_score,
            "fit_score": analysis.fit_score,
            "recommendation": analysis.overall_recommendation,
            "key_strengths": analysis.key_strengths or [],
            "key_concerns": analysis.key_concerns or [],
            "summary": analysis.summary,
        }
    
    async def _detect_scenario(
        self,
        candidates: list[Candidate],
        job: JobVacancy | None,
        wsi_data: dict[str, Any],
        vacancy_candidates: dict[str, Any],
        force_scenario: str | None = None
    ) -> ComparisonScenario:
        """
        Auto-detect comparison scenario based on available data.
        
        - Scenario A: All candidates have VacancyCandidate for this job with wsi_completed=true
        - Scenario B: Job exists but not all candidates have completed WSI for this job
        - Scenario C: No job context
        """
        if force_scenario:
            scenario_map = {
                "A": ComparisonScenario.SCENARIO_A,
                "B": ComparisonScenario.SCENARIO_B,
                "C": ComparisonScenario.SCENARIO_C,
            }
            return scenario_map.get(force_scenario.upper(), ComparisonScenario.SCENARIO_C)
        
        if not job:
            logger.info("Scenario C detected: No job context")
            return ComparisonScenario.SCENARIO_C
        
        candidates_with_wsi_for_job = 0
        for c in candidates:
            cid = str(c.id)
            vc = vacancy_candidates.get(cid)
            if vc and getattr(vc, 'wsi_completed', False):
                candidates_with_wsi_for_job += 1
        
        if candidates_with_wsi_for_job == len(candidates):
            logger.info(f"Scenario A detected: All {len(candidates)} candidates have WSI completed for this job")
            return ComparisonScenario.SCENARIO_A
        
        logger.info(f"Scenario B detected: {candidates_with_wsi_for_job}/{len(candidates)} have WSI for this job")
        return ComparisonScenario.SCENARIO_B
    
    def _get_weights_for_scenario(self, scenario: ComparisonScenario) -> ScenarioWeights:
        """Get weight configuration for the given scenario."""
        if scenario == ComparisonScenario.SCENARIO_A:
            return ScenarioWeights.for_scenario_a()
        elif scenario == ComparisonScenario.SCENARIO_B:
            return ScenarioWeights.for_scenario_b()
        else:
            return ScenarioWeights.for_scenario_c()
    
    def _get_scenario_description(self, scenario: ComparisonScenario) -> str:
        """Get human-readable description of the scenario."""
        descriptions = {
            ComparisonScenario.SCENARIO_A: (
                "Cenário A: Candidatos triados na mesma vaga (todos têm WSI). "
                "Pesos: Rubricas 40%, WSI 25%, Big Five 15%, Pré-requisitos 10%, Histórico 10%"
            ),
            ComparisonScenario.SCENARIO_B: (
                "Cenário B: Candidatos não triados para a vaga (apenas CV). "
                "Pesos: Rubricas 60%, Pré-requisitos 25%, Histórico 15%"
            ),
            ComparisonScenario.SCENARIO_C: (
                "Cenário C: Comparação geral sem vaga específica. "
                "Pesos: Histórico 50%, Completude 30%, Recência 20%"
            ),
        }
        return descriptions.get(scenario, "Cenário não identificado")
    
    def _get_methodology_for_scenario(self, scenario: ComparisonScenario) -> list[str]:
        """Get list of methodologies used for the scenario."""
        if scenario == ComparisonScenario.SCENARIO_A:
            return ["rubricas_bars", "wsi", "big_five", "pre_requisitos", "historico"]
        elif scenario == ComparisonScenario.SCENARIO_B:
            return ["rubricas_bars", "pre_requisitos", "historico"]
        else:
            return ["historico", "completude", "recencia"]
    
    def _build_data_completeness(
        self,
        candidates: list[Candidate],
        wsi_data: dict[str, Any]
    ) -> dict[str, dict[str, bool]]:
        """Build data completeness map for each candidate."""
        completeness = {}
        for candidate in candidates:
            cid = str(candidate.id)
            has_cv = bool(candidate.resume_text or candidate.experience)
            has_wsi = cid in wsi_data
            has_big_five = bool(getattr(candidate, 'big_five_profile', None))
            
            completeness[cid] = {
                "cv": has_cv,
                "wsi": has_wsi,
                "big_five": has_big_five
            }
        return completeness
    
    async def _calculate_dimension_scores(
        self,
        candidates: list[Candidate],
        job: JobVacancy | None,
        wsi_data: dict[str, Any],
        scenario: ComparisonScenario,
        weights: ScenarioWeights
    ) -> dict[str, dict[str, Any]]:
        """Calculate scores for each dimension per candidate."""
        dimension_scores = {}
        
        for candidate in candidates:
            cid = str(candidate.id)
            scores = {}
            
            if weights.rubricas > 0:
                scores["rubricas"] = self._calculate_rubricas_score(candidate, job)
            
            if weights.wsi > 0:
                wsi = wsi_data.get(cid)
                scores["wsi"] = self._calculate_wsi_score(wsi) if wsi else 0.0
            
            if weights.big_five > 0:
                scores["big_five"] = self._calculate_big_five_score(candidate)
            
            if weights.pre_requisitos > 0:
                scores["pre_requisitos"] = self._calculate_prereq_score(candidate, job)
            
            if weights.historico > 0:
                scores["historico"] = self._calculate_historico_score(candidate)
            
            if weights.completude > 0:
                scores["completude"] = self._calculate_completude_score(candidate)
            
            if weights.recency > 0:
                scores["recency"] = self._calculate_recency_score(candidate)
            
            dimension_scores[cid] = {
                "candidate_name": candidate.name,
                "dimensions": scores
            }
        
        return dimension_scores
    
    def _calculate_rubricas_score(
        self, 
        candidate: Candidate, 
        job: JobVacancy | None
    ) -> float:
        """
        Calculate BARS rubrics score (CV vs job requirements).
        Based on skills match and experience alignment.
        """
        if not job:
            return 50.0
        
        score = 50.0
        
        candidate_skills = set(s.lower() for s in (candidate.technical_skills or []))
        job_requirements = job.technical_requirements or []
        required_skills = set()
        
        for req in job_requirements:
            if isinstance(req, dict):
                tech = req.get("technology", "").lower()
                if tech:
                    required_skills.add(tech)
            elif isinstance(req, str):
                required_skills.add(req.lower())
        
        if not required_skills:
            job_reqs = job.requirements or []
            for req in job_reqs:
                if isinstance(req, str):
                    required_skills.add(req.lower())
        
        if required_skills:
            matched = candidate_skills.intersection(required_skills)
            match_ratio = len(matched) / len(required_skills)
            score = min(100, match_ratio * 100 + 20)
        
        if candidate.seniority_level and job.seniority_level:
            seniority_order = ["junior", "pleno", "senior", "especialista", "lead", "principal"]
            c_level = normalize_seniority(candidate.seniority_level)
            j_level = normalize_seniority(job.seniority_level)
            
            try:
                c_idx = next(i for i, s in enumerate(seniority_order) if s in c_level)
                j_idx = next(i for i, s in enumerate(seniority_order) if s in j_level)
                
                if c_idx >= j_idx:
                    score += 10
                elif c_idx == j_idx - 1:
                    score += 5
            except StopIteration:
                pass
        
        return min(100, score)
    
    async def _apply_score_normalization(
        self,
        db: AsyncSession,
        job_id: str,
        wsi_data: dict[str, Any]
    ) -> dict[str, Any]:
        try:
            # ADR-001 Sprint Q2 cleanup: cross-domain read via WsiRepository
            from app.domains.voice.repositories.wsi_repository import WsiRepository
            wsi_repo = WsiRepository(db)
            candidate_versions = {}
            for cid in wsi_data.keys():
                version = await wsi_repo.get_latest_completed_session_version(
                    candidate_id=cid, job_vacancy_id=job_id,
                )
                if version is not None:
                    candidate_versions[cid] = version

            unique_versions = set(candidate_versions.values())
            if len(unique_versions) <= 1:
                return wsi_data

            candidate_scores = []
            for cid, wsi in wsi_data.items():
                candidate_scores.append({
                    "candidate_id": cid,
                    "score": wsi.get("overall_score", 0.0) or 0.0,
                    "question_set_version": candidate_versions.get(cid),
                })

            normalized_results = await score_normalization_service.normalize_candidate_scores(
                db=db,
                job_vacancy_id=job_id,
                candidate_scores=candidate_scores,
            )

            for nr in normalized_results:
                if nr.candidate_id in wsi_data and nr.normalization_factor != 1.0:
                    wsi_data[nr.candidate_id]["original_overall_score"] = wsi_data[nr.candidate_id].get("overall_score")
                    wsi_data[nr.candidate_id]["overall_score"] = nr.normalized_score
                    wsi_data[nr.candidate_id]["normalization_applied"] = True
                    wsi_data[nr.candidate_id]["normalization_factor"] = nr.normalization_factor

            logger.info(f"WSI score normalization applied for job {job_id}: {len(normalized_results)} candidates normalized across versions {unique_versions}")
        except Exception as e:
            logger.warning(f"WSI score normalization failed, using raw scores: {e}")

        return wsi_data

    def _calculate_wsi_score(self, wsi_data: dict | None) -> float:
        """Calculate WSI (voice screening) score."""
        if not wsi_data:
            return 0.0
        
        overall = wsi_data.get("overall_score", 0) or 0
        tech = wsi_data.get("tech_score", 0) or 0
        comm = wsi_data.get("comm_score", 0) or 0
        fit = wsi_data.get("fit_score", 0) or 0
        
        if overall > 0:
            return float(overall)
        
        scores = [s for s in [tech, comm, fit] if s > 0]
        if scores:
            return sum(scores) / len(scores)
        
        return 50.0
    
    def _calculate_big_five_score(self, candidate: Candidate) -> float:
        """Calculate Big Five personality score from candidate data."""
        additional = candidate.additional_data or {}
        big_five = additional.get("big_five", {})
        
        if not big_five:
            return 50.0
        
        scores = []
        for trait in ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]:
            if trait in big_five and isinstance(big_five[trait], (int, float)):
                scores.append(big_five[trait])
        
        if scores:
            return sum(scores) / len(scores)
        
        return 50.0
    
    def _calculate_prereq_score(
        self, 
        candidate: Candidate, 
        job: JobVacancy | None
    ) -> float:
        """Calculate pre-requisites compliance score."""
        if not job:
            return 50.0
        
        score = 100.0
        penalties = 0
        
        job_languages = job.languages or []
        if job_languages:
            candidate_langs = candidate.languages or {}
            for lang_req in job_languages:
                if isinstance(lang_req, dict):
                    required_lang = lang_req.get("language", "").lower()
                    lang_req.get("level", "").lower()
                    is_required = lang_req.get("required", False)
                    
                    candidate_level = None
                    for lang, level in candidate_langs.items():
                        if required_lang in lang.lower():
                            candidate_level = level.lower() if isinstance(level, str) else str(level)
                            break
                    
                    if not candidate_level and is_required:
                        penalties += 25
        
        if job.is_affirmative:
            pass
        
        return max(0, score - penalties)
    
    def _calculate_historico_score(self, candidate: Candidate) -> float:
        """Calculate career history quality score."""
        score = 50.0
        
        years = candidate.years_of_experience or 0
        if years >= 10:
            score += 25
        elif years >= 5:
            score += 15
        elif years >= 2:
            score += 5
        
        if candidate.current_company:
            score += 10
        
        if candidate.current_title:
            score += 5
        
        work_history = candidate.work_history or []
        if len(work_history) >= 3:
            score += 10
        elif len(work_history) >= 1:
            score += 5
        
        return min(100, score)
    
    def _calculate_completude_score(self, candidate: Candidate) -> float:
        """Calculate profile completeness score."""
        score = 0.0
        
        if candidate.name:
            score += 10
        if candidate.email:
            score += 10
        if candidate.phone or candidate.mobile_phone:
            score += 10
        if candidate.current_title:
            score += 10
        if candidate.current_company:
            score += 10
        if candidate.location_city:
            score += 10
        if candidate.technical_skills:
            score += 10
        if candidate.resume_text or candidate.resume_url:
            score += 10
        if candidate.linkedin_url:
            score += 10
        if candidate.years_of_experience:
            score += 10
        
        return score
    
    def _calculate_recency_score(self, candidate: Candidate) -> float:
        """Calculate recency score based on last activity."""
        now = datetime.utcnow()
        
        last_activity = candidate.last_activity_at or candidate.updated_at or candidate.created_at
        if not last_activity:
            return 50.0
        
        days_since = (now - last_activity).days
        
        if days_since <= 7:
            return 100.0
        elif days_since <= 30:
            return 80.0
        elif days_since <= 90:
            return 60.0
        elif days_since <= 180:
            return 40.0
        else:
            return 20.0
    
    def _calculate_total_scores(
        self, 
        dimension_scores: dict[str, dict[str, Any]]
    ) -> dict[str, float]:
        """Calculate weighted total score for each candidate."""
        totals = {}
        
        for cid, data in dimension_scores.items():
            dimensions = data.get("dimensions", {})
            total = sum(dimensions.values())
            count = len(dimensions) if dimensions else 1
            totals[cid] = total / count if count > 0 else 0.0
        
        return totals
    
    def _determine_winner(
        self, 
        candidate_totals: dict[str, float]
    ) -> tuple[str | None, float]:
        """Determine winner and confidence level."""
        if not candidate_totals:
            return None, 0.0
        
        sorted_candidates = sorted(
            candidate_totals.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        winner_id, winner_score = sorted_candidates[0]
        
        if len(sorted_candidates) > 1:
            runner_up_score = sorted_candidates[1][1]
            difference = winner_score - runner_up_score
            
            if difference >= 20:
                confidence = 0.95
            elif difference >= 10:
                confidence = 0.85
            elif difference >= 5:
                confidence = 0.70
            elif difference >= 2:
                confidence = 0.55
            else:
                confidence = 0.50
        else:
            confidence = 1.0
        
        return winner_id, confidence
    
    async def _generate_llm_analysis(
        self,
        candidates: list[Candidate],
        job: JobVacancy | None,
        wsi_data: dict[str, Any],
        scenario: ComparisonScenario,
        dimension_scores: dict[str, dict[str, Any]],
        candidate_totals: dict[str, float]
    ) -> dict[str, Any]:
        """Generate LLM-powered comparative analysis."""
        try:
            prompt = ChatPromptTemplate.from_messages([
                ("system", """Você é um especialista em recrutamento e seleção. 
Analise os candidatos comparados e forneça insights acionáveis para o recrutador.

CENÁRIO ATUAL: {scenario}
PESOS UTILIZADOS: {weights}

Sua análise deve ser:
1. Objetiva e baseada nos dados fornecidos
2. Focada em diferenças relevantes entre os candidatos
3. Útil para tomada de decisão

Responda em JSON com:
- analysis: string com análise comparativa (2-3 parágrafos)
- recommendations: lista de objetos com "scenario" e "recommendation" para próximos passos"""),
                ("user", """CANDIDATOS COMPARADOS:
{candidates_summary}

VAGA: {job_info}

SCORES POR DIMENSÃO:
{dimension_summary}

SCORES TOTAIS:
{totals_summary}

Gere a análise comparativa em JSON.""")
            ])
            
            # SEG-3B: data minimization — remover PII antes de enviar ao LLM (LGPD Art. 12)
            from app.shared.pii_masking import strip_pii_for_llm_prompt
            candidates_summary = "\n".join([
                strip_pii_for_llm_prompt(
                    f"- {c.name}: {c.current_title or 'N/A'} @ {c.current_company or 'N/A'}, "
                    f"{c.years_of_experience or 0} anos exp, "
                    f"Skills: {', '.join((c.technical_skills or [])[:5])}"
                )
                for c in candidates
            ])
            
            job_info = "Sem vaga específica"
            if job:
                job_info = f"{job.title} ({job.seniority_level or 'N/A'}) - {job.department or 'N/A'}"
            
            dimension_summary = "\n".join([
                f"- {data.get('candidate_name', cid)}: {data.get('dimensions', {})}"
                for cid, data in dimension_scores.items()
            ])
            
            totals_summary = "\n".join([
                f"- {cid}: {score:.1f}"
                for cid, score in sorted(candidate_totals.items(), key=lambda x: x[1], reverse=True)
            ])
            
            llm = llm_service.get_audited_model()
            chain = prompt | llm | JsonOutputParser()
            
            result = await chain.ainvoke({
                "scenario": self._get_scenario_description(scenario),
                "weights": str(self._get_weights_for_scenario(scenario).to_dict()),
                "candidates_summary": candidates_summary,
                "job_info": job_info,
                "dimension_summary": dimension_summary,
                "totals_summary": totals_summary,
            })
            
            return result
            
        except Exception as e:
            logger.warning(f"LLM analysis failed: {e}")
            return {
                "analysis": "Análise automática indisponível. Os scores numéricos foram calculados com sucesso.",
                "recommendations": [
                    {
                        "scenario": "geral",
                        "recommendation": "Revisar os scores por dimensão para identificar pontos fortes de cada candidato."
                    }
                ]
            }


candidate_comparison_service = CandidateComparisonService()


def get_candidate_comparison_service() -> "CandidateComparisonService":
    return candidate_comparison_service
