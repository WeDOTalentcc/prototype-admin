"""
Outcome Predictor - ML models for predicting job vacancy outcomes.

Provides predictions for:
- Time to fill
- Optimal salary range
- Skill success likelihood
- Candidate fit scoring
"""
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from .feature_engineering import OutcomeFeatureEngineer, OutcomeFeatures

logger = logging.getLogger(__name__)


@dataclass
class PredictionResult:
    """Result of a prediction with confidence and explanation."""
    predicted_value: float
    confidence: float
    confidence_level: str
    explanation: str
    factors: list[dict[str, Any]]
    model_version: str
    predicted_at: datetime
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "predicted_value": self.predicted_value,
            "confidence": self.confidence,
            "confidence_level": self.confidence_level,
            "explanation": self.explanation,
            "factors": self.factors,
            "model_version": self.model_version,
            "predicted_at": self.predicted_at.isoformat(),
        }


@dataclass
class TimeToFillPrediction(PredictionResult):
    """Specific prediction for time to fill."""
    predicted_days: int
    range_min: int
    range_max: int
    comparison_to_market: str


@dataclass
class SalaryPrediction(PredictionResult):
    """Specific prediction for salary range."""
    suggested_min: float
    suggested_max: float
    market_percentile: int
    competitive_analysis: str


@dataclass
class SkillSuccessPrediction(PredictionResult):
    """Prediction for skill success likelihood."""
    skill_name: str
    success_probability: float
    historical_hires_with_skill: int
    recommendation: str


