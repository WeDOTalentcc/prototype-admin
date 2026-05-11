"""
Seed Full Platform — Populates all LIA platform tables with realistic Brazilian HR data.

Usage:
    python scripts/seed_full_platform.py --seed     # Insert all seed data
    python scripts/seed_full_platform.py --clean    # Remove all seed data by company_id
    python scripts/seed_full_platform.py --reset    # Clean + Seed

Idempotent: checks for existing SEED_COMPANY_ID before inserting.
"""
import asyncio
import argparse
import json
import logging
import os
import sys
import uuid
from datetime import datetime, timedelta, date
from random import choice, randint, sample, uniform

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import select, delete, text, and_
from sqlalchemy.ext.asyncio import AsyncSession

from lia_config.database import AsyncSessionLocal, engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

SEED_COMPANY_ID = uuid.UUID("00000000-0000-4000-a000-000000000001")
SEED_COMPANY_ID_STR = str(SEED_COMPANY_ID)
SEED_COMPANY_PROFILE_ID = uuid.UUID("00000000-0000-4000-a000-000000000002")

NOW = datetime.utcnow()


def _past(days_ago_min: int, days_ago_max: int) -> datetime:
    return NOW - timedelta(days=randint(days_ago_min, days_ago_max))


SEED_NS = uuid.UUID("00000000-0000-4000-a000-ffffffffffff")


def _seed_uuid(label: str) -> uuid.UUID:
    return uuid.uuid5(SEED_NS, label)


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


# Areas com peso realista no mercado BR (% candidatos/vagas distribuicao)
DEPT_WEIGHTS = {
    "engineering": 18, "data": 6, "product": 5, "design": 4,
    "sales": 12, "customer_experience": 5,
    "operations": 8, "logistics": 4, "procurement": 3,
    "finance": 6, "accounting_tax": 3,
    "marketing": 5,
    "hr": 5,
    "legal": 2, "compliance_audit": 2,
    "healthcare": 3,
    "education": 2,
    "manufacturing": 2,
    "construction": 1, "agronegocio": 2,
    "security": 1, "esg_sustainability": 1,
}
DEPT_IDS = {n: _seed_uuid(f"dept:{n}") for n in DEPT_WEIGHTS}
DEPT_DISPLAY = {
    "engineering": "Engenharia de Software", "data": "Dados & Analytics",
    "product": "Produto", "design": "Design",
    "sales": "Vendas", "customer_experience": "Atendimento & CX",
    "operations": "Operacoes", "logistics": "Logistica & Supply Chain",
    "procurement": "Compras", "finance": "Financas",
    "accounting_tax": "Contabilidade & Tributario",
    "marketing": "Marketing", "hr": "Recursos Humanos",
    "legal": "Juridico", "compliance_audit": "Compliance & Auditoria",
    "healthcare": "Saude", "education": "Educacao",
    "manufacturing": "Manufatura", "construction": "Construcao & Engenharia",
    "agronegocio": "Agronegocio", "security": "Seguranca",
    "esg_sustainability": "ESG & Sustentabilidade",
}

STAGE_DEFS = [
    {"name": "sourcing",             "display_name": "Funil",             "order": 1,  "color": "#6366F1", "icon": "search",      "type": "active",   "is_initial": True,  "cat": "system",  "behavior": "intake"},
    {"name": "screening",            "display_name": "Triagem",           "order": 2,  "color": "#8B5CF6", "icon": "file-text",   "type": "active",   "cat": "system",  "behavior": "screening"},
    {"name": "long_list",            "display_name": "Long List",         "order": 3,  "color": "#C5D9ED", "icon": "list",        "type": "active",   "cat": "custom",  "behavior": "passive"},
    {"name": "short_list",           "display_name": "Short List",        "order": 4,  "color": "#B8C5D0", "icon": "list-checks", "type": "active",   "cat": "custom",  "behavior": "passive"},
    {"name": "interview_hr",         "display_name": "Entrevista RH",     "order": 5,  "color": "#EC4899", "icon": "users",       "type": "active",   "cat": "system",  "behavior": "scheduling"},
    {"name": "technical_test",       "display_name": "Teste Técnico",     "order": 6,  "color": "#E8B8B8", "icon": "code-2",      "type": "active",   "cat": "custom",  "behavior": "evaluation"},
    {"name": "interview_technical",  "display_name": "Entrevista Técnica","order": 7,  "color": "#F59E0B", "icon": "monitor",     "type": "active",   "cat": "system",  "behavior": "scheduling"},
    {"name": "interview_manager",    "display_name": "Entrevista Gestor", "order": 8,  "color": "#10B981", "icon": "briefcase",   "type": "active",   "cat": "system",  "behavior": "scheduling"},
    {"name": "offer",                "display_name": "Proposta",          "order": 9,  "color": "#3B82F6", "icon": "file-check",  "type": "active",   "cat": "system",  "behavior": "passive", "is_final": True},
    {"name": "hired",                "display_name": "Contratado",        "order": 10, "color": "#22C55E", "icon": "check-circle","type": "terminal", "cat": "system",  "behavior": "passive", "is_final": True, "is_hired": True},
    {"name": "rejected",             "display_name": "Reprovado",         "order": 99, "color": "#EF4444", "icon": "x-circle",    "type": "terminal", "cat": "system",  "behavior": "passive", "is_final": True, "is_rejection": True},
]

STAGE_IDS = {s["name"]: _seed_uuid(f"stage:{s['name']}") for s in STAGE_DEFS}

BENEFITS_DATA = [
    {"name": "Vale Refeição",       "category": "alimentação",  "value": 1200.0, "icon": "utensils"},
    {"name": "Vale Alimentação",    "category": "alimentação",  "value": 800.0,  "icon": "shopping-cart"},
    {"name": "Plano de Saúde",      "category": "saúde",        "value": 950.0,  "icon": "heart-pulse"},
    {"name": "Plano Odontológico",  "category": "saúde",        "value": 120.0,  "icon": "smile"},
    {"name": "Seguro de Vida",      "category": "saúde",        "value": 80.0,   "icon": "shield"},
    {"name": "Gympass",             "category": "bem-estar",    "value": 150.0,  "icon": "dumbbell"},
    {"name": "Day Off Aniversário", "category": "bem-estar",    "value": None,   "icon": "cake"},
    {"name": "PLR",                 "category": "financeiro",   "value": None,   "icon": "trending-up", "value_type": "percentage", "percentage": 15.0},
    {"name": "Auxílio Home Office", "category": "trabalho",     "value": 200.0,  "icon": "home"},
    {"name": "Auxílio Educação",    "category": "desenvolvimento", "value": 500.0, "icon": "book-open"},
]

CULTURE_VALUES = [
    {"name": "Inovação Contínua",       "description": "Buscamos constantemente novas formas de resolver problemas e entregar valor.",              "category": "value", "icon": "lightbulb",  "color": "#6366F1"},
    {"name": "Diversidade & Inclusão",  "description": "Valorizamos diferentes perspectivas e promovemos um ambiente acolhedor para todos.",       "category": "value", "icon": "users",      "color": "#EC4899"},
    {"name": "Transparência",           "description": "Compartilhamos informações de forma aberta e honesta em todos os níveis.",                 "category": "value", "icon": "eye",        "color": "#3B82F6"},
    {"name": "Foco no Cliente",         "description": "Todas as decisões começam com o impacto positivo que podemos gerar para nossos clientes.", "category": "value", "icon": "target",     "color": "#10B981"},
    {"name": "Ownership",              "description": "Cada pessoa é dona do seu trabalho e responsável pelos resultados.",                        "category": "principle", "icon": "flag", "color": "#F59E0B"},
]

CLIENT_USERS = [
    {"name": "Ana Beatriz Costa",      "email": "ana.costa@wedotalent.cc",      "role": "admin",     "status": "active"},
    {"name": "Rafael Mendes",          "email": "rafael.mendes@wedotalent.cc",  "role": "recruiter", "status": "active"},
    {"name": "Camila Oliveira",        "email": "camila.oliveira@wedotalent.cc","role": "recruiter", "status": "active"},
    {"name": "Lucas Ferreira",         "email": "lucas.ferreira@wedotalent.cc", "role": "manager",   "status": "active"},
    {"name": "Juliana Santos",         "email": "juliana.santos@wedotalent.cc", "role": "viewer",    "status": "active"},
    {"name": "Pedro Almeida",          "email": "pedro.almeida@wedotalent.cc",  "role": "recruiter", "status": "pending"},
    {"name": "Mariana Duarte",         "email": "mariana.duarte@wedotalent.cc", "role": "hiring_manager", "status": "active"},
]

USER_IDS = [_seed_uuid(f"user:{u['email']}") for u in CLIENT_USERS]

# JOB_VACANCIES: gerado dinamicamente (~80 vagas) com pesos por area
import random as _jv_rng_mod
_JV_RNG = _jv_rng_mod.Random(7)

_SENIORITY_LEVELS = ["Júnior", "Pleno", "Sênior", "Especialista"]
_SENIORITY_WEIGHTS = [25, 40, 25, 10]
_VAC_STATUS_WEIGHTS = [("Ativa", 60), ("Rascunho", 12), ("Aprovada", 15), ("Concluída", 13)]
_VAC_MODELS = [("híbrido", 50), ("presencial", 30), ("remoto", 20)]
_VAC_TYPES = [("CLT", 70), ("PJ", 22), ("Estágio", 5), ("Temporário", 3)]
_VAC_PRIORITIES = [("alta", 25), ("média", 50), ("baixa", 25)]

# Salary base por seniority (min, max) — multiplicado por fator de area
_BASE_SALARY = {
    "Júnior":       (3500, 6500),
    "Pleno":        (7000, 13000),
    "Sênior":       (13000, 22000),
    "Especialista": (22000, 38000),
}
# Fator por area (engenharia mais alto, atendimento mais baixo)
_AREA_SALARY_FACTOR = {
    "engineering": 1.30, "data": 1.25, "product": 1.20, "design": 1.05,
    "sales": 1.00, "customer_experience": 0.80,
    "operations": 0.95, "logistics": 0.90, "procurement": 0.95,
    "finance": 1.15, "accounting_tax": 1.05,
    "marketing": 1.00, "hr": 0.95,
    "legal": 1.20, "compliance_audit": 1.15,
    "healthcare": 1.10, "education": 0.80,
    "manufacturing": 0.95, "construction": 1.00,
    "agronegocio": 1.00, "security": 0.95, "esg_sustainability": 1.05,
}

def _weighted(rng, items):
    keys = [k for k, _ in items]
    weights = [w for _, w in items]
    return rng.choices(keys, weights=weights)[0]

def _gen_job_vacancies(target_count: int):
    rng = _JV_RNG
    vacancies = []
    cities_list = CITIES
    dept_list = list(DEPT_WEIGHTS.keys())
    dept_weights = list(DEPT_WEIGHTS.values())

    for i in range(target_count):
        dept = rng.choices(dept_list, weights=dept_weights)[0]
        seniority = rng.choices(_SENIORITY_LEVELS, weights=_SENIORITY_WEIGHTS)[0]
        title_pool = TITLES_BY_AREA.get(dept, [DEPT_DISPLAY.get(dept, dept).title()])
        title_base = rng.choice(title_pool)
        # Sufixar com seniority quando faz sentido
        if seniority in {"Júnior", "Pleno", "Sênior"} and seniority not in title_base:
            title = f"{title_base} {seniority}"
        else:
            title = title_base
        city = rng.choices(cities_list, weights=[c[2] for c in cities_list])[0]
        loc = f"{city[0]}, {city[1]}"
        model = _weighted(rng, _VAC_MODELS)
        # Vagas em cidades pequenas tendem a ser remotas/hibridas
        if city[2] < 8 and rng.random() < 0.5:
            model = rng.choice(["remoto", "híbrido"])
        etype = _weighted(rng, _VAC_TYPES)
        status = _weighted(rng, _VAC_STATUS_WEIGHTS)
        priority = _weighted(rng, _VAC_PRIORITIES)
        sal_min_base, sal_max_base = _BASE_SALARY[seniority]
        factor = _AREA_SALARY_FACTOR.get(dept, 1.0)
        sal_min = round(sal_min_base * factor / 100) * 100
        sal_max = round(sal_max_base * factor / 100) * 100
        vacancies.append({
            "title": title, "dept": dept, "location": loc, "model": model,
            "type": etype, "seniority": seniority, "status": status,
            "priority": priority, "salary_min": sal_min, "salary_max": sal_max,
        })
    return vacancies

