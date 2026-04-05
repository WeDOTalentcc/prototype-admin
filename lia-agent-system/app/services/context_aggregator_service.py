"""
ContextAggregatorService - Agrega contexto de todos os serviços para alimentar o LLM.

Este serviço consolida informações de:
- Empresa (configurações, benefícios, departamentos)
- Histórico (vagas anteriores, padrões de sucesso)
- Catálogos (skills, responsabilidades)
- Sessão atual (campos preenchidos, correções)
"""
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.job_vacancy import JobVacancy
from app.models.company import CompanyProfile, Department
from app.models.company_benefit import CompanyBenefit

logger = logging.getLogger(__name__)


@dataclass
class CompanyContext:
    """Contexto da empresa."""
    id: str
    name: str
    industry: Optional[str] = None
    size: Optional[str] = None
    culture_insights: Optional[Dict[str, Any]] = None
    
    departments: List[Dict[str, Any]] = field(default_factory=list)
    benefits: List[Dict[str, Any]] = field(default_factory=list)
    
    common_skills: List[str] = field(default_factory=list)
    common_responsibilities: List[str] = field(default_factory=list)
    
    avg_salary_by_level: Dict[str, float] = field(default_factory=dict)
    common_work_models: List[str] = field(default_factory=list)
    common_locations: List[str] = field(default_factory=list)


@dataclass
class HistoricalContext:
    """Contexto histórico de vagas."""
    total_vacancies: int = 0
    vacancies_last_year: int = 0
    avg_time_to_fill: Optional[float] = None
    
    recent_vacancies: List[Dict[str, Any]] = field(default_factory=list)
    successful_hires: List[Dict[str, Any]] = field(default_factory=list)
    
    common_roles: List[str] = field(default_factory=list)
    common_requirements: List[str] = field(default_factory=list)


@dataclass 
class SessionContext:
    """Contexto da sessão atual do wizard."""
    session_id: str
    stage: int = 1
    started_at: datetime = field(default_factory=datetime.utcnow)
    
    filled_fields: Dict[str, Any] = field(default_factory=dict)
    corrections_made: List[Dict[str, Any]] = field(default_factory=list)
    questions_asked: List[str] = field(default_factory=list)
    
    current_cargo: Optional[str] = None
    current_area: Optional[str] = None


@dataclass
class AggregatedContext:
    """Contexto completo agregado para o LLM."""
    company: CompanyContext
    historical: HistoricalContext
    session: SessionContext
    
    generated_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_prompt_context(self) -> str:
        """Converte para string formatada para incluir no prompt do LLM."""
        lines = []
        
        lines.append("## Contexto da Empresa")
        lines.append(f"- Nome: {self.company.name}")
        if self.company.industry:
            lines.append(f"- Setor: {self.company.industry}")
        if self.company.size:
            lines.append(f"- Porte: {self.company.size}")
        
        if self.company.departments:
            dept_names = [d.get("name", "") for d in self.company.departments[:5]]
            lines.append(f"- Departamentos: {', '.join(dept_names)}")
        
        if self.company.benefits:
            benefit_names = [b.get("name", "") for b in self.company.benefits[:10]]
            lines.append(f"- Benefícios disponíveis: {', '.join(benefit_names)}")
        
        if self.company.common_locations:
            lines.append(f"- Localizações comuns: {', '.join(self.company.common_locations[:5])}")
        
        if self.company.common_work_models:
            lines.append(f"- Modelos de trabalho comuns: {', '.join(self.company.common_work_models)}")
        
        lines.append("")
        lines.append("## Histórico de Vagas")
        lines.append(f"- Total de vagas criadas: {self.historical.total_vacancies}")
        if self.historical.avg_time_to_fill:
            lines.append(f"- Tempo médio para preencher: {self.historical.avg_time_to_fill:.0f} dias")
        
        if self.historical.common_roles:
            lines.append(f"- Cargos mais comuns: {', '.join(self.historical.common_roles[:5])}")
        
        if self.historical.recent_vacancies:
            lines.append("- Vagas recentes:")
            for v in self.historical.recent_vacancies[:3]:
                lines.append(f"  * {v.get('title', 'N/A')} ({v.get('status', 'N/A')})")
        
        lines.append("")
        lines.append("## Sessão Atual")
        lines.append(f"- Estágio do wizard: {self.session.stage}/5")
        
        if self.session.filled_fields:
            filled = list(self.session.filled_fields.keys())
            lines.append(f"- Campos preenchidos: {', '.join(filled)}")
        
        if self.session.current_cargo:
            lines.append(f"- Cargo atual: {self.session.current_cargo}")
        
        if self.session.corrections_made:
            lines.append(f"- Correções feitas: {len(self.session.corrections_made)}")
        
        return "\n".join(lines)


