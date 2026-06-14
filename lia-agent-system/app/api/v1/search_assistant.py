"""
Search Assistant API - Endpoints for intelligent search guidance and suggestions.
Provides autocomplete, search analysis, and smart alerts for recruiters.
Uses centralized taxonomy library for comprehensive term matching.
"""
import logging
from enum import Enum, StrEnum
from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.taxonomy import (
    INDUSTRIES_TAXONOMY,
    LOCATIONS_BRAZIL,
    SENIORITY_LEVELS,
    TECHNICAL_SKILLS_TAXONOMY,
    WORK_MODELS,
)
from app.core.taxonomy import (
    JOB_TITLES_TAXONOMY as TAXONOMY_JOB_TITLES,
)
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search-assistant", tags=["search-assistant"])


class SuggestionCategory(StrEnum):
    JOB_TITLE = "job_title"
    SKILL = "skill"
    LOCATION = "location"
    INDUSTRY = "industry"
    EXPERIENCE = "experience"
    BEST_PRACTICE = "best_practice"


class SearchSuggestion(BaseModel):
    text: str
    category: SuggestionCategory
    description: str | None = None
    synonyms: list[str] = Field(default_factory=list)
    popularity_score: float = 0.0


class AlertSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class SearchAlert(BaseModel):
    type: str
    severity: AlertSeverity
    message: str
    suggestion: str | None = None
    action_label: str | None = None
    action_value: str | None = None


class SuggestionsResponse(BaseModel):
    suggestions: list[SearchSuggestion] = Field(default_factory=list)
    category_suggestions: dict[str, list[str]] = Field(default_factory=dict)


class SearchAnalysisResponse(BaseModel):
    completeness_score: int = Field(ge=0, le=100)
    filled_criteria: list[str] = Field(default_factory=list)
    missing_criteria: list[str] = Field(default_factory=list)
    alerts: list[SearchAlert] = Field(default_factory=list)
    enrichment_suggestions: dict[str, list[str]] = Field(default_factory=dict)
    next_recommended_action: str | None = None


JOB_TITLES_TAXONOMY = TAXONOMY_JOB_TITLES

SKILLS_TAXONOMY = TECHNICAL_SKILLS_TAXONOMY

LOCATIONS_TAXONOMY = []
for region, cities in LOCATIONS_BRAZIL.items():
    LOCATIONS_TAXONOMY.extend(cities)
for model, names in WORK_MODELS.items():
    LOCATIONS_TAXONOMY.extend(names)

LOCAL_INDUSTRIES_TAXONOMY = INDUSTRIES_TAXONOMY

EXPERIENCE_LEVELS = [
    {"label": level_data["canonical"], "value": level_data["years"], "aliases": level_data["synonyms"]}
    for level_key, level_data in SENIORITY_LEVELS.items()
]

BEST_PRACTICES = [
    {"text": "Inglês avançado", "description": "Para posições que exigem comunicação internacional"},
    {"text": "Inglês fluente", "description": "Para posições com comunicação diária em inglês"},
    {"text": "Experiência em startups", "description": "Ambiente dinâmico e adaptável"},
    {"text": "Experiência em empresas grandes", "description": "Processos estruturados e escala"},
    {"text": "Liderança de times", "description": "Para posições de gestão"},
    {"text": "Metodologias ágeis", "description": "Scrum, Kanban, SAFe"},
    {"text": "Remoto primeiro", "description": "Experiência com trabalho distribuído"},
    {"text": "Certificações Cloud", "description": "AWS, Azure, GCP certificados"},
    {"text": "Mentoria", "description": "Experiência mentorando outros desenvolvedores"},
]

SYNONYM_MAP = {
    "dev": ["desenvolvedor", "developer", "programador", "software engineer"],
    "python": ["django", "fastapi", "flask", "pandas", "numpy"],
    "javascript": ["js", "node", "nodejs", "react", "vue", "angular", "typescript", "ts"],
    "frontend": ["front-end", "front end", "ui", "interface", "react", "vue", "angular"],
    "backend": ["back-end", "back end", "api", "servidor", "node", "python", "java"],
    "fullstack": ["full-stack", "full stack", "fullstack developer"],
    "data scientist": ["cientista de dados", "ds", "ml engineer", "data science"],
    "data engineer": ["engenheiro de dados", "de", "data engineering"],
    "product manager": ["pm", "gerente de produto", "product owner", "po"],
    "devops": ["sre", "platform engineer", "infraestrutura", "cloud engineer"],
    "senior": ["sênior", "sr", "especialista", "experiente"],
    "pleno": ["mid", "mid-level", "intermediário", "nível 2"],
    "junior": ["júnior", "jr", "trainee", "estagiário", "entry level"],
    "sap": ["sap abap", "abap", "sap hana", "sap s/4hana", "consultor sap", "desenvolvedor sap", "sap fico", "sap mm", "sap sd"],
    "abap": ["sap abap", "sap", "desenvolvedor abap", "abap oo"],
    "totvs": ["protheus", "rm", "datasul", "totvs erp"],
    "erp": ["sap", "oracle erp", "totvs", "salesforce", "dynamics"],
    "aws": ["amazon web services", "cloud aws", "amazon cloud"],
    "azure": ["microsoft azure", "azure cloud"],
    "gcp": ["google cloud", "google cloud platform"],
    "kubernetes": ["k8s", "eks", "aks", "gke"],
    "docker": ["containers", "containerização"],
    "react": ["reactjs", "react.js", "react native"],
    "vue": ["vuejs", "vue.js", "nuxt"],
    "angular": ["angularjs", "angular 2+"],
}


