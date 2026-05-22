"""
Feature Engineering for Outcome Learning ML models.

Extracts and transforms features from job and candidate data
for use in predictive models.
"""
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


@dataclass
class JobFeatures:
    """Engineered features for a job vacancy."""
    role_category: str
    seniority_level: int
    department_id: str | None
    location_type: str
    salary_min: float
    salary_max: float
    salary_midpoint: float
    num_required_skills: int
    num_nice_to_have_skills: int
    has_remote_option: bool
    has_relocation: bool
    company_size_category: str
    industry_category: str
    creation_month: int
    creation_quarter: int
    creation_day_of_week: int
    is_urgent: bool
    skill_rarity_score: float
    market_demand_score: float
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "role_category": self.role_category,
            "seniority_level": self.seniority_level,
            "department_id": self.department_id,
            "location_type": self.location_type,
            "salary_min": self.salary_min,
            "salary_max": self.salary_max,
            "salary_midpoint": self.salary_midpoint,
            "num_required_skills": self.num_required_skills,
            "num_nice_to_have_skills": self.num_nice_to_have_skills,
            "has_remote_option": self.has_remote_option,
            "has_relocation": self.has_relocation,
            "company_size_category": self.company_size_category,
            "industry_category": self.industry_category,
            "creation_month": self.creation_month,
            "creation_quarter": self.creation_quarter,
            "creation_day_of_week": self.creation_day_of_week,
            "is_urgent": self.is_urgent,
            "skill_rarity_score": self.skill_rarity_score,
            "market_demand_score": self.market_demand_score,
        }


@dataclass
class OutcomeFeatures:
    """Features extracted from historical outcomes."""
    avg_time_to_fill: float
    median_time_to_fill: float
    success_rate: float
    avg_candidates_per_hire: float
    avg_salary_vs_market: float
    skill_match_rate: float
    sourcing_channel_effectiveness: dict[str, float]
    stage_conversion_rates: dict[str, float]
    is_cold_start: bool = False


