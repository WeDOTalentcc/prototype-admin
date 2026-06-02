"""
Pearch AI data models for candidate search (API v2).
Based on https://apidocs.pearch.ai/reference/post_v2-search
"""
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class SearchType(str, Enum):
    """Tipos de busca disponíveis."""
    FAST = "fast"  # 1 crédito/candidato


class MatchLevel(str, Enum):
    """Níveis de match nos insights."""
    EXCEEDS = "Exceeds Expectations"
    MEETS = "Meets Expectations"
    PARTIAL = "Partially Meets"
    DOES_NOT_MEET = "Does Not Meet"


class QueryInsight(BaseModel):
    """Insight individual para um requisito da query."""
    subquery: Optional[str] = None
    match_level: Optional[str] = None
    priority: Optional[str] = None
    short_rationale: Optional[str] = None
    short_quotes: List[str] = Field(default_factory=list)


class CandidateInsights(BaseModel):
    """Insights detalhados sobre match do candidato."""
    overall_summary: Optional[str] = None
    query_insights: List[QueryInsight] = Field(default_factory=list)


class CompanyInfo(BaseModel):
    """Informações detalhadas da empresa."""
    name: Optional[str] = None
    domain: Optional[str] = None
    website: Optional[str] = None
    linkedin_url: Optional[str] = None
    linkedin_slug: Optional[str] = None
    short_address: Optional[str] = None
    locations: List[str] = Field(default_factory=list)
    type: Optional[str] = None
    description: Optional[str] = None
    industries: List[str] = Field(default_factory=list)
    specialties: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    technologies: List[str] = Field(default_factory=list)
    founded_in: Optional[int] = None
    num_employees: Optional[int] = None
    num_employees_range: Optional[str] = None
    annual_revenue: Optional[float] = None
    followers_count: Optional[int] = None
    is_startup: Optional[bool] = None
    is_hiring: Optional[bool] = None
    icon: Optional[str] = None
    funding_stage: Optional[str] = None
    hq_city: Optional[str] = None
    hq_state: Optional[str] = None
    hq_country: Optional[str] = None


class CompanyRole(BaseModel):
    """Papel/cargo em uma empresa."""
    sequenceNo: Optional[int] = None
    company: Optional[str] = None
    company_domain: Optional[str] = None
    title: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    duration_years: Optional[float] = None
    age_years: Optional[float] = None
    description: Optional[str] = None
    location: Optional[str] = None


class CandidateExperience(BaseModel):
    """Experiência profissional completa."""
    company_info: Optional[CompanyInfo] = None
    company_roles: List[CompanyRole] = Field(default_factory=list)
    
    # Campos legados para compatibilidade
    company: Optional[str] = None
    title: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    duration: Optional[str] = None
    duration_years: Optional[float] = None
    description: Optional[str] = None
    location: Optional[str] = None
    
    # New filter fields
    funding_stage: Optional[str] = None
    company_tags: List[str] = Field(default_factory=list)
    company_hq_city: Optional[str] = None
    company_hq_state: Optional[str] = None
    company_hq_country: Optional[str] = None
    company_size: Optional[str] = None
    industries: List[str] = Field(default_factory=list)


class CandidateEducation(BaseModel):
    """Formação educacional."""
    school: Optional[str] = None
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    
    # New filter fields for institution details
    institution_city: Optional[str] = None
    institution_state: Optional[str] = None
    institution_country: Optional[str] = None
    institution_ranking: Optional[int] = None
    institution_tier: Optional[str] = None


class Language(BaseModel):
    """Idioma com proficiência."""
    language: Optional[str] = None
    proficiency: Optional[str] = None  # A1, A2, B1, B2, C1, C2, Native