class OutcomePredictor:
    """
    ML-based predictor for job vacancy outcomes.
    
    Uses historical data and feature engineering to provide
    predictions with confidence scores and explanations.
    """
    
    MODEL_VERSION = "1.0.0"
    
    MIN_SAMPLES_FOR_ML = 30
    MIN_SAMPLES_FOR_RELIABLE = 100
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.feature_engineer = OutcomeFeatureEngineer()
        
        self.base_ttf_by_role = {
            "engineering": 35,
            "data": 40,
            "design": 30,
            "product": 35,
            "marketing": 25,
            "sales": 20,
            "hr": 22,
            "finance": 28,
            "operations": 30,
            "legal": 35,
            "other": 30,
        }
        
        self.seniority_multipliers = {
            0: 0.6,
            1: 0.7,
            2: 1.0,
            3: 1.3,
            4: 1.5,
            5: 1.8,
            6: 2.0,
            7: 2.5,
        }
    
    async def predict_time_to_fill(
        self,
        db: AsyncSession,
        job_data: dict[str, Any],
        company_id: str,
        company_data: dict[str, Any] | None = None
    ) -> TimeToFillPrediction:
        """
        Predict time to fill for a job vacancy.
        
        Args:
            db: Database session
            job_data: Job vacancy data
            company_id: Company ID
            company_data: Optional company context
            
        Returns:
            TimeToFillPrediction with predicted days and confidence
        """
        job_features = self.feature_engineer.extract_job_features(
            job_data, company_data
        )
        
        historical = await self.feature_engineer.extract_historical_features(
            db, company_id,
            role=job_data.get("role"),
            seniority=job_data.get("seniority")
        )
        
        base_days = self.base_ttf_by_role.get(job_features.role_category, 30)
        
        seniority_mult = self.seniority_multipliers.get(job_features.seniority_level, 1.0)
        
        rarity_factor = 1.0 + (job_features.skill_rarity_score * 0.5)
        
        demand_factor = 1.0 - (job_features.market_demand_score * 0.3)
        
        location_factor = 1.0
        if job_features.location_type == "remote":
            location_factor = 0.85
        elif job_features.location_type == "onsite":
            location_factor = 1.15
        
        size_factor = 1.0
        if job_features.company_size_category in ["micro", "small"]:
            size_factor = 1.1
        elif job_features.company_size_category == "enterprise":
            size_factor = 0.9
        
        urgency_factor = 0.8 if job_features.is_urgent else 1.0
        
        predicted_days = base_days * seniority_mult * rarity_factor * demand_factor * location_factor * size_factor * urgency_factor
        
        historical_weight = min(1.0, historical.success_rate * 0.5)
        if historical.avg_time_to_fill > 0:
            predicted_days = (
                predicted_days * (1 - historical_weight) +
                historical.avg_time_to_fill * historical_weight
            )
        
        predicted_days = max(7, min(180, predicted_days))
        
        range_variance = predicted_days * 0.25
        range_min = max(5, int(predicted_days - range_variance))
        range_max = int(predicted_days + range_variance)
        
        confidence = self._calculate_confidence(historical)
        
        factors = [
            {"name": "Categoria do cargo", "value": job_features.role_category, "impact": "base"},
            {"name": "Senioridade", "value": f"Nível {job_features.seniority_level}", "impact": f"{seniority_mult:.1f}x"},
            {"name": "Raridade das skills", "value": f"{job_features.skill_rarity_score:.0%}", "impact": f"+{(rarity_factor-1)*100:.0f}%"},
            {"name": "Demanda de mercado", "value": f"{job_features.market_demand_score:.0%}", "impact": f"{(demand_factor-1)*100:+.0f}%"},
            {"name": "Modalidade", "value": job_features.location_type, "impact": f"{(location_factor-1)*100:+.0f}%"},
        ]
        if historical.is_cold_start:
            factors.append({
                "name": "Dados históricos",
                "value": "Sem histórico — usando benchmarks de mercado",
                "impact": "confiança reduzida"
            })
        
        market_avg = 45
        if predicted_days < market_avg * 0.8:
            comparison = "abaixo da média do mercado"
        elif predicted_days > market_avg * 1.2:
            comparison = "acima da média do mercado"
        else:
            comparison = "dentro da média do mercado"
        
        explanation = (
            f"Estimativa baseada em benchmarks de mercado para {job_features.role_category} "
            f"{job_data.get('seniority', 'mid')} (sem histórico da empresa ainda)"
            if historical.is_cold_start else
            f"Baseado em {job_features.role_category} {job_data.get('seniority', 'mid')} "
            f"com {job_features.num_required_skills} skills requeridas e histórico da empresa"
        )
        return TimeToFillPrediction(
            predicted_value=predicted_days,
            confidence=confidence,
            confidence_level=self._confidence_level(confidence),
            explanation=explanation,
            factors=factors,
            model_version=self.MODEL_VERSION,
            predicted_at=datetime.utcnow(),
            predicted_days=int(predicted_days),
            range_min=range_min,
            range_max=range_max,
            comparison_to_market=comparison,
        )
    
    async def predict_optimal_salary(
        self,
        db: AsyncSession,
        job_data: dict[str, Any],
        company_id: str,
        market_benchmark: float | None = None
    ) -> SalaryPrediction:
        """
        Predict optimal salary range for a job vacancy.
        
        Args:
            db: Database session
            job_data: Job vacancy data
            company_id: Company ID
            market_benchmark: Optional market benchmark salary
            
        Returns:
            SalaryPrediction with suggested range and analysis
        """
        job_features = self.feature_engineer.extract_job_features(job_data)
        
        historical = await self.feature_engineer.extract_historical_features(
            db, company_id,
            role=job_data.get("role"),
            seniority=job_data.get("seniority")
        )
        
        if market_benchmark:
            base_salary = market_benchmark
        else:
            base_salaries = {
                "engineering": 12000,
                "data": 14000,
                "design": 10000,
                "product": 15000,
                "marketing": 8000,
                "sales": 7000,
                "hr": 6000,
                "finance": 9000,
                "operations": 8000,
                "legal": 12000,
                "other": 8000,
            }
            base_salary = base_salaries.get(job_features.role_category, 8000)
        
        seniority_multipliers = {
            0: 0.4,
            1: 0.6,
            2: 1.0,
            3: 1.5,
            4: 2.0,
            5: 2.5,
            6: 3.0,
            7: 4.0,
        }
        
        salary_mult = seniority_multipliers.get(job_features.seniority_level, 1.0)
        predicted_salary = base_salary * salary_mult
        
        historical_ratio = historical.avg_salary_vs_market
        if historical_ratio != 1.0:
            predicted_salary *= historical_ratio
        
        range_pct = 0.15
        suggested_min = predicted_salary * (1 - range_pct)
        suggested_max = predicted_salary * (1 + range_pct)
        
        market_percentile = 50
        if historical_ratio > 1.1:
            market_percentile = 75
        elif historical_ratio < 0.9:
            market_percentile = 25
        
        if market_percentile >= 75:
            competitive = "Acima do mercado - atrai candidatos premium"
        elif market_percentile >= 50:
            competitive = "Na média do mercado - competitivo"
        else:
            competitive = "Abaixo do mercado - pode dificultar atração"
        
        confidence = self._calculate_confidence(historical)
        
        factors = [
            {"name": "Categoria", "value": job_features.role_category, "impact": f"R$ {base_salary:,.0f} base"},
            {"name": "Senioridade", "value": f"Nível {job_features.seniority_level}", "impact": f"{salary_mult:.1f}x"},
            {"name": "Histórico empresa", "value": f"{historical_ratio:.0%} vs mercado", "impact": f"{(historical_ratio-1)*100:+.0f}%"},
        ]
        
        return SalaryPrediction(
            predicted_value=predicted_salary,
            confidence=confidence,
            confidence_level=self._confidence_level(confidence),
            explanation=f"Baseado em {job_features.role_category} nível {job_features.seniority_level}",
            factors=factors,
            model_version=self.MODEL_VERSION,
            predicted_at=datetime.utcnow(),
            suggested_min=suggested_min,
            suggested_max=suggested_max,
            market_percentile=market_percentile,
            competitive_analysis=competitive,
        )
    
    async def predict_skill_success(
        self,
        db: AsyncSession,
        skill_name: str,
        company_id: str,
        role: str | None = None
    ) -> SkillSuccessPrediction:
        """
        Predict success likelihood for a skill.
        
        Args:
            db: Database session
            skill_name: Name of the skill
            company_id: Company ID
            role: Optional role context
            
        Returns:
            SkillSuccessPrediction with success probability
        """
        from sqlalchemy import and_, select

        from app.models.company_learning import CompanySkill
        
        try:
            stmt = select(CompanySkill).where(
                and_(
                    CompanySkill.company_id == company_id,
                    CompanySkill.skill_name.ilike(f"%{skill_name}%")
                )
            )
            result = await db.execute(stmt)
            skills = result.scalars().all()
            
            if skills:
                skill = skills[0]
                times_confirmed = skill.times_confirmed
                success_prob = min(0.95, 0.5 + (times_confirmed * 0.05))
                confidence = min(0.9, 0.3 + (times_confirmed * 0.1))
                
                if skill.is_promoted:
                    recommendation = "Skill promovida - alta correlação com sucesso"
                elif times_confirmed >= 3:
                    recommendation = "Skill frequente - boa correlação com contratações"
                else:
                    recommendation = "Skill em validação - dados insuficientes"
                
                return SkillSuccessPrediction(
                    predicted_value=success_prob,
                    confidence=confidence,
                    confidence_level=self._confidence_level(confidence),
                    explanation=f"Baseado em {times_confirmed} confirmações históricas",
                    factors=[
                        {"name": "Confirmações", "value": times_confirmed, "impact": f"+{times_confirmed * 5}%"},
                        {"name": "Promovida", "value": "Sim" if skill.is_promoted else "Não", "impact": "+10%" if skill.is_promoted else "0%"},
                    ],
                    model_version=self.MODEL_VERSION,
                    predicted_at=datetime.utcnow(),
                    skill_name=skill_name,
                    success_probability=success_prob,
                    historical_hires_with_skill=times_confirmed,
                    recommendation=recommendation,
                )
            else:
                return SkillSuccessPrediction(
                    predicted_value=0.5,
                    confidence=0.3,
                    confidence_level="baixa",
                    explanation="Skill sem histórico na empresa",
                    factors=[],
                    model_version=self.MODEL_VERSION,
                    predicted_at=datetime.utcnow(),
                    skill_name=skill_name,
                    success_probability=0.5,
                    historical_hires_with_skill=0,
                    recommendation="Skill nova - considere validar com benchmark de mercado",
                )
                
        except Exception as e:
            self.logger.error(f"Error predicting skill success: {e}")
            return SkillSuccessPrediction(
                predicted_value=0.5,
                confidence=0.2,
                confidence_level="muito baixa",
                explanation="Erro ao processar predição",
                factors=[],
                model_version=self.MODEL_VERSION,
                predicted_at=datetime.utcnow(),
                skill_name=skill_name,
                success_probability=0.5,
                historical_hires_with_skill=0,
                recommendation="Erro na predição - use estimativa padrão",
            )
    
    async def get_hiring_insights(
        self,
        db: AsyncSession,
        company_id: str,
        role: str | None = None
    ) -> dict[str, Any]:
        """
        Get comprehensive hiring insights for a company/role.
        
        Returns aggregated predictions and recommendations.
        """
        historical = await self.feature_engineer.extract_historical_features(
            db, company_id, role=role
        )
        
        top_skills = await self._get_top_successful_skills(db, company_id, role)
        
        insights = {
            "summary": {
                "avg_time_to_fill": historical.avg_time_to_fill,
                "success_rate": historical.success_rate,
                "avg_candidates_per_hire": historical.avg_candidates_per_hire,
            },
            "recommendations": [],
            "top_successful_skills": top_skills,
            "confidence": self._calculate_confidence(historical),
        }
        
        if historical.avg_time_to_fill > 60:
            insights["recommendations"].append({
                "type": "warning",
                "message": "Tempo médio de contratação alto - considere revisar requisitos ou ampliar sourcing",
            })
        
        if historical.success_rate < 0.5:
            insights["recommendations"].append({
                "type": "alert",
                "message": "Taxa de sucesso abaixo de 50% - revise critérios de triagem",
            })
        
        if historical.avg_candidates_per_hire > 30:
            insights["recommendations"].append({
                "type": "optimization",
                "message": "Alto volume de candidatos por vaga - considere filtros mais específicos",
            })
        
        return insights
    
    async def _get_top_successful_skills(
        self,
        db: AsyncSession,
        company_id: str,
        role: str | None = None,
        limit: int = 10
    ) -> list[dict[str, Any]]:
        """Get top skills associated with successful hires."""
        from sqlalchemy import and_, select

        from app.models.company_learning import CompanySkill
        
        try:
            conditions = [
                CompanySkill.company_id == company_id,
                CompanySkill.times_confirmed >= 1
            ]
            
            stmt = (
                select(CompanySkill)
                .where(and_(*conditions))
                .order_by(CompanySkill.times_confirmed.desc())
                .limit(limit)
            )
            
            result = await db.execute(stmt)
            skills = result.scalars().all()
            
            return [
                {
                    "skill_name": s.skill_name,
                    "times_confirmed": s.times_confirmed,
                    "is_promoted": s.is_promoted,
                    "success_score": min(1.0, 0.5 + s.times_confirmed * 0.05),
                }
                for s in skills
            ]
            
        except Exception:
            return []
    
    def _calculate_confidence(self, historical: OutcomeFeatures) -> float:
        """Calculate overall confidence based on historical data quality."""
        if historical.avg_time_to_fill == 45.0 and historical.success_rate == 0.7:
            return 0.3
        
        base_confidence = 0.5
        
        base_confidence += historical.success_rate * 0.2
        
        if historical.avg_candidates_per_hire > 0:
            base_confidence += 0.1
        
        return min(0.95, base_confidence)
    
    def _confidence_level(self, confidence: float) -> str:
        """Convert numerical confidence to level string."""
        if confidence >= 0.8:
            return "alta"
        elif confidence >= 0.6:
            return "média"
        elif confidence >= 0.4:
            return "baixa"
        else:
            return "muito baixa"