def get_synonyms(term: str) -> list[str]:
    """Get synonyms for a term."""
    term_lower = term.lower()
    for key, synonyms in SYNONYM_MAP.items():
        if term_lower == key or term_lower in synonyms:
            return [s for s in [key] + synonyms if s.lower() != term_lower]
    return []


def calculate_completeness(entities: dict[str, Any]) -> tuple[int, list[str], list[str]]:
    """Calculate search completeness based on filled criteria."""
    criteria = {
        "job_title": ("Cargo", entities.get("job_title")),
        "location": ("Localização", entities.get("location")),
        "years_experience": ("Experiência", entities.get("years_experience")),
        "skills": ("Habilidades", entities.get("skills")),
        "industry": ("Setor", entities.get("industry")),
    }
    
    filled = []
    missing = []
    
    for key, (label, value) in criteria.items():
        if value and (not isinstance(value, list) or len(value) > 0):
            filled.append(label)
        else:
            missing.append(label)
    
    score = int((len(filled) / len(criteria)) * 100)
    return score, filled, missing


def analyze_search_quality(query: str, entities: dict[str, Any]) -> list[SearchAlert]:
    """Analyze search query and return alerts."""
    alerts = []
    
    completeness, filled, missing = calculate_completeness(entities)
    
    if completeness < 40:
        alerts.append(SearchAlert(
            type="broad_search",
            severity=AlertSeverity.WARNING,
            message="Busca muito ampla pode retornar muitos resultados irrelevantes",
            suggestion=f"Adicione: {', '.join(missing[:2])}",
            action_label="Ver critérios faltantes",
        ))
    
    if completeness == 100 and len(query) > 100:
        alerts.append(SearchAlert(
            type="restrictive_search",
            severity=AlertSeverity.INFO,
            message="Muitos critérios podem limitar demais os resultados",
            suggestion="Considere flexibilizar alguns filtros se encontrar poucos candidatos",
        ))
    
    query_lower = query.lower()
    ambiguous_terms = {
        "dev": "Especifique: Frontend, Backend, Mobile ou Full Stack?",
        "analista": "Especifique: Analista de Dados, QA, Negócios ou Sistemas?",
        "gerente": "Especifique: Gerente de Produto, Projeto ou Engenharia?",
        "engineer": "Especifique: Software, Data, DevOps ou ML Engineer?",
    }
    
    for term, suggestion in ambiguous_terms.items():
        if term in query_lower and not any(
            specific in query_lower 
            for specific in ["frontend", "backend", "mobile", "fullstack", "dados", "qa", "produto", "projeto"]
        ):
            alerts.append(SearchAlert(
                type="ambiguous_term",
                severity=AlertSeverity.INFO,
                message=f"Termo '{term}' pode ser ambíguo",
                suggestion=suggestion,
            ))
            break
    
    skills = entities.get("skills", [])
    if skills:
        for skill in skills[:3]:
            synonyms = get_synonyms(skill)
            if synonyms:
                alerts.append(SearchAlert(
                    type="synonym_suggestion",
                    severity=AlertSeverity.INFO,
                    message=f"Considere também: {', '.join(synonyms[:3])}",
                    suggestion=f"Adicionar sinônimos de '{skill}'",
                    action_value=", ".join(synonyms[:2]),
                ))
                break
    
    return alerts


def get_suggestions_for_query(query: str, category: str | None = None) -> list[SearchSuggestion]:
    """Get suggestions based on current query."""
    suggestions = []
    query_lower = query.lower() if query else ""
    
    for key, titles in JOB_TITLES_TAXONOMY.items():
        if not query or key in query_lower or any(t.lower() in query_lower for t in titles[:2]):
            for title in titles[:3]:
                if not query or query_lower in title.lower() or title.lower().startswith(query_lower[:3] if len(query_lower) >= 3 else ""):
                    suggestions.append(SearchSuggestion(
                        text=title,
                        category=SuggestionCategory.JOB_TITLE,
                        synonyms=titles[:3],
                        popularity_score=0.8,
                    ))
    
    for cat, skills in SKILLS_TAXONOMY.items():
        for skill in skills:
            if not query or query_lower in skill.lower():
                suggestions.append(SearchSuggestion(
                    text=skill,
                    category=SuggestionCategory.SKILL,
                    popularity_score=0.7,
                ))
    
    for loc in LOCATIONS_TAXONOMY:
        if not query or query_lower in loc.lower():
            suggestions.append(SearchSuggestion(
                text=loc,
                category=SuggestionCategory.LOCATION,
                popularity_score=0.6,
            ))
    
    for ind in INDUSTRIES_TAXONOMY:
        if not query or query_lower in ind.lower():
            suggestions.append(SearchSuggestion(
                text=ind,
                category=SuggestionCategory.INDUSTRY,
                popularity_score=0.5,
            ))
    
    for bp in BEST_PRACTICES:
        if not query or query_lower in bp["text"].lower():
            suggestions.append(SearchSuggestion(
                text=bp["text"],
                category=SuggestionCategory.BEST_PRACTICE,
                description=bp["description"],
                popularity_score=0.4,
            ))
    
    suggestions.sort(key=lambda s: s.popularity_score, reverse=True)
    return suggestions[:20]


