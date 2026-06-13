"""
LIA Score Service - Automatic candidate scoring based on search criteria.

This service calculates a compatibility score (0-100) for candidates 
based on how well they match the search criteria/job requirements.

Also implements the Unified LIA Ranking formula:
  Ranking_Score = (
      Rubricas_Score × W_rubricas +
      WSI_Score × W_wsi +
      Prerequisites_Score × W_prereq +
      Recency_Boost × W_recency +
      Calibration_Adjustment
  ) × Completeness_Factor
"""
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from app.schemas.qualification_matrix import QualificationMatrix as _QualMatrix


from app.config.industry_weights import ScoringWeights, get_weights_for_industry

IndustryWeights = ScoringWeights

logger = logging.getLogger(__name__)
from app.shared.compliance import scoring_safeguards as _ss
from app.shared.compliance.scoring_safeguards import FairnessBlockedError


class DataAvailability(Enum):
    """
    Enum for data availability scenarios for weight redistribution.
    
    NOTE: Diferença entre serviços - 'recency' vs 'historico'
    =========================================================
    
    LIA Score Service vs Candidate Comparison Service:
    - LIA Score Service: Handles INDIVIDUAL candidate ranking/scoring
    - CandidateComparisonService: Handles COMPARISON between multiple candidates
    
    Weight differences:
    - LIA Score Service (Ranking Individual): Uses rubricas, wsi, big_five, prereq, recency
    - Comparison Service (Cenário A): Uses rubricas 40%, wsi 25%, big_five 15%, prereq 10%, historico 10%
    
    Diferença chave entre 'recency' e 'historico':
    -----------------------------------------------
    - 'recency' (usado aqui): Recência de atividade do candidato - boost baseado em
      quando o candidato foi visto/atualizado pela última vez. Favorece candidatos
      ativos recentemente no sistema.
      
    - 'historico' (usado em Comparison Service): Média de WSI/desempenho em vagas
      anteriores. Avalia a qualidade histórica do candidato em processos passados.
    
    Justificativa:
    - O LIA Score é para ranking individual onde recência de dados importa
      (candidatos com dados mais recentes são mais confiáveis)
    - A Comparação usa histórico porque compara candidatos no contexto de uma vaga
      específica, onde o desempenho passado é mais relevante que recência
    """
    CV_WSI_PREREQ = "cv_wsi_prereq"  # All data available
    CV_PREREQ = "cv_prereq"          # No WSI data
    CV_ONLY = "cv_only"              # Only CV data


WEIGHT_DISTRIBUTION = {
    DataAvailability.CV_WSI_PREREQ: {
        "rubricas": 0.40,
        "wsi": 0.25,
        "big_five": 0.10,
        "prereq": 0.15,
        "recency": 0.10,
    },
    DataAvailability.CV_PREREQ: {
        "rubricas": 0.55,
        "wsi": 0.00,
        "big_five": 0.00,
        "prereq": 0.25,
        "recency": 0.20,
    },
    DataAvailability.CV_ONLY: {
        "rubricas": 0.60,
        "wsi": 0.00,
        "big_five": 0.00,
        "prereq": 0.20,
        "recency": 0.20,
    },
}


RECENCY_BOOST_THRESHOLDS = [
    (7, 100),    # Últimos 7 dias: 100
    (30, 80),    # 8-30 dias: 80
    (90, 60),    # 31-90 dias: 60
    (180, 40),   # 91-180 dias: 40
]
RECENCY_BOOST_DEFAULT = 20  # > 180 dias: 20


@dataclass
class RankingScoreBreakdown:
    """Detailed breakdown of the unified ranking score calculation."""
    rubricas_score: float  # 0-100 - CV rubric evaluation score
    wsi_score: float | None  # 0-100 - WSI conversational score (None if not available)
    prerequisites_score: float  # 0-100 - Prerequisites/filters match score
    recency_boost: float  # 0-100 - Recency boost based on last activity
    calibration_adjustment: float  # -5 to +5 - Adjustment from CalibrationService
    completeness_factor: float  # 0.0 to 1.0 - Data completeness multiplier
    
    weights_used: dict[str, float] = field(default_factory=dict)
    data_availability: str = "cv_only"
    
    weighted_rubricas: float = 0.0
    weighted_wsi: float = 0.0
    weighted_prereq: float = 0.0
    weighted_recency: float = 0.0
    
    def calculate_raw_score(self) -> float:
        """Calculate raw score before completeness factor."""
        return (
            self.weighted_rubricas +
            self.weighted_wsi +
            self.weighted_prereq +
            self.weighted_recency +
            self.calibration_adjustment
        )
    
    def calculate_final_score(self) -> float:
        """Calculate final ranking score with completeness factor."""
        raw_score = self.calculate_raw_score()
        final = raw_score * self.completeness_factor
        return max(0.0, min(100.0, final))
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "rubricas_score": round(self.rubricas_score, 2),
            "wsi_score": round(self.wsi_score, 2) if self.wsi_score is not None else None,
            "prerequisites_score": round(self.prerequisites_score, 2),
            "recency_boost": round(self.recency_boost, 2),
            "calibration_adjustment": round(self.calibration_adjustment, 2),
            "completeness_factor": round(self.completeness_factor, 3),
            "weighted_components": {
                "rubricas": round(self.weighted_rubricas, 2),
                "wsi": round(self.weighted_wsi, 2),
                "prerequisites": round(self.weighted_prereq, 2),
                "recency": round(self.weighted_recency, 2),
            },
            "weights_used": {k: round(v, 2) for k, v in self.weights_used.items()},
            "data_availability": self.data_availability,
            "raw_score": round(self.calculate_raw_score(), 2),
            "final_score": round(self.calculate_final_score(), 2),
        }


@dataclass
class RankingScoreResult:
    """Complete ranking score result with breakdown and metadata."""
    ranking_score: float  # 0-100 final score
    breakdown: RankingScoreBreakdown
    rank_position: int | None  # Position in ranked list (if applicable)
    recommendation: str  # Altamente Recomendado, Recomendado, etc.
    strengths: list[str]
    concerns: list[str]
    reasoning: str
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "ranking_score": round(self.ranking_score, 2),
            "breakdown": self.breakdown.to_dict(),
            "rank_position": self.rank_position,
            "recommendation": self.recommendation,
            "strengths": self.strengths,
            "concerns": self.concerns,
            "reasoning": self.reasoning,
        }


