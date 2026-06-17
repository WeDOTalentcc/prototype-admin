"""
Semantic Search Service for Advanced Filters Modal

Provides semantic expansion for search terms across different domains:
- Skills/Competências
- Cargos/Títulos (Job Titles)
- Funções/Roles
- Setores/Indústrias
- Áreas de Expertise
- Áreas de Estudo (Fields of Study)
- Empresas (Company competitors)

Architecture:
- Uses Gemini for fast semantic expansion (P95 < 300ms target)
- Redis caching for hot queries (5-10 min TTL)
- Taxonomies for structured domains
- Debounce on frontend (400-500ms)
"""

import hashlib
import json
import os
from enum import Enum, StrEnum

from pydantic import BaseModel

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    redis = None
    REDIS_AVAILABLE = False
import logging

logger = logging.getLogger(__name__)


class SemanticDomain(StrEnum):
    SKILLS = "skills"
    JOB_TITLES = "job_titles"
    ROLES = "roles"
    INDUSTRIES = "industries"
    EXPERTISE = "expertise"
    FIELDS_OF_STUDY = "fields_of_study"
    COMPANIES = "companies"


class SemanticSuggestion(BaseModel):
    term: str
    confidence: float  # 0.0 to 1.0
    is_synonym: bool = False
    is_related: bool = False
    is_broader: bool = False
    is_narrower: bool = False
    canonical_id: str | None = None


class SemanticExpansionResult(BaseModel):
    original_query: str
    domain: SemanticDomain
    suggestions: list[SemanticSuggestion]
    cached: bool = False
    processing_time_ms: int = 0


DOMAIN_PROMPTS = {
    SemanticDomain.SKILLS: """You are a technical skills expert. Given a skill query, provide related skills, synonyms, and technologies that are commonly used together.

Query: "{query}"
Existing skills to exclude: {existing}

Return a JSON array of objects with: term, confidence (0-1), is_synonym, is_related, is_broader, is_narrower.
Focus on:
- Direct synonyms (React = ReactJS = React.js)
- Related technologies (React -> Next.js, Redux, TypeScript)
- Broader categories (Python -> Programming Languages)
- Specific variations (AWS -> AWS Lambda, EC2, S3)

Return max 10 suggestions, ordered by relevance. Only return the JSON array, no explanation.""",

    SemanticDomain.JOB_TITLES: """You are a recruitment expert. Given a job title query, provide equivalent titles, synonyms, and related roles.

Query: "{query}"
Existing titles to exclude: {existing}

Return a JSON array of objects with: term, confidence (0-1), is_synonym, is_related, is_broader, is_narrower.
Focus on:
- Direct equivalents (Backend Developer = Desenvolvedor Backend = Back-End Engineer)
- Seniority variations (Software Engineer -> Senior Software Engineer, Staff Engineer)
- Regional variations (Product Manager = Gerente de Produto)
- Related roles (Full Stack Developer -> Frontend Developer, Backend Developer)

Return max 10 suggestions in Portuguese and English. Only return the JSON array.""",

    SemanticDomain.ROLES: """You are a career advisor. Given a function/role query, provide equivalent roles and related functions.

Query: "{query}"
Existing roles to exclude: {existing}

Return a JSON array of objects with: term, confidence (0-1), is_synonym, is_related, is_broader, is_narrower.
Focus on:
- Synonyms (Product = PM = Product Management)
- Related functions (Engineering -> Development, Architecture)
- Broader areas (Data Science -> Analytics, Machine Learning, AI)

Return max 8 suggestions. Only return the JSON array.""",

    SemanticDomain.INDUSTRIES: """You are an industry analyst. Given a sector/industry query, provide related industries and sub-sectors.

Query: "{query}"
Existing industries to exclude: {existing}

Return a JSON array of objects with: term, confidence (0-1), is_synonym, is_related, is_broader, is_narrower.
Focus on:
- Synonyms (Fintech = Financial Technology = Serviços Financeiros Digitais)
- Sub-sectors (Tech -> SaaS, E-commerce, Fintech, AI)
- Related industries (Fintech -> Banking, Payments, Insurtech)
- Regional terms (Varejo = Retail)

Return max 10 suggestions in Portuguese and English. Only return the JSON array.""",

    SemanticDomain.EXPERTISE: """You are a skills expert. Given an expertise area query, provide related expertise domains.

Query: "{query}"
Existing areas to exclude: {existing}

Return a JSON array of objects with: term, confidence (0-1), is_synonym, is_related, is_broader, is_narrower.
Focus on:
- Synonyms (Machine Learning = ML = Aprendizado de Máquina)
- Related areas (Data Science -> Machine Learning, Analytics, Big Data)
- Specific domains (AI -> NLP, Computer Vision, Deep Learning)

Return max 8 suggestions. Only return the JSON array.""",

    SemanticDomain.FIELDS_OF_STUDY: """You are an academic advisor. Given a field of study query, provide related academic fields and disciplines.

Query: "{query}"
Existing fields to exclude: {existing}

Return a JSON array of objects with: term, confidence (0-1), is_synonym, is_related, is_broader, is_narrower.
Focus on:
- Synonyms (Computer Science = Ciência da Computação = CC)
- Related fields (Computer Science -> Software Engineering, Information Systems)
- Broader areas (Engineering -> Civil, Electrical, Mechanical)
- Interdisciplinary (Data Science -> Statistics, Computer Science, Mathematics)

Return max 8 suggestions in Portuguese and English. Only return the JSON array.""",

    SemanticDomain.COMPANIES: """You are a business analyst. Given a company name, provide its main competitors and companies in the same sector.

Query: "{query}"
Existing companies to exclude: {existing}

Return a JSON array of objects with: term, confidence (0-1), is_synonym (false), is_related (true if same sector).
Focus on:
- Direct competitors (Uber -> 99, Lyft, DiDi)
- Same sector (Nubank -> Inter, C6 Bank, PicPay)
- Similar size/stage companies

Return max 8 suggestions. Only return the JSON array.""",
}