# JOB_VACANCIES gerado mais abaixo (depois de CITIES + TITLES_BY_AREA)

DEPT_TECH_MAP = {
    "engineering": [
        {"skill": "Python", "level": "avançado", "weight": 0.3},
        {"skill": "TypeScript", "level": "avançado", "weight": 0.25},
        {"skill": "PostgreSQL", "level": "intermediário", "weight": 0.2},
        {"skill": "Docker/Kubernetes", "level": "intermediário", "weight": 0.15},
        {"skill": "CI/CD", "level": "intermediário", "weight": 0.1},
    ],
    "product": [
        {"skill": "Product Discovery", "level": "avançado", "weight": 0.3},
        {"skill": "SQL / Análise de Dados", "level": "intermediário", "weight": 0.25},
        {"skill": "Figma / Prototipagem", "level": "intermediário", "weight": 0.2},
        {"skill": "Métricas de Produto", "level": "avançado", "weight": 0.15},
        {"skill": "Roadmap & OKRs", "level": "intermediário", "weight": 0.1},
    ],
    "design": [
        {"skill": "Figma", "level": "avançado", "weight": 0.3},
        {"skill": "Design Systems", "level": "avançado", "weight": 0.25},
        {"skill": "User Research", "level": "intermediário", "weight": 0.2},
        {"skill": "Prototipagem", "level": "intermediário", "weight": 0.15},
        {"skill": "Acessibilidade (WCAG)", "level": "básico", "weight": 0.1},
    ],
    "data": [
        {"skill": "Python / PySpark", "level": "avançado", "weight": 0.3},
        {"skill": "SQL Avançado", "level": "avançado", "weight": 0.25},
        {"skill": "Machine Learning", "level": "intermediário", "weight": 0.2},
        {"skill": "Airflow / dbt", "level": "intermediário", "weight": 0.15},
        {"skill": "Estatística", "level": "intermediário", "weight": 0.1},
    ],
}

SENIORITY_BEHAVIORAL_MAP = {
    "Júnior": [
        {"competency": "Comunicação", "description": "Capacidade de se expressar com clareza e ouvir ativamente", "weight": 0.3},
        {"competency": "Aprendizado contínuo", "description": "Busca ativa por conhecimento e desenvolvimento", "weight": 0.4},
        {"competency": "Trabalho em equipe", "description": "Colaboração e espírito de equipe", "weight": 0.3},
    ],
    "Pleno": [
        {"competency": "Comunicação", "description": "Capacidade de se expressar com clareza em diferentes contextos", "weight": 0.25},
        {"competency": "Resolução de problemas", "description": "Análise e solução de problemas complexos", "weight": 0.3},
        {"competency": "Autonomia", "description": "Capacidade de conduzir tarefas com independência", "weight": 0.25},
        {"competency": "Colaboração", "description": "Trabalho eficaz com times multidisciplinares", "weight": 0.2},
    ],
    "Sênior": [
        {"competency": "Liderança técnica", "description": "Capacidade de guiar decisões técnicas e mentorar colegas", "weight": 0.3},
        {"competency": "Visão estratégica", "description": "Alinhamento de entregas com objetivos de negócio", "weight": 0.25},
        {"competency": "Comunicação executiva", "description": "Articulação clara para stakeholders de diferentes níveis", "weight": 0.2},
        {"competency": "Gestão de complexidade", "description": "Navegação eficaz em projetos ambíguos e de alto impacto", "weight": 0.25},
    ],
    "Especialista": [
        {"competency": "Liderança técnica", "description": "Referência técnica e capacidade de influenciar decisões arquiteturais", "weight": 0.3},
        {"competency": "Inovação", "description": "Proposta de soluções inovadoras e escaláveis", "weight": 0.25},
        {"competency": "Mentoria", "description": "Desenvolvimento de talentos e disseminação de conhecimento", "weight": 0.25},
        {"competency": "Visão sistêmica", "description": "Compreensão holística de impactos e trade-offs", "weight": 0.2},
    ],
}


# ----------------------------------------------------------------------------
# Expansao 2026-05-11 — areas / titulos / skills / idiomas
# ----------------------------------------------------------------------------
TITLES_BY_AREA = {
    "engineering": ["Software Engineer", "Backend Developer", "Frontend Developer", "Full Stack Developer", "DevOps Engineer", "Site Reliability Engineer", "Tech Lead", "Engineering Manager", "Mobile Developer", "iOS Developer", "Android Developer"],
    "data": ["Data Analyst", "Data Engineer", "Data Scientist", "Analytics Engineer", "Machine Learning Engineer", "BI Analyst", "Head of Data"],
    "product": ["Product Manager", "Product Owner", "Product Analyst", "Group PM", "VP of Product"],
    "design": ["UX Designer", "UI Designer", "Product Designer", "Design Lead", "UX Researcher", "Brand Designer", "Motion Designer"],
    "sales": ["Sales Development Rep (SDR)", "Account Executive", "Enterprise AE", "Sales Manager", "Head of Sales", "Inside Sales", "Customer Account Manager"],
    "customer_experience": ["Customer Success Manager", "Customer Support Specialist", "CX Analyst", "Head of CX", "Implementation Manager", "Onboarding Specialist"],
    "operations": ["Analista de Operacoes", "Coordenador(a) de Operacoes", "Gerente de Operacoes", "Diretor(a) de Operacoes", "Operations Lead"],
    "logistics": ["Analista de Logistica", "Coordenador(a) de Logistica", "Gerente de Supply Chain", "Analista de Distribuicao", "Coordenador(a) de Armazem"],
    "procurement": ["Analista de Compras", "Comprador(a) Estrategico", "Gerente de Suprimentos", "Buyer", "Sourcing Specialist"],
    "finance": ["Analista Financeiro", "Analista de FP&A", "Controller", "Gerente Financeiro", "CFO", "Tesoureiro(a)"],
    "accounting_tax": ["Analista Contabil", "Analista Tributario", "Contador(a)", "Gerente Contabil", "Tax Manager", "Auxiliar Fiscal"],
    "marketing": ["Analista de Marketing", "Coordenador(a) de Marketing", "Marketing Manager", "CMO", "Growth Marketer", "Social Media Manager", "Brand Manager"],
    "hr": ["Analista de RH", "Coordenador(a) de RH", "HRBP", "Recrutador(a)", "Talent Acquisition", "Gerente de RH", "CHRO"],
    "legal": ["Advogado(a) Trabalhista", "Advogado(a) Civel", "Advogado(a) Tributario", "Gerente Juridico", "General Counsel", "Paralegal"],
    "compliance_audit": ["Analista de Compliance", "Auditor(a) Interno(a)", "Compliance Officer", "GRC Analyst", "Privacy Officer (DPO)"],
    "healthcare": ["Medico(a)", "Enfermeiro(a)", "Tecnico(a) em Enfermagem", "Auditor(a) Medico(a)", "Coordenador(a) de Saude"],
    "education": ["Professor(a)", "Coordenador(a) Pedagogico", "Diretor(a) Escolar", "Designer Instrucional", "Tutor(a) EAD"],
    "manufacturing": ["Analista de PCP", "Supervisor(a) de Producao", "Engenheiro(a) de Producao", "Gerente Industrial", "Operador(a) de Maquina"],
    "construction": ["Engenheiro(a) Civil", "Arquiteto(a)", "Engenheiro(a) de Obras", "Mestre de Obras", "Coordenador(a) de Projetos"],
    "agronegocio": ["Engenheiro(a) Agronomo", "Tecnico(a) Agricola", "Gerente de Fazenda", "Analista AgTech", "Zootecnista"],
    "security": ["Tecnico(a) de Seguranca do Trabalho", "Engenheiro(a) de Seguranca", "CISO", "Analista de Seguranca da Informacao", "Pentester"],
    "esg_sustainability": ["Analista ESG", "Coordenador(a) de Sustentabilidade", "Carbon Manager", "ESG Reporting Specialist", "Analista Ambiental"],
}

SKILLS_BY_AREA = {
    "engineering": ["Python", "JavaScript", "TypeScript", "React", "Node.js", "PostgreSQL", "AWS", "Docker", "Kubernetes", "Java", "Go", "GraphQL", "Redis", "Kafka", "Terraform", "CI/CD", "Git", "Linux", "FastAPI", "Django", "Next.js", "Vue.js"],
    "data": ["Python", "SQL", "Spark", "Airflow", "dbt", "Snowflake", "BigQuery", "Pandas", "NumPy", "Scikit-learn", "TensorFlow", "PyTorch", "MLflow", "Power BI", "Tableau", "Looker", "Databricks"],
    "product": ["Roadmap", "OKR", "Scrum", "Kanban", "Jira", "Figma", "Mixpanel", "Amplitude", "User Research", "A/B Testing", "Product Discovery", "JTBD"],
    "design": ["Figma", "Sketch", "Adobe XD", "Photoshop", "Illustrator", "After Effects", "Webflow", "Design System", "Prototipacao", "Pesquisa UX"],
    "sales": ["Salesforce", "HubSpot", "Pipedrive", "RD Station", "Outbound", "Inbound", "Cold Call", "Cold Mail", "Negociacao", "Forecast", "LinkedIn Sales Navigator"],
    "customer_experience": ["Zendesk", "Salesforce Service", "Freshdesk", "Intercom", "NPS", "CSAT", "Service Cloud", "Customer Success", "Onboarding"],
    "operations": ["Lean", "Six Sigma", "SAP", "Oracle", "Excel Avancado", "Power Query", "BPMN", "ISO 9001", "PDCA", "Kaizen"],
    "logistics": ["SAP MM/WM", "Excel Avancado", "WMS", "TMS", "Roteirizacao", "Curva ABC", "Lean Logistics", "Gestao de Frota"],
    "procurement": ["SAP Ariba", "Negociacao", "Sourcing", "Strategic Sourcing", "RFP", "RFQ", "Cotacao", "Gestao de Fornecedores"],
    "finance": ["Excel Avancado", "Power BI", "SAP FI", "Oracle", "FP&A", "Tesouraria", "Fluxo de Caixa", "Budget", "Forecast", "DRE", "Modelagem Financeira"],
    "accounting_tax": ["SAP", "SPED", "ECF", "ECD", "EFD", "Contabilidade Tributaria", "IRRF", "ICMS", "PIS/COFINS", "Bloco K", "Reinf"],
    "marketing": ["Google Ads", "Meta Ads", "RD Station", "HubSpot Marketing", "Google Analytics 4", "GTM", "SEO", "Midia Programatica", "Content Marketing", "Brand", "ASO"],
    "hr": ["Recrutamento e Selecao", "Folha de Pagamento", "Subsistemas RH", "DP", "Cargos e Salarios", "DISC", "MBTI", "T&D", "Onboarding", "HRBP", "Engagement"],
    "legal": ["Direito do Trabalho", "Direito Civel", "Direito Tributario", "Contratos", "Compliance", "LGPD", "Jurisprudencia", "PJe", "Contencioso"],
    "compliance_audit": ["SOX", "ISO 27001", "LGPD", "PCI-DSS", "ITGC", "Auditoria Interna", "COSO", "Controles Internos", "GRC", "FCPA"],
    "healthcare": ["Tasy", "MV", "Soul MV", "Glosas", "TISS", "TUSS", "Faturamento Hospitalar", "Auditoria Medica", "Protocolos Clinicos"],
    "education": ["Plataformas EAD", "Moodle", "Google Classroom", "Avaliacao Pedagogica", "Curriculo BNCC", "Gestao Escolar", "Tutoria Online"],
    "manufacturing": ["Lean Manufacturing", "MES", "OEE", "PCP", "PCM", "TPM", "Kaizen", "5S", "Six Sigma", "Manutencao Preditiva"],
    "construction": ["AutoCAD", "Revit", "MS Project", "Sienge", "Orcamento de Obras", "Cronograma Fisico-Financeiro", "NBR", "Norma Tecnica"],
    "agronegocio": ["Agronegocio", "Manejo de Solo", "Defensivos", "Agricultura de Precisao", "AgTech", "Pecuaria", "SENAR"],
    "security": ["NR-10", "NR-12", "NR-33", "NR-35", "CIPA", "SESMT", "Seguranca da Informacao", "ISO 27001", "Pentest", "SIEM"],
    "esg_sustainability": ["GRI", "TCFD", "SASB", "CDP", "Inventario GEE", "ESG Reporting", "Pacto Global", "ISE B3", "Carbon Footprint"],
}

