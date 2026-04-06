"""
ATS Job History Service - Fetches historical job descriptions from connected ATSs.

Provides access to job descriptions and vacancy data from:
- Gupy
- Pandapé
- Merge (unified connector)

This data enriches the Job Wizard with:
- Historical salary ranges for similar positions
- Common skills patterns
- Job description templates
- Time-to-fill benchmarks
"""
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum, StrEnum
from typing import Any


logger = logging.getLogger(__name__)


class ATSJobStatus(StrEnum):
    """Job status in ATS."""
    OPEN = "open"
    FILLED = "filled"
    CLOSED = "closed"
    PAUSED = "paused"
    DRAFT = "draft"


@dataclass
class ATSJobDescription:
    """Standardized job description from any ATS."""
    ats_job_id: str
    ats_type: str
    title: str
    department: str | None = None
    location: str | None = None
    work_model: str | None = None
    seniority: str | None = None
    status: ATSJobStatus | None = None
    salary_min: float | None = None
    salary_max: float | None = None
    salary_currency: str = "BRL"
    skills: list[str] | None = None
    responsibilities: list[str] | None = None
    requirements: list[str] | None = None
    benefits: list[str] | None = None
    description_text: str | None = None
    created_at: datetime | None = None
    closed_at: datetime | None = None
    time_to_fill_days: int | None = None
    applications_count: int | None = None
    hired_count: int | None = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "ats_job_id": self.ats_job_id,
            "ats_type": self.ats_type,
            "title": self.title,
            "department": self.department,
            "location": self.location,
            "work_model": self.work_model,
            "seniority": self.seniority,
            "status": self.status.value if self.status else None,
            "salary_min": self.salary_min,
            "salary_max": self.salary_max,
            "salary_currency": self.salary_currency,
            "skills": self.skills,
            "responsibilities": self.responsibilities,
            "requirements": self.requirements,
            "benefits": self.benefits,
            "description_text": self.description_text,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "closed_at": self.closed_at.isoformat() if self.closed_at else None,
            "time_to_fill_days": self.time_to_fill_days,
            "applications_count": self.applications_count,
            "hired_count": self.hired_count
        }


@dataclass
class ATSSalaryInsight:
    """Salary insight from ATS historical data."""
    min_salary: float
    max_salary: float
    median_salary: float
    average_salary: float
    sample_size: int
    confidence: str
    ats_type: str
    role_match: str
    seniority_match: str | None = None
    location_match: str | None = None


@dataclass
class ATSSkillInsight:
    """Skill insight from ATS historical data."""
    skill_name: str
    frequency: int
    percentage: float
    ats_type: str
    role_context: str