def get_enrichment_suggestions(entities: dict[str, Any]) -> dict[str, list[str]]:
    """Get enrichment suggestions based on current entities."""
    enrichments = {}
    
    job_title = entities.get("job_title", "").lower()
    if job_title:
        if "frontend" in job_title or "react" in job_title:
            enrichments["skills"] = ["React", "TypeScript", "Next.js", "Tailwind CSS"]
        elif "backend" in job_title or "python" in job_title:
            enrichments["skills"] = ["Python", "FastAPI", "PostgreSQL", "Docker"]
        elif "data" in job_title:
            enrichments["skills"] = ["Python", "SQL", "Pandas", "Machine Learning"]
        elif "devops" in job_title:
            enrichments["skills"] = ["Docker", "Kubernetes", "AWS", "Terraform"]
        elif "product" in job_title:
            enrichments["skills"] = ["Product Discovery", "Métricas", "Roadmap", "Stakeholders"]
    
    skills = entities.get("skills", [])
    if skills:
        skill_lower = [s.lower() for s in skills]
        if "react" in skill_lower or "vue" in skill_lower:
            enrichments["job_title"] = ["Frontend Developer", "Full Stack Developer"]
        if "python" in skill_lower and "machine learning" in skill_lower:
            enrichments["job_title"] = ["Data Scientist", "ML Engineer"]
    
    return enrichments