class OutcomeFeatureEngineer:
    """
    Feature engineering service for ML models.
    
    Extracts meaningful features from job and outcome data
    to improve prediction accuracy.
    """
    
    SENIORITY_MAPPING = {
        "intern": 0,
        "junior": 1,
        "pleno": 2,
        "mid": 2,
        "senior": 3,
        "lead": 4,
        "principal": 5,
        "staff": 5,
        "manager": 4,
        "director": 5,
        "vp": 6,
        "c-level": 7,
    }
    
    COMPANY_SIZE_CATEGORIES = {
        (0, 10): "micro",
        (11, 50): "small",
        (51, 200): "medium",
        (201, 1000): "large",
        (1001, float('inf')): "enterprise",
    }
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def extract_job_features(
        self,
        job_data: dict[str, Any],
        company_data: dict[str, Any] | None = None,
        market_data: dict[str, Any] | None = None
    ) -> JobFeatures:
        """
        Extract features from job vacancy data.
        
        Args:
            job_data: Dictionary with job vacancy information
            company_data: Optional company context
            market_data: Optional market benchmark data
            
        Returns:
            JobFeatures dataclass with engineered features
        """
        seniority_raw = job_data.get("seniority", "mid").lower()
        seniority_level = self.SENIORITY_MAPPING.get(seniority_raw, 2)
        
        salary_min = job_data.get("salary_min", 0) or 0
        salary_max = job_data.get("salary_max", 0) or salary_min
        salary_midpoint = (salary_min + salary_max) / 2 if (salary_min + salary_max) > 0 else 0
        
        skills = job_data.get("required_skills", []) or []
        nice_to_have = job_data.get("nice_to_have_skills", []) or []
        
        created_at = job_data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        elif not created_at:
            created_at = datetime.now()
        
        location_type = "hybrid"
        if job_data.get("is_remote"):
            location_type = "remote"
        elif job_data.get("is_onsite"):
            location_type = "onsite"
        
        company_size = 100
        if company_data:
            company_size = company_data.get("employee_count", 100)
        company_size_cat = self._categorize_company_size(company_size)
        
        skill_rarity = self._calculate_skill_rarity(skills, market_data)
        market_demand = self._calculate_market_demand(
            job_data.get("role", ""),
            seniority_raw,
            market_data
        )
        
        return JobFeatures(
            role_category=self._categorize_role(job_data.get("role", "")),
            seniority_level=seniority_level,
            department_id=job_data.get("department_id"),
            location_type=location_type,
            salary_min=salary_min,
            salary_max=salary_max,
            salary_midpoint=salary_midpoint,
            num_required_skills=len(skills),
            num_nice_to_have_skills=len(nice_to_have),
            has_remote_option=job_data.get("is_remote", False),
            has_relocation=job_data.get("offers_relocation", False),
            company_size_category=company_size_cat,
            industry_category=company_data.get("industry", "other") if company_data else "other",
            creation_month=created_at.month,
            creation_quarter=(created_at.month - 1) // 3 + 1,
            creation_day_of_week=created_at.weekday(),
            is_urgent=job_data.get("is_urgent", False),
            skill_rarity_score=skill_rarity,
            market_demand_score=market_demand,
        )
    
    async def extract_historical_features(
        self,
        db: AsyncSession,
        company_id: str,
        role: str | None = None,
        seniority: str | None = None,
        lookback_days: int = 365
    ) -> OutcomeFeatures:
        """
        Extract features from historical outcomes.
        
        Args:
            db: Database session
            company_id: Company ID to filter
            role: Optional role to filter
            seniority: Optional seniority to filter
            lookback_days: Number of days to look back
            
        Returns:
            OutcomeFeatures with aggregated historical data
        """
        from app.models.feedback_learning import JobOutcome
        
        cutoff_date = datetime.utcnow() - timedelta(days=lookback_days)
        
        try:
            conditions = [
                JobOutcome.company_id == company_id,
                JobOutcome.created_at >= cutoff_date
            ]
            
            if role:
                conditions.append(JobOutcome.role == role)
            if seniority:
                conditions.append(JobOutcome.seniority == seniority)
            
            # TENANT-EXEMPT: query uses dynamic conditions=[Model.company_id==X, ...] builder; AST sensor cannot trace; T-RATCHET tenant_filter
            stmt = select(JobOutcome).where(and_(*conditions))
            result = await db.execute(stmt)
            outcomes = result.scalars().all()
            
            if not outcomes:
                return self._get_default_outcome_features()
            
            times_to_fill = [o.time_to_fill_days for o in outcomes if o.time_to_fill_days]
            success_count = sum(1 for o in outcomes if o.outcome_type == "filled")
            
            avg_ttf = sum(times_to_fill) / len(times_to_fill) if times_to_fill else 45.0
            
            sorted_ttf = sorted(times_to_fill)
            median_ttf = sorted_ttf[len(sorted_ttf) // 2] if sorted_ttf else 45.0
            
            success_rate = success_count / len(outcomes) if outcomes else 0.0
            
            total_candidates = sum(o.total_candidates or 0 for o in outcomes)
            avg_candidates = total_candidates / success_count if success_count > 0 else 20.0
            
            salary_ratios = []
            for o in outcomes:
                if o.final_salary and o.market_salary_benchmark:
                    salary_ratios.append(o.final_salary / o.market_salary_benchmark)
            avg_salary_ratio = sum(salary_ratios) / len(salary_ratios) if salary_ratios else 1.0
            
            sourcing_effectiveness: dict[str, float] = {}
            stage_conversions: dict[str, float] = {}
            
            return OutcomeFeatures(
                avg_time_to_fill=avg_ttf,
                median_time_to_fill=median_ttf,
                success_rate=success_rate,
                avg_candidates_per_hire=avg_candidates,
                avg_salary_vs_market=avg_salary_ratio,
                skill_match_rate=0.85,
                sourcing_channel_effectiveness=sourcing_effectiveness,
                stage_conversion_rates=stage_conversions,
            )
            
        except Exception as e:
            self.logger.error(f"Error extracting historical features: {e}")
            return self._get_default_outcome_features()
    
    def _categorize_role(self, role: str) -> str:
        """Categorize role into standard categories."""
        role_lower = role.lower()
        
        if any(kw in role_lower for kw in ["develop", "engineer", "programm", "dev", "backend", "frontend", "full"]):
            return "engineering"
        elif any(kw in role_lower for kw in ["data", "analyst", "scientist", "analytics", "bi"]):
            return "data"
        elif any(kw in role_lower for kw in ["design", "ux", "ui", "product design"]):
            return "design"
        elif any(kw in role_lower for kw in ["product", "pm", "owner"]):
            return "product"
        elif any(kw in role_lower for kw in ["market", "growth", "seo", "content"]):
            return "marketing"
        elif any(kw in role_lower for kw in ["sales", "vendas", "account", "business dev"]):
            return "sales"
        elif any(kw in role_lower for kw in ["hr", "people", "talent", "recru"]):
            return "hr"
        elif any(kw in role_lower for kw in ["finance", "contab", "financ"]):
            return "finance"
        elif any(kw in role_lower for kw in ["ops", "operation", "devops", "sre", "infra"]):
            return "operations"
        elif any(kw in role_lower for kw in ["legal", "jurídic", "compliance"]):
            return "legal"
        else:
            return "other"
    
    def _categorize_company_size(self, employee_count: int) -> str:
        """Categorize company by size."""
        for (min_size, max_size), category in self.COMPANY_SIZE_CATEGORIES.items():
            if min_size <= employee_count <= max_size:
                return category
        return "medium"
    
    def _calculate_skill_rarity(
        self,
        skills: list[str],
        market_data: dict[str, Any] | None
    ) -> float:
        """
        Calculate rarity score for skill set.
        Higher score = rarer skills = harder to find.
        """
        if not skills:
            return 0.5
        
        rare_keywords = [
            "rust", "golang", "scala", "elixir", "haskell",
            "kubernetes", "terraform", "mlops", "ml engineer",
            "blockchain", "solidity", "web3",
            "staff", "principal", "architect"
        ]
        
        rare_count = 0
        for skill in skills:
            skill_lower = skill.lower()
            if any(kw in skill_lower for kw in rare_keywords):
                rare_count += 1
        
        rarity_score = min(1.0, 0.3 + (rare_count / len(skills)) * 0.7)
        return rarity_score
    
    def _calculate_market_demand(
        self,
        role: str,
        seniority: str,
        market_data: dict[str, Any] | None
    ) -> float:
        """
        Calculate market demand score.
        Higher score = higher demand = faster to fill.
        """
        high_demand_roles = [
            "developer", "engineer", "data", "devops", "sre",
            "product", "design", "ux"
        ]
        
        role_lower = role.lower()
        base_demand = 0.5
        
        if any(kw in role_lower for kw in high_demand_roles):
            base_demand = 0.7
        
        seniority_lower = seniority.lower()
        if seniority_lower in ["senior", "lead", "principal", "staff"]:
            base_demand += 0.15
        elif seniority_lower in ["junior", "intern"]:
            base_demand -= 0.1
        
        return min(1.0, max(0.0, base_demand))
    
    def _get_default_outcome_features(self) -> OutcomeFeatures:
        """Return default features when no historical data available (cold start)."""
        return OutcomeFeatures(
            avg_time_to_fill=45.0,
            median_time_to_fill=40.0,
            success_rate=0.7,
            avg_candidates_per_hire=20.0,
            avg_salary_vs_market=1.0,
            skill_match_rate=0.8,
            sourcing_channel_effectiveness={},
            stage_conversion_rates={},
            is_cold_start=True,
        )
    
    def create_feature_vector(
        self,
        job_features: JobFeatures,
        outcome_features: OutcomeFeatures | None = None
    ) -> list[float]:
        """
        Create numerical feature vector for ML model.
        
        Args:
            job_features: Job-level features
            outcome_features: Historical outcome features
            
        Returns:
            List of numerical features for model input
        """
        role_categories = ["engineering", "data", "design", "product", "marketing", "sales", "hr", "finance", "operations", "legal", "other"]
        role_one_hot = [1.0 if job_features.role_category == cat else 0.0 for cat in role_categories]
        
        location_types = ["remote", "hybrid", "onsite"]
        location_one_hot = [1.0 if job_features.location_type == lt else 0.0 for lt in location_types]
        
        size_categories = ["micro", "small", "medium", "large", "enterprise"]
        size_one_hot = [1.0 if job_features.company_size_category == sc else 0.0 for sc in size_categories]
        
        vector = []
        
        vector.extend(role_one_hot)
        vector.append(float(job_features.seniority_level) / 7.0)
        vector.extend(location_one_hot)
        vector.append(job_features.salary_midpoint / 50000.0)
        vector.append(float(job_features.num_required_skills) / 20.0)
        vector.append(float(job_features.num_nice_to_have_skills) / 10.0)
        vector.append(1.0 if job_features.has_remote_option else 0.0)
        vector.extend(size_one_hot)
        vector.append(float(job_features.creation_month) / 12.0)
        vector.append(float(job_features.creation_quarter) / 4.0)
        vector.append(1.0 if job_features.is_urgent else 0.0)
        vector.append(job_features.skill_rarity_score)
        vector.append(job_features.market_demand_score)
        
        if outcome_features:
            vector.append(outcome_features.avg_time_to_fill / 90.0)
            vector.append(outcome_features.success_rate)
            vector.append(outcome_features.avg_candidates_per_hire / 50.0)
            vector.append(outcome_features.avg_salary_vs_market)
        else:
            vector.extend([0.5, 0.7, 0.4, 1.0])
        
        return vector