INDUSTRY_TAXONOMY = {
    "Technology": ["Software", "SaaS", "Cloud", "AI/ML", "Cybersecurity", "DevTools"],
    "Fintech": ["Banking", "Payments", "Insurance Tech", "Crypto", "Lending", "Wealth Management"],
    "E-commerce": ["Marketplace", "D2C", "Retail Tech", "Logistics Tech"],
    "Healthcare": ["Healthtech", "Biotech", "Pharma", "Medical Devices", "Digital Health"],
    "Education": ["Edtech", "E-learning", "Corporate Training", "K-12", "Higher Ed"],
    "HR Tech": ["Recruitment", "Talent Management", "Payroll", "Benefits", "People Analytics"],
}

SKILLS_TAXONOMY = {
    "Frontend": ["React", "Vue.js", "Angular", "Next.js", "TypeScript", "JavaScript", "HTML", "CSS", "Tailwind"],
    "Backend": ["Python", "Node.js", "Java", "Go", "Ruby", "C#", "PHP", "Rust"],
    "Database": ["PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch", "DynamoDB"],
    "Cloud": ["AWS", "GCP", "Azure", "Docker", "Kubernetes", "Terraform"],
    "Data": ["SQL", "Python", "Spark", "Airflow", "dbt", "Snowflake", "BigQuery"],
    "AI/ML": ["TensorFlow", "PyTorch", "Scikit-learn", "NLP", "Computer Vision", "LLMs"],
}

