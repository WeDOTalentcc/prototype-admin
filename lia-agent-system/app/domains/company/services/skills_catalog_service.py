"""

# ADR-001-EXEMPT: Skills catalog service spans 3 models (CompanySkill,
# CompanySkillsCatalog, BehavioralCompetencyCatalog) with category-based
# filtering and cross-table aggregations. Tenant scope established at
# service entry. Sprint 6 follow-up: consolidate into SkillsCatalogRepository.

Skills Catalog Service for Job Wizard Enhancement.

Provides a comprehensive catalog of technical skills and behavioral competencies
for automatic suggestion during job vacancy creation.

Features:
- Technical skills catalog organized by area and category
- Behavioral competencies with subcategories
- Role-to-skills mapping for intelligent suggestions
- Fuzzy search for skill discovery
- Seniority-based skill count adjustments
- Dynamic company skills integration from database
"""
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from difflib import SequenceMatcher
from typing import Any

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.company_learning import CompanySkill
from lia_models.skills_catalog import (
    BehavioralCompetencyCatalog,
    CompanySkillsCatalog,
    SkillSuggestionPattern,
    SkillUsageAnalytics,
)

logger = logging.getLogger(__name__)


TECH_SKILLS_CATALOG: dict[str, dict[str, list[str]]] = {
    "engineering": {
        "backend": ["Python", "Java", "Node.js", "Go", "Ruby", "C#", ".NET", "PHP", "Rust", "Scala"],
        "frontend": ["React", "Vue.js", "Angular", "TypeScript", "JavaScript", "HTML/CSS", "Next.js", "Nuxt.js", "Svelte", "Tailwind CSS"],
        "mobile": ["React Native", "Flutter", "Swift", "Kotlin", "iOS", "Android"],
        "devops": ["Docker", "Kubernetes", "AWS", "GCP", "Azure", "Terraform", "CI/CD", "Linux", "GitOps", "Ansible"],
        "data": ["SQL", "PostgreSQL", "MongoDB", "Redis", "Elasticsearch", "Apache Kafka", "Spark", "Airflow", "dbt"],
        "ai_ml": ["Machine Learning", "Deep Learning", "NLP", "Computer Vision", "TensorFlow", "PyTorch", "LangChain", "MLOps"]
    },
    "finance": {
        "accounting": ["IFRS", "GAAP", "SAP FI/CO", "Oracle Financials", "Contabilidade Geral", "Conciliação", "Fechamento Contábil"],
        "treasury": ["Gestão de Caixa", "Câmbio", "Derivativos", "Bloomberg", "Reuters", "Investimentos"],
        "fp_a": ["Orçamento", "Forecast", "Análise de Variância", "Business Intelligence", "Excel Avançado", "Power BI", "Hyperion"],
        "tax": ["Planejamento Tributário", "SPED", "eSocial", "IRPJ", "ICMS", "ISS", "Compliance Fiscal"],
        "audit": ["Auditoria Interna", "SOX", "COSO", "Gestão de Riscos", "Controles Internos"]
    },
    "hr": {
        "recruitment": ["R&S", "Entrevistas por Competências", "Assessment", "Hunting", "LinkedIn Recruiter", "ATS", "Employer Branding"],
        "development": ["T&D", "LMS", "Gestão de Desempenho", "PDI", "Feedback 360", "Coaching", "Mentoring"],
        "compensation": ["Remuneração", "Cargos e Salários", "Pesquisa Salarial", "Benefícios", "Stock Options", "ILP"],
        "people_analytics": ["People Analytics", "KPIs de RH", "Turnover", "Engagement", "Power BI", "Excel"]
    },
    "marketing": {
        "digital": ["SEO", "SEM", "Google Ads", "Meta Ads", "Analytics", "Growth Hacking", "Marketing Automation"],
        "content": ["Copywriting", "Content Strategy", "Social Media", "Inbound Marketing", "Email Marketing", "Storytelling"],
        "product": ["Product Marketing", "Go-to-Market", "Posicionamento", "Pricing", "Competitive Intelligence"],
        "brand": ["Branding", "Brand Strategy", "Design Thinking", "Pesquisa de Mercado", "CRM"]
    },
    "sales": {
        "b2b": ["Vendas Consultivas", "Solution Selling", "SPIN Selling", "Account Management", "Key Account"],
        "b2c": ["Varejo", "E-commerce", "Customer Success", "CRM", "Salesforce", "HubSpot"],
        "leadership": ["Gestão de Equipe Comercial", "Forecast", "Pipeline Management", "Metas e Indicadores"],
        "pre_sales": ["Pré-vendas", "RFP", "Proposta Comercial", "Discovery", "Demo Técnica"]
    }
}


BEHAVIORAL_COMPETENCIES_CATALOG: dict[str, dict[str, Any]] = {
    "leadership": {
        "name": "Liderança",
        "subcategories": ["Liderança de Equipe", "Liderança Situacional", "Desenvolvimento de Pessoas", "Delegação", "Tomada de Decisão Estratégica"]
    },
    "communication": {
        "name": "Comunicação",
        "subcategories": ["Comunicação Verbal", "Comunicação Escrita", "Apresentações", "Negociação", "Influência"]
    },
    "collaboration": {
        "name": "Colaboração",
        "subcategories": ["Trabalho em Equipe", "Cooperação", "Gestão de Conflitos", "Networking", "Parceria"]
    },
    "problem_solving": {
        "name": "Resolução de Problemas",
        "subcategories": ["Pensamento Analítico", "Pensamento Crítico", "Criatividade", "Inovação", "Solução de Problemas Complexos"]
    },
    "adaptability": {
        "name": "Adaptabilidade",
        "subcategories": ["Flexibilidade", "Resiliência", "Gestão de Mudanças", "Aprendizado Contínuo", "Tolerância à Ambiguidade"]
    },
    "results_orientation": {
        "name": "Orientação a Resultados",
        "subcategories": ["Foco em Metas", "Proatividade", "Ownership", "Senso de Urgência", "Entrega de Valor"]
    },
    "customer_focus": {
        "name": "Foco no Cliente",
        "subcategories": ["Empatia", "Atendimento ao Cliente", "Experiência do Usuário", "Orientação a Serviço"]
    },
    "ethics": {
        "name": "Ética e Integridade",
        "subcategories": ["Honestidade", "Transparência", "Compliance", "Responsabilidade", "Confidencialidade"]
    }
}


