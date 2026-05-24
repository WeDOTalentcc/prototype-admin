"""
Search Archetypes model for pre-configured candidate search profiles.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
import uuid
from sqlalchemy import Column, String, Text, JSON, Boolean, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from lia_config.database import Base


class SearchArchetype(Base):
    """
    Represents a pre-configured search archetype for quick candidate searches.
    
    Archetypes are reusable search templates that combine:
    - Natural language query
    - Pre-configured filters
    - Tags and metadata
    - Seniority/industry targeting
    """
    __tablename__ = "search_archetypes"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    emoji = Column(String(10), default="🎯")
    
    query = Column(Text, nullable=False)
    filters = Column(JSON, default=dict)
    tags = Column(JSON, default=list)
    
    industry = Column(String(100), nullable=True, index=True)
    seniority = Column(String(50), nullable=True, index=True)
    
    is_default = Column(Boolean, default=False, index=True)
    is_active = Column(Boolean, default=True, index=True)
    
    usage_count = Column(Integer, default=0)
    
    # TENANT-EXEMPT: SearchArchetype com company_id NULL = template publico do marketplace
    company_id = Column(String(100), nullable=True, index=True)
    created_by = Column(String(255), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, server_default=func.now())
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<SearchArchetype {self.id} - {self.name}>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert archetype to dictionary for API responses."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "emoji": self.emoji,
            "query": self.query,
            "filters": self.filters or {},
            "tags": self.tags or [],
            "industry": self.industry,
            "seniority": self.seniority,
            "is_default": self.is_default,
            "is_active": self.is_active,
            "usage_count": self.usage_count,
            "company_id": self.company_id,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


DEFAULT_ARCHETYPES = [
    # ============================================================================
    # TECNOLOGIA
    # ============================================================================
    {
        "id": "tech-lead",
        "name": "Tech Lead",
        "description": "Líder técnico com experiência em gestão de equipes e arquitetura de sistemas",
        "emoji": "🎯",
        "query": "Tech Lead com experiência em gestão de equipes, arquitetura de sistemas, 8+ anos em desenvolvimento",
        "filters": {
            "seniority": "senior",
            "experience_years_min": 8,
            "skills": ["liderança técnica", "arquitetura", "gestão de equipes"]
        },
        "tags": ["liderança", "arquitetura", "gestão"],
        "industry": "tecnologia",
        "seniority": "senior",
        "is_default": True
    },
    {
        "id": "dev-senior",
        "name": "Dev Sênior Full-Stack",
        "description": "Desenvolvedor sênior full-stack com ampla experiência em tecnologias modernas",
        "emoji": "🚀",
        "query": "Desenvolvedor sênior full-stack, 5+ anos experiência, React, Node.js, Python",
        "filters": {
            "seniority": "senior",
            "experience_years_min": 5,
            "skills": ["React", "Node.js", "Python", "Full-Stack"]
        },
        "tags": ["full-stack", "React", "Node.js", "Python"],
        "industry": "tecnologia",
        "seniority": "senior",
        "is_default": True
    },
    {
        "id": "product-manager",
        "name": "Product Manager",
        "description": "Product Manager com experiência em metodologias ágeis e gestão de produto",
        "emoji": "📊",
        "query": "Product Manager com experiência em metodologias ágeis, discovery, roadmap, métricas",
        "filters": {
            "seniority": "pleno",
            "experience_years_min": 3,
            "skills": ["Product Management", "Agile", "Discovery", "Roadmap"]
        },
        "tags": ["produto", "agile", "discovery", "métricas"],
        "industry": "tecnologia",
        "seniority": "pleno",
        "is_default": True
    },
    {
        "id": "data-scientist",
        "name": "Data Scientist",
        "description": "Cientista de dados com experiência em Machine Learning e produção",
        "emoji": "🧠",
        "query": "Data Scientist com Python, Machine Learning, estatística, SQL, experiência em produção",
        "filters": {
            "seniority": "senior",
            "experience_years_min": 3,
            "skills": ["Python", "Machine Learning", "Estatística", "SQL", "Data Science"]
        },
        "tags": ["data science", "machine learning", "python", "analytics"],
        "industry": "tecnologia",
        "seniority": "senior",
        "is_default": True
    },
    {
        "id": "backend-nodejs",
        "name": "Backend Sênior Node.js",
        "description": "Desenvolvedor backend sênior especializado em Node.js e APIs RESTful",
        "emoji": "⚡",
        "query": "Backend Sênior Node.js com experiência em APIs RESTful, microserviços e arquitetura escalável",
        "filters": {
            "seniority": "senior",
            "experience_years_min": 5,
            "skills": ["Node.js", "APIs RESTful", "Microserviços", "TypeScript"]
        },
        "tags": ["backend", "Node.js", "APIs", "microserviços"],
        "industry": "tecnologia",
        "seniority": "senior",
        "is_default": True
    },
    {
        "id": "frontend-react",
        "name": "Frontend React Sênior",
        "description": "Desenvolvedor frontend especializado em React e ecossistema moderno",
        "emoji": "💎",
        "query": "Frontend Sênior React com experiência em TypeScript, Redux, testes e design systems",
        "filters": {
            "seniority": "senior",
            "experience_years_min": 4,
            "skills": ["React", "TypeScript", "Redux", "CSS-in-JS", "Testing"]
        },
        "tags": ["frontend", "React", "TypeScript", "UI/UX"],
        "industry": "tecnologia",
        "seniority": "senior",
        "is_default": True
    },
    {
        "id": "devops-sre",
        "name": "DevOps / SRE",
        "description": "Engenheiro DevOps/SRE com experiência em cloud e automação",
        "emoji": "☁️",
        "query": "DevOps SRE com AWS, Kubernetes, Docker, Terraform, CI/CD, monitoramento",
        "filters": {
            "seniority": "senior",
            "experience_years_min": 4,
            "skills": ["AWS", "Kubernetes", "Docker", "Terraform", "CI/CD"]
        },
        "tags": ["devops", "SRE", "cloud", "kubernetes", "AWS"],
        "industry": "tecnologia",
        "seniority": "senior",
        "is_default": True
    },
    {
        "id": "ux-designer",
        "name": "UX/UI Designer",
        "description": "Designer de experiência do usuário com foco em produto digital",
        "emoji": "🎨",
        "query": "UX/UI Designer com experiência em Figma, pesquisa de usuários, design systems, prototipagem",
        "filters": {
            "seniority": "pleno",
            "experience_years_min": 3,
            "skills": ["Figma", "UX Research", "Design Systems", "Prototyping"]
        },
        "tags": ["design", "UX", "UI", "Figma", "produto"],
        "industry": "tecnologia",
        "seniority": "pleno",
        "is_default": True
    },
    {
        "id": "data-engineer",
        "name": "Data Engineer",
        "description": "Engenheiro de dados com experiência em pipelines e infraestrutura de dados",
        "emoji": "🔧",
        "query": "Data Engineer com Python, Spark, Airflow, SQL, experiência em data lakes e ETL",
        "filters": {
            "seniority": "senior",
            "experience_years_min": 4,
            "skills": ["Python", "Spark", "Airflow", "SQL", "ETL", "Data Lake"]
        },
        "tags": ["data engineering", "ETL", "Spark", "pipeline"],
        "industry": "tecnologia",
        "seniority": "senior",
        "is_default": True
    },
    {
        "id": "qa-engineer",
        "name": "QA Engineer",
        "description": "Engenheiro de qualidade com experiência em automação de testes",
        "emoji": "🔍",
        "query": "QA Engineer com automação de testes, Selenium, Cypress, API testing, CI/CD",
        "filters": {
            "seniority": "pleno",
            "experience_years_min": 3,
            "skills": ["Selenium", "Cypress", "API Testing", "Test Automation", "CI/CD"]
        },
        "tags": ["QA", "testes", "automação", "qualidade"],
        "industry": "tecnologia",
        "seniority": "pleno",
        "is_default": True
    },
    {
        "id": "mobile-developer",
        "name": "Mobile Developer",
        "description": "Desenvolvedor mobile com experiência em iOS e/ou Android",
        "emoji": "📱",
        "query": "Mobile Developer com React Native ou Flutter, experiência em apps nativos, publicação em stores",
        "filters": {
            "seniority": "pleno",
            "experience_years_min": 3,
            "skills": ["React Native", "Flutter", "iOS", "Android", "Mobile"]
        },
        "tags": ["mobile", "React Native", "Flutter", "iOS", "Android"],
        "industry": "tecnologia",
        "seniority": "pleno",
        "is_default": True
    },
    
    # ============================================================================
    # FINANÇAS
    # ============================================================================
    {
        "id": "fp-and-a",
        "name": "Analista FP&A",
        "description": "Analista de planejamento financeiro e análise com foco em orçamento e forecast",
        "emoji": "📊",
        "query": "Analista FP&A com experiência em planejamento financeiro, orçamento, forecast, modelagem financeira",
        "filters": {
            "seniority": "pleno",
            "experience_years_min": 3,
            "skills": ["FP&A", "Planejamento Financeiro", "Excel Avançado", "Power BI", "Orçamento"]
        },
        "tags": ["FP&A", "finanças", "orçamento", "forecast", "análise"],
        "industry": "financas",
        "seniority": "pleno",
        "is_default": True
    },
    {
        "id": "controller",
        "name": "Controller",
        "description": "Controller com experiência em controladoria, fechamento contábil e reporting",
        "emoji": "📈",
        "query": "Controller com experiência em controladoria, fechamento contábil, IFRS, SOX, reporting gerencial",
        "filters": {
            "seniority": "senior",
            "experience_years_min": 6,
            "skills": ["Controladoria", "IFRS", "Fechamento Contábil", "SOX", "SAP"]
        },
        "tags": ["controller", "controladoria", "contabilidade", "IFRS"],
        "industry": "financas",
        "seniority": "senior",
        "is_default": True
    },
    {
        "id": "analista-financeiro",
        "name": "Analista Financeiro",
        "description": "Analista financeiro com experiência em tesouraria e fluxo de caixa",
        "emoji": "💰",
        "query": "Analista Financeiro com experiência em tesouraria, fluxo de caixa, contas a pagar e receber",
        "filters": {
            "seniority": "pleno",
            "experience_years_min": 2,
            "skills": ["Tesouraria", "Fluxo de Caixa", "Contas a Pagar", "Contas a Receber", "Excel"]
        },
        "tags": ["financeiro", "tesouraria", "fluxo de caixa"],
        "industry": "financas",
        "seniority": "pleno",
        "is_default": True
    },
    {
        "id": "contador",
        "name": "Contador Sênior",
        "description": "Contador com CRC ativo e experiência em contabilidade fiscal e societária",
        "emoji": "📑",
        "query": "Contador com CRC ativo, experiência em contabilidade fiscal, societária, SPED, ECD, ECF",
        "filters": {
            "seniority": "senior",
            "experience_years_min": 5,
            "skills": ["Contabilidade Fiscal", "SPED", "ECD", "ECF", "CPC", "IFRS"]
        },
        "tags": ["contador", "fiscal", "tributário", "SPED"],
        "industry": "financas",
        "seniority": "senior",
        "is_default": True
    },
    {
        "id": "analista-tributario",
        "name": "Analista Tributário",
        "description": "Analista tributário com experiência em impostos diretos e indiretos",
        "emoji": "🧮",
        "query": "Analista Tributário com experiência em ICMS, PIS, COFINS, IR, planejamento tributário",
        "filters": {
            "seniority": "pleno",
            "experience_years_min": 3,
            "skills": ["ICMS", "PIS/COFINS", "IR", "Planejamento Tributário", "Tax"]
        },
        "tags": ["tributário", "fiscal", "impostos", "tax"],
        "industry": "financas",
        "seniority": "pleno",
        "is_default": True
    },
    
    # ============================================================================
    # RECURSOS HUMANOS
    # ============================================================================
    {
        "id": "hr-bp",
        "name": "HR Business Partner",
        "description": "Business Partner de RH com foco estratégico e consultoria interna",
        "emoji": "🤝",
        "query": "HR Business Partner com experiência em consultoria interna, gestão de talentos, desenvolvimento organizacional",
        "filters": {
            "seniority": "senior",
            "experience_years_min": 5,
            "skills": ["Business Partner", "Gestão de Talentos", "Desenvolvimento Organizacional", "Consultoria RH"]
        },
        "tags": ["HRBP", "business partner", "estratégico", "consultoria"],
        "industry": "rh",
        "seniority": "senior",
        "is_default": True
    },
    {
        "id": "tech-recruiter",
        "name": "Tech Recruiter",
        "description": "Recrutador especializado em posições de tecnologia",
        "emoji": "🎯",
        "query": "Tech Recruiter com experiência em sourcing, hunting, vagas de tecnologia, LinkedIn Recruiter",
        "filters": {
            "seniority": "pleno",
            "experience_years_min": 2,
            "skills": ["Sourcing", "Hunting", "LinkedIn Recruiter", "Tech Recruiting", "ATS"]
        },
        "tags": ["recrutamento", "tech", "sourcing", "hunting"],
        "industry": "rh",
        "seniority": "pleno",
        "is_default": True
    },
    {
        "id": "dp-specialist",
        "name": "Analista de DP",
        "description": "Analista de Departamento Pessoal com experiência em folha e legislação trabalhista",
        "emoji": "📋",
        "query": "Analista de DP com experiência em folha de pagamento, eSocial, férias, rescisão, legislação trabalhista",
        "filters": {
            "seniority": "pleno",
            "experience_years_min": 3,
            "skills": ["Folha de Pagamento", "eSocial", "Legislação Trabalhista", "FGTS", "INSS"]
        },
        "tags": ["DP", "folha", "eSocial", "trabalhista"],
        "industry": "rh",
        "seniority": "pleno",
        "is_default": True
    },
    {
        "id": "td-analyst",
        "name": "Analista de T&D",
        "description": "Analista de Treinamento e Desenvolvimento com foco em capacitação",
        "emoji": "🎓",
        "query": "Analista de T&D com experiência em LMS, e-learning, trilhas de desenvolvimento, onboarding",
        "filters": {
            "seniority": "pleno",
            "experience_years_min": 3,
            "skills": ["T&D", "LMS", "E-learning", "Onboarding", "Trilhas de Desenvolvimento"]
        },
        "tags": ["T&D", "treinamento", "desenvolvimento", "e-learning"],
        "industry": "rh",
        "seniority": "pleno",
        "is_default": True
    },
    {
        "id": "hr-generalist",
        "name": "Generalista de RH",
        "description": "Generalista de RH com visão ampla de todos os subsistemas",
        "emoji": "👥",
        "query": "Generalista de RH com experiência em R&S, T&D, DP, benefícios, clima organizacional",
        "filters": {
            "seniority": "pleno",
            "experience_years_min": 3,
            "skills": ["R&S", "T&D", "DP", "Benefícios", "Clima Organizacional"]
        },
        "tags": ["generalista", "RH", "subsistemas"],
        "industry": "rh",
        "seniority": "pleno",
        "is_default": True
    },
    
    # ============================================================================
    # COMPRAS / SUPPLY CHAIN
    # ============================================================================
    {
        "id": "buyer-senior",
        "name": "Comprador Sênior",
        "description": "Comprador sênior com experiência em negociação e gestão de fornecedores",
        "emoji": "🛒",
        "query": "Comprador Sênior com experiência em negociação, gestão de fornecedores, strategic sourcing",
        "filters": {
            "seniority": "senior",
            "experience_years_min": 5,
            "skills": ["Negociação", "Strategic Sourcing", "Gestão de Fornecedores", "SAP MM", "Contratos"]
        },
        "tags": ["compras", "buyer", "sourcing", "negociação"],
        "industry": "compras",
        "seniority": "senior",
        "is_default": True
    },
    {
        "id": "procurement-analyst",
        "name": "Analista de Procurement",
        "description": "Analista de compras com foco em processos e análise de custos",
        "emoji": "📦",
        "query": "Analista de Procurement com experiência em análise de custos, cotações, pedidos de compra, ERP",
        "filters": {
            "seniority": "pleno",
            "experience_years_min": 2,
            "skills": ["Procurement", "Análise de Custos", "ERP", "Excel Avançado", "Cotações"]
        },
        "tags": ["procurement", "compras", "custos", "análise"],
        "industry": "compras",
        "seniority": "pleno",
        "is_default": True
    },
    {
        "id": "supply-chain-manager",
        "name": "Gerente de Supply Chain",
        "description": "Gerente de cadeia de suprimentos com visão end-to-end",
        "emoji": "🔄",
        "query": "Gerente de Supply Chain com experiência em logística, planejamento de demanda, S&OP, gestão de estoques",
        "filters": {
            "seniority": "senior",
            "experience_years_min": 7,
            "skills": ["Supply Chain", "S&OP", "Logística", "Gestão de Estoques", "Planejamento de Demanda"]
        },
        "tags": ["supply chain", "logística", "S&OP", "gestão"],
        "industry": "compras",
        "seniority": "senior",
        "is_default": True
    },
    {
        "id": "logistics-analyst",
        "name": "Analista de Logística",
        "description": "Analista de logística com experiência em transporte e distribuição",
        "emoji": "🚚",
        "query": "Analista de Logística com experiência em transporte, distribuição, WMS, roteirização",
        "filters": {
            "seniority": "pleno",
            "experience_years_min": 2,
            "skills": ["Logística", "WMS", "Transporte", "Distribuição", "Roteirização"]
        },
        "tags": ["logística", "transporte", "distribuição", "WMS"],
        "industry": "compras",
        "seniority": "pleno",
        "is_default": True
    },
    {
        "id": "import-export",
        "name": "Analista de Comércio Exterior",
        "description": "Analista de importação e exportação com conhecimento em legislação aduaneira",
        "emoji": "🌐",
        "query": "Analista de Comércio Exterior com experiência em importação, exportação, despacho aduaneiro, Siscomex",
        "filters": {
            "seniority": "pleno",
            "experience_years_min": 3,
            "skills": ["Importação", "Exportação", "Siscomex", "Despacho Aduaneiro", "Incoterms"]
        },
        "tags": ["comex", "importação", "exportação", "aduaneiro"],
        "industry": "compras",
        "seniority": "pleno",
        "is_default": True
    }
]


async def seed_default_archetypes(db) -> int:
    """
    Seed the database with default archetypes if they don't exist.
    
    Returns:
        Number of archetypes created
    """
    from sqlalchemy import select
    
    created_count = 0
    
    for archetype_data in DEFAULT_ARCHETYPES:
        result = await db.execute(
            select(SearchArchetype).where(SearchArchetype.id == archetype_data["id"])
        )
        existing = result.scalar_one_or_none()
        
        if not existing:
            archetype = SearchArchetype(**archetype_data)
            db.add(archetype)
            created_count += 1
    
    if created_count > 0:
        await db.commit()
    
    return created_count