class CandidateProfile(BaseModel):
    """Perfil completo do candidato da Pearch AI v2."""
    # Identificadores
    docid: Optional[str] = None
    linkedin_slug: Optional[str] = None
    
    # Informações básicas
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    name: Optional[str] = None  # Campo calculado (first + last)
    picture_url: Optional[str] = None
    
    # Posição atual
    title: Optional[str] = None
    headline: Optional[str] = None
    current_title: Optional[str] = None
    current_company: Optional[str] = None
    summary: Optional[str] = None
    
    # Localização e dados demográficos
    location: Optional[str] = None
    gender: Optional[str] = None
    estimated_age: Optional[int] = None
    
    # Status profissional
    is_decision_maker: Optional[int] = None
    is_opentowork: Optional[bool] = None
    is_hiring: Optional[bool] = None
    is_top_universities: Optional[bool] = None
    
    # Experiência
    total_experience_years: Optional[float] = None
    experiences: List[CandidateExperience] = Field(default_factory=list)
    
    # Educação
    education: List[CandidateEducation] = Field(default_factory=list)
    
    # Skills e expertise
    skills: List[str] = Field(default_factory=list)
    expertise: List[str] = Field(default_factory=list)
    
    # Idiomas
    languages: List[Language] = Field(default_factory=list)
    inferred_languages: List[Language] = Field(default_factory=list)
    
    # Contato
    has_emails: Optional[bool] = None
    emails: List[str] = Field(default_factory=list)
    best_personal_email: Optional[str] = None
    best_business_email: Optional[str] = None
    personal_emails: List[str] = Field(default_factory=list)
    business_emails: List[str] = Field(default_factory=list)
    
    has_phone_numbers: Optional[bool] = None
    phone_numbers: List[str] = Field(default_factory=list)
    phone_types: List[str] = Field(default_factory=list)
    
    # Redes sociais
    linkedin_url: Optional[str] = None
    followers_count: Optional[int] = None
    connections_count: Optional[int] = None
    
    # Score e match
    score: Optional[int] = None  # 0-4 do Pearch
    match_score: Optional[float] = None  # Convertido para 0-100
    match_reasoning: Optional[str] = None
    
    # Insights detalhados
    insights: Optional[CandidateInsights] = None
    
    # Outreach
    outreach_message: Optional[str] = None
    
    # Discovered flag - True if from staging table (ExternalCandidateProfile)
    is_discovered: bool = False
    
    def get_full_name(self) -> str:
        """Retorna nome completo."""
        parts = [self.first_name, self.middle_name, self.last_name]
        return " ".join(p for p in parts if p) or self.name or "Candidato"
    
    def get_linkedin_url(self) -> Optional[str]:
        """Retorna URL do LinkedIn."""
        if self.linkedin_url:
            return self.linkedin_url
        if self.linkedin_slug:
            return f"https://linkedin.com/in/{self.linkedin_slug}"
        return None
    
    def get_score_percentage(self) -> float:
        """Converte score 0-4 para percentual 0-100."""
        if self.match_score is not None:
            return self.match_score
        if self.score is not None:
            return (self.score / 4) * 100
        return 0


class PearchSearchResult(BaseModel):
    """Resultado individual da busca."""
    docid: str
    score: Optional[int] = None
    insights: Optional[CandidateInsights] = None
    profile: CandidateProfile
    outreach_message: Optional[str] = None


class PearchSearchRequest(BaseModel):
    """Request para busca de candidatos v2."""
    query: str = Field(..., description="Query em linguagem natural")
    thread_id: Optional[str] = Field(None, description="ID do thread para refinamento")
    type: SearchType = Field(SearchType.FAST, description="Tipo de busca: fast ou pro")
    
    # Opções de qualidade
    insights: bool = Field(True, description="Incluir insights detalhados (+1 crédito)")
    high_freshness: bool = Field(False, description="Dados em tempo real (+2 créditos)")
    profile_scoring: bool = Field(True, description="Scoring e reranking (+1 crédito)")
    
    # Filtros
    custom_filters: Optional[Dict[str, Any]] = Field(None, description="Filtros customizados")
    strict_filters: bool = Field(False, description="Filtros mais rigorosos")
    
    # Contato
    require_emails: bool = Field(False, description="Apenas perfis com email (+1 crédito)")
    show_emails: bool = Field(False, description="Mostrar emails (+2 créditos)")
    require_phone_numbers: bool = Field(False, description="Apenas perfis com telefone (+1 crédito)")
    require_phones_or_emails: bool = Field(False, description="Perfis com email OU telefone (+1 crédito)")
    show_phone_numbers: bool = Field(False, description="Mostrar telefones (+14 créditos)")
    
    # Paginação
    limit: int = Field(10, ge=1, le=1000, description="Número de resultados")
    docid_blacklist: List[str] = Field(default_factory=list, description="IDs a excluir")


class PearchSearchResponse(BaseModel):
    """Response da busca de candidatos v2."""
    uuid: str
    thread_id: str  # Para refinamento de busca
    query: str
    user: Optional[str] = None
    created_at: Optional[float] = None
    duration: Optional[float] = None
    status: str
    
    total_estimate: int
    total_estimate_is_lower_bound: bool = False
    credits_remaining: Optional[int] = None
    
    search_results: List[PearchSearchResult] = Field(default_factory=list)
    
    # Campos legados para compatibilidade
    total_results: Optional[int] = None
    candidates: List[CandidateProfile] = Field(default_factory=list)
    search_time_seconds: Optional[float] = None
    credits_used: Optional[int] = None
    
    def get_candidates(self) -> List[CandidateProfile]:
        """Retorna lista de candidatos (compatibilidade)."""
        if self.search_results:
            return [r.profile for r in self.search_results]
        return self.candidates


