"""
Organization Catalog Service - Comprehensive Brazilian Organizational Catalog.

Provides a complete catalog of areas, roles, seniority levels, and competencies
typical of Brazilian medium and large companies.

Features:
- 20 organizational areas/departments
- 12 seniority levels with descriptions
- 10-15 roles per area
- 30-50 technical skills per area
- 50 universal behavioral competencies
- Area detection from text
- Role-to-skills mapping
- Fuzzy search capabilities
"""
import logging
from dataclasses import asdict, dataclass, field
from difflib import SequenceMatcher
from typing import Any

logger = logging.getLogger(__name__)


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class Area:
    """Organizational area/department definition."""
    id: str
    nome: str
    descricao: str
    palavras_chave: list[str]
    
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SeniorityLevel:
    """Seniority level definition."""
    id: str
    nome: str
    descricao: str
    ordem: int
    anos_experiencia_min: int
    anos_experiencia_max: int | None
    
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Role:
    """Job role/position definition."""
    id: str
    nome: str
    area_id: str
    niveis_aplicaveis: list[str]
    descricao: str
    competencias_tecnicas: list[str]
    competencias_comportamentais: list[str]
    variantes_nome: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TechnicalSkill:
    """Technical skill/competency definition."""
    id: str
    nome: str
    areas: list[str]
    nivel_minimo: str
    descricao: str
    categoria: str
    palavras_chave: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class BehavioralSkill:
    """Behavioral competency definition."""
    id: str
    nome: str
    descricao: str
    categoria: str
    subcategorias: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)



# =============================================================================
# STATIC CATALOG DATA (imported from _catalog_data)
# =============================================================================
from ._catalog_data import (  # noqa: E402
    AREAS_CATALOG,
    SENIORITY_LEVELS,
    BEHAVIORAL_SKILLS,
    TECHNICAL_SKILLS,
    ROLES_CATALOG,
)