CEFR_LEVELS = ["Basico", "Intermediario", "Avancado", "Fluente"]
WORK_MODELS = ["remoto", "hibrido", "presencial"]
CONTRACT_PREFS = ["CLT", "PJ", "Freelance/PJ", "Indiferente"]
EDUCATION_LEVELS_BY_AREA = {
    "manufacturing": ["Tecnico", "Bacharelado"],
    "construction": ["Tecnico", "Bacharelado"],
    "agronegocio": ["Tecnico", "Bacharelado"],
    "healthcare": ["Bacharelado", "Pos-graduacao", "Mestrado"],
    "education": ["Licenciatura", "Pos-graduacao", "Mestrado"],
}

def _gen_languages(rng):
    """PT nativo + EN (variado) + chance de outros idiomas."""
    langs = [{"language": "Portugues", "level": "Nativo"}]
    en_lvl = rng.choices(CEFR_LEVELS, weights=[15, 30, 35, 20])[0]
    langs.append({"language": "Ingles", "level": en_lvl})
    if rng.random() < 0.25:
        es_lvl = rng.choices(CEFR_LEVELS, weights=[40, 35, 20, 5])[0]
        langs.append({"language": "Espanhol", "level": es_lvl})
    if rng.random() < 0.05:
        extra = rng.choice(["Frances", "Alemao", "Italiano", "Mandarim"])
        langs.append({"language": extra, "level": rng.choice(["Basico", "Intermediario"])})
    return langs


def _gen_headline(rng, dept, seniority, years):
    title = rng.choice(TITLES_BY_AREA.get(dept, ["Profissional"]))
    return f"{seniority} {title} - {years}+ anos de experiencia"


def _avatar_url(seed_uuid):
    """DiceBear personas — SVG humanizado, LGPD-safe, gratuito."""
    return f"https://api.dicebear.com/9.x/personas/svg?seed={seed_uuid}"


def _vacancy_tech_requirements(dept: str):
    default = [
        {"skill": "Comunicação escrita", "level": "intermediário", "weight": 0.4},
        {"skill": "Excel / Google Sheets", "level": "intermediário", "weight": 0.3},
        {"skill": "Ferramentas de gestão", "level": "básico", "weight": 0.3},
    ]
    return DEPT_TECH_MAP.get(dept, default)


def _vacancy_behavioral_competencies(seniority: str):
    return SENIORITY_BEHAVIORAL_MAP.get(seniority, SENIORITY_BEHAVIORAL_MAP["Pleno"])


FIRST_NAMES = [
    "Ana", "Beatriz", "Carlos", "Daniel", "Eduardo", "Fernanda", "Gabriel", "Helena",
    "Igor", "Julia", "Karen", "Leonardo", "Mariana", "Nicolas", "Olivia", "Paulo",
    "Renata", "Samuel", "Tatiana", "Vinicius", "Wagner", "Yasmin", "Bruna", "Caio",
    "Débora", "Enzo", "Fabiana", "Gustavo", "Isabela", "João", "Larissa", "Mateus",
    "Natália", "Otávio", "Patrícia", "Rafael", "Sofia", "Thiago", "Vanessa", "Wesley",
    "Amanda", "Bruno", "Carla", "Diego", "Elaine", "Felipe", "Gabriela", "Henrique",
    "Iris", "Juliana",
]

LAST_NAMES = [
    "Silva", "Santos", "Oliveira", "Souza", "Rodrigues", "Ferreira", "Almeida", "Costa",
    "Pereira", "Carvalho", "Gomes", "Martins", "Araújo", "Melo", "Barbosa", "Ribeiro",
    "Lima", "Rocha", "Correia", "Nascimento", "Dias", "Moreira", "Vieira", "Lopes",
    "Freitas", "Monteiro", "Cardoso", "Mendes", "Barros", "Pinto", "Reis", "Teixeira",
    "Castro", "Duarte", "Campos", "Andrade", "Moura", "Nunes", "Marques", "Fonseca",
]

TECH_SKILLS_POOL = [
    "Python", "JavaScript", "TypeScript", "React", "Node.js", "PostgreSQL", "MongoDB",
    "AWS", "Docker", "Kubernetes", "Java", "Go", "Rust", "C#", ".NET", "GraphQL",
    "Redis", "Kafka", "Terraform", "CI/CD", "Git", "Linux", "SQL", "NoSQL",
    "FastAPI", "Django", "Flask", "Next.js", "Vue.js", "Angular", "TailwindCSS",
    "Figma", "Sketch", "Adobe XD", "Photoshop", "Illustrator",
    "Power BI", "Tableau", "Spark", "Airflow", "dbt", "Snowflake", "BigQuery",
    "Pandas", "NumPy", "Scikit-learn", "TensorFlow", "PyTorch", "MLflow",
    "Scrum", "Kanban", "SAP", "Salesforce", "HubSpot", "Google Analytics",
]

SOFT_SKILLS = [
    "Comunicação", "Liderança", "Trabalho em equipe", "Resolução de problemas",
    "Pensamento crítico", "Adaptabilidade", "Criatividade", "Gestão de tempo",
    "Negociação", "Empatia", "Proatividade", "Resiliência",
]

COMPANIES_BR = [
    "Nubank", "iFood", "Magazine Luiza", "Stone", "PagSeguro", "Mercado Livre",
    "VTEX", "Totvs", "Locaweb", "Movile", "CI&T", "Dasa", "Loft", "QuintoAndar",
    "Gympass (Wellhub)", "Wildlife Studios", "Creditas", "Neon", "Inter", "XP Inc",
    "Itaú Unibanco", "Bradesco", "Ambev", "Vale", "Petrobras", "Embraer",
    "Natura", "Boticário", "B3", "Globo", "Accenture Brasil", "IBM Brasil",
    "ThoughtWorks", "Resultados Digitais (RD Station)", "Hotmart",
]

UNIVERSITIES_BR = [
    ("Universidade de São Paulo", "USP", "São Paulo", "SP"),
    ("Universidade Estadual de Campinas", "UNICAMP", "Campinas", "SP"),
    ("Universidade Federal do Rio de Janeiro", "UFRJ", "Rio de Janeiro", "RJ"),
    ("Universidade Federal de Minas Gerais", "UFMG", "Belo Horizonte", "MG"),
    ("Pontifícia Universidade Católica de São Paulo", "PUC-SP", "São Paulo", "SP"),
    ("Pontifícia Universidade Católica do Rio de Janeiro", "PUC-Rio", "Rio de Janeiro", "RJ"),
    ("Universidade Federal do Rio Grande do Sul", "UFRGS", "Porto Alegre", "RS"),
    ("Universidade Federal de Santa Catarina", "UFSC", "Florianópolis", "SC"),
    ("Universidade Federal de Pernambuco", "UFPE", "Recife", "PE"),
    ("Instituto Tecnológico de Aeronáutica", "ITA", "São José dos Campos", "SP"),
    ("Fundação Getulio Vargas", "FGV", "São Paulo", "SP"),
    ("Insper", "Insper", "São Paulo", "SP"),
    ("Universidade Federal da Bahia", "UFBA", "Salvador", "BA"),
    ("Universidade Federal do Paraná", "UFPR", "Curitiba", "PR"),
    ("SENAC", "SENAC", "São Paulo", "SP"),
    ("Universidade Presbiteriana Mackenzie", "Mackenzie", "São Paulo", "SP"),
]

DEGREES = ["Bacharelado", "Licenciatura", "Tecnólogo", "Mestrado", "MBA", "Pós-graduação"]
FIELDS_OF_STUDY = [
    "Ciência da Computação", "Engenharia de Software", "Sistemas de Informação",
    "Administração", "Economia", "Engenharia Elétrica", "Engenharia Mecânica",
    "Design", "Comunicação Social", "Psicologia", "Direito", "Contabilidade",
    "Marketing", "Gestão de RH", "Engenharia de Produção", "Matemática", "Estatística",
]

# (cidade, UF, peso) — peso proxy de populacao + hub profissional
CITIES = [
    ("São Paulo", "SP", 100), ("Rio de Janeiro", "RJ", 60), ("Belo Horizonte", "MG", 40),
    ("Curitiba", "PR", 30), ("Porto Alegre", "RS", 30), ("Brasília", "DF", 25),
    ("Salvador", "BA", 22), ("Recife", "PE", 20), ("Fortaleza", "CE", 18),
    ("Florianópolis", "SC", 18), ("Campinas", "SP", 15), ("Manaus", "AM", 10),
    ("Goiânia", "GO", 10), ("Belém", "PA", 8), ("São Bernardo do Campo", "SP", 8),
    ("Guarulhos", "SP", 8), ("Vitória", "ES", 8), ("São Luís", "MA", 6),
    ("João Pessoa", "PB", 6), ("Maceió", "AL", 6), ("Natal", "RN", 6),
    ("Teresina", "PI", 5), ("Cuiabá", "MT", 5), ("Campo Grande", "MS", 5),
    ("Aracaju", "SE", 4), ("Boa Vista", "RR", 2), ("Rio Branco", "AC", 2),
    ("Macapá", "AP", 2), ("Palmas", "TO", 2), ("Porto Velho", "RO", 2),
    ("Joinville", "SC", 6), ("Londrina", "PR", 6), ("Ribeirão Preto", "SP", 6),
    ("Sorocaba", "SP", 5), ("Caxias do Sul", "RS", 4), ("Niterói", "RJ", 6),
    ("Uberlândia", "MG", 5), ("Juiz de Fora", "MG", 4), ("Feira de Santana", "BA", 4),
    ("São José dos Campos", "SP", 6), ("Santos", "SP", 5),
]

# JOB_VACANCIES + VACANCY_IDS — agora que CITIES + TITLES_BY_AREA + DEPT_WEIGHTS estao prontos
JOB_VACANCIES = _gen_job_vacancies(80)
VACANCY_IDS = [_seed_uuid(f"vacancy:{i}:{v['title']}") for i, v in enumerate(JOB_VACANCIES)]


SEED_SOURCE = "seed_script"
import random as _rng
_CANDIDATE_RNG = _rng.Random(42)