class HybridSearchRequest(BaseModel):
    """Request para busca híbrida (banco local + Pearch)."""
    query: str = Field(..., description="Query em linguagem natural")
    thread_id: Optional[str] = Field(None, description="Thread para refinamento")
    
    # SearchSpec - metadados estruturados do LLM
    search_spec: Optional[Dict[str, Any]] = Field(None, description="Metadados estruturados extraídos pelo LLM")
    
    # Configurações de busca
    search_local_first: bool = Field(True, description="Buscar primeiro no banco local")
    include_pearch: bool = Field(True, description="Complementar com Pearch se necessário")
    pearch_type: SearchType = Field(SearchType.FAST, description="Tipo de busca Pearch")
    
    # Limites
    local_limit: int = Field(20, ge=1, le=100, description="Limite de resultados locais")
    pearch_limit: int = Field(15, ge=0, le=100, description="Limite de resultados Pearch")
    
    # Opções Pearch
    require_emails: bool = Field(False, description="Apenas perfis com email (+1 crédito)")
    require_phone_numbers: bool = Field(False, description="Apenas perfis com telefone (+1 crédito)")
    show_emails: bool = Field(False, description="Mostrar emails (+2 créditos)")
    show_phone_numbers: bool = Field(False, description="Mostrar telefones (+14 créditos)")
    
    # Filtros
    job_vacancy_id: Optional[int] = Field(None, description="ID da vaga para contexto")
    exclude_candidate_ids: List[str] = Field(default_factory=list, description="IDs a excluir")
    
    # Include discovered candidates from staging table
    include_discovered: bool = Field(True, description="Include discovered candidates from staging table")
    
    def get_search_spec(self) -> Optional["SearchSpec"]:
        """Converte dict search_spec para objeto SearchSpec."""
        if self.search_spec:
            return SearchSpec(**self.search_spec)
        return None


class HybridSearchResponse(BaseModel):
    """Response da busca híbrida."""
    query: str
    thread_id: Optional[str] = None
    
    # Resultados
    local_candidates: List[CandidateProfile] = Field(default_factory=list)
    pearch_candidates: List[CandidateProfile] = Field(default_factory=list)
    
    # Metadados
    local_count: int = 0
    pearch_count: int = 0
    total_count: int = 0
    
    # Custos
    pearch_credits_used: Optional[int] = None
    pearch_credits_remaining: Optional[int] = None
    
    # Status
    local_search_time: Optional[float] = None
    pearch_search_time: Optional[float] = None
    status: str = "completed"
    
    # Mensagem de aviso (custo de créditos, etc.)
    warning_message: Optional[str] = None

    # Task #1219 — diagnósticos do loop de completude "Híbrida com email".
    # filtered_no_contact: candidatos descartados por NÃO terem email (modo
    # require_emails). sources_exhausted: True quando as fontes (local + Pearch)
    # acabaram antes de atingir o alvo. enrichment_attempted: nº de candidatos
    # para os quais houve tentativa de enriquecimento de contato.
    filtered_no_contact: int = 0
    sources_exhausted: bool = False
    enrichment_attempted: int = 0

    def get_all_candidates(self) -> List[CandidateProfile]:
        """Retorna todos os candidatos combinados."""
        return self.local_candidates + self.pearch_candidates


class CreditEstimate(BaseModel):
    """Estimativa de custo em créditos."""
    base_cost: int  # Custo base (fast=1, pro=5)
    insights_cost: int = 0
    email_cost: int = 0
    phone_cost: int = 0
    freshness_cost: int = 0
    total_per_candidate: int = 0
    estimated_candidates: int = 0
    total_estimated: int = 0
    
    def calculate_total(self, num_candidates: int) -> int:
        """Calcula custo total para N candidatos."""
        per_candidate = (
            self.base_cost + 
            self.insights_cost + 
            self.email_cost + 
            self.phone_cost + 
            self.freshness_cost
        )
        return per_candidate * num_candidates


class SearchConfirmation(BaseModel):
    """Confirmação antes de executar busca Pearch."""
    query: str
    estimated_results: int
    credit_estimate: CreditEstimate
    requires_confirmation: bool = True
    confirmation_message: str
    search_request: PearchSearchRequest