class ContextAggregatorService:
    """
    Serviço que agrega contexto de múltiplas fontes para alimentar o LLM.
    """
    
    _cache: Dict[str, AggregatedContext] = {}
    _cache_ttl_seconds: int = 300
    
    async def get_full_context(
        self,
        company_id: str,
        session_id: str,
        db: AsyncSession,
        stage: int = 1,
        filled_fields: Optional[Dict[str, Any]] = None
    ) -> AggregatedContext:
        """
        Obtém contexto completo para uma sessão.
        
        Args:
            company_id: ID da empresa
            session_id: ID da sessão
            db: Sessão do banco de dados
            stage: Estágio atual do wizard
            filled_fields: Campos já preenchidos
            
        Returns:
            AggregatedContext com todas as informações
        """
        cache_key = f"{company_id}:{session_id}"
        
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            age = (datetime.utcnow() - cached.generated_at).total_seconds()
            if age < self._cache_ttl_seconds:
                cached.session.stage = stage
                cached.session.filled_fields = filled_fields or {}
                return cached
        
        company_context = await self._get_company_context(company_id, db)
        historical_context = await self._get_historical_context(company_id, db)
        session_context = SessionContext(
            session_id=session_id,
            stage=stage,
            filled_fields=filled_fields or {}
        )
        
        if filled_fields:
            session_context.current_cargo = filled_fields.get("cargo") or filled_fields.get("title")
            session_context.current_area = filled_fields.get("area") or filled_fields.get("department")
        
        context = AggregatedContext(
            company=company_context,
            historical=historical_context,
            session=session_context
        )
        
        self._cache[cache_key] = context
        
        return context

    async def _get_company_context(self, company_id: str, db: AsyncSession) -> CompanyContext:
        """Obtém contexto da empresa."""
        try:
            result = await db.execute(
                select(CompanyProfile).where(CompanyProfile.is_active == True).limit(1)
            )
            company = result.scalar_one_or_none()
            
            if not company:
                return CompanyContext(id=company_id, name="Empresa")
            
            dept_result = await db.execute(
                select(Department)
                .where(Department.company_id == company.id)
                .where(Department.is_active == True)
                .order_by(Department.name)
            )
            departments = dept_result.scalars().all()
            
            benefit_result = await db.execute(
                select(CompanyBenefit)
                .where(CompanyBenefit.company_id == company_id)
                .where(CompanyBenefit.is_active == True)
                .order_by(CompanyBenefit.order)
            )
            benefits = benefit_result.scalars().all()
            
            locations_result = await db.execute(
                select(JobVacancy.location, func.count(JobVacancy.id).label("count"))
                .where(JobVacancy.company_id == company_id)
                .where(JobVacancy.location.isnot(None))
                .group_by(JobVacancy.location)
                .order_by(func.count(JobVacancy.id).desc())
                .limit(5)
            )
            locations = [row[0] for row in locations_result.fetchall() if row[0]]
            
            work_models_result = await db.execute(
                select(JobVacancy.work_model, func.count(JobVacancy.id).label("count"))
                .where(JobVacancy.company_id == company_id)
                .where(JobVacancy.work_model.isnot(None))
                .group_by(JobVacancy.work_model)
                .order_by(func.count(JobVacancy.id).desc())
            )
            work_models = [row[0] for row in work_models_result.fetchall() if row[0]]
            
            common_skills = []
            
            return CompanyContext(
                id=company_id,
                name=company.name or "Empresa",
                industry=company.industry,
                size=company.company_size,
                culture_insights=company.culture_insights,
                departments=[
                    {"id": str(d.id), "name": d.name, "manager": d.manager_name}
                    for d in departments
                ],
                benefits=[
                    {"name": b.name, "category": b.category, "value": b.value}
                    for b in benefits
                ],
                common_skills=common_skills,
                common_locations=locations,
                common_work_models=work_models
            )
            
        except Exception as e:
            logger.error(f"Error getting company context: {e}")
            return CompanyContext(id=company_id, name="Empresa")

    async def _get_historical_context(self, company_id: str, db: AsyncSession) -> HistoricalContext:
        """Obtém contexto histórico de vagas."""
        try:
            effective_company_id = company_id
            
            total_result = await db.execute(
                select(func.count(JobVacancy.id))
                .where(JobVacancy.company_id == effective_company_id)
            )
            total = total_result.scalar() or 0
            
            recent_result = await db.execute(
                select(JobVacancy)
                .where(JobVacancy.company_id == effective_company_id)
                .order_by(JobVacancy.created_at.desc())
                .limit(10)
            )
            recent_vacancies = recent_result.scalars().all()
            
            roles_result = await db.execute(
                select(JobVacancy.title, func.count(JobVacancy.id).label("count"))
                .where(JobVacancy.company_id == effective_company_id)
                .group_by(JobVacancy.title)
                .order_by(func.count(JobVacancy.id).desc())
                .limit(10)
            )
            common_roles = [row[0] for row in roles_result.fetchall() if row[0]]
            
            return HistoricalContext(
                total_vacancies=total,
                recent_vacancies=[
                    {
                        "id": str(v.id),
                        "title": v.title,
                        "department": v.department,
                        "status": v.status,
                        "created_at": v.created_at.isoformat() if v.created_at else None
                    }
                    for v in recent_vacancies
                ],
                common_roles=common_roles
            )
            
        except Exception as e:
            logger.error(f"Error getting historical context: {e}")
            return HistoricalContext()

    def update_session_context(
        self,
        company_id: str,
        session_id: str,
        filled_fields: Optional[Dict[str, Any]] = None,
        correction: Optional[Dict[str, Any]] = None,
        question: Optional[str] = None
    ):
        """Atualiza o contexto da sessão."""
        cache_key = f"{company_id}:{session_id}"
        
        if cache_key not in self._cache:
            return
        
        context = self._cache[cache_key]
        
        if filled_fields:
            context.session.filled_fields.update(filled_fields)
        
        if correction:
            context.session.corrections_made.append(correction)
        
        if question:
            context.session.questions_asked.append(question)

    def clear_cache(self, company_id: Optional[str] = None):
        """Limpa o cache de contexto."""
        if company_id:
            keys_to_remove = [k for k in self._cache.keys() if k.startswith(f"{company_id}:")]
            for key in keys_to_remove:
                del self._cache[key]
        else:
            self._cache.clear()


context_aggregator = ContextAggregatorService()