def _generate_candidates(count: int):
    rng = _CANDIDATE_RNG
    candidates = []
    used_names = set()
    dept_list = list(DEPT_WEIGHTS.keys())
    dept_weights = list(DEPT_WEIGHTS.values())
    cities_weighted = [(c[0], c[1]) for c in CITIES]
    city_weights = [c[2] for c in CITIES]

    for i in range(count):
        while True:
            fn = rng.choice(FIRST_NAMES)
            ln = rng.choice(LAST_NAMES)
            name = f"{fn} {ln}"
            if name not in used_names:
                used_names.add(name)
                break

        # Area canonical do candidato (peso realista do mercado BR)
        dept = rng.choices(dept_list, weights=dept_weights)[0]

        # Senioridade derivada do tempo de mercado (bell-ish)
        yrs = rng.choices(
            list(range(0, 30)),
            weights=[3, 5, 8, 10, 12, 13, 12, 10, 8, 6, 5, 4, 3, 3, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        )[0]
        if yrs <= 1:
            seniority = "Estagiario" if rng.random() < 0.4 else "Junior"
        elif yrs <= 3:
            seniority = "Junior"
        elif yrs <= 7:
            seniority = "Pleno"
        elif yrs <= 12:
            seniority = "Senior"
        else:
            seniority = "Especialista"

        city, state = rng.choices(cities_weighted, weights=city_weights)[0]

        email_base = (
            f"{fn.lower()}.{ln.lower()}"
            .replace("á","a").replace("ã","a").replace("â","a")
            .replace("é","e").replace("ê","e")
            .replace("í","i").replace("ó","o").replace("ô","o").replace("õ","o")
            .replace("ú","u").replace("ç","c")
        )
        email = f"{email_base}{rng.randint(1,999)}@email.com"

        # Titulo por area
        title_pool = TITLES_BY_AREA.get(dept, ["Profissional"])
        title = rng.choice(title_pool)

        # Skills por area (mais ricas)
        skills_pool = SKILLS_BY_AREA.get(dept, TECH_SKILLS_POOL)
        skills_count = min(rng.randint(5, 12), len(skills_pool))
        technical_skills = rng.sample(skills_pool, skills_count)

        # Soft skills (3-6)
        soft_skills = rng.sample(SOFT_SKILLS, rng.randint(3, 6))

        # Salary por seniority + area
        sal_min_base, sal_max_base = _BASE_SALARY.get(seniority, _BASE_SALARY["Pleno"])
        factor = _AREA_SALARY_FACTOR.get(dept, 1.0)
        sal_current = round(sal_min_base * factor * rng.uniform(0.9, 1.15), 2)
        sal_min = round(sal_current * rng.uniform(1.05, 1.15), 2)
        sal_max = round(sal_min * rng.uniform(1.20, 1.45), 2)

        # Mobility / work model preference
        work_model_pref = rng.choices(WORK_MODELS, weights=[35, 45, 20])[0]
        willing_to_relocate = rng.random() < 0.18
        # mobility = abertura a mudar (boolean canonical na tabela)
        mobility = willing_to_relocate or (work_model_pref == "remoto" and rng.random() < 0.3)
        is_remote_pref = work_model_pref == "remoto"
        contract_pref = rng.choices(CONTRACT_PREFS, weights=[55, 25, 10, 10])[0]

        # LIA score — bell curve canonical
        lia_score = max(20.0, min(99.0, rng.gauss(65, 14)))

        # Languages, headline, expertise, certifications
        languages = _gen_languages(rng)
        headline = _gen_headline(rng, dept, seniority, yrs)
        cand_uuid = _seed_uuid(f"candidate:{i}")
        avatar_url = _avatar_url(cand_uuid)
        expertise = [DEPT_DISPLAY.get(dept, dept).title()]

        # Self-introduction breve
        self_intro = (
            f"Profissional {seniority} em {DEPT_DISPLAY.get(dept, dept).title()} "
            f"com {yrs} anos de experiencia. Atualmente como {title}. "
            f"Forte em {', '.join(technical_skills[:3])}."
        )

        is_open_to_work = rng.random() < 0.55  # 55% open to work

        candidates.append({
            "id": cand_uuid,
            "name": name,
            "email": email,
            "phone": f"+55 {rng.choice([11,21,31,41,51,61,71,81])} 9{rng.randint(1000,9999)}-{rng.randint(1000,9999)}",
            "city": city,
            "state": state,
            "current_company": rng.choice(COMPANIES_BR),
            "current_title": title,
            "headline": headline,
            "self_introduction": self_intro,
            "expertise": expertise,
            "seniority": seniority,
            "years_of_experience": yrs,
            "department_focus": dept,
            "technical_skills": technical_skills,
            "soft_skills": soft_skills,
            "languages": languages,
            "avatar_url": avatar_url,
            "source": SEED_SOURCE,
            "salary_current": sal_current,
            "salary_min": sal_min,
            "salary_max": sal_max,
            "lia_score": round(lia_score, 1),
            "mobility": mobility,
            "willing_to_relocate": willing_to_relocate,
            "is_remote": is_remote_pref,
            "work_model_preference": work_model_pref,
            "contract_type_preference": contract_pref,
            "is_open_to_work": is_open_to_work,
            "linkedin_url": f"https://linkedin.com/in/{email_base}-{rng.randint(100,999)}",
            "created_at": _past(5, 240),
        })
    return candidates


CANDIDATES = _generate_candidates(300)
CANDIDATE_IDS = [c["id"] for c in CANDIDATES]


async def seed_client_account(db: AsyncSession):
    logger.info("Seeding ClientAccount...")
    existing = await db.execute(
        text("SELECT id FROM client_accounts WHERE id = :id"),
        {"id": SEED_COMPANY_ID},
    )
    if existing.fetchone():
        # Expansao 2026-05-11: garantir nome canonical mesmo quando ja existe
        await db.execute(text("""
            UPDATE client_accounts SET name = :name, trade_name = :trade, updated_at = :now
            WHERE id = :id
        """), {
            "name": "WeDOTalent Demo",
            "trade": "WeDOTalent Demo — Ambiente de Demonstracao",
            "now": NOW, "id": SEED_COMPANY_ID,
        })
        logger.info("  ClientAccount exists — renamed to 'WeDOTalent Demo'.")
        return
    await db.execute(text("""
        INSERT INTO client_accounts (id, name, trade_name, cnpj, primary_email, primary_phone, website, status, plan_id,
            contract_start_date, contract_end_date, user_limit, job_limit, ai_credits_monthly, industry, company_size,
            created_at, updated_at, is_deleted, welcome_email_sent, workos_organization_created, sso_configured)
        VALUES (:id, :name, :trade_name, :cnpj, :email, :phone, :website, :status, :plan,
            :start, :end, :user_limit, :job_limit, :credits, :industry, :size,
            :now, :now, false, true, false, false)
    """), {
        "id": SEED_COMPANY_ID, "name": "WeDOTalent Demo", "trade_name": "WeDOTalent Demo — Ambiente de Demonstracao",
        "cnpj": "12.345.678/0001-90", "email": "contato@wedotalent.cc", "phone": "+55 11 3456-7890",
        "website": "https://wedotalent.cc", "status": "active", "plan": "enterprise",
        "start": NOW - timedelta(days=365), "end": NOW + timedelta(days=365),
        "user_limit": 50, "job_limit": 200, "credits": 5000,
        "industry": "Tecnologia", "size": "medium", "now": NOW,
    })
    logger.info("  ClientAccount created.")


async def seed_company_profile(db: AsyncSession):
    logger.info("Seeding CompanyProfile...")
    existing = await db.execute(
        text("SELECT id FROM company_profiles WHERE id = :id"),
        {"id": SEED_COMPANY_PROFILE_ID},
    )
    if existing.fetchone():
        logger.info("  CompanyProfile already exists, skipping.")
        return
    await db.execute(text("""
        INSERT INTO company_profiles (id, name, trading_name, website, cnpj, industry, sector,
            company_size, founded_year, description, short_description, headquarters_city, headquarters_state,
            headquarters_country, main_phone, hr_email, employee_count, is_active, is_default,
            created_at, updated_at)
        VALUES (:id, :name, :trade, :web, :cnpj, :industry, :sector,
            :size, :year, :desc, :short, :city, :state, :country, :phone, :hr_email,
            :count, true, true, :now, :now)
    """), {
        "id": SEED_COMPANY_PROFILE_ID,
        "name": "WeDo Talent", "trade": "WeDo Talent Tecnologia Ltda",
        "web": "https://wedotalent.cc", "cnpj": "12.345.678/0001-90",
        "industry": "Tecnologia", "sector": "HR Tech", "size": "medium",
        "year": 2020, "desc": "Plataforma de recrutamento inteligente com IA que conecta empresas aos melhores talentos do mercado brasileiro. Utilizamos inteligência artificial para otimizar todo o processo de seleção, desde a triagem até a contratação.",
        "short": "Plataforma de recrutamento inteligente com IA",
        "city": "São Paulo", "state": "São Paulo", "country": "Brasil",
        "phone": "+55 11 3456-7890", "hr_email": "rh@wedotalent.cc",
        "count": 85, "now": NOW,
    })
    logger.info("  CompanyProfile created.")


async def seed_departments(db: AsyncSession):
    logger.info("Seeding Departments...")
    dept_info = [
        ("engineering", "Engenharia",  "ENG", "Desenvolvimento de software e infraestrutura", 25),
        ("product",     "Produto",     "PRD", "Gestão de produto e estratégia",                8),
        ("design",      "Design",      "DES", "UX/UI e Design de produto",                    6),
        ("data",        "Dados & IA",  "DAT", "Ciência de dados e Machine Learning",           10),
        ("hr",          "Recursos Humanos", "RH", "Gestão de pessoas e cultura",               7),
        ("finance",     "Financeiro",  "FIN", "Contabilidade e planejamento financeiro",        5),
        ("sales",       "Vendas",      "VEN", "Vendas enterprise e inside sales",              12),
        ("marketing",   "Marketing",   "MKT", "Marketing digital e growth",                    6),
        ("legal",       "Jurídico",    "JUR", "Compliance e assessoria jurídica",               3),
        ("operations",  "Operações",   "OPS", "Operações e suporte ao cliente",                 8),
    ]
    for key, name, code, desc, headcount in dept_info:
        did = DEPT_IDS[key]
        existing = await db.execute(text("SELECT id FROM departments WHERE id = :id"), {"id": did})
        if existing.fetchone():
            continue
        await db.execute(text("""
            INSERT INTO departments (id, company_id, name, code, description, headcount, is_active, created_at, updated_at, "order", hiring_priority)
            VALUES (:id, :cid, :name, :code, :desc, :hc, true, :now, :now, :ord, :pri)
        """), {
            "id": did, "cid": SEED_COMPANY_PROFILE_ID, "name": name, "code": code,
            "desc": desc, "hc": headcount, "now": NOW, "ord": dept_info.index((key, name, code, desc, headcount)),
            "pri": "alta" if key in ("engineering", "data") else "normal",
        })
    logger.info(f"  {len(dept_info)} departments seeded.")


async def seed_benefits(db: AsyncSession):
    logger.info("Seeding Benefits...")
    count = 0
    for b in BENEFITS_DATA:
        bid = _uuid()
        existing = await db.execute(
            text("SELECT id FROM benefits WHERE company_id = :cid AND name = :name"),
            {"cid": SEED_COMPANY_PROFILE_ID, "name": b["name"]},
        )
        if existing.fetchone():
            continue
        vt = b.get("value_type", "monetary")
        await db.execute(text("""
            INSERT INTO benefits (id, company_id, name, category, icon, value, value_type, percentage_value,
                is_active, is_highlighted, is_mandatory, created_at, updated_at, "order")
            VALUES (:id, :cid, :name, :cat, :icon, :val, :vt, :pct, true, :hl, :mand, :now, :now, :ord)
        """), {
            "id": bid, "cid": SEED_COMPANY_PROFILE_ID, "name": b["name"], "cat": b["category"],
            "icon": b.get("icon"), "val": b.get("value"), "vt": vt,
            "pct": b.get("percentage"), "hl": b["name"] in ("Plano de Saúde", "PLR"),
            "mand": b["name"] in ("Vale Refeição", "Plano de Saúde"), "now": NOW,
            "ord": BENEFITS_DATA.index(b),
        })
        count += 1
    logger.info(f"  {count} benefits seeded.")


async def seed_culture_values(db: AsyncSession):
    logger.info("Seeding CultureValues...")
    count = 0
    for cv in CULTURE_VALUES:
        existing = await db.execute(
            text("SELECT id FROM culture_values WHERE company_id = :cid AND name = :name"),
            {"cid": SEED_COMPANY_PROFILE_ID, "name": cv["name"]},
        )
        if existing.fetchone():
            continue
        await db.execute(text("""
            INSERT INTO culture_values (id, company_id, name, description, category, icon, color, weight, is_active, created_at, updated_at, "order")
            VALUES (:id, :cid, :name, :desc, :cat, :icon, :color, 1.0, true, :now, :now, :ord)
        """), {
            "id": _uuid(), "cid": SEED_COMPANY_PROFILE_ID, "name": cv["name"],
            "desc": cv["description"], "cat": cv["category"], "icon": cv["icon"],
            "color": cv["color"], "now": NOW, "ord": CULTURE_VALUES.index(cv),
        })
        count += 1
    logger.info(f"  {count} culture values seeded.")


async def seed_client_users(db: AsyncSession):
    logger.info("Seeding ClientUsers...")
    count = 0
    for i, u in enumerate(CLIENT_USERS):
        uid = USER_IDS[i]
        existing = await db.execute(
            text("SELECT id FROM client_users WHERE company_id = :cid AND email = :email"),
            {"cid": SEED_COMPANY_ID, "email": u["email"]},
        )
        if existing.fetchone():
            continue
        await db.execute(text("""
            INSERT INTO client_users (id, company_id, email, name, role, status, invited_at, accepted_at,
                last_login_at, created_at, updated_at, is_deleted)
            VALUES (:id, :cid, :email, :name, :role, :status, :inv, :acc, :login, :now, :now, false)
        """), {
            "id": uid, "cid": SEED_COMPANY_ID, "email": u["email"], "name": u["name"],
            "role": u["role"], "status": u["status"],
            "inv": _past(60, 180), "acc": _past(1, 59) if u["status"] == "active" else None,
            "login": _past(0, 3) if u["status"] == "active" else None, "now": NOW,
        })
        count += 1
    logger.info(f"  {count} client users seeded.")


async def seed_recruitment_stages(db: AsyncSession):
    logger.info("Seeding RecruitmentStages...")
    count = 0
    for s in STAGE_DEFS:
        sid = STAGE_IDS[s["name"]]
        existing = await db.execute(
            text("SELECT id FROM recruitment_stages WHERE company_id = :cid AND name = :name"),
            {"cid": SEED_COMPANY_ID_STR, "name": s["name"]},
        )
        if existing.fetchone():
            continue
        await db.execute(text("""
            INSERT INTO recruitment_stages (id, company_id, name, display_name, stage_order, color, icon,
                stage_type, is_initial, is_final, is_rejection, is_hired, is_active, is_system,
                stage_category, action_behavior, created_at, updated_at)
            VALUES (:id, :cid, :name, :dn, :ord, :color, :icon, :type, :init, :final, :rej, :hired,
                true, :sys, :cat, :beh, :now, :now)
        """), {
            "id": sid, "cid": SEED_COMPANY_ID_STR, "name": s["name"], "dn": s["display_name"],
            "ord": s["order"], "color": s["color"], "icon": s["icon"], "type": s["type"],
            "init": s.get("is_initial", False), "final": s.get("is_final", False),
            "rej": s.get("is_rejection", False), "hired": s.get("is_hired", False),
            "sys": s["cat"] == "system", "cat": s["cat"], "beh": s["behavior"], "now": NOW,
        })
        count += 1
    logger.info(f"  {count} recruitment stages seeded.")


async def seed_job_vacancies(db: AsyncSession):
    logger.info("Seeding JobVacancies...")
    count = 0
    for i, j in enumerate(JOB_VACANCIES):
        vid = VACANCY_IDS[i]
        existing = await db.execute(text("SELECT id FROM job_vacancies WHERE id = :id"), {"id": vid})
        if existing.fetchone():
            continue
        job_id = f"WDT-2025-{(i+1):03d}"
        recruiter = choice(["rafael.mendes@wedotalent.cc", "camila.oliveira@wedotalent.cc"])
        open_date = _past(10, 60)
        deadline = open_date + timedelta(days=randint(30, 90))
        salary_json = json.dumps({"min": j["salary_min"], "max": j["salary_max"], "currency": "BRL"})
        tech_reqs = _vacancy_tech_requirements(j["dept"])
        behav_comps = _vacancy_behavioral_competencies(j["seniority"])
        reqs_list = [r["skill"] for r in tech_reqs[:3]]
        await db.execute(text("""
            INSERT INTO job_vacancies (id, company_id, job_id, title, department, location, work_model,
                employment_type, seniority_level, description, salary_range, status, stage, priority,
                urgency_level, open_date, deadline, recruiter_email, manager, created_by, visibility,
                requirements, technical_requirements, behavioral_competencies,
                created_at, updated_at, is_pipeline_customized)
            VALUES (:id, :cid, :jid, :title, :dept, :loc, :model, :etype, :sen, :desc,
                cast(:salary as jsonb), :status, :stage, :pri, :urg, :open, :dead, :rec, :mgr, :cb,
                'public', :reqs, cast(:tech_reqs as json), cast(:behav as json),
                :created, :now, false)
        """), {
            "id": vid, "cid": SEED_COMPANY_ID_STR, "jid": job_id, "title": j["title"],
            "dept": j["dept"].replace("_", " ").title(), "loc": j["location"], "model": j["model"],
            "etype": j["type"], "sen": j["seniority"],
            "desc": f"Estamos buscando um(a) {j['title']} para integrar nosso time de {j['dept'].replace('_',' ').title()}. "
                    f"Modelo de trabalho: {j['model']}. Contratação: {j['type']}.",
            "salary": salary_json,
            "status": j["status"], "stage": "Publicada" if j["status"] == "Ativa" else "Planejamento",
            "pri": j["priority"], "urg": {"alta": 5, "média": 3, "baixa": 1}[j["priority"]],
            "open": open_date, "dead": deadline, "rec": recruiter,
            "mgr": "Lucas Ferreira", "cb": "ana.costa@wedotalent.cc",
            "reqs": reqs_list,
            "tech_reqs": json.dumps(tech_reqs),
            "behav": json.dumps(behav_comps),
            "created": open_date, "now": NOW,
        })
        count += 1
    logger.info(f"  {count} job vacancies seeded.")


async def seed_candidates(db: AsyncSession):
    logger.info("Seeding Candidates...")
    count = 0
    for c in CANDIDATES:
        existing = await db.execute(text("SELECT id FROM candidates WHERE id = :id"), {"id": c["id"]})
        if existing.fetchone():
            continue
        await db.execute(text("""
            INSERT INTO candidates (id, company_id, name, email, phone, location_city, location_state, location_country,
                current_company, current_title, seniority_level, years_of_experience,
                technical_skills, soft_skills, languages, expertise, certifications,
                source, current_salary, desired_salary_min, desired_salary_max,
                linkedin_url, avatar_url, headline, self_introduction,
                is_remote, willing_to_relocate, mobility, work_model_preference,
                contract_type_preference, is_open_to_work, lia_score,
                status, is_active, salary_currency,
                created_at, updated_at)
            VALUES (:id, :cid, :name, :email, :phone, :city, :state, 'Brasil',
                :company, :title, :seniority, :yrs,
                :tech, :soft, cast(:languages as json), :expertise, ARRAY[]::varchar[],
                :source, :sal, :sal_min, :sal_max,
                :li, :avatar, :headline, :intro,
                :is_remote, :willing_reloc, :mobility, :work_model,
                :contract_pref, :open_to_work, :lia_score,
                'active', true, 'BRL',
                :created, :now)
            ON CONFLICT (id) DO NOTHING
        """), {
            "cid": SEED_COMPANY_ID_STR,
            "id": c["id"], "name": c["name"], "email": c["email"], "phone": c["phone"],
            "city": c["city"], "state": c["state"], "company": c["current_company"],
            "title": c["current_title"], "seniority": c["seniority"], "yrs": c["years_of_experience"],
            "tech": c["technical_skills"],
            "soft": c["soft_skills"],
            "languages": json.dumps(c["languages"]),
            "expertise": c["expertise"],
            "source": c["source"], "sal": c["salary_current"],
            "sal_min": c["salary_min"], "sal_max": c["salary_max"],
            "li": c["linkedin_url"], "avatar": c["avatar_url"],
            "headline": c["headline"], "intro": c["self_introduction"],
            "is_remote": c["is_remote"], "willing_reloc": c["willing_to_relocate"],
            "mobility": c["mobility"], "work_model": c["work_model_preference"],
            "contract_pref": c["contract_type_preference"], "open_to_work": c["is_open_to_work"],
            "lia_score": c["lia_score"],
            "created": c["created_at"], "now": NOW,
        })
        count += 1
    logger.info(f"  {count} candidates seeded.")


async def seed_candidate_experiences(db: AsyncSession):
    logger.info("Seeding CandidateExperiences...")
    count = 0
    for c in CANDIDATES:
        existing = await db.execute(
            text("SELECT id FROM candidate_experiences WHERE candidate_id = :cid LIMIT 1"),
            {"cid": c["id"]},
        )
        if existing.fetchone():
            continue
        num_exp = randint(1, 4)
        for seq in range(num_exp):
            company = choice(COMPANIES_BR)
            start_year = 2024 - c["years_of_experience"] + seq * 2
            end_year = start_year + randint(1, 3) if seq < num_exp - 1 else None
            is_current = seq == num_exp - 1
            await db.execute(text("""
                INSERT INTO candidate_experiences (id, candidate_id, company_name, title, start_date, end_date,
                    is_current, location, industries, sequence_order, created_at, updated_at)
                VALUES (:id, :cid, :comp, :title, :start, :end, :cur, :loc, :ind, :seq, :now, :now)
            """), {
                "id": _uuid(), "cid": c["id"], "comp": company,
                "title": c["current_title"] if is_current else choice([
                    "Analista", "Desenvolvedor", "Coordenador", "Especialista", "Consultor",
                ]),
                "start": f"{start_year}-01", "end": f"{end_year}-12" if end_year else None,
                "cur": is_current, "loc": f"{c['city']}, {c['state']}",
                "ind": ["Tecnologia"], "seq": seq, "now": NOW,
            })
            count += 1
    logger.info(f"  {count} candidate experiences seeded.")


async def seed_candidate_education(db: AsyncSession):
    logger.info("Seeding CandidateEducation...")
    count = 0
    for c in CANDIDATES:
        existing = await db.execute(
            text("SELECT id FROM candidate_education WHERE candidate_id = :cid LIMIT 1"),
            {"cid": c["id"]},
        )
        if existing.fetchone():
            continue
        num_edu = randint(1, 2)
        for seq in range(num_edu):
            uni_name, uni_short, uni_city, uni_state = choice(UNIVERSITIES_BR)
            await db.execute(text("""
                INSERT INTO candidate_education (id, candidate_id, institution, degree, field_of_study,
                    start_date, end_date, is_completed, institution_city, institution_state, institution_country,
                    sequence_order, created_at, updated_at)
                VALUES (:id, :cid, :inst, :deg, :field, :start, :end, true, :city, :state, 'Brasil', :seq, :now, :now)
            """), {
                "id": _uuid(), "cid": c["id"], "inst": uni_name,
                "deg": choice(DEGREES), "field": choice(FIELDS_OF_STUDY),
                "start": f"{2024 - c['years_of_experience'] - 4 + seq*2}-02",
                "end": f"{2024 - c['years_of_experience'] + seq*2}-12",
                "city": uni_city, "state": uni_state, "seq": seq, "now": NOW,
            })
            count += 1
    logger.info(f"  {count} education records seeded.")


async def seed_vacancy_candidates(db: AsyncSession):
    logger.info("Seeding VacancyCandidates (pipeline)...")
    existing = await db.execute(
        text("SELECT id FROM vacancy_candidates WHERE company_id = :cid LIMIT 1"),
        {"cid": SEED_COMPANY_ID_STR},
    )
    if existing.fetchone():
        logger.info("  VacancyCandidates already exist, skipping.")
        return
    count = 0
    active_vacancy_indices = [i for i, j in enumerate(JOB_VACANCIES) if j["status"] == "Ativa"]
    concluded_idx = [i for i, j in enumerate(JOB_VACANCIES) if j["status"] == "Concluída"]

    stage_names_ordered = ["sourcing", "screening", "long_list", "short_list", "interview_hr",
                           "technical_test", "interview_technical", "interview_manager", "offer", "hired"]

    candidate_pool = list(CANDIDATES)
    assignment_idx = 0

    for vi in active_vacancy_indices + concluded_idx:
        vid = VACANCY_IDS[vi]
        num_candidates = randint(8, 18) if vi in active_vacancy_indices else randint(15, 25)
        selected = candidate_pool[assignment_idx:assignment_idx + num_candidates]
        if len(selected) < num_candidates:
            selected = candidate_pool[:num_candidates]
            assignment_idx = num_candidates
        else:
            assignment_idx += num_candidates

        for ci, cand in enumerate(selected):
            existing = await db.execute(
                text("SELECT id FROM vacancy_candidates WHERE vacancy_id = :vid AND candidate_id = :cid"),
                {"vid": vid, "cid": cand["id"]},
            )
            if existing.fetchone():
                continue

            if vi in concluded_idx:
                if ci == 0:
                    status, stage = "hired", "hired"
                elif ci < 3:
                    status, stage = "offer", "offer"
                else:
                    status, stage = "not_selected", "rejected"
            else:
                progress = ci / max(len(selected) - 1, 1)
                if progress < 0.2:
                    stage = choice(["interview_manager", "offer"])
                    status = "approved"
                elif progress < 0.4:
                    stage = choice(["interview_hr", "interview_technical"])
                    status = "approved"
                elif progress < 0.6:
                    stage = choice(["screening", "long_list", "short_list"])
                    status = "screening"
                elif progress < 0.8:
                    stage = "sourcing"
                    status = "sourced"
                else:
                    stage = choice(["screening", "interview_hr"])
                    status = "rejected"

            vc_id = _uuid()
            lia_score = round(uniform(40, 98), 1)
            match_pct = round(uniform(50, 95), 1)
            added = _past(2, 45)

            await db.execute(text("""
                INSERT INTO vacancy_candidates (id, vacancy_id, candidate_id, company_id, source, origin,
                    lia_score, match_percentage, status, stage, added_by, created_at, updated_at, stage_entered_at)
                VALUES (:id, :vid, :cid, :comp, :src, 'web', :score, :match, :status, :stage,
                    :added_by, :created, :now, :entered)
            """), {
                "id": vc_id, "vid": vid, "cid": cand["id"], "comp": SEED_COMPANY_ID_STR,
                "src": cand["source"], "score": lia_score, "match": match_pct,
                "status": status, "stage": stage,
                "added_by": choice(["rafael.mendes@wedotalent.cc", "camila.oliveira@wedotalent.cc", "lia_agent"]),
                "created": added, "now": NOW, "entered": added + timedelta(days=randint(0, 5)),
            })
            count += 1
    logger.info(f"  {count} vacancy-candidate associations seeded.")


async def seed_stage_history(db: AsyncSession):
    logger.info("Seeding CandidateStageHistory...")
    existing = await db.execute(
        text("SELECT id FROM candidate_stage_history WHERE company_id = :cid LIMIT 1"),
        {"cid": SEED_COMPANY_ID_STR},
    )
    if existing.fetchone():
        logger.info("  StageHistory already exists, skipping.")
        return
    count = 0
    stage_order_map = {s["name"]: s["order"] for s in STAGE_DEFS}
    stage_progression = ["sourcing", "screening", "long_list", "short_list", "interview_hr",
                         "technical_test", "interview_technical", "interview_manager", "offer", "hired"]

    rows = await db.execute(
        text("SELECT id, vacancy_id, candidate_id, stage, company_id FROM vacancy_candidates WHERE company_id = :cid"),
        {"cid": SEED_COMPANY_ID_STR},
    )
    vcs = rows.fetchall()

    for vc in vcs:
        vc_id, vacancy_id, candidate_id, current_stage, company_id = vc
        existing = await db.execute(
            text("SELECT id FROM candidate_stage_history WHERE vacancy_candidate_id = :vcid LIMIT 1"),
            {"vcid": vc_id},
        )
        if existing.fetchone():
            continue

        if current_stage not in stage_progression:
            target_idx = 0
        else:
            target_idx = stage_progression.index(current_stage)

        prev_stage = None
        base_time = _past(30, 60)

        for step in range(target_idx + 1):
            stage_name = stage_progression[step]
            sid = STAGE_IDS.get(stage_name)
            if not sid:
                continue
            transition_time = base_time + timedelta(days=step * randint(2, 5))
            hours_in_prev = round(uniform(4, 72), 1) if prev_stage else None

            await db.execute(text("""
                INSERT INTO candidate_stage_history (id, vacancy_candidate_id, vacancy_id, candidate_id, company_id,
                    from_stage_id, from_stage_name, to_stage_id, to_stage_name,
                    transition_type, triggered_by, time_in_previous_stage_hours, created_at)
                VALUES (:id, :vcid, :vid, :cid, :comp,
                    :from_id, :from_name, :to_id, :to_name,
                    :tt, :tb, :hours, :created)
            """), {
                "id": _uuid(), "vcid": vc_id, "vid": vacancy_id, "cid": candidate_id,
                "comp": company_id,
                "from_id": STAGE_IDS.get(prev_stage) if prev_stage else None,
                "from_name": prev_stage,
                "to_id": sid, "to_name": stage_name,
                "tt": choice(["manual", "auto", "lia_agent"]),
                "tb": choice(["recruiter", "lia_agent", "system"]),
                "hours": hours_in_prev, "created": transition_time,
            })
            count += 1
            prev_stage = stage_name

    logger.info(f"  {count} stage history entries seeded.")


async def seed_interviews(db: AsyncSession):
    logger.info("Seeding Interviews & Feedbacks...")
    existing = await db.execute(
        text("SELECT id FROM interviews WHERE created_by = :src LIMIT 1"),
        {"src": SEED_SOURCE},
    )
    if existing.fetchone():
        logger.info("  Interviews already exist, skipping.")
        return

    rows = await db.execute(
        text("""SELECT vc.id, vc.vacancy_id, vc.candidate_id, vc.stage
                FROM vacancy_candidates vc
                WHERE vc.company_id = :cid
                AND vc.stage IN ('interview_hr', 'interview_technical', 'interview_manager', 'offer', 'hired')"""),
        {"cid": SEED_COMPANY_ID_STR},
    )
    vc_rows = rows.fetchall()

    interview_types = {
        "interview_hr": ("Entrevista RH", "behavioral", "video_call"),
        "interview_technical": ("Entrevista Técnica", "technical", "video_call"),
        "interview_manager": ("Entrevista Gestor", "final", "in_person"),
        "offer": ("Entrevista Final", "final", "video_call"),
        "hired": ("Entrevista Final", "final", "in_person"),
    }

    interviewers = [
        ("Ana Beatriz Costa", "ana.costa@wedotalent.cc", "Head de RH"),
        ("Rafael Mendes", "rafael.mendes@wedotalent.cc", "Recrutador"),
        ("Camila Oliveira", "camila.oliveira@wedotalent.cc", "Recrutadora"),
        ("Lucas Ferreira", "lucas.ferreira@wedotalent.cc", "Gestor"),
    ]

    interview_count = 0
    feedback_count = 0
    for vc_id, vacancy_id, candidate_id, stage in vc_rows:
        cand_row = await db.execute(
            text("SELECT name, email FROM candidates WHERE id = :id"),
            {"id": candidate_id},
        )
        cand = cand_row.fetchone()
        if not cand:
            continue

        title, itype, mode = interview_types.get(stage, ("Entrevista", "general", "video_call"))
        interviewer_name, interviewer_email, interviewer_role = choice(interviewers)
        start = _past(1, 20)
        duration = choice([30, 45, 60])
        status = choice(["completed", "completed", "completed", "scheduled", "confirmed"])

        interview_id = _uuid()
        stage_id = STAGE_IDS.get(stage if stage in STAGE_IDS else "interview_hr")

        await db.execute(text("""
            INSERT INTO interviews (id, title, description, interview_type, interview_mode,
                candidate_id, candidate_name, candidate_email,
                interviewer_name, interviewer_email,
                start_time, end_time, timezone, duration_minutes,
                location, meeting_platform, status, confirmation_status,
                job_vacancy_id, job_title, application_stage,
                recruitment_stage_id, created_by, created_at, updated_at)
            VALUES (:id, :title, :desc, :itype, :mode,
                :cand_id, :cand_name, :cand_email,
                :int_name, :int_email,
                :start, :end, 'America/Sao_Paulo', :dur,
                :loc, :platform, :status, :conf,
                :vac_id, :job_title, :stage,
                :stage_id, :created_by, :now, :now)
        """), {
            "id": interview_id, "title": title,
            "desc": f"{title} para a vaga — candidato(a) {cand[0]}",
            "itype": itype, "mode": mode,
            "cand_id": candidate_id, "cand_name": cand[0], "cand_email": cand[1],
            "int_name": interviewer_name, "int_email": interviewer_email,
            "start": start, "end": start + timedelta(minutes=duration),
            "dur": duration, "loc": "Google Meet" if mode == "video_call" else "Escritório SP",
            "platform": "google_meet" if mode == "video_call" else None,
            "status": status, "conf": "confirmed" if status in ("completed", "confirmed") else "pending",
            "vac_id": vacancy_id, "job_title": title, "stage": stage,
            "stage_id": stage_id, "created_by": SEED_SOURCE, "now": NOW,
        })
        interview_count += 1

        if status == "completed":
            tech_rating = round(uniform(3.0, 5.0), 1)
            comm_rating = round(uniform(3.0, 5.0), 1)
            culture_rating = round(uniform(3.0, 5.0), 1)
            overall = round((tech_rating + comm_rating + culture_rating) / 3, 1)
            recommendation = "strong_hire" if overall >= 4.5 else "hire" if overall >= 3.8 else "no_hire"
            await db.execute(text("""
                INSERT INTO interview_feedbacks (id, interview_id,
                    interviewer_name, interviewer_email, interviewer_role,
                    technical_skills_rating, communication_rating, cultural_fit_rating,
                    overall_rating, strengths, weaknesses, notes, recommendation,
                    next_steps_suggested, created_at, updated_at)
                VALUES (:id, :iid, :name, :email, :role,
                    :tech, :comm, :culture, :overall,
                    cast(:str as json), cast(:weak as json), :notes, :rec,
                    :next, :now, :now)
            """), {
                "id": _uuid(), "iid": interview_id,
                "name": interviewer_name, "email": interviewer_email, "role": interviewer_role,
                "tech": tech_rating, "comm": comm_rating, "culture": culture_rating,
                "overall": overall,
                "str": json.dumps(["Boa comunicação", "Experiência relevante", "Fit cultural"]),
                "weak": json.dumps(["Pode melhorar em liderança"]),
                "notes": f"Candidato(a) {cand[0]} demonstrou bom domínio técnico.",
                "rec": recommendation,
                "next": "Avançar para próxima etapa" if recommendation != "no_hire" else "Encerrar processo",
                "now": NOW,
            })
            feedback_count += 1

    logger.info(f"  {interview_count} interviews seeded.")
    logger.info(f"  {feedback_count} interview feedbacks seeded.")


async def seed_department_members(db: AsyncSession):
    logger.info("Seeding DepartmentMembers...")
    count = 0
    members_data = [
        ("engineering", [
            ("Marcos Ribeiro",    "Tech Lead",                "marcos.ribeiro@wedotalent.cc",   "c-level"),
            ("Fernanda Lima",     "Software Engineer Sênior", "fernanda.lima@wedotalent.cc",    "senior"),
            ("Diego Souza",       "Software Engineer Pleno",  "diego.souza@wedotalent.cc",      "pleno"),
            ("Aline Barros",      "QA Engineer",              "aline.barros@wedotalent.cc",     "pleno"),
        ]),
        ("product", [
            ("Carla Mendes",      "Head de Produto",          "carla.mendes@wedotalent.cc",     "c-level"),
            ("Thiago Nunes",      "Product Manager",          "thiago.nunes@wedotalent.cc",     "senior"),
        ]),
        ("design", [
            ("Juliana Moreira",   "Design Lead",              "juliana.moreira@wedotalent.cc",  "senior"),
            ("Bruno Castro",      "UX Designer",              "bruno.castro@wedotalent.cc",     "pleno"),
        ]),
        ("data", [
            ("Renato Gomes",      "Data Engineering Lead",    "renato.gomes@wedotalent.cc",     "senior"),
            ("Patrícia Duarte",   "Data Scientist",           "patricia.duarte@wedotalent.cc",  "pleno"),
        ]),
        ("hr", [
            ("Ana Beatriz Costa", "Head de RH",               "ana.costa@wedotalent.cc",        "c-level"),
            ("Camila Oliveira",   "Recrutadora Sênior",       "camila.oliveira@wedotalent.cc",  "senior"),
        ]),
    ]
    for dept_key, members in members_data:
        dept_id = DEPT_IDS.get(dept_key)
        if not dept_id:
            continue
        for i, (name, title, email, level) in enumerate(members):
            existing = await db.execute(
                text("SELECT id FROM department_members WHERE company_id = :cid AND email = :email"),
                {"cid": SEED_COMPANY_PROFILE_ID, "email": email},
            )
            if existing.fetchone():
                continue
            await db.execute(text("""
                INSERT INTO department_members (id, department_id, company_id, name, title, email, level,
                    is_active, "order", created_at, updated_at)
                VALUES (:id, :did, :cid, :name, :title, :email, :level, true, :ord, :now, :now)
            """), {
                "id": _uuid(), "did": dept_id, "cid": SEED_COMPANY_PROFILE_ID,
                "name": name, "title": title, "email": email, "level": level,
                "ord": i, "now": NOW,
            })
            count += 1
    logger.info(f"  {count} department members seeded.")


SUB_STATUS_DATA = {
    "sourcing": [
        ("identified",         "Identificado",           0, False),
        ("contacted",          "Contatado",              1, True),
        ("awaiting_response",  "Aguardando Retorno",     2, True),
    ],
    "screening": [
        ("cv_review",          "Análise de CV",          0, False),
        ("scheduled",          "Triagem Agendada",       1, True),
        ("completed",          "Triagem Realizada",      2, False),
        ("documents_pending",  "Documentos Pendentes",   3, True),
    ],
    "interview_hr": [
        ("to_schedule",        "A Agendar",              0, False),
        ("scheduled",          "Agendada",               1, True),
        ("completed",          "Realizada",              2, False),
        ("feedback_pending",   "Feedback Pendente",      3, True),
    ],
    "interview_technical": [
        ("to_schedule",        "A Agendar",              0, False),
        ("scheduled",          "Agendada",               1, True),
        ("completed",          "Realizada",              2, False),
    ],
    "offer": [
        ("drafting",           "Elaborando Proposta",    0, False),
        ("sent",               "Proposta Enviada",       1, True),
        ("negotiating",        "Em Negociação",          2, True),
        ("accepted",           "Aceita",                 3, False),
    ],
}


async def seed_recruitment_sub_statuses(db: AsyncSession):
    logger.info("Seeding RecruitmentSubStatuses...")
    count = 0
    for stage_name, subs in SUB_STATUS_DATA.items():
        stage_id = STAGE_IDS.get(stage_name)
        if not stage_id:
            continue
        for name, display, order, is_waiting in subs:
            existing = await db.execute(
                text("SELECT id FROM recruitment_sub_statuses WHERE stage_id = :sid AND name = :name"),
                {"sid": stage_id, "name": name},
            )
            if existing.fetchone():
                continue
            await db.execute(text("""
                INSERT INTO recruitment_sub_statuses (id, stage_id, company_id, name, display_name,
                    sub_status_order, is_default, is_waiting, is_active, created_at, updated_at)
                VALUES (:id, :sid, :cid, :name, :dn, :ord, :def, :wait, true, :now, :now)
            """), {
                "id": _uuid(), "sid": stage_id, "cid": SEED_COMPANY_ID_STR,
                "name": name, "dn": display, "ord": order,
                "def": order == 0, "wait": is_waiting, "now": NOW,
            })
            count += 1
    logger.info(f"  {count} recruitment sub-statuses seeded.")


async def seed_activity_feed(db: AsyncSession):
    logger.info("Seeding ActivityFeed...")
    existing = await db.execute(
        text("SELECT id FROM activity_feed WHERE actor_id = :aid LIMIT 1"),
        {"aid": SEED_COMPANY_ID_STR},
    )
    if existing.fetchone():
        logger.info("  ActivityFeed already exists, skipping.")
        return
    activities = [
        ("vacancy_created",   "Nova vaga criada",                       "Engenheiro(a) de Software Sênior",            "job_vacancy"),
        ("candidate_added",   "Candidato adicionado ao pipeline",       "Ana Silva adicionada à vaga Eng. Software",   "candidate"),
        ("stage_change",      "Candidato avançou de etapa",             "Carlos Souza movido para Entrevista RH",      "candidate"),
        ("interview_scheduled","Entrevista agendada",                   "Entrevista técnica com Julia Santos",         "interview"),
        ("feedback_submitted","Feedback submetido",                     "Avaliação positiva para Pedro Mendes",        "feedback"),
        ("vacancy_created",   "Nova vaga criada",                       "Product Manager — Remoto",                    "job_vacancy"),
        ("candidate_added",   "Novo candidato via LinkedIn",            "Fernanda Lima importada do LinkedIn",         "candidate"),
        ("offer_sent",        "Proposta enviada",                       "Proposta CLT para Marcos Ribeiro",            "offer"),
        ("stage_change",      "Candidato avançou de etapa",             "Bruna Costa movida para Short List",          "candidate"),
        ("vacancy_closed",    "Vaga concluída",                         "Vendedor(a) Enterprise — vaga preenchida",    "job_vacancy"),
        ("candidate_hired",   "Candidato contratado",                   "Ricardo Santos contratado como vendedor",     "candidate"),
        ("screening_done",    "Triagem realizada por LIA",              "LIA triou 15 candidatos para Eng. ML",        "screening"),
        ("document_uploaded", "Documento recebido",                     "CV atualizado de Tatiana Vieira",             "document"),
        ("feedback_submitted","Feedback do gestor",                     "Lucas Ferreira avaliou candidato Tech Lead",  "feedback"),
        ("vacancy_created",   "Nova vaga criada",                       "Advogado(a) Trabalhista",                     "job_vacancy"),
    ]
    count = 0
    actors = ["ana.costa@wedotalent.cc", "rafael.mendes@wedotalent.cc", "camila.oliveira@wedotalent.cc", "lia_agent"]
    actor_names = ["Ana Costa", "Rafael Mendes", "Camila Oliveira", "LIA"]
    for i, (atype, title, desc, ttype) in enumerate(activities):
        actor_idx = i % len(actors)
        await db.execute(text("""
            INSERT INTO activity_feed (id, activity_type, actor_id, actor_name, actor_type,
                target_type, title, description, priority, category, is_visible, created_at)
            VALUES (:id, :atype, :aid, :aname, :at, :tt, :title, :desc, :pri, :cat, true, :created)
        """), {
            "id": str(_uuid()), "atype": atype, "aid": SEED_COMPANY_ID_STR,
            "aname": actor_names[actor_idx], "at": "user" if actors[actor_idx] != "lia_agent" else "agent",
            "tt": ttype, "title": title, "desc": desc,
            "pri": choice(["normal", "high"]), "cat": "recruitment",
            "created": _past(0, 30),
        })
        count += 1
    logger.info(f"  {count} activity feed entries seeded.")


async def seed_goals(db: AsyncSession):
    logger.info("Seeding Goals...")
    existing = await db.execute(
        text("SELECT id FROM goals WHERE company_id = :cid LIMIT 1"),
        {"cid": SEED_COMPANY_PROFILE_ID},
    )
    if existing.fetchone():
        logger.info("  Goals already exist, skipping.")
        return
    goals_data = [
        ("Candidatos na pipeline",          "Manter pelo menos 50 candidatos ativos no pipeline",   50, 46, "candidatos",   "monthly",  "pipeline"),
        ("Vagas ativas",                    "Preencher todas as vagas abertas no trimestre",         12,  9, "vagas",        "quarterly","hiring"),
        ("Tempo médio de contratação",      "Reduzir tempo de contratação para menos de 30 dias",   30, 35, "dias",         "quarterly","efficiency"),
        ("Taxa de conversão — triagem",     "Converter 60% dos triados para entrevista",            60, 52, "percentual",   "monthly",  "conversion"),
        ("Entrevistas realizadas",          "Realizar 40 entrevistas por mês",                      40, 28, "entrevistas",  "monthly",  "hiring"),
        ("NPS do processo seletivo",        "Manter NPS acima de 70",                               70, 75, "pontos",       "quarterly","satisfaction"),
        ("Diversidade no pipeline",         "30% de candidatos de grupos sub-representados",         30, 22, "percentual",   "quarterly","diversity"),
        ("Custo por contratação",           "Manter custo abaixo de R$ 3.000 por contratação",    3000,2800, "BRL",         "monthly",  "financial"),
    ]
    count = 0
    for name, desc, target, current, unit, period, category in goals_data:
        progress = min(round((current / target) * 100, 1), 100.0) if target > 0 else 0
        status = "completed" if current >= target else "in_progress"
        await db.execute(text("""
            INSERT INTO goals (id, user_id, company_id, name, description, target, current, unit,
                period, category, status, progress, is_custom, is_active, start_date, end_date,
                created_at, updated_at)
            VALUES (:id, :uid, :cid, :name, :desc, :target, :current, :unit, :period, :cat,
                :status, :progress, false, true, :start, :end, :now, :now)
        """), {
            "id": _uuid(), "uid": "ana.costa@wedotalent.cc", "cid": SEED_COMPANY_PROFILE_ID,
            "name": name, "desc": desc, "target": target, "current": current,
            "unit": unit, "period": period, "cat": category, "status": status,
            "progress": progress,
            "start": NOW.replace(day=1), "end": (NOW.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1),
            "now": NOW,
        })
        count += 1
    logger.info(f"  {count} goals seeded.")


async def seed_tasks(db: AsyncSession):
    logger.info("Seeding Tasks...")
    existing = await db.execute(
        text("SELECT id FROM tasks WHERE created_by_agent = 'seed_script' LIMIT 1"),
    )
    if existing.fetchone():
        logger.info("  Tasks already exist, skipping.")
        return
    tasks_data = [
        ("Dar feedback — Ana Silva (Eng. Software)",         "FEEDBACK_PENDING",    "HIGH",     "PENDING",      "rafael.mendes@wedotalent.cc",   2),
        ("Agendar entrevista técnica — Carlos Souza",        "INTERVIEW_SCHEDULE",  "HIGH",     "PENDING",      "camila.oliveira@wedotalent.cc",  1),
        ("Revisar CV — 5 novos candidatos Product Manager",  "CV_REVIEW",           "MEDIUM",   "PENDING",      "rafael.mendes@wedotalent.cc",   3),
        ("Enviar proposta — Marcos Ribeiro (Tech Lead)",     "GENERAL",             "CRITICAL", "IN_PROGRESS",  "ana.costa@wedotalent.cc",       1),
        ("Follow-up — candidatos sem resposta (7 dias)",     "FOLLOW_UP",           "MEDIUM",   "PENDING",      "camila.oliveira@wedotalent.cc",  5),
        ("Calibrar triagem — vaga ML Engineer",              "SOURCING",            "MEDIUM",   "PENDING",      "rafael.mendes@wedotalent.cc",   4),
        ("Entrevista com gestor — Julia Santos",             "INTERVIEW_SCHEDULE",  "HIGH",     "PENDING",      "camila.oliveira@wedotalent.cc",  2),
        ("Atualizar descrição de vaga — UX Designer",        "GENERAL",             "LOW",      "COMPLETED",    "rafael.mendes@wedotalent.cc",   7),
        ("Feedback negativo — 3 candidatos reprovados",      "FEEDBACK_PENDING",    "MEDIUM",   "PENDING",      "camila.oliveira@wedotalent.cc",  3),
        ("Reunião de alinhamento — nova vaga Jurídico",      "GENERAL",             "MEDIUM",   "PENDING",      "ana.costa@wedotalent.cc",       2),
    ]
    count = 0
    for title, ttype, priority, status, assigned_to, due_days in tasks_data:
        await db.execute(text("""
            INSERT INTO tasks (id, title, task_type, priority, status, created_by_agent,
                assigned_to_user_id, due_date, is_automated, requires_confirmation,
                created_at, updated_at)
            VALUES (:id, :title, :ttype, :pri, :status, 'seed_script',
                :assigned, :due, :auto, false, :created, :now)
        """), {
            "id": str(_uuid()), "title": title, "ttype": ttype, "pri": priority,
            "status": status, "assigned": assigned_to,
            "due": NOW + timedelta(days=due_days),
            "auto": ttype in ("FOLLOW_UP", "ALERT"),
            "created": _past(0, 10), "now": NOW,
        })
        count += 1
    logger.info(f"  {count} tasks seeded.")


async def seed_client_metrics(db: AsyncSession):
    logger.info("Seeding ClientUsageMetrics, ClientHealthMetrics, ClientSaasMetrics...")
    existing = await db.execute(
        text("SELECT id FROM client_usage_metrics WHERE client_id = :cid LIMIT 1"),
        {"cid": SEED_COMPANY_ID},
    )
    if existing.fetchone():
        logger.info("  Client metrics already exist, skipping.")
        return
    count = 0
    for month_offset in range(3):
        period_start = (NOW - timedelta(days=30 * month_offset)).replace(day=1)
        period_end = (period_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        await db.execute(text("""
            INSERT INTO client_usage_metrics (id, client_id, ai_credits_used, ai_credits_limit,
                users_active, users_limit, jobs_active, jobs_limit,
                storage_used_mb, storage_limit_mb, api_calls_month, api_calls_limit,
                period_start, period_end, created_at, updated_at)
            VALUES (:id, :cid, :credits_used, :credits_limit, :users, :users_limit,
                :jobs, :jobs_limit, :storage, :storage_limit, :api, :api_limit,
                :start, :end, :now, :now)
        """), {
            "id": _uuid(), "cid": SEED_COMPANY_ID,
            "credits_used": randint(800, 3500), "credits_limit": 5000,
            "users": 5 + month_offset, "users_limit": 50,
            "jobs": 8 + month_offset * 2, "jobs_limit": 200,
            "storage": round(uniform(500, 2000), 1), "storage_limit": 10000,
            "api": randint(5000, 20000), "api_limit": 50000,
            "start": period_start.date(), "end": period_end.date(), "now": NOW,
        })
        count += 1

    await db.execute(text("""
        INSERT INTO client_health_metrics (id, client_id, churn_risk, health_score,
            last_login, days_since_login, nps_score, csat_score,
            support_tickets_open, support_tickets_total,
            avg_response_time_hours, engagement_level, feature_adoption_rate,
            logins_last_30_days, actions_last_30_days, created_at, updated_at)
        VALUES (:id, :cid, :risk, :score, :login, :days, :nps, :csat,
            :open, :total, :rt, :eng, :adopt, :logins, :actions, :now, :now)
    """), {
        "id": _uuid(), "cid": SEED_COMPANY_ID, "risk": "low", "score": 85,
        "login": _past(0, 1), "days": 0, "nps": 78, "csat": 4.2,
        "open": 1, "total": 12, "rt": 2.5, "eng": "high", "adopt": 72.5,
        "logins": 45, "actions": 320, "now": NOW,
    })
    count += 1

    await db.execute(text("""
        INSERT INTO client_saas_metrics (id, client_id, mrr, arr, ltv, cac,
            payback_months, contract_start, contract_end, plan_name,
            billing_cycle, discount_percent, currency, created_at, updated_at)
        VALUES (:id, :cid, :mrr, :arr, :ltv, :cac, :payback, :start, :end,
            :plan, :cycle, :discount, 'BRL', :now, :now)
    """), {
        "id": _uuid(), "cid": SEED_COMPANY_ID,
        "mrr": 8500.0, "arr": 102000.0, "ltv": 306000.0, "cac": 15000.0,
        "payback": 1.8, "start": (NOW - timedelta(days=365)).date(),
        "end": (NOW + timedelta(days=365)).date(), "plan": "Enterprise",
        "cycle": "annual", "discount": 10.0, "now": NOW,
    })
    count += 1
    logger.info(f"  {count} client metric records seeded.")


async def clean_seed_data(db: AsyncSession):
    logger.info("Cleaning seed data...")

    await db.execute(text("DELETE FROM client_saas_metrics WHERE client_id = :cid"), {"cid": SEED_COMPANY_ID})
    await db.execute(text("DELETE FROM client_health_metrics WHERE client_id = :cid"), {"cid": SEED_COMPANY_ID})
    await db.execute(text("DELETE FROM client_usage_metrics WHERE client_id = :cid"), {"cid": SEED_COMPANY_ID})
    logger.info("  client metrics cleaned.")

    await db.execute(text("DELETE FROM tasks WHERE created_by_agent = 'seed_script'"))
    logger.info("  tasks cleaned.")

    await db.execute(text("DELETE FROM activity_feed WHERE actor_id = :cid"), {"cid": SEED_COMPANY_ID_STR})
    logger.info("  activity_feed cleaned.")

    await db.execute(text("DELETE FROM goals WHERE company_id = :cid"), {"cid": SEED_COMPANY_PROFILE_ID})
    logger.info("  goals cleaned.")

    await db.execute(text("""
        DELETE FROM interview_feedbacks WHERE interview_id IN
        (SELECT id FROM interviews WHERE created_by = :src)
    """), {"src": SEED_SOURCE})
    await db.execute(text("DELETE FROM interviews WHERE created_by = :src"), {"src": SEED_SOURCE})
    logger.info("  interviews & feedbacks cleaned.")

    await db.execute(text("DELETE FROM candidate_stage_history WHERE company_id = :cid"), {"cid": SEED_COMPANY_ID_STR})
    logger.info("  candidate_stage_history cleaned.")

    await db.execute(text("DELETE FROM vacancy_candidates WHERE company_id = :cid"), {"cid": SEED_COMPANY_ID_STR})
    logger.info("  vacancy_candidates cleaned.")

    # Expansao 2026-05-11: limpar FK tables que apontam pra job_vacancies
    # antes do DELETE FROM job_vacancies (auditado via pg_constraint).
    _vacancy_fk_tables = [
        "job_vacancy_audit_logs",
        "job_requirements",
        "job_vacancy_interview_stages",
        "job_drafts",
        "affirmative_audit_logs",
        "candidate_affirmative_documents",
        "data_requests",
        "lia_opinions",
        "rubric_evaluations",
        "vacancy_data_request_configs",
        "whatsapp_conversations",
        "wsi_response_analyses",
        "wsi_results",
        "wsi_sessions",
    ]
    _fk_col_map = {
        "job_drafts": "published_job_id",
        "data_requests": "vacancy_id",
        "affirmative_audit_logs": "vacancy_id",
        "candidate_affirmative_documents": "vacancy_id",
        "vacancy_data_request_configs": "vacancy_id",
    }
    for _t in _vacancy_fk_tables:
        _col = _fk_col_map.get(_t, "job_vacancy_id")
        try:
            await db.execute(
                text(f"DELETE FROM {_t} WHERE {_col} IN (SELECT id FROM job_vacancies WHERE company_id = :cid)"),
                {"cid": SEED_COMPANY_ID_STR},
            )
        except Exception as exc:
            logger.debug("  clean %s skipped (%s)", _t, exc)
    logger.info("  job_vacancies FK tables cleaned.")

    await db.execute(text("DELETE FROM job_vacancies WHERE company_id = :cid"), {"cid": SEED_COMPANY_ID_STR})
    logger.info("  job_vacancies cleaned.")

    await db.execute(text("""
        DELETE FROM candidate_experiences WHERE candidate_id IN
        (SELECT id FROM candidates WHERE source = :src)
    """), {"src": SEED_SOURCE})
    logger.info("  candidate_experiences cleaned.")
    await db.execute(text("""
        DELETE FROM candidate_education WHERE candidate_id IN
        (SELECT id FROM candidates WHERE source = :src)
    """), {"src": SEED_SOURCE})
    logger.info("  candidate_education cleaned.")
    await db.execute(text("DELETE FROM candidates WHERE source = :src"), {"src": SEED_SOURCE})
    logger.info("  candidates cleaned.")

    await db.execute(text("DELETE FROM recruitment_sub_statuses WHERE company_id = :cid"), {"cid": SEED_COMPANY_ID_STR})
    logger.info("  recruitment_sub_statuses cleaned.")

    await db.execute(text("DELETE FROM recruitment_stages WHERE company_id = :cid"), {"cid": SEED_COMPANY_ID_STR})
    logger.info("  recruitment_stages cleaned.")

    await db.execute(text("""
        DELETE FROM client_users WHERE company_id = :cid
        AND email NOT IN ('demo@wedotalent.com', 'demo@wedotalent.cc')
    """), {"cid": SEED_COMPANY_ID})
    logger.info("  client_users cleaned (demo user preserved).")

    await db.execute(text("DELETE FROM department_members WHERE company_id = :cid"), {"cid": SEED_COMPANY_PROFILE_ID})
    logger.info("  department_members cleaned.")

    await db.execute(text("DELETE FROM culture_values WHERE company_id = :cid"), {"cid": SEED_COMPANY_PROFILE_ID})
    logger.info("  culture_values cleaned.")
    await db.execute(text("DELETE FROM benefits WHERE company_id = :cid"), {"cid": SEED_COMPANY_PROFILE_ID})
    logger.info("  benefits cleaned.")
    await db.execute(text("DELETE FROM departments WHERE company_id = :cid"), {"cid": SEED_COMPANY_PROFILE_ID})
    logger.info("  departments cleaned.")

    # Expansao 2026-05-11: client_accounts e company_profiles tem muitas FK
    # (invoices, subscriptions, payment_history, etc.). Em vez de DELETE+INSERT,
    # apenas UPDATE para refletir nome canonical. Idempotente.
    await db.execute(text("""
        UPDATE client_accounts SET name = :name, trade_name = :trade, updated_at = :now
        WHERE id = :id
    """), {
        "name": "WeDOTalent Demo",
        "trade": "WeDOTalent Demo — Ambiente de Demonstracao",
        "now": NOW, "id": SEED_COMPANY_ID,
    })
    logger.info("  client_accounts renamed (UPDATE in-place, no FK churn).")

    logger.info("All seed data cleaned (client_accounts/company_profiles preserved + renamed).")


async def run_seed():
    async with AsyncSessionLocal() as db:
        try:
            await seed_client_account(db)
            await seed_company_profile(db)
            await seed_departments(db)
            await seed_department_members(db)
            await seed_benefits(db)
            await seed_culture_values(db)
            await seed_client_users(db)
            await seed_recruitment_stages(db)
            await seed_recruitment_sub_statuses(db)
            await seed_job_vacancies(db)
            await seed_candidates(db)
            await seed_candidate_experiences(db)
            await seed_candidate_education(db)
            await seed_vacancy_candidates(db)
            await seed_stage_history(db)
            await seed_interviews(db)
            await seed_activity_feed(db)
            await seed_goals(db)
            await seed_tasks(db)
            await seed_client_metrics(db)
            await db.commit()
            logger.info("All seed data committed successfully!")
        except Exception as e:
            await db.rollback()
            logger.error(f"Seed failed: {e}")
            raise


async def run_clean():
    async with AsyncSessionLocal() as db:
        try:
            await clean_seed_data(db)
            await db.commit()
            logger.info("Clean completed successfully!")
        except Exception as e:
            await db.rollback()
            logger.error(f"Clean failed: {e}")
            raise


async def run_reset():
    await run_clean()
    await run_seed()


def main():
    parser = argparse.ArgumentParser(description="LIA Platform Full Seed Data")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--seed", action="store_true", help="Insert all seed data (default)")
    group.add_argument("--clean", action="store_true", help="Remove all seed data")
    group.add_argument("--reset", action="store_true", help="Clean + Seed")
    args = parser.parse_args()

    if args.clean:
        asyncio.run(run_clean())
    elif args.reset:
        asyncio.run(run_reset())
    else:
        asyncio.run(run_seed())


if __name__ == "__main__":
    main()