JOB_TITLES_TAXONOMY = {
    "gerente": ["Gerente de Projetos", "Gerente de Produto", "Gerente Comercial", "Gerente de Vendas", "Gerente de Operações", "Gerente Financeiro", "Gerente de RH", "Gerente de TI", "Manager", "General Manager"],
    "desenvolvedor": ["Desenvolvedor Backend", "Desenvolvedor Frontend", "Desenvolvedor Full Stack", "Desenvolvedor Mobile", "Software Developer", "Software Engineer", "Programador", "Dev Senior"],
    "developer": ["Backend Developer", "Frontend Developer", "Full Stack Developer", "Software Developer", "Web Developer", "Mobile Developer", "Senior Developer", "Staff Developer"],
    "engineer": ["Software Engineer", "Backend Engineer", "Frontend Engineer", "Data Engineer", "DevOps Engineer", "Site Reliability Engineer", "ML Engineer", "Platform Engineer"],
    "analista": ["Analista de Sistemas", "Analista de Dados", "Analista de Negócios", "Analista de BI", "Analista Financeiro", "Analista de RH", "Analista de Marketing", "Business Analyst"],
    "designer": ["Product Designer", "UX Designer", "UI Designer", "UX/UI Designer", "Graphic Designer", "Visual Designer", "Design Lead", "Head of Design"],
    "product": ["Product Manager", "Product Owner", "Product Designer", "Product Lead", "Head of Product", "VP of Product", "Chief Product Officer", "Gerente de Produto"],
    "data": ["Data Analyst", "Data Scientist", "Data Engineer", "Analytics Engineer", "BI Analyst", "Analista de Dados", "Cientista de Dados", "Head of Data"],
    "marketing": ["Marketing Manager", "Digital Marketing Manager", "Growth Manager", "CMO", "Head of Marketing", "Brand Manager", "Content Manager", "Gerente de Marketing"],
    "vendas": ["Gerente de Vendas", "Sales Manager", "Account Executive", "SDR", "BDR", "Sales Representative", "Head of Sales", "VP of Sales", "Diretor Comercial"],
    "diretor": ["Diretor de TI", "Diretor Comercial", "Diretor Financeiro", "Diretor de RH", "Diretor de Operações", "Diretor Executivo", "Director", "Managing Director"],
    "coordenador": ["Coordenador de Projetos", "Coordenador de TI", "Coordenador de Marketing", "Coordenador de Vendas", "Coordenador de RH", "Coordinator", "Team Lead"],
    "senior": ["Senior Developer", "Senior Engineer", "Senior Analyst", "Senior Designer", "Senior Manager", "Senior Consultant", "Desenvolvedor Senior", "Engenheiro Senior"],
    "lead": ["Tech Lead", "Team Lead", "Engineering Lead", "Product Lead", "Design Lead", "Project Lead", "Development Lead", "Líder Técnico"],
    "head": ["Head of Engineering", "Head of Product", "Head of Design", "Head of Data", "Head of Marketing", "Head of Sales", "Head of HR", "Head of Operations"],
}