class SeniorityLevel(Enum):
    JUNIOR = "junior"
    PLENO = "pleno"
    SENIOR = "senior"
    STAFF = "staff"
    LEAD = "lead"
    PRINCIPAL = "principal"


SENIORITY_YEARS_MAP = {
    SeniorityLevel.JUNIOR: (0, 2),
    SeniorityLevel.PLENO: (2, 5),
    SeniorityLevel.SENIOR: (5, 10),
    SeniorityLevel.STAFF: (8, 15),
    SeniorityLevel.LEAD: (8, 20),
    SeniorityLevel.PRINCIPAL: (10, 25),
}

SENIORITY_ALIASES = {
    "jr": SeniorityLevel.JUNIOR,
    "júnior": SeniorityLevel.JUNIOR,
    "junior": SeniorityLevel.JUNIOR,
    "entry": SeniorityLevel.JUNIOR,
    "mid": SeniorityLevel.PLENO,
    "mid-level": SeniorityLevel.PLENO,
    "pleno": SeniorityLevel.PLENO,
    "sr": SeniorityLevel.SENIOR,
    "sênior": SeniorityLevel.SENIOR,
    "senior": SeniorityLevel.SENIOR,
    "staff": SeniorityLevel.STAFF,
    "lead": SeniorityLevel.LEAD,
    "líder": SeniorityLevel.LEAD,
    "tech lead": SeniorityLevel.LEAD,
    "principal": SeniorityLevel.PRINCIPAL,
}


@dataclass
class LIAScoreBreakdown:
    """Detailed breakdown of the LIA score calculation."""
    skills_match: float  # 0-100
    experience_match: float  # 0-100
    seniority_match: float  # 0-100
    location_match: float  # 0-100
    title_match: float  # 0-100
    
    def total_score(self, weights: IndustryWeights | None = None) -> float:
        """Calculate weighted total score."""
        if weights is None:
            weights = IndustryWeights()
        
        return (
            self.skills_match * weights.skills_match +
            self.experience_match * weights.experience_match +
            self.seniority_match * weights.seniority_match +
            self.location_match * weights.location_match +
            self.title_match * weights.title_match
        )
    
    def to_dict(self) -> dict[str, float]:
        return {
            "skills_match": round(self.skills_match, 1),
            "experience_match": round(self.experience_match, 1),
            "seniority_match": round(self.seniority_match, 1),
            "location_match": round(self.location_match, 1),
            "title_match": round(self.title_match, 1),
        }


@dataclass
class LIAScoreResult:
    """Complete LIA score result with reasoning."""
    score: float  # 0-100
    breakdown: LIAScoreBreakdown
    reasoning: str
    matched_skills: list[str]
    missing_skills: list[str]
    strengths: list[str]
    concerns: list[str]
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "score": round(self.score, 1),
            "breakdown": self.breakdown.to_dict(),
            "reasoning": self.reasoning,
            "matched_skills": self.matched_skills,
            "missing_skills": self.missing_skills,
            "strengths": self.strengths,
            "concerns": self.concerns,
        }




def must_have_prerequisites_score(matrix) -> float:
    """3.1: 0-100 baseado em must_have_met/must_have_total.
    0 must_haves -> 100 (sem penalidade). 0/N met -> 0."""
    total = getattr(matrix, 'must_have_total', 0) or 0
    if total == 0:
        return 100.0
    met = getattr(matrix, 'must_have_met', 0) or 0
    return round(100.0 * met / total, 2)