class OrganizationCatalogService:
    """
    Service for managing and querying the organizational catalog.
    
    Provides comprehensive access to areas, roles, seniority levels,
    and competencies typical of Brazilian organizations.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    # -------------------------------------------------------------------------
    # AREAS
    # -------------------------------------------------------------------------
    
    def get_all_areas(self) -> list[dict[str, Any]]:
        """Get all organizational areas."""
        return [area.to_dict() for area in AREAS_CATALOG.values()]
    
    def get_area_by_id(self, area_id: str) -> dict[str, Any] | None:
        """Get a specific area by ID."""
        area = AREAS_CATALOG.get(area_id)
        return area.to_dict() if area else None
    
    def detect_area_from_text(self, text: str) -> dict[str, Any] | None:
        """
        Detect the most likely area from a text (job title, description, etc).
        
        Args:
            text: Text to analyze
            
        Returns:
            Best matching area or None
        """
        if not text:
            return None
        
        text_lower = text.lower()
        best_match = None
        best_score = 0
        
        for area in AREAS_CATALOG.values():
            score = 0
            for keyword in area.palavras_chave:
                if keyword.lower() in text_lower:
                    score += 1
                    if keyword.lower() == text_lower:
                        score += 2
            
            if score > best_score:
                best_score = score
                best_match = area
        
        return best_match.to_dict() if best_match else None
    
    # -------------------------------------------------------------------------
    # SENIORITY LEVELS
    # -------------------------------------------------------------------------
    
    def get_all_seniority_levels(self) -> list[dict[str, Any]]:
        """Get all seniority levels ordered by hierarchy."""
        levels = list(SENIORITY_LEVELS.values())
        levels.sort(key=lambda x: x.ordem)
        return [level.to_dict() for level in levels]
    
    def get_seniority_by_id(self, seniority_id: str) -> dict[str, Any] | None:
        """Get a specific seniority level by ID."""
        level = SENIORITY_LEVELS.get(seniority_id)
        return level.to_dict() if level else None
    
    # -------------------------------------------------------------------------
    # ROLES
    # -------------------------------------------------------------------------
    
    def get_roles_by_area(self, area_id: str) -> list[dict[str, Any]]:
        """Get all roles for a specific area."""
        roles = [
            role.to_dict() for role in ROLES_CATALOG.values()
            if role.area_id == area_id
        ]
        return roles
    
    def get_all_roles(self) -> list[dict[str, Any]]:
        """Get all roles."""
        return [role.to_dict() for role in ROLES_CATALOG.values()]
    
    def get_role_by_id(self, role_id: str) -> dict[str, Any] | None:
        """Get a specific role by ID."""
        role = ROLES_CATALOG.get(role_id)
        return role.to_dict() if role else None
    
    def get_role_by_name(self, name: str) -> dict[str, Any] | None:
        """
        Get a role by name, checking main name and variants.
        
        Args:
            name: Role name to search
            
        Returns:
            Matching role or None
        """
        name_lower = name.lower().strip()
        
        for role in ROLES_CATALOG.values():
            if role.nome.lower() == name_lower:
                return role.to_dict()
            
            for variant in role.variantes_nome:
                if variant.lower() == name_lower:
                    return role.to_dict()
        
        best_match = None
        best_score = 0.6
        
        for role in ROLES_CATALOG.values():
            score = SequenceMatcher(None, role.nome.lower(), name_lower).ratio()
            if score > best_score:
                best_score = score
                best_match = role
            
            for variant in role.variantes_nome:
                score = SequenceMatcher(None, variant.lower(), name_lower).ratio()
                if score > best_score:
                    best_score = score
                    best_match = role
        
        return best_match.to_dict() if best_match else None
    
    # -------------------------------------------------------------------------
    # TECHNICAL SKILLS
    # -------------------------------------------------------------------------
    
    def get_technical_skills_by_area(self, area_id: str) -> list[dict[str, Any]]:
        """Get all technical skills for a specific area."""
        skills = [
            skill.to_dict() for skill in TECHNICAL_SKILLS.values()
            if area_id in skill.areas
        ]
        return skills
    
    def get_all_technical_skills(self) -> list[dict[str, Any]]:
        """Get all technical skills."""
        return [skill.to_dict() for skill in TECHNICAL_SKILLS.values()]
    
    def get_technical_skill_by_id(self, skill_id: str) -> dict[str, Any] | None:
        """Get a specific technical skill by ID."""
        skill = TECHNICAL_SKILLS.get(skill_id)
        return skill.to_dict() if skill else None
    
    # -------------------------------------------------------------------------
    # BEHAVIORAL SKILLS
    # -------------------------------------------------------------------------
    
    def get_all_behavioral_skills(self) -> list[dict[str, Any]]:
        """Get all behavioral competencies."""
        return [skill.to_dict() for skill in BEHAVIORAL_SKILLS.values()]
    
    def get_behavioral_skill_by_id(self, skill_id: str) -> dict[str, Any] | None:
        """Get a specific behavioral skill by ID."""
        skill = BEHAVIORAL_SKILLS.get(skill_id)
        return skill.to_dict() if skill else None
    
    def get_behavioral_skills_by_category(self, category: str) -> list[dict[str, Any]]:
        """Get behavioral skills by category."""
        return [
            skill.to_dict() for skill in BEHAVIORAL_SKILLS.values()
            if skill.categoria == category
        ]
    
    # -------------------------------------------------------------------------
    # SUGGESTIONS
    # -------------------------------------------------------------------------
    
    def suggest_skills_for_role(
        self,
        role_name: str,
        seniority_id: str | None = None
    ) -> dict[str, list[dict[str, Any]]]:
        """
        Suggest technical and behavioral skills for a role.
        
        Args:
            role_name: Name of the role
            seniority_id: Optional seniority level to adjust suggestions
            
        Returns:
            Dict with 'technical' and 'behavioral' skill lists
        """
        role_data = self.get_role_by_name(role_name)
        
        if not role_data:
            return {"technical": [], "behavioral": []}
        
        technical_skills = []
        for skill_id in role_data.get("competencias_tecnicas", []):
            skill = self.get_technical_skill_by_id(skill_id)
            if skill:
                technical_skills.append(skill)
        
        area_skills = self.get_technical_skills_by_area(role_data.get("area_id", ""))
        for skill in area_skills[:10]:
            if skill["id"] not in [s["id"] for s in technical_skills]:
                technical_skills.append(skill)
        
        behavioral_skills = []
        for skill_id in role_data.get("competencias_comportamentais", []):
            skill = self.get_behavioral_skill_by_id(skill_id)
            if skill:
                behavioral_skills.append(skill)
        
        if seniority_id:
            seniority = self.get_seniority_by_id(seniority_id)
            if seniority and seniority.get("ordem", 0) >= 10:
                leadership_skills = ["lideranca", "gestao_stakeholders", "visao_estrategica", "tomada_decisao"]
                for skill_id in leadership_skills:
                    skill = self.get_behavioral_skill_by_id(skill_id)
                    if skill and skill["id"] not in [s["id"] for s in behavioral_skills]:
                        behavioral_skills.append(skill)
        
        return {
            "technical": technical_skills,
            "behavioral": behavioral_skills
        }
    
    def search_skills(self, query: str) -> dict[str, list[dict[str, Any]]]:
        """
        Search for skills by name or keyword.
        
        Args:
            query: Search query
            
        Returns:
            Dict with 'technical' and 'behavioral' matching skills
        """
        if not query or len(query) < 2:
            return {"technical": [], "behavioral": []}
        
        query_lower = query.lower()
        
        technical_matches = []
        for skill in TECHNICAL_SKILLS.values():
            if query_lower in skill.nome.lower():
                technical_matches.append((skill, 1.0))
                continue
            
            for keyword in skill.palavras_chave:
                if query_lower in keyword.lower():
                    technical_matches.append((skill, 0.8))
                    break
            else:
                if query_lower in skill.descricao.lower():
                    technical_matches.append((skill, 0.5))
        
        behavioral_matches = []
        for skill in BEHAVIORAL_SKILLS.values():
            if query_lower in skill.nome.lower():
                behavioral_matches.append((skill, 1.0))
                continue
            
            for sub in skill.subcategorias:
                if query_lower in sub.lower():
                    behavioral_matches.append((skill, 0.8))
                    break
            else:
                if query_lower in skill.descricao.lower():
                    behavioral_matches.append((skill, 0.5))
        
        technical_matches.sort(key=lambda x: x[1], reverse=True)
        behavioral_matches.sort(key=lambda x: x[1], reverse=True)
        
        return {
            "technical": [s.to_dict() for s, _ in technical_matches[:20]],
            "behavioral": [s.to_dict() for s, _ in behavioral_matches[:20]]
        }
    
    # -------------------------------------------------------------------------
    # SUMMARY
    # -------------------------------------------------------------------------
    
    def get_catalog_summary(self) -> dict[str, Any]:
        """
        Get a complete summary of the catalog for review.
        
        Returns:
            Complete catalog summary with counts and samples
        """
        areas = self.get_all_areas()
        seniority_levels = self.get_all_seniority_levels()
        all_roles = self.get_all_roles()
        all_technical_skills = self.get_all_technical_skills()
        all_behavioral_skills = self.get_all_behavioral_skills()
        
        roles_by_area = {}
        for area in areas:
            area_roles = self.get_roles_by_area(area["id"])
            roles_by_area[area["id"]] = {
                "area_nome": area["nome"],
                "quantidade_cargos": len(area_roles),
                "cargos": [r["nome"] for r in area_roles]
            }
        
        technical_by_area = {}
        for area in areas:
            area_skills = self.get_technical_skills_by_area(area["id"])
            technical_by_area[area["id"]] = {
                "area_nome": area["nome"],
                "quantidade_skills": len(area_skills),
                "skills": [s["nome"] for s in area_skills]
            }
        
        behavioral_by_category = {}
        for skill in all_behavioral_skills:
            cat = skill["categoria"]
            if cat not in behavioral_by_category:
                behavioral_by_category[cat] = []
            behavioral_by_category[cat].append(skill["nome"])
        
        return {
            "resumo": {
                "total_areas": len(areas),
                "total_niveis_senioridade": len(seniority_levels),
                "total_cargos": len(all_roles),
                "total_competencias_tecnicas": len(all_technical_skills),
                "total_competencias_comportamentais": len(all_behavioral_skills)
            },
            "areas": areas,
            "niveis_senioridade": seniority_levels,
            "cargos_por_area": roles_by_area,
            "competencias_tecnicas_por_area": technical_by_area,
            "competencias_comportamentais_por_categoria": behavioral_by_category,
            "todos_cargos": all_roles,
            "todas_competencias_tecnicas": all_technical_skills,
            "todas_competencias_comportamentais": all_behavioral_skills
        }


organization_catalog_service = OrganizationCatalogService()


# FastAPI dependency injection factory
def get_organization_catalog_service() -> "OrganizationCatalogService":
    return organization_catalog_service