class ATSJobHistoryService:
    """
    Service for fetching and analyzing historical job data from connected ATSs.
    
    Features:
    - Fetch job listings from multiple ATS providers
    - Normalize data to standard format
    - Extract salary benchmarks
    - Identify common skills patterns
    - Cache results for performance
    """
    
    ROLE_SIMILARITY_KEYWORDS = {
        "desenvolvedor": ["developer", "dev", "engenheiro", "programmer"],
        "analista": ["analyst", "especialista"],
        "gerente": ["manager", "head", "líder", "lider"],
        "coordenador": ["coordinator", "supervisor"],
        "designer": ["ux", "ui", "product designer"],
        "data": ["dados", "analytics", "bi", "scientist"],
        "devops": ["sre", "platform", "infrastructure", "infra"],
        "qa": ["quality", "tester", "test", "automação"],
        "product": ["produto", "pm", "owner"],
    }
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._ats_service = None
    
    def _get_ats_service(self):
        """Lazy load ATS sync service to avoid circular imports."""
        if self._ats_service is None:
            from app.domains.ats_integration.services.ats_sync_service import ats_sync_service
            self._ats_service = ats_sync_service
        return self._ats_service
    
    def _normalize_role(self, role: str) -> list[str]:
        """Normalize role name for matching."""
        role_lower = role.lower()
        variations = [role_lower]
        
        for base, synonyms in self.ROLE_SIMILARITY_KEYWORDS.items():
            if base in role_lower or any(s in role_lower for s in synonyms):
                variations.extend(synonyms)
                variations.append(base)
        
        return list(set(variations))
    
    def _role_matches(self, job_title: str, target_role: str) -> bool:
        """Check if job title matches target role."""
        job_lower = job_title.lower()
        target_variations = self._normalize_role(target_role)
        
        return any(var in job_lower for var in target_variations)
    
    def _extract_seniority(self, title: str) -> str | None:
        """Extract seniority level from job title."""
        title_lower = title.lower()
        
        seniority_keywords = {
            "júnior": ["junior", "júnior", "jr", "trainee", "estagiário"],
            "pleno": ["pleno", "mid", "mid-level"],
            "sênior": ["senior", "sênior", "sr", "lead"],
            "especialista": ["especialista", "specialist", "principal", "staff"],
            "gerente": ["gerente", "manager", "head", "diretor", "director"],
        }
        
        for level, keywords in seniority_keywords.items():
            if any(kw in title_lower for kw in keywords):
                return level
        
        return None
    
    async def get_jobs_from_ats(
        self,
        ats_type: str,
        company_id: str,
        status: ATSJobStatus | None = None,
        months_back: int = 12,
        limit: int = 100
    ) -> list[ATSJobDescription]:
        """
        Fetch jobs from a specific ATS.
        
        Args:
            ats_type: Type of ATS (gupy, pandape, merge)
            company_id: Company ID for scoping
            status: Filter by job status
            months_back: How many months of history to fetch
            limit: Maximum number of jobs to return
        
        Returns:
            List of normalized job descriptions
        """
        ats_service = self._get_ats_service()
        client = ats_service.get_client(ats_type)
        
        if not client:
            self.logger.warning(f"No ATS client configured for {ats_type}")
            return []
        
        try:
            if hasattr(client, 'get_jobs'):
                cutoff_date = datetime.utcnow() - timedelta(days=months_back * 30)
                raw_jobs = await client.get_jobs(
                    status=status.value if status else None,
                    created_after=cutoff_date,
                    limit=limit
                )
                
                return [
                    self._normalize_job(job, ats_type)
                    for job in raw_jobs
                ]
            else:
                self.logger.warning(f"ATS client {ats_type} does not support job fetching")
                return []
                
        except Exception as e:
            self.logger.error(f"Error fetching jobs from {ats_type}: {e}")
            return []
    
    def _normalize_job(self, raw_job: dict[str, Any], ats_type: str) -> ATSJobDescription:
        """Normalize job data from specific ATS format to standard format."""
        if ats_type == "gupy":
            return self._normalize_gupy_job(raw_job)
        elif ats_type == "pandape":
            return self._normalize_pandape_job(raw_job)
        elif ats_type in ["merge"]:
            return self._normalize_unified_job(raw_job, ats_type)
        else:
            return self._normalize_generic_job(raw_job, ats_type)
    
    def _normalize_gupy_job(self, job: dict[str, Any]) -> ATSJobDescription:
        """Normalize Gupy job format."""
        salary_data = job.get("salary", {}) or {}
        
        return ATSJobDescription(
            ats_job_id=str(job.get("id", "")),
            ats_type="gupy",
            title=job.get("name", "") or job.get("title", ""),
            department=job.get("department", {}).get("name") if isinstance(job.get("department"), dict) else job.get("department"),
            location=job.get("city", "") or job.get("location", ""),
            work_model=self._map_work_model(job.get("workplaceType", "")),
            seniority=self._extract_seniority(job.get("name", "")),
            status=self._map_status(job.get("status", "")),
            salary_min=salary_data.get("min") or salary_data.get("from"),
            salary_max=salary_data.get("max") or salary_data.get("to"),
            skills=job.get("skills", []),
            description_text=job.get("description", ""),
            created_at=self._parse_date(job.get("createdAt")),
            closed_at=self._parse_date(job.get("closedAt")),
            applications_count=job.get("applicationsCount", 0)
        )
    
    def _normalize_pandape_job(self, job: dict[str, Any]) -> ATSJobDescription:
        """Normalize Pandapé job format."""
        return ATSJobDescription(
            ats_job_id=str(job.get("id", "")),
            ats_type="pandape",
            title=job.get("titulo", "") or job.get("title", ""),
            department=job.get("area", "") or job.get("departamento", ""),
            location=job.get("cidade", "") or job.get("local", ""),
            work_model=self._map_work_model(job.get("modelo_trabalho", "")),
            seniority=job.get("nivel", "") or self._extract_seniority(job.get("titulo", "")),
            status=self._map_status(job.get("situacao", "") or job.get("status", "")),
            salary_min=job.get("salario_minimo") or job.get("faixa_salarial", {}).get("min"),
            salary_max=job.get("salario_maximo") or job.get("faixa_salarial", {}).get("max"),
            skills=job.get("competencias", []) or job.get("skills", []),
            description_text=job.get("descricao", ""),
            created_at=self._parse_date(job.get("data_criacao")),
            closed_at=self._parse_date(job.get("data_fechamento"))
        )
    
    def _normalize_unified_job(self, job: dict[str, Any], ats_type: str) -> ATSJobDescription:
        """Normalize Merge unified format."""
        compensation = job.get("compensation", {}) or {}
        
        return ATSJobDescription(
            ats_job_id=str(job.get("id", "")),
            ats_type=ats_type,
            title=job.get("title", "") or job.get("name", ""),
            department=job.get("department", ""),
            location=self._extract_location(job.get("locations", [])),
            work_model=self._map_work_model(job.get("remote_status", "")),
            seniority=self._extract_seniority(job.get("title", "")),
            status=self._map_status(job.get("status", "")),
            salary_min=compensation.get("min") or compensation.get("low"),
            salary_max=compensation.get("max") or compensation.get("high"),
            description_text=job.get("description", ""),
            created_at=self._parse_date(job.get("created_at")),
            closed_at=self._parse_date(job.get("closed_at"))
        )
    
    def _normalize_generic_job(self, job: dict[str, Any], ats_type: str) -> ATSJobDescription:
        """Fallback normalization for unknown ATS formats."""
        return ATSJobDescription(
            ats_job_id=str(job.get("id", "")),
            ats_type=ats_type,
            title=job.get("title", "") or job.get("name", ""),
            department=job.get("department", ""),
            location=job.get("location", ""),
            description_text=job.get("description", "")
        )
    
    def _map_work_model(self, value: str) -> str | None:
        """Map ATS work model to standard format."""
        value_lower = str(value).lower()
        
        if any(kw in value_lower for kw in ["remote", "remoto"]):
            return "remoto"
        elif any(kw in value_lower for kw in ["hybrid", "híbrido", "hibrido"]):
            return "híbrido"
        elif any(kw in value_lower for kw in ["presencial", "onsite", "office"]):
            return "presencial"
        
        return None
    
    def _map_status(self, value: str) -> ATSJobStatus | None:
        """Map ATS status to standard enum."""
        value_lower = str(value).lower()
        
        status_map = {
            ATSJobStatus.OPEN: ["open", "aberta", "ativo", "active", "published"],
            ATSJobStatus.FILLED: ["filled", "preenchida", "contratado", "hired"],
            ATSJobStatus.CLOSED: ["closed", "fechada", "encerrada", "cancelled"],
            ATSJobStatus.PAUSED: ["paused", "pausada", "on_hold"],
            ATSJobStatus.DRAFT: ["draft", "rascunho"],
        }
        
        for status, keywords in status_map.items():
            if any(kw in value_lower for kw in keywords):
                return status
        
        return None
    
    def _extract_location(self, locations: list[Any]) -> str | None:
        """Extract primary location from locations list."""
        if not locations:
            return None
        
        if isinstance(locations[0], dict):
            return locations[0].get("city") or locations[0].get("name")
        
        return str(locations[0])
    
    def _parse_date(self, value: Any) -> datetime | None:
        """Parse date from various formats."""
        if not value:
            return None
        
        if isinstance(value, datetime):
            return value
        
        try:
            if isinstance(value, str):
                for fmt in ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%d/%m/%Y"]:
                    try:
                        return datetime.strptime(value[:19], fmt)
                    except ValueError:
                        continue
        except Exception:
            pass
        
        return None
    
    async def get_salary_insights(
        self,
        company_id: str,
        role: str,
        seniority: str | None = None,
        location: str | None = None,
        months_back: int = 12
    ) -> ATSSalaryInsight | None:
        """
        Get salary insights from ATS historical data.
        
        Aggregates salary data from all connected ATSs for similar roles.
        """
        ats_service = self._get_ats_service()
        all_salaries = []
        ats_sources = []
        
        for ats_type in ["gupy", "pandape", "merge"]:
            if not ats_service.has_client(ats_type):
                continue
            
            jobs = await self.get_jobs_from_ats(
                ats_type=ats_type,
                company_id=company_id,
                months_back=months_back,
                limit=200
            )
            
            for job in jobs:
                if not self._role_matches(job.title, role):
                    continue
                
                if seniority:
                    job_seniority = job.seniority or self._extract_seniority(job.title)
                    if job_seniority and seniority.lower() not in job_seniority.lower():
                        continue
                
                if job.salary_min and job.salary_max:
                    all_salaries.append({
                        "min": job.salary_min,
                        "max": job.salary_max,
                        "mid": (job.salary_min + job.salary_max) / 2
                    })
                    ats_sources.append(ats_type)
        
        if not all_salaries:
            return None
        
        import statistics
        
        all_mins = [s["min"] for s in all_salaries]
        all_maxs = [s["max"] for s in all_salaries]
        all_mids = [s["mid"] for s in all_salaries]
        
        sample_size = len(all_salaries)
        confidence = "high" if sample_size >= 10 else "medium" if sample_size >= 5 else "low"
        
        return ATSSalaryInsight(
            min_salary=statistics.mean(all_mins),
            max_salary=statistics.mean(all_maxs),
            median_salary=statistics.median(all_mids),
            average_salary=statistics.mean(all_mids),
            sample_size=sample_size,
            confidence=confidence,
            ats_type=",".join(set(ats_sources)),
            role_match=role,
            seniority_match=seniority,
            location_match=location
        )
    
    async def get_skill_insights(
        self,
        company_id: str,
        role: str,
        months_back: int = 12,
        limit: int = 20
    ) -> list[ATSSkillInsight]:
        """
        Get common skills for a role from ATS historical data.
        
        Analyzes skills used in similar job postings.
        """
        ats_service = self._get_ats_service()
        skill_counts: dict[str, int] = {}
        total_jobs = 0
        ats_sources = []
        
        for ats_type in ["gupy", "pandape", "merge"]:
            if not ats_service.has_client(ats_type):
                continue
            
            jobs = await self.get_jobs_from_ats(
                ats_type=ats_type,
                company_id=company_id,
                months_back=months_back,
                limit=200
            )
            
            for job in jobs:
                if not self._role_matches(job.title, role):
                    continue
                
                total_jobs += 1
                ats_sources.append(ats_type)
                
                if job.skills:
                    for skill in job.skills:
                        skill_name = skill.get("name") if isinstance(skill, dict) else str(skill)
                        skill_counts[skill_name] = skill_counts.get(skill_name, 0) + 1
        
        if not skill_counts:
            return []
        
        sorted_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)
        ats_type_str = ",".join(set(ats_sources))
        
        return [
            ATSSkillInsight(
                skill_name=skill,
                frequency=count,
                percentage=(count / total_jobs * 100) if total_jobs > 0 else 0,
                ats_type=ats_type_str,
                role_context=role
            )
            for skill, count in sorted_skills[:limit]
        ]
    
    async def get_similar_jobs(
        self,
        company_id: str,
        role: str,
        seniority: str | None = None,
        limit: int = 10
    ) -> list[ATSJobDescription]:
        """
        Find similar jobs from ATS history.
        
        Useful for templates and benchmarking.
        """
        ats_service = self._get_ats_service()
        similar_jobs = []
        
        for ats_type in ["gupy", "pandape", "merge"]:
            if not ats_service.has_client(ats_type):
                continue
            
            jobs = await self.get_jobs_from_ats(
                ats_type=ats_type,
                company_id=company_id,
                months_back=24,
                limit=100
            )
            
            for job in jobs:
                if not self._role_matches(job.title, role):
                    continue
                
                if seniority:
                    job_seniority = job.seniority or self._extract_seniority(job.title)
                    if job_seniority and seniority.lower() not in job_seniority.lower():
                        continue
                
                similar_jobs.append(job)
        
        similar_jobs.sort(
            key=lambda j: (j.closed_at or j.created_at or datetime.min),
            reverse=True
        )
        
        return similar_jobs[:limit]


ats_job_history_service = ATSJobHistoryService()