class SearchSpec(BaseModel):
    """
    SearchSpec canônico - metadados estruturados extraídos pelo LLM.
    Usado para converter em filtros locais e parâmetros avançados da Pearch.
    """
    location: Optional[str] = Field(None, description="Localização: cidade, estado ou país")
    location_city: Optional[str] = Field(None, description="Cidade específica")
    location_state: Optional[str] = Field(None, description="Estado/região")
    location_country: Optional[str] = Field(None, description="País")
    
    job_title: Optional[str] = Field(None, description="Cargo/título do profissional")
    seniority: Optional[str] = Field(None, description="Nível de senioridade: junior, pleno, senior, lead, manager, director, c-level")
    
    years_experience: Optional[str] = Field(None, description="Anos de experiência (ex: '5+', '3-5', '10+')")
    years_experience_min: Optional[int] = Field(None, description="Anos mínimos de experiência")
    years_experience_max: Optional[int] = Field(None, description="Anos máximos de experiência")
    
    skills: List[str] = Field(default_factory=list, description="Skills técnicas e comportamentais")
    required_skills: List[str] = Field(default_factory=list, description="Skills obrigatórias")
    preferred_skills: List[str] = Field(default_factory=list, description="Skills desejáveis")
    
    industry: Optional[str] = Field(None, description="Setor/indústria")
    industries: List[str] = Field(default_factory=list, description="Lista de setores aceitáveis")
    
    company: Optional[str] = Field(None, description="Empresa atual ou anterior")
    companies: List[str] = Field(default_factory=list, description="Lista de empresas de interesse")
    exclude_companies: List[str] = Field(default_factory=list, description="Empresas a excluir")
    
    salary_min: Optional[float] = Field(None, description="Salário mínimo pretendido")
    salary_max: Optional[float] = Field(None, description="Salário máximo pretendido")
    salary_currency: str = Field("BRL", description="Moeda do salário")
    
    work_model: Optional[str] = Field(None, description="Modelo de trabalho: remote, hybrid, onsite")
    contract_type: Optional[str] = Field(None, description="Tipo de contrato: CLT, PJ, freelance")
    
    languages: List[str] = Field(default_factory=list, description="Idiomas requeridos")
    education_level: Optional[str] = Field(None, description="Nível de formação: graduação, pós, mestrado, doutorado")
    
    is_open_to_work: Optional[bool] = Field(None, description="Apenas candidatos abertos a oportunidades")
    has_email: Optional[bool] = Field(None, description="Deve ter email de contato")
    has_phone: Optional[bool] = Field(None, description="Deve ter telefone de contato")
    
    # New filter fields for experiences table
    funding_stages: List[str] = Field(default_factory=list, description="Funding stages to filter by (seed, series_a, series_b, etc)")
    funding_stage: Optional[str] = Field(None, description="Single funding stage filter")
    company_hq_countries: List[str] = Field(default_factory=list, description="Company HQ countries to filter by")
    company_hq_country: Optional[str] = Field(None, description="Single company HQ country filter")
    company_tags: List[str] = Field(default_factory=list, description="Company tags/keywords to filter by")
    
    # New filter fields for education table
    institution_tiers: List[str] = Field(default_factory=list, description="Institution tiers to filter by (tier1, tier2, tier3)")
    institution_tier: Optional[str] = Field(None, description="Single institution tier filter")
    institution_countries: List[str] = Field(default_factory=list, description="Institution countries to filter by")
    institution_country: Optional[str] = Field(None, description="Single institution country filter")
    institution_ranking_max: Optional[int] = Field(None, description="Maximum institution ranking (lower is better)")
    
    # New filter fields for candidates table
    timezones: List[str] = Field(default_factory=list, description="Timezones to filter by")
    timezone: Optional[str] = Field(None, description="Single timezone filter (exact or pattern match)")
    
    def to_pearch_custom_filters(self) -> Dict[str, Any]:
        """Converte SearchSpec para custom_filters da Pearch API."""
        filters: Dict[str, Any] = {}
        
        if self.location:
            filters["location"] = self.location
        if self.job_title:
            filters["title"] = self.job_title
        if self.seniority:
            filters["seniority"] = self.seniority
        if self.years_experience_min:
            filters["min_years_experience"] = self.years_experience_min
        if self.industries:
            filters["industries"] = self.industries
        elif self.industry:
            filters["industries"] = [self.industry]
        if self.companies:
            filters["companies"] = self.companies
        if self.exclude_companies:
            filters["exclude_companies"] = self.exclude_companies
        if self.skills or self.required_skills:
            filters["skills"] = list(set(self.skills + self.required_skills))
        if self.languages:
            filters["languages"] = self.languages
        
        return filters if filters else {}
    
    def should_use_strict_filters(self) -> bool:
        """Determina se deve usar filtros rigorosos baseado na especificidade."""
        specificity_count = sum([
            bool(self.location),
            bool(self.seniority),
            bool(self.years_experience_min),
            len(self.required_skills) > 0,
            bool(self.industry or self.industries)
        ])
        return specificity_count >= 3