class SemanticSearchService:
    def __init__(self):
        self.redis_client: redis.Redis | None = None
        self.cache_ttl = 600  # 10 minutes
        self._init_redis()

    def _init_redis(self):
        if not REDIS_AVAILABLE:
            logger.info("redis not installed, using in-memory fallback")
            return
            
        redis_url = os.environ.get("REDIS_URL")
        if redis_url:
            try:
                self.redis_client = redis.from_url(redis_url)
                self.redis_client.ping()
                logger.info("Redis connected for semantic search caching")
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}, using in-memory cache")
                self.redis_client = None
        else:
            logger.info("No Redis URL, using in-memory fallback")
    
    def _get_cache_key(self, domain: SemanticDomain, query: str, existing: list[str]) -> str:
        content = f"{domain.value}:{query.lower().strip()}:{sorted(existing)}"
        return f"semantic:{hashlib.md5(content.encode()).hexdigest()}"
    
    def _get_from_cache(self, key: str) -> SemanticExpansionResult | None:
        if not self.redis_client:
            return None
        try:
            data = self.redis_client.get(key)
            if data:
                if isinstance(data, bytes):
                    data = data.decode('utf-8')
                result = SemanticExpansionResult.model_validate_json(data)
                result.cached = True
                return result
        except Exception as e:
            logger.warning(f"Cache read error: {e}")
        return None
    
    def _set_cache(self, key: str, result: SemanticExpansionResult):
        if not self.redis_client:
            return
        try:
            self.redis_client.setex(key, self.cache_ttl, result.model_dump_json())
        except Exception as e:
            logger.warning(f"Cache write error: {e}")
    
    def _get_taxonomy_suggestions(
        self, 
        domain: SemanticDomain, 
        query: str, 
        existing: list[str]
    ) -> list[SemanticSuggestion]:
        """Get suggestions from static taxonomies (fast fallback)"""
        suggestions = []
        query_lower = query.lower()
        existing_lower = [e.lower() for e in existing]
        
        taxonomy = {}
        if domain == SemanticDomain.SKILLS:
            taxonomy = SKILLS_TAXONOMY
        elif domain == SemanticDomain.INDUSTRIES:
            taxonomy = INDUSTRY_TAXONOMY
        elif domain == SemanticDomain.JOB_TITLES:
            taxonomy = JOB_TITLES_TAXONOMY
        
        for category, items in taxonomy.items():
            if query_lower in category.lower():
                for item in items:
                    if item.lower() not in existing_lower:
                        suggestions.append(SemanticSuggestion(
                            term=item,
                            confidence=0.8,
                            is_related=True,
                            is_narrower=True
                        ))
            else:
                for item in items:
                    if query_lower in item.lower() and item.lower() not in existing_lower:
                        suggestions.append(SemanticSuggestion(
                            term=category,
                            confidence=0.7,
                            is_related=True,
                            is_broader=True
                        ))
                        for related in items:
                            if related.lower() not in existing_lower and related != item:
                                suggestions.append(SemanticSuggestion(
                                    term=related,
                                    confidence=0.6,
                                    is_related=True
                                ))
                        break
        
        return suggestions[:10]
    
    async def expand_query(
        self,
        domain: SemanticDomain,
        query: str,
        existing: list[str] = [],
        use_cache: bool = True
    ) -> SemanticExpansionResult:
        """
        Expand a search query with semantic suggestions.
        
        Args:
            domain: The type of field being searched
            query: The user's search input
            existing: Already selected items to exclude
            use_cache: Whether to use Redis cache
        
        Returns:
            SemanticExpansionResult with suggestions
        """
        import time
        start_time = time.time()
        
        query = query.strip()
        if not query or len(query) < 2:
            return SemanticExpansionResult(
                original_query=query,
                domain=domain,
                suggestions=[],
                processing_time_ms=0
            )
        
        cache_key = self._get_cache_key(domain, query, existing)
        if use_cache:
            cached = self._get_from_cache(cache_key)
            if cached:
                cached.processing_time_ms = int((time.time() - start_time) * 1000)
                return cached
        
        suggestions = []
        
        try:
            from app.shared.providers.llm_factory import get_provider_for_tenant

            prompt = DOMAIN_PROMPTS.get(domain, DOMAIN_PROMPTS[SemanticDomain.SKILLS])
            formatted_prompt = prompt.format(
                query=query,
                existing=json.dumps(existing) if existing else "[]"
            )

            container = get_provider_for_tenant()
            text = await container.generate_with_fallback(formatted_prompt, agent_type="SemanticSearchAgent")
            text = text.strip()
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]

            parsed = json.loads(text)
            for item in parsed:
                if isinstance(item, dict):
                    suggestions.append(SemanticSuggestion(
                        term=item.get("term", ""),
                        confidence=float(item.get("confidence", 0.5)),
                        is_synonym=item.get("is_synonym", False),
                        is_related=item.get("is_related", False),
                        is_broader=item.get("is_broader", False),
                        is_narrower=item.get("is_narrower", False),
                    ))
        except Exception as e:
            logger.warning(f"LLM expansion failed: {e}, using taxonomy fallback")
            suggestions = self._get_taxonomy_suggestions(domain, query, existing)
        
        existing_lower = [e.lower() for e in existing]
        suggestions = [
            s for s in suggestions 
            if s.term and s.term.lower() not in existing_lower
        ]
        
        suggestions = sorted(suggestions, key=lambda x: x.confidence, reverse=True)[:10]
        
        result = SemanticExpansionResult(
            original_query=query,
            domain=domain,
            suggestions=suggestions,
            cached=False,
            processing_time_ms=int((time.time() - start_time) * 1000)
        )
        
        if use_cache and suggestions:
            self._set_cache(cache_key, result)
        
        return result
    
    async def expand_skills(self, query: str, existing: list[str] = []) -> SemanticExpansionResult:
        return await self.expand_query(SemanticDomain.SKILLS, query, existing)
    
    async def expand_job_titles(self, query: str, existing: list[str] = []) -> SemanticExpansionResult:
        return await self.expand_query(SemanticDomain.JOB_TITLES, query, existing)
    
    async def expand_roles(self, query: str, existing: list[str] = []) -> SemanticExpansionResult:
        return await self.expand_query(SemanticDomain.ROLES, query, existing)
    
    async def expand_industries(self, query: str, existing: list[str] = []) -> SemanticExpansionResult:
        return await self.expand_query(SemanticDomain.INDUSTRIES, query, existing)
    
    async def expand_expertise(self, query: str, existing: list[str] = []) -> SemanticExpansionResult:
        return await self.expand_query(SemanticDomain.EXPERTISE, query, existing)
    
    async def expand_fields_of_study(self, query: str, existing: list[str] = []) -> SemanticExpansionResult:
        return await self.expand_query(SemanticDomain.FIELDS_OF_STUDY, query, existing)
    
    async def expand_company_competitors(self, query: str, existing: list[str] = []) -> SemanticExpansionResult:
        return await self.expand_query(SemanticDomain.COMPANIES, query, existing)


semantic_search_service = SemanticSearchService()