class LIAScoreService:
    """Service for calculating LIA compatibility scores."""
    
    def __init__(self):
        self.skill_synonyms = self._build_skill_synonyms()
    
    def _build_skill_synonyms(self) -> dict[str, list[str]]:
        """Build a dictionary of skill synonyms for fuzzy matching."""
        return {
            "javascript": ["js", "ecmascript", "es6", "es2015"],
            "typescript": ["ts"],
            "python": ["py", "python3"],
            "react": ["reactjs", "react.js"],
            "angular": ["angularjs", "angular.js"],
            "vue": ["vuejs", "vue.js"],
            "node": ["nodejs", "node.js"],
            "postgres": ["postgresql", "pg"],
            "mongodb": ["mongo"],
            "kubernetes": ["k8s"],
            "docker": ["containers", "containerization"],
            "aws": ["amazon web services", "amazon aws"],
            "gcp": ["google cloud", "google cloud platform"],
            "azure": ["microsoft azure"],
            "machine learning": ["ml", "aprendizado de máquina"],
            "deep learning": ["dl", "aprendizado profundo"],
            "data science": ["ciência de dados"],
            "frontend": ["front-end", "front end"],
            "backend": ["back-end", "back end"],
            "fullstack": ["full-stack", "full stack"],
        }
    
    def _normalize_skill(self, skill: str) -> str:
        """Normalize a skill name for comparison."""
        skill_lower = skill.lower().strip()
        
        for main_skill, synonyms in self.skill_synonyms.items():
            if skill_lower == main_skill or skill_lower in synonyms:
                return main_skill
        
        return skill_lower
    
    def _extract_skills_from_query(self, query: str) -> list[str]:
        """Extract skill keywords from a search query."""
        common_skills = [
            "python", "java", "javascript", "typescript", "react", "angular", "vue",
            "node", "nodejs", "django", "flask", "fastapi", "spring", "aws", "gcp",
            "azure", "docker", "kubernetes", "terraform", "sql", "postgresql", "mongodb",
            "redis", "kafka", "rabbitmq", "graphql", "rest", "api", "git", "ci/cd",
            "machine learning", "ml", "deep learning", "tensorflow", "pytorch",
            "pandas", "numpy", "spark", "hadoop", "airflow", "dbt", "tableau", "power bi",
            "figma", "sketch", "jira", "confluence", "scrum", "agile", "product",
            "liderança", "leadership", "arquitetura", "architecture", "microserviços",
            "microservices", "devops", "sre", "frontend", "backend", "fullstack",
        ]
        
        query_lower = query.lower()
        found_skills = []
        
        for skill in common_skills:
            if skill in query_lower:
                found_skills.append(self._normalize_skill(skill))
        
        return list(set(found_skills))
    
    def _extract_experience_years_from_query(self, query: str) -> int | None:
        """Extract minimum experience years from query."""
        patterns = [
            r'(\d+)\s*\+?\s*(?:anos?|years?)',
            r'(\d+)\s*\+?\s*(?:anos?|years?)\s*de?\s*experi[eê]ncia',
            r'experi[eê]ncia\s*(?:de\s*)?(\d+)\s*\+?\s*anos?',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query.lower())
            if match:
                return int(match.group(1))
        
        return None
    
    def _extract_seniority_from_query(self, query: str) -> SeniorityLevel | None:
        """Extract seniority level from query."""
        query_lower = query.lower()
        
        for alias, level in SENIORITY_ALIASES.items():
            if alias in query_lower:
                return level
        
        return None
    
    def _extract_location_from_query(self, query: str) -> str | None:
        """Extract location preference from query."""
        locations = [
            "são paulo", "sp", "rio de janeiro", "rj", "belo horizonte", "bh",
            "curitiba", "porto alegre", "brasília", "salvador", "fortaleza",
            "remoto", "remote", "híbrido", "hybrid", "presencial", "onsite",
        ]
        
        query_lower = query.lower()
        
        for loc in locations:
            if loc in query_lower:
                return loc
        
        return None
    
    def _calculate_skills_match(
        self,
        candidate_skills: list[str],
        required_skills: list[str]
    ) -> tuple[float, list[str], list[str]]:
        """
        Calculate skills match percentage.
        
        Returns:
            Tuple of (match_percentage, matched_skills, missing_skills)
        """
        if not required_skills:
            return 100.0, [], []
        
        candidate_normalized = {self._normalize_skill(s) for s in candidate_skills}
        required_normalized = [self._normalize_skill(s) for s in required_skills]
        
        matched = []
        missing = []
        
        for skill in required_normalized:
            if skill in candidate_normalized:
                matched.append(skill)
            else:
                for c_skill in candidate_normalized:
                    if skill in c_skill or c_skill in skill:
                        matched.append(skill)
                        break
                else:
                    missing.append(skill)
        
        match_percentage = (len(matched) / len(required_normalized)) * 100 if required_normalized else 100
        
        return match_percentage, matched, missing
    
    def _calculate_experience_match(
        self,
        candidate_years: float | None,
        required_years: int | None
    ) -> float:
        """Calculate experience match score."""
        if required_years is None:
            return 100.0
        
        if candidate_years is None:
            return 50.0
        
        if candidate_years >= required_years:
            return 100.0
        elif candidate_years >= required_years * 0.8:
            return 85.0
        elif candidate_years >= required_years * 0.6:
            return 70.0
        elif candidate_years >= required_years * 0.4:
            return 50.0
        else:
            return 30.0
    
    def _calculate_seniority_match(
        self,
        candidate_seniority: str | None,
        candidate_years: float | None,
        required_seniority: SeniorityLevel | None
    ) -> float:
        """Calculate seniority level match score."""
        if required_seniority is None:
            return 100.0
        
        candidate_level = None
        if candidate_seniority:
            candidate_level = SENIORITY_ALIASES.get(candidate_seniority.lower())
        
        if candidate_level is None and candidate_years is not None:
            for level, (min_years, max_years) in SENIORITY_YEARS_MAP.items():
                if min_years <= candidate_years <= max_years:
                    candidate_level = level
                    break
        
        if candidate_level is None:
            return 50.0
        
        seniority_order = [
            SeniorityLevel.JUNIOR, SeniorityLevel.PLENO, SeniorityLevel.SENIOR,
            SeniorityLevel.STAFF, SeniorityLevel.LEAD, SeniorityLevel.PRINCIPAL
        ]
        
        try:
            required_idx = seniority_order.index(required_seniority)
            candidate_idx = seniority_order.index(candidate_level)
            
            diff = candidate_idx - required_idx
            
            if diff == 0:
                return 100.0
            elif diff == 1:
                return 90.0  # Slightly overqualified
            elif diff == -1:
                return 75.0  # Slightly underqualified
            elif diff >= 2:
                return 70.0  # More overqualified
            else:
                return max(40.0, 75.0 + (diff * 15))
        except ValueError:
            return 50.0
    
    def _calculate_location_match(
        self,
        candidate_location: str | None,
        candidate_remote: bool | None,
        required_location: str | None
    ) -> float:
        """Calculate location match score."""
        if required_location is None:
            return 100.0
        
        required_lower = required_location.lower()
        
        if required_lower in ["remoto", "remote"]:
            if candidate_remote:
                return 100.0
            return 70.0
        
        if candidate_location:
            candidate_lower = candidate_location.lower()
            
            if required_lower in candidate_lower or candidate_lower in required_lower:
                return 100.0
            
            same_state_mapping = {
                "sp": ["são paulo", "campinas", "santos", "guarulhos"],
                "rj": ["rio de janeiro", "niterói"],
                "mg": ["belo horizonte", "uberlândia"],
            }
            
            for state, cities in same_state_mapping.items():
                req_in_state = required_lower == state or any(c in required_lower for c in cities)
                cand_in_state = candidate_lower == state or any(c in candidate_lower for c in cities)
                
                if req_in_state and cand_in_state:
                    return 80.0
        
        if candidate_remote:
            return 75.0
        
        return 50.0
    
    def _calculate_title_match(
        self,
        candidate_title: str | None,
        query: str
    ) -> float:
        """Calculate title match score based on query terms."""
        if not candidate_title:
            return 50.0
        
        title_lower = candidate_title.lower()
        query_lower = query.lower()
        
        title_keywords = [
            "developer", "desenvolvedor", "engineer", "engenheiro",
            "analyst", "analista", "manager", "gerente", "lead", "líder",
            "architect", "arquiteto", "designer", "scientist", "cientista",
            "devops", "sre", "data", "product", "frontend", "backend", "fullstack"
        ]
        
        query_titles = [kw for kw in title_keywords if kw in query_lower]
        title_titles = [kw for kw in title_keywords if kw in title_lower]
        
        if not query_titles:
            return 80.0
        
        matches = set(query_titles) & set(title_titles)
        
        if matches:
            return 100.0
        
        for q_title in query_titles:
            for t_title in title_titles:
                if q_title in t_title or t_title in q_title:
                    return 85.0
        
        return 40.0
    
    def _generate_reasoning(
        self,
        score: float,
        breakdown: LIAScoreBreakdown,
        matched_skills: list[str],
        missing_skills: list[str]
    ) -> str:
        """Generate human-readable reasoning for the score."""
        parts = []
        
        if score >= 85:
            parts.append("Excelente compatibilidade com os requisitos.")
        elif score >= 70:
            parts.append("Boa compatibilidade com os requisitos.")
        elif score >= 50:
            parts.append("Compatibilidade moderada com os requisitos.")
        else:
            parts.append("Baixa compatibilidade com os requisitos.")
        
        if matched_skills:
            parts.append(f"Possui {len(matched_skills)} skills requeridas: {', '.join(matched_skills[:5])}")
            if len(matched_skills) > 5:
                parts.append(f"e mais {len(matched_skills) - 5}.")
        
        if missing_skills:
            parts.append(f"Skills não encontradas: {', '.join(missing_skills[:3])}")
        
        return " ".join(parts)
    
    def _identify_strengths_and_concerns(
        self,
        breakdown: LIAScoreBreakdown,
        matched_skills: list[str],
        missing_skills: list[str],
        candidate: dict[str, Any]
    ) -> tuple[list[str], list[str]]:
        """Identify candidate strengths and concerns."""
        strengths = []
        concerns = []
        
        if breakdown.skills_match >= 80:
            strengths.append(f"Alta correspondência de skills ({int(breakdown.skills_match)}%)")
        elif breakdown.skills_match < 50:
            concerns.append(f"Baixa correspondência de skills ({int(breakdown.skills_match)}%)")
        
        if breakdown.experience_match >= 80:
            years = candidate.get("years_of_experience") or candidate.get("total_experience_years")
            if years:
                strengths.append(f"Experiência adequada ({years} anos)")
        elif breakdown.experience_match < 50:
            concerns.append("Experiência abaixo do esperado")
        
        if breakdown.seniority_match >= 90:
            strengths.append("Nível de senioridade compatível")
        elif breakdown.seniority_match < 60:
            concerns.append("Senioridade não compatível com o perfil")
        
        if breakdown.location_match >= 80:
            strengths.append("Localização compatível")
        elif breakdown.location_match < 60:
            concerns.append("Localização pode ser um obstáculo")
        
        if breakdown.title_match >= 80:
            title = candidate.get("current_title", "")
            if title:
                strengths.append(f"Cargo atual relevante: {title}")
        
        if candidate.get("is_opentowork") or candidate.get("is_open_to_work"):
            strengths.append("Disponível para novas oportunidades")
        
        return strengths, concerns
    
    def calculate_score(
        self,
        candidate: dict[str, Any],
        criteria: dict[str, Any],
        industry: str | None = None
    ) -> LIAScoreResult:
        """
        Calculate LIA score for a candidate based on search criteria.
        
        Args:
            candidate: Dictionary with candidate data (from local DB or Pearch)
            criteria: Dictionary with search criteria (query, filters, etc.)
            industry: Optional industry string for industry-specific weights
        
        Returns:
            LIAScoreResult with score, breakdown, and reasoning
        """
        # C2 — Fairness gate (LGPD Art.20 / CLAUDE.md #2/#3).
        _lia_query = (criteria.get("query") or "")
        _lia_company = criteria.get("company_id") or "unknown"
        _lia_fg, _lia_unavail = _ss.run_fairness_check(_lia_query)
        if _lia_unavail or (_lia_fg and _lia_fg.is_blocked):
            _lia_fg = _lia_fg or type(
                "FR", (), {"is_blocked": True, "category": "unavailable",
                           "educational_message": "fairness guard unavailable"}
            )()
            _ss.schedule_audit_log(_ss.log_scoring_decision(
                company_id=_lia_company,
                agent_name="lia_score_service",
                decision_type="fairness_block",
                action="cv_screening.fairness_block",
                decision="blocked",
                reasoning=[f"FairnessGuard: category={_lia_fg.category}",
                            _lia_fg.educational_message or ""],
                criteria_used=["fairness_guard"],
                human_review_required=True,
            ))
            raise FairnessBlockedError(_lia_fg)

        weights = get_weights_for_industry(industry) if industry else IndustryWeights()
        
        query = criteria.get("query", "")
        filters = criteria.get("filters", {})
        
        required_skills = filters.get("skills", []) or self._extract_skills_from_query(query)
        required_experience = filters.get("experience_years_min") or self._extract_experience_years_from_query(query)
        required_seniority = filters.get("seniority")
        if required_seniority and isinstance(required_seniority, str):
            required_seniority = SENIORITY_ALIASES.get(required_seniority.lower())
        else:
            required_seniority = self._extract_seniority_from_query(query)
        required_location = filters.get("location") or self._extract_location_from_query(query)
        
        candidate_skills = (
            candidate.get("skills", []) or 
            candidate.get("technical_skills", []) or 
            []
        )
        candidate_years = (
            candidate.get("total_experience_years") or 
            candidate.get("years_of_experience")
        )
        candidate_seniority = candidate.get("seniority_level") or candidate.get("seniority")
        candidate_location = (
            candidate.get("location") or 
            f"{candidate.get('location_city', '')} {candidate.get('location_state', '')}".strip()
        )
        candidate_remote = candidate.get("is_remote") or candidate.get("remote_ok")
        candidate_title = candidate.get("current_title") or candidate.get("headline")
        
        skills_match, matched_skills, missing_skills = self._calculate_skills_match(
            candidate_skills, required_skills
        )
        
        experience_match = self._calculate_experience_match(
            candidate_years, required_experience
        )
        
        seniority_match = self._calculate_seniority_match(
            candidate_seniority, candidate_years, required_seniority
        )
        
        location_match = self._calculate_location_match(
            candidate_location, candidate_remote, required_location
        )
        
        title_match = self._calculate_title_match(candidate_title, query)
        
        breakdown = LIAScoreBreakdown(
            skills_match=skills_match,
            experience_match=experience_match,
            seniority_match=seniority_match,
            location_match=location_match,
            title_match=title_match,
        )
        
        score = breakdown.total_score(weights)
        
        reasoning = self._generate_reasoning(
            score, breakdown, matched_skills, missing_skills
        )
        
        strengths, concerns = self._identify_strengths_and_concerns(
            breakdown, matched_skills, missing_skills, candidate
        )
        
        return LIAScoreResult(
            score=score,
            breakdown=breakdown,
            reasoning=reasoning,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            strengths=strengths,
            concerns=concerns,
        )
    
    def calculate_scores_batch(
        self,
        candidates: list[dict[str, Any]],
        criteria: dict[str, Any],
        sort_by_score: bool = True,
        industry: str | None = None
    ) -> list[tuple[dict[str, Any], LIAScoreResult]]:
        """
        Calculate LIA scores for multiple candidates.
        
        Args:
            candidates: List of candidate dictionaries
            criteria: Search criteria (query, filters)
            sort_by_score: Whether to sort results by score (descending)
            industry: Optional industry string for industry-specific weights
        
        Returns:
            List of tuples (candidate, score_result)
        """
        results = []
        
        for candidate in candidates:
            try:
                score_result = self.calculate_score(candidate, criteria, industry)
                results.append((candidate, score_result))
            except Exception as e:
                logger.warning(f"Failed to calculate score for candidate: {e}")
                default_breakdown = LIAScoreBreakdown(
                    skills_match=50.0,
                    experience_match=50.0,
                    seniority_match=50.0,
                    location_match=50.0,
                    title_match=50.0,
                )
                default_result = LIAScoreResult(
                    score=50.0,
                    breakdown=default_breakdown,
                    reasoning="Não foi possível calcular o score para este candidato.",
                    matched_skills=[],
                    missing_skills=[],
                    strengths=[],
                    concerns=["Score não calculado"],
                )
                results.append((candidate, default_result))
        
        if sort_by_score:
            results.sort(key=lambda x: x[1].score, reverse=True)
        
        return results
    
    def _calculate_recency_boost(self, last_activity_date: datetime | None) -> float:
        """
        Calculate recency boost based on candidate's last activity.
        
        Recency Boost Thresholds:
        - Últimos 7 dias: 100
        - 8-30 dias: 80
        - 31-90 dias: 60
        - 91-180 dias: 40
        - > 180 dias: 20
        
        Args:
            last_activity_date: Date of candidate's last activity (update, application, etc.)
        
        Returns:
            Recency boost value (0-100)
        """
        if last_activity_date is None:
            return RECENCY_BOOST_DEFAULT
        
        now = datetime.utcnow()
        if isinstance(last_activity_date, str):
            try:
                last_activity_date = datetime.fromisoformat(last_activity_date.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                return RECENCY_BOOST_DEFAULT
        
        days_since_activity = (now - last_activity_date).days
        
        for threshold_days, boost_value in RECENCY_BOOST_THRESHOLDS:
            if days_since_activity <= threshold_days:
                return float(boost_value)
        
        return float(RECENCY_BOOST_DEFAULT)
    
    def _determine_data_availability(
        self,
        has_rubricas_score: bool,
        has_wsi_score: bool,
        has_prerequisites: bool
    ) -> DataAvailability:
        """
        Determine data availability scenario for weight redistribution.
        
        Args:
            has_rubricas_score: Whether CV rubric score is available
            has_wsi_score: Whether WSI conversational score is available
            has_prerequisites: Whether prerequisites evaluation is available
        
        Returns:
            DataAvailability enum value
        """
        if has_rubricas_score and has_wsi_score and has_prerequisites:
            return DataAvailability.CV_WSI_PREREQ
        elif has_rubricas_score and has_prerequisites:
            return DataAvailability.CV_PREREQ
        else:
            return DataAvailability.CV_ONLY
    
    def _calculate_completeness_factor(
        self,
        candidate: dict[str, Any],
        has_rubricas: bool,
        has_wsi: bool,
        has_prereq: bool
    ) -> float:
        """
        Calculate data completeness factor (0.0-1.0).
        
        The completeness factor penalizes candidates with incomplete data
        to prevent false high rankings.
        
        Args:
            candidate: Candidate data dictionary
            has_rubricas: Whether rubric evaluation was performed
            has_wsi: Whether WSI evaluation was completed
            has_prereq: Whether prerequisites were checked
        
        Returns:
            Completeness factor between 0.0 and 1.0
        """
        factors = []
        
        if has_rubricas:
            factors.append(1.0)
        else:
            factors.append(0.5)
        
        if has_wsi:
            factors.append(1.0)
        else:
            factors.append(0.7)
        
        if has_prereq:
            factors.append(1.0)
        else:
            factors.append(0.8)
        
        has_cv = bool(candidate.get("cv_url") or candidate.get("resume_url") or candidate.get("cv_text"))
        if has_cv:
            factors.append(1.0)
        else:
            factors.append(0.6)
        
        has_contact = bool(candidate.get("email") or candidate.get("phone"))
        if has_contact:
            factors.append(1.0)
        else:
            factors.append(0.9)
        
        return sum(factors) / len(factors) if factors else 0.5
    
    def _get_calibration_adjustment(
        self,
        candidate_id: str | None = None,
        job_id: str | None = None,
        calibration_data: dict[str, Any] | None = None
    ) -> float:
        """
        Get calibration adjustment from pre-fetched data + search feedback.

        Sources:
        1. calibration_data dict (passed by caller, e.g. from CalibrationService)
        (search feedback movido p/ o funil como boost stateless — load_search_feedback, P1-3)

        The adjustment is a value between -5 and +5 that adjusts the final
        score based on recruiter feedback patterns.

        Returns:
            Calibration adjustment value (-5 to +5)
        """
        adjustment = 0.0

        # Source 1: pre-fetched calibration data
        if calibration_data:
            adjustment += calibration_data.get("adjustment", 0.0)

        # Source 2 (search feedback) REMOVIDO daqui (P1-3): vivia em
        # o cache de instancia (atributo no singleton), estado mutavel
        # compartilhado -> vazava cross-tenant. O boost por feedback agora e
        # stateless e escopado por company_id no funil (search.py via
        # lia_score_service.load_search_feedback).

        return max(-5.0, min(5.0, adjustment))

    async def _get_calibration_adjustment_async(
        self,
        candidate_id: str | None = None,
        job_id: str | None = None,
        company_id: str | None = None,
        db=None,
    ) -> float:
        """
        Retorna ajuste de calibração baseado em feedback do loop adaptativo (D6).

        Usa MLFeedbackService.compute_calibration_adjustment() quando db disponível.
        Fail-open: retorna 0.0 em caso de erro ou dados insuficientes.

        Args:
            candidate_id: ID do candidato (reservado para ajustes futuros)
            job_id: ID da vaga para buscar pesos específicos
            company_id: ID da empresa (multi-tenant)
            db: AsyncSession — obrigatório para consultar feedback histórico

        Returns:
            Ajuste de calibração entre -5.0 e +5.0
        """
        try:
            if db is None:
                return 0.0
            from app.shared.services.ml_feedback_service import ml_feedback_service
            adjustment = await ml_feedback_service.compute_calibration_adjustment(
                db=db,
                company_id=company_id or "",
                job_id=job_id,
            )
            return adjustment
        except Exception as exc:
            logger.warning(
                "[LIAScore] _get_calibration_adjustment_async falhou (0.0): %s", exc
            )
            return 0.0
    
    def _calculate_prerequisites_score(
        self,
        candidate: dict[str, Any],
        job_requirements: dict[str, Any] | None = None
    ) -> float:
        """
        Calculate prerequisites match score.
        
        Evaluates mandatory requirements like:
        - Language proficiency
        - Location/work model compatibility
        - Salary range match
        - Availability match
        - Affirmative action eligibility
        
        Args:
            candidate: Candidate data dictionary
            job_requirements: Job requirements dictionary
        
        Returns:
            Prerequisites score (0-100)
        """
        if job_requirements is None:
            return 100.0
        
        prereq_scores = []
        
        required_languages = job_requirements.get("required_languages", [])
        if required_languages:
            candidate_languages = candidate.get("languages", [])
            if isinstance(candidate_languages, list):
                matched = 0
                for req_lang in required_languages:
                    lang_name = req_lang.get("language", "").lower() if isinstance(req_lang, dict) else str(req_lang).lower()
                    for cand_lang in candidate_languages:
                        cand_lang_name = cand_lang.get("language", "").lower() if isinstance(cand_lang, dict) else str(cand_lang).lower()
                        if lang_name in cand_lang_name or cand_lang_name in lang_name:
                            matched += 1
                            break
                prereq_scores.append((matched / len(required_languages)) * 100 if required_languages else 100)
            else:
                prereq_scores.append(50.0)
        
        work_model = job_requirements.get("work_model", "").lower()
        if work_model:
            candidate_remote = candidate.get("is_remote") or candidate.get("remote_ok")
            candidate_location = candidate.get("location", "")
            job_location = job_requirements.get("location", "")
            
            if work_model in ["remoto", "remote"]:
                prereq_scores.append(100.0 if candidate_remote else 70.0)
            elif work_model in ["presencial", "onsite"]:
                if candidate_location and job_location:
                    if job_location.lower() in candidate_location.lower():
                        prereq_scores.append(100.0)
                    else:
                        prereq_scores.append(40.0)
                else:
                    prereq_scores.append(60.0)
            else:
                prereq_scores.append(80.0)
        
        job_salary_max = job_requirements.get("salary_max")
        candidate_salary = candidate.get("salary_expectation") or candidate.get("expected_salary")
        if job_salary_max and candidate_salary:
            try:
                job_max = float(job_salary_max)
                cand_salary = float(candidate_salary)
                if cand_salary <= job_max:
                    prereq_scores.append(100.0)
                elif cand_salary <= job_max * 1.15:
                    prereq_scores.append(70.0)
                else:
                    prereq_scores.append(30.0)
            except (ValueError, TypeError):
                prereq_scores.append(75.0)
        
        job_availability = job_requirements.get("availability")
        candidate_availability = candidate.get("availability") or candidate.get("notice_period")
        if job_availability and candidate_availability:
            availability_map = {
                "imediata": 0, "immediate": 0,
                "15d": 15, "15 dias": 15,
                "30d": 30, "30 dias": 30, "1 month": 30,
                "60d": 60, "60 dias": 60, "2 months": 60,
                "90d": 90, "90 dias": 90, "3 months": 90,
            }
            job_days = availability_map.get(str(job_availability).lower(), 30)
            cand_days = availability_map.get(str(candidate_availability).lower(), 30)
            if cand_days <= job_days:
                prereq_scores.append(100.0)
            elif cand_days <= job_days + 15:
                prereq_scores.append(80.0)
            else:
                prereq_scores.append(50.0)
        
        if prereq_scores:
            return sum(prereq_scores) / len(prereq_scores)
        return 100.0
    
    def _get_ranking_recommendation(self, score: float) -> str:
        """
        Get recommendation label based on ranking score.
        
        Args:
            score: Ranking score (0-100)
        
        Returns:
            Recommendation string
        """
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
    
    def _generate_ranking_reasoning(
        self,
        breakdown: RankingScoreBreakdown,
        recommendation: str
    ) -> str:
        """Generate human-readable reasoning for the ranking score."""
        parts = []
        
        parts.append(f"Candidato classificado como '{recommendation}'.")
        
        if breakdown.rubricas_score >= 80:
            parts.append(f"Excelente avaliação de CV ({breakdown.rubricas_score:.0f}%).")
        elif breakdown.rubricas_score >= 60:
            parts.append(f"Boa avaliação de CV ({breakdown.rubricas_score:.0f}%).")
        else:
            parts.append(f"Avaliação de CV abaixo do esperado ({breakdown.rubricas_score:.0f}%).")
        
        if breakdown.wsi_score is not None:
            if breakdown.wsi_score >= 80:
                parts.append(f"Triagem conversacional excelente ({breakdown.wsi_score:.0f}%).")
            elif breakdown.wsi_score >= 60:
                parts.append(f"Triagem conversacional satisfatória ({breakdown.wsi_score:.0f}%).")
            else:
                parts.append(f"Triagem conversacional necessita atenção ({breakdown.wsi_score:.0f}%).")
        
        if breakdown.prerequisites_score < 70:
            parts.append("Alguns pré-requisitos não foram atendidos.")
        
        if breakdown.recency_boost >= 80:
            parts.append("Candidato ativo recentemente.")
        elif breakdown.recency_boost <= 40:
            parts.append("Perfil não atualizado há algum tempo.")
        
        if breakdown.calibration_adjustment > 0:
            parts.append(f"Ajuste de calibração positivo (+{breakdown.calibration_adjustment:.1f}).")
        elif breakdown.calibration_adjustment < 0:
            parts.append(f"Ajuste de calibração negativo ({breakdown.calibration_adjustment:.1f}).")
        
        if breakdown.completeness_factor < 0.8:
            parts.append(f"Dados do candidato incompletos (fator: {breakdown.completeness_factor:.0%}).")
        
        return " ".join(parts)
    
    def _identify_ranking_strengths_concerns(
        self,
        breakdown: RankingScoreBreakdown,
        candidate: dict[str, Any]
    ) -> tuple[list[str], list[str]]:
        """Identify strengths and concerns from ranking breakdown."""
        strengths = []
        concerns = []
        
        if breakdown.rubricas_score >= 80:
            strengths.append(f"Excelente match com requisitos da vaga ({breakdown.rubricas_score:.0f}%)")
        elif breakdown.rubricas_score < 50:
            concerns.append(f"Baixo match com requisitos ({breakdown.rubricas_score:.0f}%)")
        
        if breakdown.wsi_score is not None:
            if breakdown.wsi_score >= 80:
                strengths.append(f"Performance excepcional na triagem ({breakdown.wsi_score:.0f}%)")
            elif breakdown.wsi_score < 50:
                concerns.append(f"Triagem conversacional abaixo do esperado ({breakdown.wsi_score:.0f}%)")
        
        if breakdown.prerequisites_score >= 90:
            strengths.append("Atende todos os pré-requisitos obrigatórios")
        elif breakdown.prerequisites_score < 60:
            concerns.append("Não atende alguns pré-requisitos")
        
        if breakdown.recency_boost >= 80:
            strengths.append("Perfil atualizado recentemente")
        elif breakdown.recency_boost <= 40:
            concerns.append("Perfil desatualizado (última atividade > 3 meses)")
        
        if breakdown.completeness_factor < 0.7:
            concerns.append("Informações incompletas no perfil")
        
        if candidate.get("is_opentowork") or candidate.get("is_open_to_work"):
            strengths.append("Disponível para novas oportunidades")
        
        return strengths, concerns
    
    def calculate_ranking_score(
        self,
        candidate: dict[str, Any],
        rubricas_score: float | None = None,
        wsi_score: float | None = None,
        job_requirements: dict[str, Any] | None = None,
        calibration_data: dict[str, Any] | None = None,
        last_activity_date: datetime | None = None,
        prerequisites_score: float | None = None,
        qualification_matrix=None,
    ) -> RankingScoreResult:
        """
        Calculate unified LIA ranking score for a candidate.
        
        Implements the formula:
          Ranking_Score = (
              Rubricas_Score × W_rubricas +
              WSI_Score × W_wsi +
              Prerequisites_Score × W_prereq +
              Recency_Boost × W_recency +
              Calibration_Adjustment
          ) × Completeness_Factor
        
        Weight redistribution by data availability:
        - CV + WSI + Prereq: Rubricas 40%, WSI 30%, Prereq 15%, Recency 15%
        - CV + Prereq (sem WSI): Rubricas 55%, Prereq 25%, Recency 20%
        - Apenas CV: Rubricas 60%, Prereq 20%, Recency 20%
        
        Args:
            candidate: Candidate data dictionary
            rubricas_score: CV rubric evaluation score (0-100). If None, uses basic matching.
            wsi_score: WSI conversational score (0-100). If None, WSI weight is redistributed.
            job_requirements: Job requirements for prerequisites evaluation
            calibration_data: Pre-fetched calibration adjustments from CalibrationService
            last_activity_date: Date of candidate's last activity for recency boost
        
        Returns:
            RankingScoreResult with score, breakdown, and metadata
        """
        has_rubricas = rubricas_score is not None
        has_wsi = wsi_score is not None
        has_prereq = job_requirements is not None
        
        if not has_rubricas:
            basic_result = self.calculate_score(candidate, {"query": "", "filters": {}})
            rubricas_score = basic_result.score
            has_rubricas = True
        
        data_availability = self._determine_data_availability(has_rubricas, has_wsi, has_prereq)
        weights = WEIGHT_DISTRIBUTION[data_availability]
        
        # 3.1: override via matrix ou param direto
        if prerequisites_score is None and qualification_matrix is not None:
            prerequisites_score = must_have_prerequisites_score(qualification_matrix)
        elif prerequisites_score is None:
            prerequisites_score = self._calculate_prerequisites_score(candidate, job_requirements)

        
        if last_activity_date is None:
            last_activity_str = candidate.get("last_activity") or candidate.get("updated_at") or candidate.get("last_seen")
            if last_activity_str:
                if isinstance(last_activity_str, datetime):
                    last_activity_date = last_activity_str
                elif isinstance(last_activity_str, str):
                    try:
                        last_activity_date = datetime.fromisoformat(last_activity_str.replace('Z', '+00:00'))
                    except ValueError:
                        last_activity_date = None
        
        recency_boost = self._calculate_recency_boost(last_activity_date)
        
        calibration_adjustment = self._get_calibration_adjustment(
            candidate_id=candidate.get("id"),
            job_id=job_requirements.get("job_id") if job_requirements else None,
            calibration_data=calibration_data
        )
        
        completeness_factor = self._calculate_completeness_factor(
            candidate, has_rubricas, has_wsi, has_prereq
        )
        
        rubricas_score_safe = rubricas_score or 0.0
        weighted_rubricas = rubricas_score_safe * weights["rubricas"]
        weighted_wsi = (wsi_score or 0.0) * weights["wsi"]
        weighted_prereq = prerequisites_score * weights["prereq"]
        weighted_recency = recency_boost * weights["recency"]
        
        breakdown = RankingScoreBreakdown(
            rubricas_score=rubricas_score_safe,
            wsi_score=wsi_score,
            prerequisites_score=prerequisites_score,
            recency_boost=recency_boost,
            calibration_adjustment=calibration_adjustment,
            completeness_factor=completeness_factor,
            weights_used=weights,
            data_availability=data_availability.value,
            weighted_rubricas=weighted_rubricas,
            weighted_wsi=weighted_wsi,
            weighted_prereq=weighted_prereq,
            weighted_recency=weighted_recency,
        )
        
        ranking_score = breakdown.calculate_final_score()
        recommendation = self._get_ranking_recommendation(ranking_score)
        reasoning = self._generate_ranking_reasoning(breakdown, recommendation)
        strengths, concerns = self._identify_ranking_strengths_concerns(breakdown, candidate)
        
        return RankingScoreResult(
            ranking_score=ranking_score,
            breakdown=breakdown,
            rank_position=None,
            recommendation=recommendation,
            strengths=strengths,
            concerns=concerns,
            reasoning=reasoning,
        )
    
    async def load_search_feedback(
        self,
        candidate_ids: list[str],
        company_id: str,
        job_id: str | None = None,
        user_id: str | None = None,
    ) -> dict[str, str]:
        """Carrega feedback de busca (like/dislike) ESCOPADO por company_id.

        STATELESS (P1-3): retorna {candidate_id: feedback_type}, sem tocar
        estado de instancia. O service e singleton compartilhado entre tenants;
        estado de instancia (cache de feedback no singleton) vazaria feedback
        cross-tenant sob concorrencia async. company_id e OBRIGATORIO
        (fail-closed multi-tenancy / REGRA ZERO). Usa tenant_session para RLS
        como defesa-em-profundidade; o WHERE company_id e a barreira real
        (a app conecta como superuser, RLS inerte na sessao).
        """
        fb_map: dict[str, str] = {}
        if not candidate_ids or not company_id:
            return fb_map
        try:
            from app.core.database import tenant_session
            from sqlalchemy import and_, select
            from lia_models.search_feedback import SearchFeedback

            conditions = [
                SearchFeedback.candidate_id.in_(candidate_ids),
                SearchFeedback.company_id == str(company_id),
            ]
            if job_id:
                conditions.append(SearchFeedback.job_id == job_id)
            if user_id:
                conditions.append(SearchFeedback.user_id == user_id)

            query = select(
                SearchFeedback.candidate_id,
                SearchFeedback.feedback_type,
            ).where(and_(*conditions)).order_by(SearchFeedback.created_at.desc())

            async with tenant_session(str(company_id)) as db:
                result = await db.execute(query)
                for cid, fb_type in result.all():
                    if cid not in fb_map:
                        fb_map[cid] = fb_type
        except Exception as exc:
            logger.warning("[LIAScore] load_search_feedback falhou (sem boost): %s", exc)
            return {}
        return fb_map

    def rank_candidates(
        self,
        candidates: list[dict[str, Any]],
        rubricas_scores: dict[str, float] | None = None,
        wsi_scores: dict[str, float] | None = None,
        job_requirements: dict[str, Any] | None = None,
        calibration_data: dict[str, Any] | None = None,
        limit: int | None = None,
    ) -> list[tuple[dict[str, Any], RankingScoreResult]]:
        """
        Rank a list of candidates by their unified ranking score.
        
        This method calculates ranking scores for all candidates and returns
        them sorted in descending order by score, with rank positions assigned.
        
        Args:
            candidates: List of candidate data dictionaries
            rubricas_scores: Dict mapping candidate_id to rubricas score
            wsi_scores: Dict mapping candidate_id to WSI score
            job_requirements: Job requirements for prerequisites evaluation
            calibration_data: Pre-fetched calibration adjustments
            limit: Maximum number of candidates to return (None for all)
        
        Returns:
            List of tuples (candidate, RankingScoreResult) sorted by ranking_score descending
        """
        rubricas_scores = rubricas_scores or {}
        wsi_scores = wsi_scores or {}
        
        results: list[tuple[dict[str, Any], RankingScoreResult]] = []
        
        for candidate in candidates:
            candidate_id = str(candidate.get("id", ""))
            
            try:
                result = self.calculate_ranking_score(
                    candidate=candidate,
                    rubricas_score=rubricas_scores.get(candidate_id),
                    wsi_score=wsi_scores.get(candidate_id),
                    job_requirements=job_requirements,
                    calibration_data=calibration_data,
                    last_activity_date=None,
                )
                results.append((candidate, result))
            except Exception as e:
                logger.warning(f"Failed to calculate ranking score for candidate {candidate_id}: {e}")
                default_breakdown = RankingScoreBreakdown(
                    rubricas_score=0.0,
                    wsi_score=None,
                    prerequisites_score=0.0,
                    recency_boost=RECENCY_BOOST_DEFAULT,
                    calibration_adjustment=0.0,
                    completeness_factor=0.5,
                )
                default_result = RankingScoreResult(
                    ranking_score=0.0,
                    breakdown=default_breakdown,
                    rank_position=None,
                    recommendation="Erro no Cálculo",
                    strengths=[],
                    concerns=["Não foi possível calcular o ranking score"],
                    reasoning="Erro ao processar dados do candidato.",
                )
                results.append((candidate, default_result))
        
        results.sort(key=lambda x: x[1].ranking_score, reverse=True)
        
        for idx, (candidate, result) in enumerate(results):
            result.rank_position = idx + 1
        
        if limit is not None:
            results = results[:limit]
        
        return results


lia_score_service = LIAScoreService()


def get_lia_score_service() -> "LIAScoreService":
    return lia_score_service

    async def _get_cultural_fit_score(self, candidate_id: str, company_id: str) -> float | None:
        """Get cultural fit score if available. Returns None if not computed."""
        try:
            from app.shared.services.cultural_fit_integration_service import cultural_fit_service
            result = await cultural_fit_service.compute_integrated_fit(
                candidate_id=candidate_id, company_id=company_id
            )
            return result.get("integrated_score") if result else None
        except Exception:
            return None