@router.get("/suggestions", response_model=SuggestionsResponse)
async def get_search_suggestions(
    query: str = Query("", description="Texto atual da busca"),
    category: str | None = Query(None, description="Filtrar por categoria"),
    limit: int = Query(15, ge=1, le=50),
    db: AsyncSession = Depends(get_db), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Get intelligent search suggestions based on current query.
    Returns autocomplete suggestions, related terms, and best practices.
    """
    suggestions = get_suggestions_for_query(query, category)[:limit]
    
    category_suggestions = {
        "cargo": [s.text for s in suggestions if s.category == SuggestionCategory.JOB_TITLE][:5],
        "habilidades": [s.text for s in suggestions if s.category == SuggestionCategory.SKILL][:8],
        "localizacao": [s.text for s in suggestions if s.category == SuggestionCategory.LOCATION][:5],
        "setor": [s.text for s in suggestions if s.category == SuggestionCategory.INDUSTRY][:5],
        "melhores_praticas": [s.text for s in suggestions if s.category == SuggestionCategory.BEST_PRACTICE][:3],
    }
    
    return SuggestionsResponse(
        suggestions=suggestions,
        category_suggestions=category_suggestions,
    )


class SearchAnalyzeRequest(WeDoBaseModel):
    query: str = Field(..., description="Texto da busca")
    entities: dict[str, Any] = Field(default_factory=dict, description="Entidades parseadas")


@router.post("/analyze", response_model=SearchAnalysisResponse)
async def analyze_search(
    request: SearchAnalyzeRequest,
    db: AsyncSession = Depends(get_db), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Analyze search query and provide quality feedback.
    Returns completeness score, alerts, and improvement suggestions.
    """
    entities = request.entities or {}
    completeness, filled, missing = calculate_completeness(entities)
    alerts = analyze_search_quality(request.query, entities)
    enrichments = get_enrichment_suggestions(entities)
    
    if missing:
        next_action = f"Adicione {missing[0].lower()} para melhorar os resultados"
    elif completeness == 100:
        next_action = "Busca bem definida! Pronta para executar"
    else:
        next_action = "Continue descrevendo o perfil ideal"
    
    return SearchAnalysisResponse(
        completeness_score=completeness,
        filled_criteria=filled,
        missing_criteria=missing,
        alerts=alerts,
        enrichment_suggestions=enrichments,
        next_recommended_action=next_action,
    )


@router.get("/synonyms", response_model=None)
async def get_term_synonyms(
    term: str = Query(..., description="Termo para buscar sinônimos"),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Get synonyms for a specific term."""
    synonyms = get_synonyms(term)
    return {"term": term, "synonyms": synonyms}


class AutocompleteItem(BaseModel):
    text: str
    category: str
    icon: str = "sparkles"
    description: str | None = None
    insert_text: str  # What to insert when selected


class AutocompleteResponse(BaseModel):
    items: list[AutocompleteItem] = Field(default_factory=list)
    context_hint: str | None = None


AUTOCOMPLETE_TEMPLATES = [
    {"pattern": "dev", "suggestions": [
        {"text": "Desenvolvedor Backend", "category": "cargo", "icon": "code"},
        {"text": "Desenvolvedor Frontend", "category": "cargo", "icon": "layout"},
        {"text": "Desenvolvedor Full Stack", "category": "cargo", "icon": "layers"},
        {"text": "Desenvolvedor Mobile", "category": "cargo", "icon": "smartphone"},
    ]},
    {"pattern": "python", "suggestions": [
        {"text": "Python com Django", "category": "stack", "icon": "code"},
        {"text": "Python com FastAPI", "category": "stack", "icon": "zap"},
        {"text": "Python para Data Science", "category": "stack", "icon": "bar-chart"},
    ]},
    {"pattern": "react", "suggestions": [
        {"text": "React com TypeScript", "category": "stack", "icon": "code"},
        {"text": "React Native (Mobile)", "category": "stack", "icon": "smartphone"},
        {"text": "Next.js (Full Stack)", "category": "stack", "icon": "layers"},
    ]},
    {"pattern": "senior", "suggestions": [
        {"text": "Sênior (6+ anos)", "category": "experiencia", "icon": "award"},
        {"text": "Tech Lead Sênior", "category": "cargo", "icon": "users"},
    ]},
    {"pattern": "remoto", "suggestions": [
        {"text": "100% Remoto", "category": "modalidade", "icon": "home"},
        {"text": "Remoto Brasil", "category": "localizacao", "icon": "map-pin"},
        {"text": "Híbrido (2-3x escritório)", "category": "modalidade", "icon": "building"},
    ]},
    {"pattern": "são paulo", "suggestions": [
        {"text": "São Paulo - Capital", "category": "localizacao", "icon": "map-pin"},
        {"text": "Grande São Paulo", "category": "localizacao", "icon": "map"},
        {"text": "São Paulo - Híbrido", "category": "modalidade", "icon": "building"},
    ]},
    {"pattern": "product", "suggestions": [
        {"text": "Product Manager", "category": "cargo", "icon": "target"},
        {"text": "Product Owner", "category": "cargo", "icon": "clipboard"},
        {"text": "Product Designer", "category": "cargo", "icon": "pen-tool"},
    ]},
    {"pattern": "data", "suggestions": [
        {"text": "Data Scientist", "category": "cargo", "icon": "brain"},
        {"text": "Data Engineer", "category": "cargo", "icon": "database"},
        {"text": "Data Analyst", "category": "cargo", "icon": "bar-chart"},
    ]},
    {"pattern": "fintech", "suggestions": [
        {"text": "Fintech / Serviços Financeiros", "category": "setor", "icon": "dollar-sign"},
        {"text": "Experiência em bancos digitais", "category": "experiencia", "icon": "credit-card"},
    ]},
    {"pattern": "inglês", "suggestions": [
        {"text": "Inglês Avançado", "category": "idioma", "icon": "globe"},
        {"text": "Inglês Fluente", "category": "idioma", "icon": "message-circle"},
        {"text": "Inglês Intermediário", "category": "idioma", "icon": "book"},
    ]},
    {"pattern": "sap", "suggestions": [
        {"text": "Desenvolvedor SAP ABAP", "category": "cargo", "icon": "code"},
        {"text": "Consultor SAP MM", "category": "cargo", "icon": "briefcase"},
        {"text": "Consultor SAP SD", "category": "cargo", "icon": "briefcase"},
        {"text": "Consultor SAP FI/CO", "category": "cargo", "icon": "dollar-sign"},
        {"text": "SAP Basis", "category": "cargo", "icon": "database"},
        {"text": "SAP S/4HANA", "category": "habilidade", "icon": "layers"},
    ]},
    {"pattern": "abap", "suggestions": [
        {"text": "Desenvolvedor ABAP", "category": "cargo", "icon": "code"},
        {"text": "SAP ABAP", "category": "habilidade", "icon": "code"},
        {"text": "ABAP com SAP HANA", "category": "stack", "icon": "database"},
        {"text": "ABAP OO (Orientado a Objetos)", "category": "habilidade", "icon": "box"},
    ]},
    {"pattern": "totvs", "suggestions": [
        {"text": "Desenvolvedor TOTVS", "category": "cargo", "icon": "code"},
        {"text": "Consultor Protheus", "category": "cargo", "icon": "briefcase"},
        {"text": "TOTVS RM", "category": "habilidade", "icon": "layers"},
    ]},
    {"pattern": "erp", "suggestions": [
        {"text": "Consultor ERP", "category": "cargo", "icon": "briefcase"},
        {"text": "SAP ERP", "category": "habilidade", "icon": "layers"},
        {"text": "Oracle ERP", "category": "habilidade", "icon": "database"},
        {"text": "TOTVS Protheus", "category": "habilidade", "icon": "layers"},
    ]},
    {"pattern": "consultor", "suggestions": [
        {"text": "Consultor SAP", "category": "cargo", "icon": "briefcase"},
        {"text": "Consultor Funcional", "category": "cargo", "icon": "clipboard"},
        {"text": "Consultor Técnico", "category": "cargo", "icon": "code"},
        {"text": "Consultor de Negócios", "category": "cargo", "icon": "target"},
    ]},
    {"pattern": "aws", "suggestions": [
        {"text": "AWS (Amazon Web Services)", "category": "skill", "icon": "cloud"},
        {"text": "AWS + Terraform", "category": "stack", "icon": "settings"},
        {"text": "AWS + Kubernetes", "category": "stack", "icon": "box"},
    ]},
    {"pattern": "java", "suggestions": [
        {"text": "Java com Spring Boot", "category": "stack", "icon": "coffee"},
        {"text": "Java Backend Sênior", "category": "cargo", "icon": "code"},
        {"text": "JavaScript/TypeScript", "category": "skill", "icon": "file-code"},
    ]},
    {"pattern": "analista", "suggestions": [
        {"text": "Analista Financeiro Pleno", "category": "cargo", "icon": "bar-chart"},
        {"text": "Analista de RH Sênior", "category": "cargo", "icon": "users"},
        {"text": "Analista de Marketing Digital", "category": "cargo", "icon": "trending-up"},
        {"text": "Analista de BI (Power BI)", "category": "cargo", "icon": "pie-chart"},
        {"text": "Analista Contábil", "category": "cargo", "icon": "file-text"},
    ]},
    {"pattern": "financeiro", "suggestions": [
        {"text": "Controller Financeiro", "category": "cargo", "icon": "dollar-sign"},
        {"text": "Gerente Financeiro", "category": "cargo", "icon": "briefcase"},
        {"text": "Analista Financeiro Sênior", "category": "cargo", "icon": "bar-chart"},
        {"text": "Tesoureiro", "category": "cargo", "icon": "credit-card"},
    ]},
    {"pattern": "contab", "suggestions": [
        {"text": "Contador CRC", "category": "cargo", "icon": "file-text"},
        {"text": "Controller", "category": "cargo", "icon": "dollar-sign"},
        {"text": "Fiscal Tributário", "category": "cargo", "icon": "clipboard"},
        {"text": "IFRS / CPC", "category": "habilidade", "icon": "book"},
    ]},
    {"pattern": "rh", "suggestions": [
        {"text": "HRBP (HR Business Partner)", "category": "cargo", "icon": "users"},
        {"text": "Especialista em Recrutamento", "category": "cargo", "icon": "user-check"},
        {"text": "Analista de Remuneração", "category": "cargo", "icon": "dollar-sign"},
        {"text": "DHO - Desenvolvimento Humano", "category": "cargo", "icon": "heart"},
    ]},
    {"pattern": "marketing", "suggestions": [
        {"text": "Growth Marketing Sênior", "category": "cargo", "icon": "trending-up"},
        {"text": "Marketing de Performance (ROI)", "category": "cargo", "icon": "target"},
        {"text": "SEO / SEM Especialista", "category": "cargo", "icon": "search"},
        {"text": "Marketing Digital B2B", "category": "cargo", "icon": "briefcase"},
    ]},
    {"pattern": "vendas", "suggestions": [
        {"text": "Account Executive (AE)", "category": "cargo", "icon": "target"},
        {"text": "SDR / BDR (Prospecção)", "category": "cargo", "icon": "phone"},
        {"text": "Gerente de Vendas B2B", "category": "cargo", "icon": "briefcase"},
        {"text": "Key Account Manager", "category": "cargo", "icon": "star"},
    ]},
    {"pattern": "commercial", "suggestions": [
        {"text": "Diretor Comercial", "category": "cargo", "icon": "briefcase"},
        {"text": "Gerente Comercial Sênior", "category": "cargo", "icon": "target"},
        {"text": "Account Manager Enterprise", "category": "cargo", "icon": "users"},
    ]},
    {"pattern": "logistica", "suggestions": [
        {"text": "Analista de Supply Chain", "category": "cargo", "icon": "truck"},
        {"text": "Coordenador de Logística", "category": "cargo", "icon": "map-pin"},
        {"text": "Especialista em Compras", "category": "cargo", "icon": "shopping-cart"},
        {"text": "Analista de Estoque / WMS", "category": "cargo", "icon": "package"},
    ]},
    {"pattern": "supply", "suggestions": [
        {"text": "Analista de Supply Chain Sênior", "category": "cargo", "icon": "truck"},
        {"text": "Supply Chain + S&OP", "category": "stack", "icon": "bar-chart"},
        {"text": "Compras Estratégicas", "category": "cargo", "icon": "shopping-cart"},
    ]},
    {"pattern": "juridico", "suggestions": [
        {"text": "Advogado Trabalhista", "category": "cargo", "icon": "book"},
        {"text": "Advogado Tributário", "category": "cargo", "icon": "file-text"},
        {"text": "Compliance Officer", "category": "cargo", "icon": "shield"},
        {"text": "DPO (Proteção de Dados / LGPD)", "category": "cargo", "icon": "lock"},
    ]},
    {"pattern": "gerente", "suggestions": [
        {"text": "Gerente de Projetos (PMP)", "category": "cargo", "icon": "clipboard"},
        {"text": "Gerente de Produto / Product Manager", "category": "cargo", "icon": "target"},
        {"text": "Gerente Comercial", "category": "cargo", "icon": "briefcase"},
        {"text": "Gerente de RH / Pessoas", "category": "cargo", "icon": "users"},
    ]},
    {"pattern": "diretor", "suggestions": [
        {"text": "Diretor Financeiro (CFO)", "category": "cargo", "icon": "dollar-sign"},
        {"text": "Diretor Comercial", "category": "cargo", "icon": "target"},
        {"text": "Diretor de RH / Pessoas (CHRO)", "category": "cargo", "icon": "users"},
        {"text": "Diretor de Tecnologia (CTO)", "category": "cargo", "icon": "cpu"},
    ]},
    {"pattern": "saude", "suggestions": [
        {"text": "Médico Especialista", "category": "cargo", "icon": "heart"},
        {"text": "Enfermeiro(a) UTI", "category": "cargo", "icon": "activity"},
        {"text": "Analista de Saúde Corporativa", "category": "cargo", "icon": "clipboard"},
    ]},
    # ── Tech gaps ────────────────────────────────────────────────────────────
    {"pattern": "node", "suggestions": [
        {"text": "Node.js com Express", "category": "stack", "icon": "zap"},
        {"text": "Node.js com NestJS", "category": "stack", "icon": "layers"},
        {"text": "Node.js + TypeScript Sênior", "category": "stack", "icon": "code"},
        {"text": "Node.js + GraphQL", "category": "stack", "icon": "git-branch"},
    ]},
    {"pattern": "angular", "suggestions": [
        {"text": "Angular + TypeScript", "category": "stack", "icon": "code"},
        {"text": "Angular + RxJS Sênior", "category": "stack", "icon": "zap"},
        {"text": "Angular 17+ (Standalone Components)", "category": "stack", "icon": "layers"},
    ]},
    {"pattern": "vue", "suggestions": [
        {"text": "Vue.js 3 + Composition API", "category": "stack", "icon": "code"},
        {"text": "Vue.js + Nuxt.js", "category": "stack", "icon": "layers"},
        {"text": "Vue.js + TypeScript", "category": "stack", "icon": "code"},
    ]},
    {"pattern": "azure", "suggestions": [
        {"text": "Azure Cloud (AZ-900/AZ-204)", "category": "habilidade", "icon": "cloud"},
        {"text": "Azure DevOps (CI/CD)", "category": "stack", "icon": "git-merge"},
        {"text": ".NET com Azure", "category": "stack", "icon": "layers"},
        {"text": "Azure + Kubernetes (AKS)", "category": "stack", "icon": "box"},
    ]},
    {"pattern": "devops", "suggestions": [
        {"text": "DevOps Engineer (CI/CD)", "category": "cargo", "icon": "git-merge"},
        {"text": "SRE (Site Reliability Engineer)", "category": "cargo", "icon": "activity"},
        {"text": "DevSecOps", "category": "cargo", "icon": "shield"},
        {"text": "Platform Engineer (IaC)", "category": "cargo", "icon": "settings"},
    ]},
    {"pattern": "mobile", "suggestions": [
        {"text": "iOS Developer (Swift/SwiftUI)", "category": "cargo", "icon": "smartphone"},
        {"text": "Android Developer (Kotlin)", "category": "cargo", "icon": "smartphone"},
        {"text": "Flutter Developer", "category": "cargo", "icon": "layers"},
        {"text": "React Native Developer", "category": "cargo", "icon": "smartphone"},
    ]},
    {"pattern": "flutter", "suggestions": [
        {"text": "Flutter Developer Sênior", "category": "cargo", "icon": "smartphone"},
        {"text": "Flutter + Dart", "category": "stack", "icon": "code"},
        {"text": "Flutter + Firebase", "category": "stack", "icon": "layers"},
    ]},
    {"pattern": "qa", "suggestions": [
        {"text": "QA Engineer (Automação)", "category": "cargo", "icon": "check-circle"},
        {"text": "Analista de Testes (Cypress/Selenium)", "category": "cargo", "icon": "check-square"},
        {"text": "SDET (Dev em Teste)", "category": "cargo", "icon": "code"},
        {"text": "QA Manual + Automação", "category": "cargo", "icon": "clipboard"},
    ]},
    {"pattern": "qualidade", "suggestions": [
        {"text": "QA Engineer (Automação)", "category": "cargo", "icon": "check-circle"},
        {"text": "Analista de Qualidade de Software", "category": "cargo", "icon": "check-square"},
        {"text": "Quality Assurance Sênior", "category": "cargo", "icon": "award"},
    ]},
    {"pattern": "seguranca", "suggestions": [
        {"text": "Analista de Segurança da Informação", "category": "cargo", "icon": "shield"},
        {"text": "Pentest / Red Team", "category": "cargo", "icon": "alert-triangle"},
        {"text": "Analista SOC / Blue Team", "category": "cargo", "icon": "eye"},
        {"text": "DPO (Proteção de Dados / LGPD)", "category": "cargo", "icon": "lock"},
    ]},
    {"pattern": ".net", "suggestions": [
        {"text": ".NET Developer (C#)", "category": "cargo", "icon": "code"},
        {"text": ".NET com Azure", "category": "stack", "icon": "cloud"},
        {"text": ".NET Sênior (Microserviços)", "category": "cargo", "icon": "layers"},
        {"text": "C# Backend Sênior", "category": "cargo", "icon": "code"},
    ]},
    {"pattern": "scrum", "suggestions": [
        {"text": "Scrum Master (CSM)", "category": "cargo", "icon": "repeat"},
        {"text": "Agile Coach", "category": "cargo", "icon": "users"},
        {"text": "RTE (Release Train Engineer — SAFe)", "category": "cargo", "icon": "activity"},
    ]},
    # ── Seniority normalization (aliases sem acento) ──────────────────────
    {"pattern": "junior", "suggestions": [
        {"text": "Desenvolvedor Júnior (0-2 anos)", "category": "experiencia", "icon": "user"},
        {"text": "Analista Júnior", "category": "experiencia", "icon": "user"},
        {"text": "Estágio → Júnior (recém-formado)", "category": "experiencia", "icon": "graduation-cap"},
    ]},
    {"pattern": "pleno", "suggestions": [
        {"text": "Desenvolvedor Pleno (2-5 anos)", "category": "experiencia", "icon": "user-check"},
        {"text": "Analista Pleno", "category": "experiencia", "icon": "user-check"},
        {"text": "Pleno com potencial de Sênior", "category": "experiencia", "icon": "trending-up"},
    ]},
    {"pattern": "nivel", "suggestions": [
        {"text": "Júnior (0-2 anos)", "category": "experiencia", "icon": "user"},
        {"text": "Pleno (2-5 anos)", "category": "experiencia", "icon": "user-check"},
        {"text": "Sênior (5+ anos)", "category": "experiencia", "icon": "award"},
        {"text": "Tech Lead / Especialista", "category": "experiencia", "icon": "star"},
    ]},
    # ── Gestão / Ops (aliases com acentuação diferente) ──────────────────
    {"pattern": "gestao", "suggestions": [
        {"text": "Gestor de Projetos (PMP)", "category": "cargo", "icon": "clipboard"},
        {"text": "Gestão de Pessoas / HRBP", "category": "cargo", "icon": "users"},
        {"text": "Head de Produto (Product Manager)", "category": "cargo", "icon": "target"},
        {"text": "Gestão de Operações", "category": "cargo", "icon": "settings"},
    ]},
    {"pattern": "operacoes", "suggestions": [
        {"text": "Analista de Operações Sênior", "category": "cargo", "icon": "settings"},
        {"text": "Gerente de Operações", "category": "cargo", "icon": "briefcase"},
        {"text": "COO / Head de Operações", "category": "cargo", "icon": "activity"},
    ]},
    {"pattern": "pmo", "suggestions": [
        {"text": "Analista de PMO Sênior", "category": "cargo", "icon": "clipboard"},
        {"text": "Gestor de PMO", "category": "cargo", "icon": "briefcase"},
        {"text": "PMO + Agile/Scrum", "category": "cargo", "icon": "repeat"},
    ]},
    # ── Não-tech adicionais ───────────────────────────────────────────────
    {"pattern": "fiscal", "suggestions": [
        {"text": "Analista Fiscal (ICMS/ISS/PIS/COFINS)", "category": "cargo", "icon": "file-text"},
        {"text": "Especialista Tributário", "category": "cargo", "icon": "dollar-sign"},
        {"text": "Auditor Fiscal", "category": "cargo", "icon": "search"},
        {"text": "Contador / Fiscal (CRC)", "category": "cargo", "icon": "clipboard"},
    ]},
    {"pattern": "atendimento", "suggestions": [
        {"text": "Customer Success Manager (CSM)", "category": "cargo", "icon": "heart"},
        {"text": "CX Analyst / Customer Experience", "category": "cargo", "icon": "smile"},
        {"text": "Analista de Atendimento ao Cliente", "category": "cargo", "icon": "phone"},
        {"text": "Supervisor de Atendimento", "category": "cargo", "icon": "users"},
    ]},
    {"pattern": "engenheiro", "suggestions": [
        {"text": "Engenheiro de Produção", "category": "cargo", "icon": "settings"},
        {"text": "Engenheiro Civil", "category": "cargo", "icon": "building"},
        {"text": "Engenheiro Mecânico", "category": "cargo", "icon": "tool"},
        {"text": "Engenheiro Eletricista", "category": "cargo", "icon": "zap"},
    ]},
    {"pattern": "assistente", "suggestions": [
        {"text": "Assistente Administrativo", "category": "cargo", "icon": "clipboard"},
        {"text": "Assistente Comercial / Vendas", "category": "cargo", "icon": "briefcase"},
        {"text": "Assistente de RH", "category": "cargo", "icon": "users"},
        {"text": "Assistente Financeiro", "category": "cargo", "icon": "dollar-sign"},
    ]},
]


def get_predictive_suggestions(query: str, cursor_position: int | None = None) -> list[AutocompleteItem]:
    """Get predictive autocomplete suggestions based on current query."""
    if not query or len(query) < 2:
        return []
    
    query_lower = query.lower().strip()
    words = query_lower.split()
    last_word = words[-1] if words else ""
    
    suggestions = []
    seen_texts = set()
    
    # 1. Match against templates
    for template in AUTOCOMPLETE_TEMPLATES:
        if template["pattern"] in query_lower or last_word.startswith(template["pattern"][:3]):
            for sugg in template["suggestions"]:
                if sugg["text"] not in seen_texts:
                    # Create insert text that completes/replaces
                    insert_text = sugg["text"]
                    if last_word and sugg["text"].lower().startswith(last_word):
                        # Complete the word
                        insert_text = sugg["text"]
                    
                    suggestions.append(AutocompleteItem(
                        text=sugg["text"],
                        category=sugg["category"],
                        icon=sugg.get("icon", "sparkles"),
                        insert_text=insert_text,
                    ))
                    seen_texts.add(sugg["text"])
    
    # 2. Job title suggestions
    for key, titles in JOB_TITLES_TAXONOMY.items():
        for title in titles:
            if last_word and title.lower().startswith(last_word) and title not in seen_texts:
                suggestions.append(AutocompleteItem(
                    text=title,
                    category="cargo",
                    icon="briefcase",
                    insert_text=title,
                ))
                seen_texts.add(title)
    
    # 3. Skill suggestions
    for cat, skills in SKILLS_TAXONOMY.items():
        for skill in skills:
            if last_word and skill.lower().startswith(last_word) and skill not in seen_texts:
                suggestions.append(AutocompleteItem(
                    text=skill,
                    category="habilidade",
                    icon="code",
                    insert_text=skill,
                ))
                seen_texts.add(skill)
    
    # 4. Location suggestions
    for loc in LOCATIONS_TAXONOMY:
        if last_word and loc.lower().startswith(last_word) and loc not in seen_texts:
            suggestions.append(AutocompleteItem(
                text=loc,
                category="localização",
                icon="map-pin",
                insert_text=loc,
            ))
            seen_texts.add(loc)
    
    # 5. Industry suggestions
    for ind in INDUSTRIES_TAXONOMY:
        if last_word and ind.lower().startswith(last_word) and ind not in seen_texts:
            suggestions.append(AutocompleteItem(
                text=ind,
                category="setor",
                icon="building",
                insert_text=ind,
            ))
            seen_texts.add(ind)
    
    return suggestions[:8]


@router.get("/autocomplete", response_model=AutocompleteResponse)
async def get_autocomplete(
    query: str = Query("", description="Texto atual da busca"),
    cursor: int | None = Query(None, description="Posição do cursor"),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Get predictive autocomplete suggestions as user types.
    Returns contextual suggestions based on query and cursor position.
    """
    items = get_predictive_suggestions(query, cursor)
    
    context_hint = None
    if not query:
        context_hint = "Digite para ver sugestões inteligentes"
    elif len(items) == 0 and len(query) > 3:
        context_hint = "Pressione Enter para buscar"
    
    return AutocompleteResponse(
        items=items,
        context_hint=context_hint,
    )


@router.get("/taxonomy/{category}", response_model=None)
async def get_taxonomy(
    category: str,
    search: str = Query("", description="Filtrar por texto"),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Get taxonomy items for a category."""
    if category == "job_titles":
        items = []
        for key, titles in JOB_TITLES_TAXONOMY.items():
            for title in titles:
                if not search or search.lower() in title.lower():
                    items.append({"text": title, "group": key})
        return {"category": category, "items": items[:30]}
    
    elif category == "skills":
        items = []
        for group, skills in SKILLS_TAXONOMY.items():
            for skill in skills:
                if not search or search.lower() in skill.lower():
                    items.append({"text": skill, "group": group})
        return {"category": category, "items": items[:40]}
    
    elif category == "locations":
        items = [loc for loc in LOCATIONS_TAXONOMY if not search or search.lower() in loc.lower()]
        return {"category": category, "items": items}
    
    elif category == "industries":
        items = [ind for ind in INDUSTRIES_TAXONOMY if not search or search.lower() in ind.lower()]
        return {"category": category, "items": items}
    
    elif category == "experience":
        return {"category": category, "items": EXPERIENCE_LEVELS}
    
    return {"category": category, "items": []}