ROLE_SKILLS_MAPPING: dict[str, dict[str, Any]] = {
    "desenvolvedor backend": {"area": "engineering", "category": "backend", "behavioral": ["problem_solving", "collaboration"]},
    "desenvolvedor frontend": {"area": "engineering", "category": "frontend", "behavioral": ["communication", "adaptability"]},
    "desenvolvedor fullstack": {"area": "engineering", "category": ["backend", "frontend"], "behavioral": ["problem_solving", "adaptability"]},
    "engenheiro de dados": {"area": "engineering", "category": "data", "behavioral": ["problem_solving", "results_orientation"]},
    "engenheiro devops": {"area": "engineering", "category": "devops", "behavioral": ["problem_solving", "adaptability"]},
    "cientista de dados": {"area": "engineering", "category": "ai_ml", "behavioral": ["problem_solving", "communication"]},
    "tech lead": {"area": "engineering", "category": "backend", "behavioral": ["leadership", "communication"]},
    "analista contábil": {"area": "finance", "category": "accounting", "behavioral": ["ethics", "results_orientation"]},
    "analista financeiro": {"area": "finance", "category": "fp_a", "behavioral": ["problem_solving", "results_orientation"]},
    "controller": {"area": "finance", "category": "accounting", "behavioral": ["leadership", "ethics"]},
    "tesoureiro": {"area": "finance", "category": "treasury", "behavioral": ["results_orientation", "ethics"]},
    "analista de rh": {"area": "hr", "category": "recruitment", "behavioral": ["communication", "collaboration"]},
    "business partner": {"area": "hr", "category": "development", "behavioral": ["communication", "leadership"]},
    "headhunter": {"area": "hr", "category": "recruitment", "behavioral": ["communication", "results_orientation"]},
    "analista de marketing": {"area": "marketing", "category": "digital", "behavioral": ["adaptability", "results_orientation"]},
    "gerente de marketing": {"area": "marketing", "category": "brand", "behavioral": ["leadership", "communication"]},
    "growth": {"area": "marketing", "category": "digital", "behavioral": ["problem_solving", "adaptability"]},
    "vendedor": {"area": "sales", "category": "b2b", "behavioral": ["communication", "results_orientation"]},
    "account executive": {"area": "sales", "category": "b2b", "behavioral": ["communication", "results_orientation"]},
    "gerente comercial": {"area": "sales", "category": "leadership", "behavioral": ["leadership", "results_orientation"]}
}


SENIORITY_SKILL_COUNTS: dict[str, dict[str, int]] = {
    "junior": {"min": 3, "max": 5},
    "jr": {"min": 3, "max": 5},
    "júnior": {"min": 3, "max": 5},
    "pleno": {"min": 5, "max": 8},
    "pl": {"min": 5, "max": 8},
    "mid": {"min": 5, "max": 8},
    "senior": {"min": 8, "max": 12},
    "sr": {"min": 8, "max": 12},
    "sênior": {"min": 8, "max": 12},
    "lead": {"min": 10, "max": 15},
    "líder": {"min": 10, "max": 15},
    "principal": {"min": 10, "max": 15},
    "staff": {"min": 10, "max": 15},
    "gerente": {"min": 8, "max": 12},
    "manager": {"min": 8, "max": 12},
    "diretor": {"min": 10, "max": 15},
    "director": {"min": 10, "max": 15}
}


@dataclass
class SkillSuggestion:
    """Represents a skill suggestion with metadata."""
    skill: str
    category: str
    area: str
    relevance_score: float = 1.0


@dataclass
class CompetencySuggestion:
    """Represents a behavioral competency suggestion."""
    key: str
    name: str
    subcategories: list[str]
    relevance_score: float = 1.0


