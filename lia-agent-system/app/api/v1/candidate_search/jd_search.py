"""
Job description search, refine, local search, and parse-query routes.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ._shared import (
    CandidateSearchResultDTO,
    HybridSearchRequest,
    PearchService,
    SearchResponseDTO,
    SearchType,
    enrich_and_filter_candidates,
    get_db,
    get_pearch_service,
)

router = APIRouter()

class JobDescriptionSearchRequest(BaseModel):
    """Request para busca por job description."""
    job_description: str = Field(..., min_length=50, description="Descrição completa da vaga")
    location: str | None = Field(None, description="Localização preferida")
    limit: int = Field(20, ge=1, le=50)
    search_pearch: bool = Field(True, description="Buscar também na Pearch AI")
    pearch_type: str = Field("fast", description="Tipo de busca (sempre fast)")


class ExtractedCriteria(BaseModel):
    """Critérios extraídos da job description."""
    job_title: str | None = None
    seniority: str | None = None
    skills: list[str] = Field(default_factory=list)
    experience_years: int | None = None
    location: str | None = None
    languages: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)


class JobDescriptionSearchResponse(BaseModel):
    """Response da busca por job description."""
    extracted_criteria: ExtractedCriteria
    query_generated: str
    candidates: list[CandidateSearchResultDTO] = Field(default_factory=list)
    local_count: int = 0
    pearch_count: int = 0
    total_count: int = 0
    credits_remaining: int | None = None
    search_time_seconds: float | None = None


@router.post("/by-job-description", response_model=JobDescriptionSearchResponse)
async def search_by_job_description(
    request: JobDescriptionSearchRequest,
    db: AsyncSession = Depends(get_db),
    pearch_svc: PearchService = Depends(get_pearch_service),
):
    """
    Busca candidatos a partir de uma descrição de vaga completa.
    
    Extrai automaticamente critérios (skills, experiência, localização) 
    e gera uma query otimizada para encontrar candidatos compatíveis.
    """
    import re
    
    jd_lower = request.job_description.lower()
    extracted = ExtractedCriteria()
    
    job_titles = [
        'desenvolvedor', 'developer', 'engenheiro', 'engineer', 'analista', 'analyst',
        'gerente', 'manager', 'coordenador', 'coordinator', 'designer', 'architect',
        'data scientist', 'cientista de dados', 'devops', 'sre', 'qa', 'tester',
        'product manager', 'scrum master', 'tech lead', 'líder técnico'
    ]
    for title in job_titles:
        if title in jd_lower:
            extracted.job_title = title.title()
            break
    
    seniority_patterns = {
        r'\b(júnior|junior|jr)\b': 'Junior',
        r'\b(pleno|mid|mid-level)\b': 'Pleno',
        r'\b(sênior|senior|sr)\b': 'Senior',
        r'\b(staff|principal)\b': 'Staff',
        r'\b(lead|líder)\b': 'Lead'
    }
    for pattern, level in seniority_patterns.items():
        if re.search(pattern, jd_lower):
            extracted.seniority = level
            break
    
    skills_list = [
        'python', 'java', 'javascript', 'typescript', 'react', 'angular', 'vue',
        'node', 'nodejs', 'django', 'flask', 'fastapi', 'spring', 'aws', 'gcp',
        'azure', 'docker', 'kubernetes', 'terraform', 'sql', 'postgresql', 'mongodb',
        'redis', 'kafka', 'rabbitmq', 'graphql', 'rest', 'api', 'git', 'ci/cd',
        'machine learning', 'ml', 'deep learning', 'tensorflow', 'pytorch',
        'pandas', 'numpy', 'spark', 'hadoop', 'airflow', 'dbt', 'tableau', 'power bi',
        'figma', 'sketch', 'adobe xd', 'jira', 'confluence', 'scrum', 'agile'
    ]
    found_skills = [s for s in skills_list if s in jd_lower]
    extracted.skills = list(set(found_skills))[:10]
    
    exp_match = re.search(r'(\d+)\s*(?:\+)?\s*(?:anos?|years?)', jd_lower)
    if exp_match:
        extracted.experience_years = int(exp_match.group(1))
    
    languages = ['inglês', 'english', 'espanhol', 'spanish', 'português', 'french', 'francês']
    found_languages = [l for l in languages if l in jd_lower]
    extracted.languages = list(set(found_languages))
    
    if request.location:
        extracted.location = request.location
    else:
        locations = ['são paulo', 'sp', 'rio de janeiro', 'rj', 'belo horizonte', 'curitiba', 
                    'porto alegre', 'brasília', 'remoto', 'remote', 'híbrido', 'hybrid']
        for loc in locations:
            if loc in jd_lower:
                extracted.location = loc.title()
                break
    
    query_parts = []
    if extracted.job_title:
        query_parts.append(extracted.job_title)
    if extracted.seniority:
        query_parts.append(extracted.seniority)
    if extracted.skills:
        query_parts.append(" ".join(extracted.skills[:5]))
    if extracted.experience_years:
        query_parts.append(f"{extracted.experience_years}+ anos")
    if extracted.location:
        query_parts.append(f"em {extracted.location}")
    
    generated_query = " ".join(query_parts) if query_parts else "profissional"
    
    try:
        hybrid_request = HybridSearchRequest(
            query=generated_query,
            search_local_first=True,
            include_pearch=request.search_pearch,
            pearch_type=SearchType.FAST,
            local_limit=request.limit,
            pearch_limit=request.limit
        )
        
        result = await pearch_svc.hybrid_search(db, hybrid_request)
        
        candidates = []
        for profile in result.local_candidates:
            candidates.append(CandidateSearchResultDTO.from_profile(profile, "local"))
        for profile in result.pearch_candidates:
            candidates.append(CandidateSearchResultDTO.from_profile(profile, "pearch"))
        
        candidates = await enrich_and_filter_candidates(db, candidates)
        
        return JobDescriptionSearchResponse(
            extracted_criteria=extracted,
            query_generated=generated_query,
            candidates=candidates,
            local_count=result.local_count,
            pearch_count=result.pearch_count,
            total_count=result.total_count,
            credits_remaining=result.pearch_credits_remaining,
            search_time_seconds=(result.local_search_time or 0) + (result.pearch_search_time or 0)
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Job description search failed: {str(e)}")


@router.post("/candidates/refine", response_model=SearchResponseDTO)
async def refine_search(
    thread_id: str = Query(..., description="Thread ID da busca anterior"),
    additional_query: str = Query(..., description="Critérios adicionais"),
    limit: int | None = Query(None, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
,
    pearch_svc: PearchService = Depends(get_pearch_service),
):
    """
    Refina uma busca existente usando o thread_id.
    
    Use para adicionar critérios ou pedir mais resultados sem custo completo.
    """
    try:
        result = await pearch_svc.refine_search(
            thread_id=thread_id,
            additional_query=additional_query,
            limit=limit
        )
        
        candidates = [
            CandidateSearchResultDTO.from_profile(profile, "pearch")
            for profile in result.get_candidates()
        ]
        
        return SearchResponseDTO(
            query=additional_query,
            thread_id=result.thread_id,
            candidates=candidates,
            pearch_count=len(candidates),
            total_count=len(candidates),
            credits_remaining=result.credits_remaining,
            search_time_seconds=result.search_time_seconds
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Refine failed: {str(e)}")


@router.get("/candidates/local", response_model=SearchResponseDTO)
async def search_local_only(
    query: str = Query(..., description="Query de busca"),
    limit: int = Query(20, ge=1, le=100),
    industries: str | None = Query(None, description="Setores separados por vírgula (ex: Tecnologia,Fintech)"),
    require_email: bool = Query(False, description="Apenas candidatos com email"),
    require_phone: bool = Query(False, description="Apenas candidatos com telefone"),
    db: AsyncSession = Depends(get_db)
,
    pearch_svc: PearchService = Depends(get_pearch_service),
):
    """
    Busca APENAS no banco de dados local (sem custo de créditos).
    
    Útil para verificar se já temos candidatos antes de usar Pearch.
    Suporta filtros por setores/indústrias e disponibilidade de contato.
    """
    try:
        # Parse industries string para lista
        industries_list = None
        if industries:
            industries_list = [ind.strip() for ind in industries.split(',') if ind.strip()]
        
        profiles, count = await pearch_svc.search_local_candidates(
            db=db,
            query=query,
            limit=limit,
            industries=industries_list,
            require_email=require_email,
            require_phone=require_phone
        )
        
        candidates = [
            CandidateSearchResultDTO.from_profile(profile, "local")
            for profile in profiles
        ]
        
        candidates = await enrich_and_filter_candidates(db, candidates)
        
        return SearchResponseDTO(
            query=query,
            candidates=candidates,
            local_count=len(candidates),
            total_count=len(candidates)
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Local search failed: {str(e)}")


class ParseQueryRequest(BaseModel):
    """Request para parsing de query em linguagem natural."""
    query: str = Field(..., min_length=1, max_length=500)


class ParsedEntities(BaseModel):
    """Entidades extraídas da query."""
    location: str | None = None
    job_title: str | None = None
    years_experience: str | None = None
    industry: str | None = None
    skills: list[str] = Field(default_factory=list)
    seniority: str | None = None
    company: str | None = None


class ParseQueryResponse(BaseModel):
    """Response do parsing de query."""
    query: str
    entities: ParsedEntities
    confidence: float = 0.0
    suggestions: list[str] = Field(default_factory=list)


@router.post("/parse-query", response_model=ParseQueryResponse)
async def parse_search_query(request: ParseQueryRequest):
    """
    Extrai entidades de uma query de busca em linguagem natural.
    
    Usado para preencher tags dinâmicas no SmartSearchInput.
    Análise rápida sem custo de créditos.
    """
    import re
    
    query = request.query.lower().strip()
    entities = ParsedEntities()
    confidence = 0.0
    suggestions = []
    
    # ============================================
    # 1. LOCATION - Cidades, Estados, Países, Modelo de Trabalho
    # ============================================
    brazilian_cities = [
        'são paulo', 'sp', 'rio de janeiro', 'rj', 'belo horizonte', 'bh', 
        'brasília', 'df', 'curitiba', 'porto alegre', 'poa', 'salvador', 
        'fortaleza', 'recife', 'manaus', 'belém', 'goiânia', 'guarulhos',
        'campinas', 'são bernardo', 'santo andré', 'osasco', 'sorocaba',
        'ribeirão preto', 'uberlândia', 'contagem', 'niterói', 'florianópolis',
        'joinville', 'londrina', 'juiz de fora', 'santos', 'são josé dos campos',
        'natal', 'joão pessoa', 'maceió', 'teresina', 'campo grande', 'cuiabá',
        'aracaju', 'vitória', 'são luís', 'vila velha', 'feira de santana'
    ]
    
    brazilian_states = [
        'minas gerais', 'mg', 'rio grande do sul', 'rs', 'paraná', 'pr',
        'santa catarina', 'sc', 'bahia', 'ba', 'pernambuco', 'pe', 'ceará', 'ce',
        'goiás', 'go', 'espírito santo', 'es', 'pará', 'pa', 'amazonas', 'am',
        'maranhão', 'ma', 'mato grosso', 'mt', 'mato grosso do sul', 'ms',
        'rio grande do norte', 'rn', 'paraíba', 'pb', 'alagoas', 'al',
        'piauí', 'pi', 'sergipe', 'se', 'tocantins', 'to', 'acre', 'ac',
        'amapá', 'ap', 'rondônia', 'ro', 'roraima', 'rr'
    ]
    
    work_models = ['remote', 'remoto', 'híbrido', 'hibrido', 'presencial', 'home office', 'anywhere', 'global']
    countries_regions = ['brasil', 'brazil', 'usa', 'eua', 'estados unidos', 'europa', 'latam', 'américa latina', 'portugal', 'argentina', 'chile', 'méxico', 'canada', 'uk', 'reino unido', 'alemanha', 'espanha']
    
    all_locations = brazilian_cities + brazilian_states + work_models + countries_regions
    location_pattern = r'\b(' + '|'.join(re.escape(loc) for loc in all_locations) + r')\b'
    
    match = re.search(location_pattern, query, re.IGNORECASE)
    if match:
        entities.location = match.group(0).strip().title()
        confidence += 0.2
    else:
        em_pattern = r'\bem\s+([a-záàâãéèêíïóôõöúçñ\s]{3,25})(?:\s+com|\s+que|\s+de|\s+e\s|,|$)'
        match = re.search(em_pattern, query, re.IGNORECASE)
        if match:
            potential_loc = match.group(1).strip()
            if len(potential_loc) >= 3 and potential_loc not in ['experiência', 'experiencia', 'empresa', 'startup']:
                entities.location = potential_loc.title()
                confidence += 0.15
    
    # ============================================
    # 2. JOB TITLE - Cargos e Funções
    # ============================================
    job_titles = [
        # Product & Management
        'product manager', 'product managers', 'gerente de produto', 'pm', 'product owner', 'po',
        'project manager', 'gerente de projeto', 'program manager', 'scrum master', 'agile coach',
        'tech lead', 'technical lead', 'líder técnico', 'engineering manager', 'gerente de engenharia',
        'cto', 'cio', 'vp engineering', 'head of engineering', 'diretor de tecnologia',
        
        # Development
        'desenvolvedor', 'desenvolvedora', 'developer', 'programador', 'programadora',
        'engenheiro de software', 'engenheira de software', 'software engineer',
        'fullstack', 'full-stack', 'full stack', 'frontend', 'front-end', 'front end',
        'backend', 'back-end', 'back end', 'mobile developer', 'desenvolvedor mobile',
        'ios developer', 'android developer', 'react developer', 'java developer',
        'python developer', 'node developer', 'golang developer', '.net developer',
        
        # Data & AI
        'data scientist', 'cientista de dados', 'data engineer', 'engenheiro de dados',
        'data analyst', 'analista de dados', 'ml engineer', 'machine learning engineer',
        'ai engineer', 'engenheiro de ia', 'bi analyst', 'analista de bi',
        'data architect', 'arquiteto de dados',
        
        # DevOps & Infrastructure
        'devops', 'devops engineer', 'sre', 'site reliability engineer',
        'cloud engineer', 'engenheiro de cloud', 'platform engineer',
        'infrastructure engineer', 'network engineer', 'security engineer',
        'devsecops', 'cloud architect', 'arquiteto de soluções', 'solutions architect',
        
        # QA & Testing
        'qa', 'qa engineer', 'quality assurance', 'tester', 'test engineer',
        'automation engineer', 'sdet', 'qa analyst', 'analista de qualidade',
        
        # Design
        'designer', 'ux designer', 'ui designer', 'ux/ui', 'product designer',
        'visual designer', 'graphic designer', 'motion designer', 'ux researcher',
        
        # Other Tech
        'arquiteto', 'arquiteta', 'architect', 'analista', 'analyst', 'consultor', 'consultant',
        'especialista', 'specialist', 'coordenador', 'coordenadora', 'supervisor', 'supervisora',
        'gerente', 'manager', 'diretor', 'diretora', 'director', 'head', 'chief',
        
        # Support & Operations
        'support engineer', 'suporte técnico', 'help desk', 'dba', 'database administrator',
        'system administrator', 'sysadmin', 'administrador de sistemas'
    ]
    
    job_pattern = r'\b(' + '|'.join(re.escape(title) for title in job_titles) + r')\b'
    match = re.search(job_pattern, query, re.IGNORECASE)
    if match:
        entities.job_title = match.group(0).strip().title()
        confidence += 0.2
    
    # ============================================
    # 3. EXPERIENCE - Anos de experiência e senioridade
    # ============================================
    exp_patterns = [
        (r'(\d+)\s*\+?\s*(?:anos?|years?|yrs?)\s*(?:de\s+)?(?:experiência|experience|exp)?', 'years'),
        (r'(?:experiência|experience|exp)\s*(?:de\s+)?(\d+)\s*\+?\s*(?:anos?|years?)?', 'years'),
        (r'(?:mínimo|minimo|pelo menos|no mínimo|at least)\s*(\d+)\s*(?:anos?|years?)', 'years'),
        (r'(\d+)\s*(?:a|to|-)\s*(\d+)\s*(?:anos?|years?)', 'range'),
        (r'mais de\s*(\d+)\s*(?:anos?|years?)', 'years'),
    ]
    
    for pattern, ptype in exp_patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            if ptype == 'range':
                entities.years_experience = f"{match.group(1)}-{match.group(2)} anos"
            else:
                entities.years_experience = f"{match.group(1)}+ anos"
            confidence += 0.2
            break
    
    seniority_patterns = {
        r'\b(júnior|junior|jr|trainee|estagiário|estagiaria|intern)\b': 'Junior',
        r'\b(pleno|mid|mid-level|middle|intermediário|intermediario)\b': 'Pleno',
        r'\b(sênior|senior|sr|experiente|experienced)\b': 'Senior',
        r'\b(staff|principal|distinguished)\b': 'Staff',
        r'\b(lead|líder|lider|head)\b': 'Lead',
        r'\b(specialist|especialista|expert)\b': 'Especialista',
    }
    
    for pattern, level in seniority_patterns.items():
        if re.search(pattern, query, re.IGNORECASE):
            entities.seniority = level
            if not entities.years_experience:
                entities.years_experience = level
            confidence += 0.1
            break
    
    # ============================================
    # 4. SKILLS - Tecnologias, Linguagens, Ferramentas
    # ============================================
    skills_list = [
        # Programming Languages
        'python', 'java', 'javascript', 'js', 'typescript', 'ts', 'golang', 'go',
        'rust', 'ruby', 'php', 'c\\+\\+', 'cpp', 'c#', 'csharp', '\\.net', 'dotnet',
        'kotlin', 'swift', 'scala', 'perl', 'r', 'matlab', 'julia', 'elixir',
        'clojure', 'haskell', 'lua', 'dart', 'objective-c', 'cobol', 'fortran',
        
        # Frontend
        'react', 'reactjs', 'react\\.js', 'angular', 'vue', 'vuejs', 'vue\\.js',
        'svelte', 'next\\.?js', 'nextjs', 'nuxt', 'gatsby', 'remix',
        'html', 'css', 'sass', 'scss', 'less', 'tailwind', 'bootstrap', 'material-ui',
        'styled-components', 'webpack', 'vite', 'babel', 'redux', 'mobx', 'zustand',
        
        # Backend
        'node\\.?js', 'nodejs', 'express', 'fastapi', 'django', 'flask', 'fastify',
        'spring', 'spring boot', 'springboot', 'rails', 'ruby on rails', 'laravel',
        'asp\\.net', 'gin', 'echo', 'fiber', 'nestjs', 'nest\\.js', 'graphql', 'rest',
        
        # Mobile
        'react native', 'flutter', 'ionic', 'xamarin', 'swiftui', 'jetpack compose',
        
        # Databases
        'sql', 'nosql', 'mongodb', 'mongo', 'postgresql', 'postgres', 'mysql',
        'mariadb', 'sqlite', 'oracle', 'sql server', 'dynamodb', 'cassandra',
        'redis', 'elasticsearch', 'elastic', 'neo4j', 'couchdb', 'firestore',
        
        # Cloud & DevOps
        'aws', 'amazon web services', 'azure', 'gcp', 'google cloud',
        'docker', 'kubernetes', 'k8s', 'terraform', 'ansible', 'puppet', 'chef',
        'jenkins', 'github actions', 'gitlab ci', 'circleci', 'travis',
        'nginx', 'apache', 'linux', 'unix', 'bash', 'shell',
        
        # Data & AI
        'machine learning', 'ml', 'deep learning', 'ai', 'inteligência artificial',
        'tensorflow', 'pytorch', 'keras', 'scikit-learn', 'sklearn', 'pandas',
        'numpy', 'spark', 'pyspark', 'hadoop', 'airflow', 'kafka', 'rabbitmq',
        'tableau', 'power bi', 'looker', 'metabase', 'dbt', 'snowflake', 'databricks',
        'nlp', 'computer vision', 'llm', 'gpt', 'openai', 'langchain',
        
        # Tools & Practices
        'git', 'github', 'gitlab', 'bitbucket', 'jira', 'confluence', 'notion',
        'figma', 'sketch', 'adobe xd', 'invision', 'zeplin',
        'agile', 'scrum', 'kanban', 'lean', 'ci/cd', 'cicd', 'tdd', 'bdd',
        'microservices', 'microsserviços', 'api', 'rest api', 'websocket',
        'serverless', 'lambda', 'event-driven', 'ddd', 'clean architecture',
        
        # Security
        'security', 'segurança', 'owasp', 'penetration testing', 'pentest',
        'soc', 'siem', 'firewall', 'vpn', 'ssl', 'tls', 'oauth', 'jwt',
        
        # Languages (human)
        'inglês', 'ingles', 'english', 'espanhol', 'spanish', 'francês', 'french',
        'alemão', 'german', 'italiano', 'italian', 'mandarim', 'mandarin',
        'inglês fluente', 'inglês avançado', 'bilíngue', 'bilingue'
    ]
    
    skills_found = set()
    for skill in skills_list:
        pattern = r'\b' + skill + r'\b'
        if re.search(pattern, query, re.IGNORECASE):
            skill_clean = skill.replace('\\', '').replace('.?', '.').replace('\\+\\+', '++')
            if skill_clean.lower() in ['js', 'javascript']:
                skill_clean = 'JavaScript'
            elif skill_clean.lower() in ['ts', 'typescript']:
                skill_clean = 'TypeScript'
            elif skill_clean.lower() in ['node.js', 'nodejs']:
                skill_clean = 'Node.js'
            elif skill_clean.lower() in ['k8s', 'kubernetes']:
                skill_clean = 'Kubernetes'
            elif skill_clean.lower() in ['ml', 'machine learning']:
                skill_clean = 'Machine Learning'
            elif skill_clean.lower() in ['ai', 'inteligência artificial']:
                skill_clean = 'AI'
            elif skill_clean.lower() in ['inglês', 'ingles', 'english']:
                skill_clean = 'Inglês'
            elif skill_clean.lower() in ['inglês fluente', 'inglês avançado']:
                skill_clean = 'Inglês Avançado'
            elif len(skill_clean) <= 3:
                skill_clean = skill_clean.upper()
            else:
                skill_clean = skill_clean.title()
            skills_found.add(skill_clean)
    
    if skills_found:
        entities.skills = list(skills_found)[:8]
        confidence += 0.2
    
    # ============================================
    # 5. INDUSTRY - Setores e Indústrias
    # ============================================
    industries = {
        # Tech Verticals
        r'\b(fintech|fin-tech)\b': 'Fintech',
        r'\b(healthtech|health-tech|saúde digital)\b': 'Healthtech',
        r'\b(edtech|ed-tech|educação digital)\b': 'Edtech',
        r'\b(agritech|agri-tech|agrotech)\b': 'Agritech',
        r'\b(legaltech|legal-tech|lawtech)\b': 'Legaltech',
        r'\b(insurtech|insur-tech)\b': 'Insurtech',
        r'\b(proptech|prop-tech|real estate tech)\b': 'Proptech',
        r'\b(logtech|log-tech|logística tech)\b': 'Logtech',
        r'\b(retailtech|retail-tech)\b': 'Retailtech',
        r'\b(martech|mar-tech|marketing tech)\b': 'Martech',
        r'\b(hrtech|hr-tech|rh tech)\b': 'HRtech',
        r'\b(govtech|gov-tech)\b': 'Govtech',
        r'\b(foodtech|food-tech)\b': 'Foodtech',
        r'\b(cleantech|clean-tech|greentech)\b': 'Cleantech',
        
        # Traditional Industries  
        r'\b(?:mercado\s+)?financeiro\b': 'Mercado Financeiro',
        r'\b(finanças|finance|banking|banco|bancos)\b': 'Finanças',
        r'\b(investimento|investment|asset management)\b': 'Investimentos',
        r'\b(seguros?|insurance)\b': 'Seguros',
        r'\b(saúde|health|healthcare|hospitalar?)\b': 'Saúde',
        r'\b(educação|education|ensino)\b': 'Educação',
        r'\b(varejo|retail|e-commerce|ecommerce|comércio)\b': 'Varejo',
        r'\b(logística|logistics|supply chain|cadeia de suprimentos)\b': 'Logística',
        r'\b(telecomunicações?|telecom|telecommunications?)\b': 'Telecom',
        r'\b(energia|energy|utilities|utilities)\b': 'Energia',
        r'\b(automotivo|automotive|automobilístico)\b': 'Automotivo',
        r'\b(farmacêutico|pharma|pharmaceutical)\b': 'Farmacêutico',
        r'\b(imobiliário|real estate|construção|construction)\b': 'Imobiliário',
        r'\b(mídia|media|entretenimento|entertainment)\b': 'Mídia',
        r'\b(agricultura|agro|agronegócio|agribusiness)\b': 'Agronegócio',
        r'\b(manufatura|manufacturing|indústria|industrial)\b': 'Manufatura',
        r'\b(aviação|aviation|aéreo|aerospace)\b': 'Aviação',
        r'\b(jurídico|legal|advocacia|law)\b': 'Jurídico',
        r'\b(rh|recursos humanos|human resources|hr)\b': 'RH',
        
        # Company Types
        r'\b(startup|startups)\b': 'Startup',
        r'\b(scale-?up)\b': 'Scale-up',
        r'\b(consultoria|consulting|consultancy)\b': 'Consultoria',
        r'\b(agência|agency|agencias)\b': 'Agência',
        r'\b(software house|fábrica de software)\b': 'Software House',
        r'\b(big tech|faang|maang)\b': 'Big Tech',
        r'\b(multinacional|multinational|global company)\b': 'Multinacional',
        r'\b(b2b|business to business)\b': 'B2B',
        r'\b(b2c|business to consumer)\b': 'B2C',
        r'\b(saas|software as a service)\b': 'SaaS',
    }
    
    for pattern, industry in industries.items():
        if re.search(pattern, query, re.IGNORECASE):
            entities.industry = industry
            confidence += 0.15
            break
    
    confidence = min(confidence, 1.0)
    
    if not entities.job_title:
        suggestions.append("Especifique o cargo (ex: Product Manager, Desenvolvedor Python)")
    if not entities.location:
        suggestions.append("Adicione a localização (ex: São Paulo, Remoto)")
    if not entities.skills:
        suggestions.append("Liste as skills técnicas (ex: React, Python, AWS)")
    if not entities.years_experience and not entities.seniority:
        suggestions.append("Defina a senioridade (ex: Senior, 5+ anos)")
    if not entities.industry:
        suggestions.append("Mencione o setor (ex: Fintech, Mercado Financeiro)")
    
    return ParseQueryResponse(
        query=request.query,
        entities=entities,
        confidence=confidence,
        suggestions=suggestions
    )


# ========================
# REVEAL CONTACT ENDPOINTS
# ========================

class RevealType(str):
    EMAIL = "email"
    PHONE = "phone"


class RevealContactRequest(BaseModel):
    """Request para revelar email ou telefone de um candidato Pearch."""
    candidate_id: str = Field(..., description="ID do candidato (docid do Pearch)")
    candidate_name: str = Field(..., description="Nome do candidato para busca")
    reveal_type: str = Field(..., description="Tipo: 'email' ou 'phone'", pattern="^(email|phone)$")
    linkedin_slug: str | None = Field(None, description="LinkedIn slug para busca mais precisa")


class RevealContactResponse(BaseModel):
    """Response com dados de contato revelados."""
    success: bool
    candidate_id: str
    reveal_type: str
    
    # Dados revelados
    email: str | None = None
    emails: list[str] = Field(default_factory=list)
    phone: str | None = None
    phones: list[str] = Field(default_factory=list)
    
    # Custos
    credits_used: int = 0
    credits_remaining: int | None = None
    
    # Mensagem
    message: str = ""


class RevealCostEstimate(BaseModel):
    """Estimativa de custo para reveal."""
    reveal_type: str
    credits_required: int
    description: str