class SkillsCatalogService:
    """
    Service for managing and querying the skills and competencies catalog.
    
    Provides intelligent skill suggestions based on role, seniority,
    and company context for the job wizard enhancement.
    """
    
    FUZZY_MATCH_THRESHOLD = 0.6
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._skills_index: dict[str, dict[str, str]] = {}
        self._build_skills_index()
    
    def _build_skills_index(self) -> None:
        """Build an index of all skills for fast lookup."""
        for area, categories in TECH_SKILLS_CATALOG.items():
            for category, skills in categories.items():
                for skill in skills:
                    normalized = skill.lower()
                    self._skills_index[normalized] = {
                        "skill": skill,
                        "area": area,
                        "category": category
                    }
    
    def normalize_role(self, role: str) -> str:
        """
        Normalize a job role/title for matching against the catalog.
        
        Args:
            role: The job role/title to normalize
            
        Returns:
            Normalized role string (lowercase, trimmed, standardized)
        """
        if not role:
            return ""
        
        normalized = role.lower().strip()
        normalized = re.sub(r'\s+', ' ', normalized)
        
        replacements = {
            "desenvolvedor(a)": "desenvolvedor",
            "analista de ti": "desenvolvedor",
            "programador": "desenvolvedor",
            "software engineer": "desenvolvedor",
            "dev ": "desenvolvedor ",
            "engenheiro(a)": "engenheiro",
            "gerente de": "gerente",
            "coordenador(a)": "coordenador",
            "analista sr": "analista senior",
            "analista pl": "analista pleno",
            "analista jr": "analista junior",
        }
        
        for pattern, replacement in replacements.items():
            normalized = normalized.replace(pattern, replacement)
        
        return normalized.strip()
    
    def _fuzzy_match_role(self, role: str) -> str | None:
        """
        Find the best matching role in the catalog using fuzzy matching.
        
        Args:
            role: The normalized role to match
            
        Returns:
            Best matching role key or None if no good match found
        """
        best_match = None
        best_score = 0.0
        
        for catalog_role in ROLE_SKILLS_MAPPING.keys():
            score = SequenceMatcher(None, role, catalog_role).ratio()
            
            if role in catalog_role or catalog_role in role:
                score = max(score, 0.8)
            
            if score > best_score and score >= self.FUZZY_MATCH_THRESHOLD:
                best_score = score
                best_match = catalog_role
        
        return best_match
    
    def get_seniority_adjusted_count(self, seniority: str) -> dict[str, int]:
        """
        Get the recommended skill count range based on seniority level.
        
        Args:
            seniority: The seniority level (jr, pleno, senior, lead, etc.)
            
        Returns:
            Dictionary with 'min' and 'max' skill counts
        """
        if not seniority:
            return {"min": 5, "max": 8}
        
        normalized = seniority.lower().strip()
        
        if normalized in SENIORITY_SKILL_COUNTS:
            return SENIORITY_SKILL_COUNTS[normalized]
        
        for key, counts in SENIORITY_SKILL_COUNTS.items():
            if key in normalized or normalized in key:
                return counts
        
        return {"min": 5, "max": 8}
    
    def get_skills_for_role(
        self,
        role: str,
        seniority: str | None = None
    ) -> dict[str, Any]:
        """
        Get suggested technical skills based on role and seniority.
        
        Args:
            role: Job role/title
            seniority: Seniority level (optional)
            
        Returns:
            Dictionary containing suggested skills with metadata
        """
        normalized_role = self.normalize_role(role)
        
        mapping = ROLE_SKILLS_MAPPING.get(normalized_role)
        if not mapping:
            matched_role = self._fuzzy_match_role(normalized_role)
            if matched_role:
                mapping = ROLE_SKILLS_MAPPING[matched_role]
        
        if not mapping:
            self.logger.warning(f"No skill mapping found for role: {role}")
            return {
                "skills": [],
                "area": None,
                "categories": [],
                "skill_count": self.get_seniority_adjusted_count(seniority or "pleno"),
                "matched_role": None
            }
        
        area = mapping["area"]
        categories = mapping["category"]
        
        if isinstance(categories, str):
            categories = [categories]
        
        skills: list[str] = []
        for category in categories:
            category_skills = TECH_SKILLS_CATALOG.get(area, {}).get(category, [])
            skills.extend(category_skills)
        
        skills = list(dict.fromkeys(skills))
        
        skill_count = self.get_seniority_adjusted_count(seniority or "pleno")
        
        return {
            "skills": skills,
            "area": area,
            "categories": categories,
            "skill_count": skill_count,
            "matched_role": normalized_role if mapping else None
        }
    
    def get_behavioral_competencies_for_role(
        self,
        role: str
    ) -> list[dict[str, Any]]:
        """
        Get suggested behavioral competencies based on role.
        
        Args:
            role: Job role/title
            
        Returns:
            List of behavioral competency dictionaries
        """
        normalized_role = self.normalize_role(role)
        
        mapping = ROLE_SKILLS_MAPPING.get(normalized_role)
        if not mapping:
            matched_role = self._fuzzy_match_role(normalized_role)
            if matched_role:
                mapping = ROLE_SKILLS_MAPPING[matched_role]
        
        if not mapping or "behavioral" not in mapping:
            return self._get_default_competencies()
        
        behavioral_keys = mapping["behavioral"]
        competencies: list[dict[str, Any]] = []
        
        for key in behavioral_keys:
            if key in BEHAVIORAL_COMPETENCIES_CATALOG:
                comp = BEHAVIORAL_COMPETENCIES_CATALOG[key]
                competencies.append({
                    "key": key,
                    "name": comp["name"],
                    "subcategories": comp["subcategories"],
                    "relevance": "high"
                })
        
        for key, comp in BEHAVIORAL_COMPETENCIES_CATALOG.items():
            if key not in behavioral_keys:
                competencies.append({
                    "key": key,
                    "name": comp["name"],
                    "subcategories": comp["subcategories"],
                    "relevance": "medium"
                })
        
        return competencies
    
    def _get_default_competencies(self) -> list[dict[str, Any]]:
        """Get default competencies when role is not found."""
        return [
            {
                "key": key,
                "name": comp["name"],
                "subcategories": comp["subcategories"],
                "relevance": "medium"
            }
            for key, comp in BEHAVIORAL_COMPETENCIES_CATALOG.items()
        ]
    
    def search_skills(
        self,
        query: str,
        area: str | None = None,
        limit: int = 20
    ) -> list[dict[str, Any]]:
        """
        Search for skills using fuzzy matching.
        
        Args:
            query: Search query string
            area: Optional area filter (engineering, finance, etc.)
            limit: Maximum number of results to return
            
        Returns:
            List of matching skills with metadata
        """
        if not query:
            return []
        
        query_lower = query.lower().strip()
        results: list[dict[str, Any]] = []
        
        areas_to_search = [area] if area and area in TECH_SKILLS_CATALOG else TECH_SKILLS_CATALOG.keys()
        
        for search_area in areas_to_search:
            categories = TECH_SKILLS_CATALOG.get(search_area, {})
            for category, skills in categories.items():
                for skill in skills:
                    skill_lower = skill.lower()
                    
                    if query_lower in skill_lower:
                        score = 1.0 if skill_lower.startswith(query_lower) else 0.9
                    else:
                        score = SequenceMatcher(None, query_lower, skill_lower).ratio()
                    
                    if score >= 0.4:
                        results.append({
                            "skill": skill,
                            "area": search_area,
                            "category": category,
                            "score": score
                        })
        
        results.sort(key=lambda x: x["score"], reverse=True)
        
        seen_skills = set()
        unique_results = []
        for result in results:
            if result["skill"] not in seen_skills:
                seen_skills.add(result["skill"])
                unique_results.append(result)
        
        return unique_results[:limit]
    
    def get_all_skills_for_area(self, area: str) -> dict[str, list[str]]:
        """
        Get all skills organized by category for a specific area.
        
        Args:
            area: The area (engineering, finance, hr, marketing, sales)
            
        Returns:
            Dictionary mapping categories to skill lists
        """
        if area not in TECH_SKILLS_CATALOG:
            self.logger.warning(f"Area not found: {area}")
            return {}
        
        return TECH_SKILLS_CATALOG[area].copy()
    
    def get_all_areas(self) -> list[str]:
        """Get all available skill areas."""
        return list(TECH_SKILLS_CATALOG.keys())
    
    def get_all_behavioral_competencies(self) -> dict[str, dict[str, Any]]:
        """Get the complete behavioral competencies catalog."""
        return BEHAVIORAL_COMPETENCIES_CATALOG.copy()
    
    def combine_with_company_defaults(
        self,
        company_competencies: list[str],
        role_suggestions: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        Combine company default competencies with role-based suggestions.
        
        Company competencies take priority and are marked as 'company_default'.
        Role suggestions are added if not already present.
        
        Args:
            company_competencies: List of competency keys from company profile
            role_suggestions: List of competency dicts from role matching
            
        Returns:
            Combined and deduplicated list of competencies
        """
        combined: list[dict[str, Any]] = []
        seen_keys: set = set()
        
        for comp_key in company_competencies:
            if comp_key in BEHAVIORAL_COMPETENCIES_CATALOG:
                comp = BEHAVIORAL_COMPETENCIES_CATALOG[comp_key]
                combined.append({
                    "key": comp_key,
                    "name": comp["name"],
                    "subcategories": comp["subcategories"],
                    "source": "company_default",
                    "relevance": "high"
                })
                seen_keys.add(comp_key)
        
        for suggestion in role_suggestions:
            key = suggestion.get("key")
            if key and key not in seen_keys:
                combined.append({
                    **suggestion,
                    "source": "role_suggestion"
                })
                seen_keys.add(key)
        
        return combined
    
    def validate_skills(self, skills: list[str]) -> dict[str, Any]:
        """
        Validate a list of skills against the catalog.
        
        Args:
            skills: List of skill names to validate
            
        Returns:
            Dictionary with valid and invalid skills
        """
        valid: list[dict[str, str]] = []
        invalid: list[str] = []
        
        for skill in skills:
            skill_lower = skill.lower()
            if skill_lower in self._skills_index:
                info = self._skills_index[skill_lower]
                valid.append({
                    "skill": info["skill"],
                    "area": info["area"],
                    "category": info["category"]
                })
            else:
                invalid.append(skill)
        
        return {
            "valid": valid,
            "invalid": invalid,
            "valid_count": len(valid),
            "invalid_count": len(invalid)
        }
    
    def suggest_skills(
        self,
        role: str,
        seniority: str | None = None,
        limit: int = 10
    ) -> dict[str, Any]:
        """
        Suggest skills for a given role and seniority level.
        
        This is a convenience method that combines role-based skill lookup
        with behavioral competencies.
        
        Args:
            role: Job role/title
            seniority: Seniority level (optional, defaults to 'pleno')
            limit: Maximum number of technical skills to return
            
        Returns:
            Dictionary with suggested technical and behavioral skills
        """
        seniority = seniority or "pleno"
        
        role_skills = self.get_skills_for_role(role, seniority)
        behavioral = self.get_behavioral_competencies_for_role(role)
        
        tech_skills = role_skills.get("skills", [])[:limit]
        skill_count = role_skills.get("skill_count", {"min": 5, "max": 8})
        
        high_relevance_behavioral = [
            comp for comp in behavioral if comp.get("relevance") == "high"
        ]
        
        return {
            "technical_skills": tech_skills,
            "behavioral_competencies": high_relevance_behavioral,
            "area": role_skills.get("area"),
            "categories": role_skills.get("categories"),
            "matched_role": role_skills.get("matched_role"),
            "recommended_skill_count": skill_count
        }
    
    def validate_skills_quality(
        self,
        detected_skills: list[str],
        seniority: str
    ) -> dict[str, Any]:
        """
        Validate the quality and quantity of detected skills for a given seniority.
        
        Provides feedback on whether the number of skills is appropriate
        for the seniority level.
        
        Args:
            detected_skills: List of skills detected from job description
            seniority: Seniority level (junior, pleno, senior, lead, etc.)
            
        Returns:
            Dictionary with feedback about skill quantity and quality
        """
        skill_counts = self.get_seniority_adjusted_count(seniority or "pleno")
        count = len(detected_skills)
        
        feedback: dict[str, Any] = {
            "count": count,
            "recommended_min": skill_counts["min"],
            "recommended_max": skill_counts["max"],
            "status": "ok",
            "message": ""
        }
        
        seniority_display = seniority or "pleno"
        
        if count < skill_counts["min"]:
            feedback["status"] = "too_few"
            feedback["message"] = f"Poucas skills detectadas ({count}). Recomendado: {skill_counts['min']}-{skill_counts['max']} para nível {seniority_display}."
        elif count > skill_counts["max"]:
            feedback["status"] = "too_many"
            feedback["message"] = f"Muitas skills obrigatórias ({count}). Recomendado: máximo {skill_counts['max']} para nível {seniority_display}."
        else:
            feedback["status"] = "ok"
            feedback["message"] = f"Quantidade adequada de skills ({count}) para nível {seniority_display}."
        
        validated = self.validate_skills(detected_skills)
        feedback["valid_skills"] = validated["valid"]
        feedback["invalid_skills"] = validated["invalid"]
        feedback["catalog_match_rate"] = (
            validated["valid_count"] / count if count > 0 else 0
        )
        
        return feedback
    
    async def _get_company_skills(
        self,
        db: AsyncSession,
        company_id: str,
        role: str | None = None,
        seniority: str | None = None,
        only_promoted: bool = False
    ) -> list[str]:
        """
        Query company skills from the database.
        
        Retrieves dynamic skills learned for a company from the CompanySkill table.
        Optionally filters by role and seniority if provided.
        
        Args:
            db: Async database session
            company_id: Company identifier
            role: Optional role filter
            seniority: Optional seniority level filter
            only_promoted: If True, only return promoted skills (is_promoted=True)
            
        Returns:
            List of skill names from company's dynamic catalog
        """
        try:
            conditions = [CompanySkill.company_id == company_id]

            if only_promoted:
                conditions.append(CompanySkill.is_promoted)

            # TENANT-EXEMPT: CompanySkill.company_id == company_id é PRIMEIRO
            # elemento de `conditions` (statically guaranteed). Sensor AST não
            # rastreia através de and_(*conditions) unpacking.
            stmt = (
                select(CompanySkill)
                .where(and_(*conditions))
                .order_by(
                    CompanySkill.is_promoted.desc(),
                    CompanySkill.times_confirmed.desc(),
                    CompanySkill.confidence_score.desc()
                )
            )
            
            result = await db.execute(stmt)
            company_skills = result.scalars().all()
            
            skill_names: list[str] = []
            for skill in company_skills:
                roles_attr = getattr(skill, 'roles_associated', None)
                levels_attr = getattr(skill, 'seniority_levels', None)
                
                if role is not None and roles_attr:
                    roles_list = list(roles_attr) if roles_attr else []
                    if roles_list and role.lower() not in [r.lower() for r in roles_list]:
                        continue
                
                if seniority is not None and levels_attr:
                    levels_list = list(levels_attr) if levels_attr else []
                    if levels_list and seniority.lower() not in [s.lower() for s in levels_list]:
                        continue
                
                skill_names.append(str(getattr(skill, 'skill_name', '')))
            
            return skill_names
            
        except Exception as e:
            self.logger.error(f"Error querying company skills: {e}")
            return []
    
    async def suggest_skills_with_learning(
        self,
        db: AsyncSession,
        company_id: str,
        role: str,
        seniority: str | None = None,
        limit: int = 10
    ) -> dict[str, Any]:
        """
        Suggest skills combining dynamic company learning with static catalog.
        
        Prioritizes company-learned promoted skills, then adds static role-based
        skills to reach the desired limit. Returns extra field 'company_learned_skills'
        to track which skills came from company's dynamic catalog.
        
        Args:
            db: Async database session
            company_id: Company identifier
            role: Job role/title
            seniority: Seniority level (optional, defaults to 'pleno')
            limit: Maximum number of technical skills to return
            
        Returns:
            Dictionary with suggested technical and behavioral skills,
            including company_learned_skills field and metadata
        """
        seniority = seniority or "pleno"
        
        try:
            company_skill_names = await self._get_company_skills(
                db=db,
                company_id=company_id,
                role=role,
                seniority=seniority,
                only_promoted=True
            )
        except Exception as e:
            self.logger.error(f"Error fetching company skills for suggestion: {e}")
            company_skill_names = []
        
        base_suggestions = self.suggest_skills(role, seniority, limit)
        
        static_skills = base_suggestions.get("technical_skills", [])
        
        final_skills = []
        skill_set = set()
        
        for skill_name in company_skill_names:
            if skill_name not in skill_set:
                final_skills.append(skill_name)
                skill_set.add(skill_name)
        
        for skill_name in static_skills:
            if skill_name not in skill_set and len(final_skills) < limit:
                final_skills.append(skill_name)
                skill_set.add(skill_name)
        
        return {
            "technical_skills": final_skills[:limit],
            "behavioral_competencies": base_suggestions.get("behavioral_competencies", []),
            "area": base_suggestions.get("area"),
            "categories": base_suggestions.get("categories"),
            "matched_role": base_suggestions.get("matched_role"),
            "recommended_skill_count": base_suggestions.get("recommended_skill_count"),
            "company_learned_skills": company_skill_names,
            "source_mix": {
                "company_learned": len([s for s in final_skills if s in company_skill_names]),
                "static_catalog": len([s for s in final_skills if s not in company_skill_names])
            }
        }


class SkillsCatalogDBService:
    """
    Database-backed skills catalog service.
    
    Extends the static catalog with company-specific persistent storage.
    Integrates with:
    - CompanySkillsCatalog: Company-configured technical skills
    - BehavioralCompetencyCatalog: Company-configured competencies
    - SkillUsageAnalytics: Analytics on skill usage patterns
    - SkillSuggestionPattern: Learned patterns for better suggestions
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.static_catalog = SkillsCatalogService()
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def get_company_catalog(
        self,
        company_id: str,
        include_inactive: bool = False,
        category: str | None = None
    ) -> dict[str, Any]:
        """
        Get the complete company-specific skills catalog.
        
        Combines company-configured skills from the database with
        the static global catalog.
        
        Args:
            company_id: Company identifier
            include_inactive: Whether to include inactive skills
            category: Optional category filter
            
        Returns:
            Dictionary with company catalog and metadata
        """
        try:
            conditions = [CompanySkillsCatalog.company_id == company_id]

            if not include_inactive:
                conditions.append(CompanySkillsCatalog.is_active)

            if category:
                conditions.append(CompanySkillsCatalog.category == category)

            # TENANT-EXEMPT: CompanySkillsCatalog.company_id == company_id é
            # PRIMEIRO elemento de `conditions` (statically guaranteed). Sensor
            # AST não rastreia através de and_(*conditions) unpacking.
            stmt = (
                select(CompanySkillsCatalog)
                .where(and_(*conditions))
                .order_by(
                    CompanySkillsCatalog.usage_count.desc(),
                    CompanySkillsCatalog.acceptance_rate.desc(),
                    CompanySkillsCatalog.skill_name
                )
            )

            result = await self.db.execute(stmt)
            company_skills = result.scalars().all()

            competency_conditions = [BehavioralCompetencyCatalog.company_id == company_id]
            if not include_inactive:
                competency_conditions.append(BehavioralCompetencyCatalog.is_active)

            # TENANT-EXEMPT: BehavioralCompetencyCatalog.company_id == company_id
            # é PRIMEIRO elemento de `competency_conditions` (statically guaranteed).
            stmt_competencies = (
                select(BehavioralCompetencyCatalog)
                .where(and_(*competency_conditions))
                .order_by(BehavioralCompetencyCatalog.usage_count.desc())
            )
            
            result_comp = await self.db.execute(stmt_competencies)
            competencies = result_comp.scalars().all()
            
            skills_by_category: dict[str, list[dict[str, Any]]] = {}
            for skill in company_skills:
                cat = skill.category
                if cat not in skills_by_category:
                    skills_by_category[cat] = []
                
                skills_by_category[cat].append({
                    "name": skill.skill_name,
                    "subcategory": skill.subcategory,
                    "default_weight": skill.default_weight,
                    "default_level": skill.default_level,
                    "is_required_default": skill.is_required_default,
                    "description": skill.description,
                    "usage_count": skill.usage_count,
                    "acceptance_rate": skill.acceptance_rate,
                    "source": skill.source
                })
            
            competencies_list = [
                {
                    "name": comp.name,
                    "description": comp.description,
                    "default_weight": comp.default_weight,
                    "category": comp.category,
                    "usage_count": comp.usage_count,
                    "acceptance_rate": comp.acceptance_rate,
                    "wsi_questions": comp.wsi_questions
                }
                for comp in competencies
            ]
            
            self.logger.info(
                f"Retrieved company catalog for {company_id}: "
                f"{len(company_skills)} skills, {len(competencies)} competencies"
            )
            
            return {
                "company_id": company_id,
                "skills_by_category": skills_by_category,
                "competencies": competencies_list,
                "total_skills": len(company_skills),
                "total_competencies": len(competencies),
                "static_areas": self.static_catalog.get_all_areas()
            }
        
        except Exception as e:
            self.logger.error(f"Error retrieving company catalog for {company_id}: {e}")
            raise
    
    async def add_skill_to_catalog(
        self,
        company_id: str,
        skill_name: str,
        category: str,
        **kwargs
    ) -> dict:
        """
        Add a skill to the company's catalog.
        
        Creates or updates a CompanySkillsCatalog entry.
        
        Args:
            company_id: Company identifier
            skill_name: Name of the skill
            category: Skill category
            **kwargs: Additional fields (subcategory, default_weight, default_level, 
                     is_required_default, description, created_by)
            
        Returns:
            Dictionary with the created/updated skill data
        """
        try:
            stmt = select(CompanySkillsCatalog).where(
                and_(
                    CompanySkillsCatalog.company_id == company_id,
                    CompanySkillsCatalog.skill_name == skill_name
                )
            )
            result = await self.db.execute(stmt)
            existing_skill = result.scalars().first()
            
            if existing_skill:
                existing_skill.category = category
                existing_skill.subcategory = kwargs.get("subcategory")
                existing_skill.default_weight = kwargs.get("default_weight", 3)
                existing_skill.default_level = kwargs.get("default_level", "Intermediário")
                existing_skill.is_required_default = kwargs.get("is_required_default", False)
                existing_skill.description = kwargs.get("description")
                existing_skill.updated_at = datetime.utcnow()
                
                # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
                self.logger.info(f"Updated skill {skill_name} for company {company_id}")
            else:
                new_skill = CompanySkillsCatalog(
                    company_id=company_id,
                    skill_name=skill_name,
                    category=category,
                    subcategory=kwargs.get("subcategory"),
                    default_weight=kwargs.get("default_weight", 3),
                    default_level=kwargs.get("default_level", "Intermediário"),
                    is_required_default=kwargs.get("is_required_default", False),
                    description=kwargs.get("description"),
                    source=kwargs.get("source", "manual"),
                    is_active=True,
                    created_by=kwargs.get("created_by")
                )
                self.db.add(new_skill)
                existing_skill = new_skill
                
                # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
                self.logger.info(f"Added skill {skill_name} to company {company_id} catalog")
            
            await self.db.commit()
            
            return {
                "skill_name": existing_skill.skill_name,
                "category": existing_skill.category,
                "subcategory": existing_skill.subcategory,
                "default_weight": existing_skill.default_weight,
                "default_level": existing_skill.default_level,
                "is_required_default": existing_skill.is_required_default,
                "created_at": existing_skill.created_at.isoformat(),
                "updated_at": existing_skill.updated_at.isoformat()
            }
        
        except Exception as e:
            await self.db.rollback()
            # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
            self.logger.error(f"Error adding skill {skill_name} to catalog: {e}")
            raise
    
    async def sync_from_tech_stack(
        self,
        company_id: str,
        tech_stack: list[str]
    ) -> dict[str, int]:
        """
        Sync skills from company's tech stack configuration.
        
        Takes technologies from company config and adds/updates them
        in the company skills catalog.
        
        Args:
            company_id: Company identifier
            tech_stack: List of technology names to sync
            
        Returns:
            Dictionary with sync statistics (added, updated, skipped)
        """
        try:
            added = 0
            updated = 0
            skipped = 0
            
            for tech in tech_stack:
                if not tech or not tech.strip():
                    skipped += 1
                    continue
                
                tech_name = tech.strip()
                
                matched_results = self.static_catalog.search_skills(tech_name, limit=1)
                if matched_results:
                    matched = matched_results[0]
                    category = matched["category"]
                    matched["area"]
                else:
                    category = "general"
                
                stmt = select(CompanySkillsCatalog).where(
                    and_(
                        CompanySkillsCatalog.company_id == company_id,
                        CompanySkillsCatalog.skill_name == tech_name
                    )
                )
                result = await self.db.execute(stmt)
                existing = result.scalars().first()
                
                if existing:
                    existing.updated_at = datetime.utcnow()
                    updated += 1
                else:
                    new_skill = CompanySkillsCatalog(
                        company_id=company_id,
                        skill_name=tech_name,
                        category=category,
                        source="company_config",
                        is_active=True
                    )
                    self.db.add(new_skill)
                    added += 1
            
            await self.db.commit()

            # Bug 4 fix (2026-05-24): dual-write to culture_profile.tech_stack so
            # the frontend (useCompanySettingsCards.fetchCultureProfile) sees the
            # new stack immediately. Without this, write store (CompanySkillsCatalog)
            # and read store (CompanyCultureProfile.tech_stack) diverge — Paulo's
            # bug 4. Lazy import to avoid circular deps at module load.
            try:
                from app.repositories.company_culture_repository import (
                    CompanyCultureRepository,
                )
                import uuid as _uuid
                _cid = _uuid.UUID(str(company_id)) if not isinstance(company_id, _uuid.UUID) else company_id
                _culture_repo = CompanyCultureRepository(self.db)
                await _culture_repo.upsert_profile_fields(
                    _cid,
                    {"tech_stack": [t.strip() for t in tech_stack if t and t.strip()]},
                )
                await self.db.commit()
            except Exception as _dw_err:
                # Dual-write failure should NOT roll back the primary skills_catalog
                # commit above. Surface via logger; sensor can pick this up later.
                self.logger.warning(
                    "[sync_from_tech_stack] culture_profile dual-write failed for "
                    "company=%s: %s", company_id, _dw_err,
                )

            self.logger.info(
                f"Synced tech stack for company {company_id}: "
                f"added={added}, updated={updated}, skipped={skipped}"
            )
            
            return {
                "added": added,
                "updated": updated,
                "skipped": skipped,
                "total_processed": len(tech_stack)
            }
        
        except Exception as e:
            await self.db.rollback()
            self.logger.error(f"Error syncing tech stack for company {company_id}: {e}")
            raise
    
    async def record_skill_usage(
        self,
        company_id: str,
        skill_name: str,
        outcome: str,
        **kwargs
    ) -> None:
        """
        Record the usage of a skill (for analytics and learning).
        
        Creates a SkillUsageAnalytics entry that tracks when and how
        a skill was used in job vacancies.
        
        Args:
            company_id: Company identifier
            skill_name: Name of the skill being recorded
            outcome: Outcome of skill usage ('accepted', 'modified', 'rejected')
            **kwargs: Additional context (job_vacancy_id, job_draft_id, job_title,
                     department, seniority, source, skill_type, category,
                     original_weight, final_weight, original_level, final_level,
                     was_required, suggestion_confidence, suggestion_reasoning)
            
        Returns:
            None
        """
        try:
            analytics_entry = SkillUsageAnalytics(
                company_id=company_id,
                skill_name=skill_name,
                skill_type=kwargs.get("skill_type", "technical"),
                category=kwargs.get("category"),
                job_vacancy_id=kwargs.get("job_vacancy_id"),
                job_draft_id=kwargs.get("job_draft_id"),
                job_title=kwargs.get("job_title"),
                department=kwargs.get("department"),
                seniority=kwargs.get("seniority"),
                source=kwargs.get("source", "suggestion"),
                outcome=outcome,
                original_weight=kwargs.get("original_weight"),
                final_weight=kwargs.get("final_weight"),
                original_level=kwargs.get("original_level"),
                final_level=kwargs.get("final_level"),
                was_required=kwargs.get("was_required"),
                suggestion_confidence=kwargs.get("suggestion_confidence"),
                suggestion_reasoning=kwargs.get("suggestion_reasoning")
            )
            
            self.db.add(analytics_entry)
            
            stmt = select(CompanySkillsCatalog).where(
                and_(
                    CompanySkillsCatalog.company_id == company_id,
                    CompanySkillsCatalog.skill_name == skill_name
                )
            )
            result = await self.db.execute(stmt)
            catalog_skill = result.scalars().first()
            
            if catalog_skill:
                catalog_skill.usage_count = (catalog_skill.usage_count or 0) + 1
                catalog_skill.last_used_at = datetime.utcnow()
                
                if outcome == "accepted":
                    catalog_skill.acceptance_rate = (
                        (catalog_skill.acceptance_rate * (catalog_skill.usage_count - 1) + 1) 
                        / catalog_skill.usage_count
                    )
                elif outcome == "modified":
                    catalog_skill.acceptance_rate = (
                        (catalog_skill.acceptance_rate * (catalog_skill.usage_count - 1) + 0.5) 
                        / catalog_skill.usage_count
                    )
            
            await self.db.commit()
            
            self.logger.debug(
                f"Recorded {skill_name} usage for company {company_id}: outcome={outcome}"
            )
        
        except Exception as e:
            await self.db.rollback()
            # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
            self.logger.error(f"Error recording skill usage for {skill_name}: {e}")
            raise
    
    async def get_merged_suggestions(
        self,
        company_id: str,
        job_title: str,
        seniority: str | None = None,
        limit: int = 10
    ) -> dict[str, Any]:
        """
        Get merged skill suggestions combining multiple sources.
        
        Combines:
        1. Learned skill patterns from SkillSuggestionPattern
        2. Company-configured skills from CompanySkillsCatalog
        3. Static catalog suggestions based on role
        
        Args:
            company_id: Company identifier
            job_title: Job title for role-based matching
            seniority: Seniority level (optional)
            limit: Maximum number of suggestions
            
        Returns:
            Dictionary with merged suggestions and source information
        """
        try:
            suggestions_dict: dict[str, dict[str, Any]] = {}
            
            context_key = f"{job_title.lower()}_{seniority or 'general'}"
            
            stmt_patterns = (
                select(SkillSuggestionPattern)
                .where(
                    and_(
                        SkillSuggestionPattern.company_id == company_id,
                        SkillSuggestionPattern.is_promoted,
                        or_(
                            SkillSuggestionPattern.context_key == context_key,
                            SkillSuggestionPattern.context_key.contains(job_title.lower())
                        )
                    )
                )
                .order_by(
                    SkillSuggestionPattern.confidence_score.desc(),
                    SkillSuggestionPattern.acceptance_rate.desc()
                )
                .limit(limit)
            )
            
            result = await self.db.execute(stmt_patterns)
            learned_patterns = result.scalars().all()
            
            for pattern in learned_patterns:
                suggestions_dict[pattern.skill_name] = {
                    "skill": pattern.skill_name,
                    "category": pattern.skill_category,
                    "suggested_weight": pattern.suggested_weight,
                    "suggested_level": pattern.suggested_level,
                    "is_typically_required": pattern.is_typically_required,
                    "source": "learned_pattern",
                    "confidence": pattern.confidence_score,
                    "acceptance_rate": pattern.acceptance_rate
                }
            
            stmt_company = (
                select(CompanySkillsCatalog)
                .where(
                    and_(
                        CompanySkillsCatalog.company_id == company_id,
                        CompanySkillsCatalog.is_active
                    )
                )
                .order_by(CompanySkillsCatalog.usage_count.desc())
                .limit(limit)
            )
            
            result = await self.db.execute(stmt_company)
            company_skills = result.scalars().all()
            
            for skill in company_skills:
                if skill.skill_name not in suggestions_dict:
                    suggestions_dict[skill.skill_name] = {
                        "skill": skill.skill_name,
                        "category": skill.category,
                        "subcategory": skill.subcategory,
                        "default_weight": skill.default_weight,
                        "default_level": skill.default_level,
                        "is_required_default": skill.is_required_default,
                        "source": "company_catalog",
                        "confidence": 0.7,
                        "usage_count": skill.usage_count
                    }
            
            static_suggestions = self.static_catalog.suggest_skills(
                job_title,
                seniority,
                limit
            )
            
            for skill in static_suggestions.get("technical_skills", []):
                if skill not in suggestions_dict:
                    suggestions_dict[skill] = {
                        "skill": skill,
                        "source": "static_catalog",
                        "confidence": 0.5
                    }
            
            final_suggestions = sorted(
                suggestions_dict.values(),
                key=lambda x: (
                    x.get("confidence", 0.5),
                    x.get("usage_count", 0)
                ),
                reverse=True
            )[:limit]
            
            behavioral = self.static_catalog.get_behavioral_competencies_for_role(job_title)
            
            self.logger.info(
                f"Generated merged suggestions for company {company_id}, "
                f"job: {job_title}: {len(final_suggestions)} skills from "
                f"{len(learned_patterns)} patterns"
            )
            
            return {
                "job_title": job_title,
                "seniority": seniority,
                "technical_skills": final_suggestions,
                "behavioral_competencies": [
                    c for c in behavioral if c.get("relevance") == "high"
                ],
                "sources_included": {
                    "learned_patterns": len(learned_patterns),
                    "company_catalog": len([s for s in company_skills]),
                    "static_catalog": len([s for s in final_suggestions if s.get("source") == "static_catalog"])
                },
                "total_suggestions": len(final_suggestions)
            }
        
        except Exception as e:
            self.logger.error(f"Error getting merged suggestions for company {company_id}: {e}")
            raise


def get_skills_catalog_service() -> SkillsCatalogService:
    """
    Factory function to create a SkillsCatalogService instance.
    
    Returns:
        SkillsCatalogService instance for static catalog operations
    """
    return SkillsCatalogService()


def get_skills_catalog_db_service(db: AsyncSession) -> SkillsCatalogDBService:
    """
    Factory function to create a SkillsCatalogDBService instance.
    
    Args:
        db: Async database session
        
    Returns:
        SkillsCatalogDBService instance for database-backed operations
    """
    return SkillsCatalogDBService(db)


skills_catalog_service = SkillsCatalogService()
