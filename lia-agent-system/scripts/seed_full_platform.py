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


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


DEPT_IDS = {n: _uuid() for n in [
    "engineering", "product", "design", "data", "hr",
    "finance", "sales", "marketing", "legal", "operations",
]}

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

STAGE_IDS = {s["name"]: _uuid() for s in STAGE_DEFS}

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
]

USER_IDS = [_uuid() for _ in CLIENT_USERS]

JOB_VACANCIES = [
    {"title": "Engenheiro(a) de Software Sênior",       "dept": "engineering",  "location": "São Paulo, SP",       "model": "híbrido",     "type": "CLT", "seniority": "Sênior",       "status": "Ativa",      "priority": "alta",    "salary_min": 18000, "salary_max": 25000},
    {"title": "Product Manager",                        "dept": "product",      "location": "São Paulo, SP",       "model": "híbrido",     "type": "CLT", "seniority": "Pleno",        "status": "Ativa",      "priority": "alta",    "salary_min": 15000, "salary_max": 22000},
    {"title": "UX/UI Designer Pleno",                   "dept": "design",       "location": "Remoto",              "model": "remoto",      "type": "CLT", "seniority": "Pleno",        "status": "Ativa",      "priority": "média",   "salary_min": 10000, "salary_max": 15000},
    {"title": "Analista de Dados Sênior",               "dept": "data",         "location": "São Paulo, SP",       "model": "híbrido",     "type": "CLT", "seniority": "Sênior",       "status": "Ativa",      "priority": "média",   "salary_min": 14000, "salary_max": 20000},
    {"title": "Tech Lead — Backend",                    "dept": "engineering",  "location": "São Paulo, SP",       "model": "presencial",  "type": "CLT", "seniority": "Especialista", "status": "Ativa",      "priority": "alta",    "salary_min": 22000, "salary_max": 32000},
    {"title": "Analista de RH Pleno",                   "dept": "hr",           "location": "São Paulo, SP",       "model": "híbrido",     "type": "CLT", "seniority": "Pleno",        "status": "Ativa",      "priority": "média",   "salary_min": 7000,  "salary_max": 10000},
    {"title": "DevOps Engineer",                        "dept": "engineering",  "location": "Remoto",              "model": "remoto",      "type": "PJ",  "seniority": "Sênior",       "status": "Ativa",      "priority": "alta",    "salary_min": 16000, "salary_max": 24000},
    {"title": "Analista Financeiro Júnior",             "dept": "finance",      "location": "São Paulo, SP",       "model": "presencial",  "type": "CLT", "seniority": "Júnior",       "status": "Rascunho",   "priority": "baixa",   "salary_min": 4500,  "salary_max": 6500},
    {"title": "Gerente de Marketing Digital",           "dept": "marketing",    "location": "São Paulo, SP",       "model": "híbrido",     "type": "CLT", "seniority": "Sênior",       "status": "Pausada",    "priority": "média",   "salary_min": 14000, "salary_max": 20000},
    {"title": "Engenheiro(a) de Machine Learning",      "dept": "data",         "location": "Remoto",              "model": "remoto",      "type": "CLT", "seniority": "Sênior",       "status": "Ativa",      "priority": "alta",    "salary_min": 20000, "salary_max": 30000},
    {"title": "Vendedor(a) Enterprise",                 "dept": "sales",        "location": "São Paulo, SP",       "model": "híbrido",     "type": "CLT", "seniority": "Pleno",        "status": "Concluída",  "priority": "alta",    "salary_min": 8000,  "salary_max": 12000},
    {"title": "Advogado(a) Trabalhista",                "dept": "legal",        "location": "São Paulo, SP",       "model": "presencial",  "type": "CLT", "seniority": "Sênior",       "status": "Ativa",      "priority": "média",   "salary_min": 12000, "salary_max": 18000},
]

VACANCY_IDS = [_uuid() for _ in JOB_VACANCIES]

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

CITIES = [
    ("São Paulo", "SP"), ("Rio de Janeiro", "RJ"), ("Belo Horizonte", "MG"),
    ("Curitiba", "PR"), ("Porto Alegre", "RS"), ("Florianópolis", "SC"),
    ("Brasília", "DF"), ("Recife", "PE"), ("Salvador", "BA"), ("Campinas", "SP"),
    ("Goiânia", "GO"), ("Fortaleza", "CE"),
]


def _generate_candidates(count: int):
    candidates = []
    used_names = set()
    for i in range(count):
        while True:
            fn = choice(FIRST_NAMES)
            ln = choice(LAST_NAMES)
            name = f"{fn} {ln}"
            if name not in used_names:
                used_names.add(name)
                break
        city, state = choice(CITIES)
        email_base = f"{fn.lower()}.{ln.lower()}".replace("á","a").replace("ã","a").replace("é","e").replace("ê","e").replace("í","i").replace("ó","o").replace("ô","o").replace("ú","u")
        email = f"{email_base}{randint(1,99)}@email.com"
        yrs = randint(1, 18)
        seniority_map = {(1,3): "Júnior", (4,7): "Pleno", (8,12): "Sênior", (13,99): "Especialista"}
        seniority = next(v for (lo,hi),v in seniority_map.items() if lo <= yrs <= hi)
        skills_count = randint(4, 10)
        candidates.append({
            "id": _uuid(),
            "name": name,
            "email": email,
            "phone": f"+55 11 9{randint(1000,9999)}-{randint(1000,9999)}",
            "city": city,
            "state": state,
            "current_company": choice(COMPANIES_BR),
            "current_title": choice([
                "Software Engineer", "Analista de Sistemas", "Product Manager",
                "UX Designer", "Data Analyst", "DevOps Engineer", "QA Engineer",
                "Gerente de Projetos", "Tech Lead", "Analista de Dados",
                "Desenvolvedor Full Stack", "Analista de BI", "Scrum Master",
                "Analista Financeiro", "Consultor de RH", "Advogado(a)",
            ]),
            "seniority": seniority,
            "years_of_experience": yrs,
            "technical_skills": sample(TECH_SKILLS_POOL, min(skills_count, len(TECH_SKILLS_POOL))),
            "soft_skills": sample(SOFT_SKILLS, randint(2, 5)),
            "source": choice(["manual", "linkedin", "ats", "referral", "pearch"]),
            "salary_current": round(uniform(5000, 30000), 2),
            "salary_min": round(uniform(6000, 25000), 2),
            "salary_max": round(uniform(15000, 35000), 2),
            "linkedin_url": f"https://linkedin.com/in/{email_base}{randint(1,99)}",
            "created_at": _past(5, 120),
        })
    return candidates


CANDIDATES = _generate_candidates(50)
CANDIDATE_IDS = [c["id"] for c in CANDIDATES]


async def seed_client_account(db: AsyncSession):
    logger.info("Seeding ClientAccount...")
    existing = await db.execute(
        text("SELECT id FROM client_accounts WHERE id = :id"),
        {"id": SEED_COMPANY_ID},
    )
    if existing.fetchone():
        logger.info("  ClientAccount already exists, skipping.")
        return
    await db.execute(text("""
        INSERT INTO client_accounts (id, name, trade_name, cnpj, primary_email, primary_phone, website, status, plan_id,
            contract_start_date, contract_end_date, user_limit, job_limit, ai_credits_monthly, industry, company_size,
            created_at, updated_at, is_deleted, welcome_email_sent, workos_organization_created, sso_configured)
        VALUES (:id, :name, :trade_name, :cnpj, :email, :phone, :website, :status, :plan,
            :start, :end, :user_limit, :job_limit, :credits, :industry, :size,
            :now, :now, false, true, false, false)
    """), {
        "id": SEED_COMPANY_ID, "name": "WeDo Talent", "trade_name": "WeDo Talent Tecnologia Ltda",
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
        await db.execute(text("""
            INSERT INTO job_vacancies (id, company_id, job_id, title, department, location, work_model,
                employment_type, seniority_level, description, salary_range, status, stage, priority,
                urgency_level, open_date, deadline, recruiter_email, manager, created_by, visibility,
                created_at, updated_at, is_pipeline_customized)
            VALUES (:id, :cid, :jid, :title, :dept, :loc, :model, :etype, :sen, :desc,
                cast(:salary as jsonb), :status, :stage, :pri, :urg, :open, :dead, :rec, :mgr, :cb,
                'public', :created, :now, false)
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
            INSERT INTO candidates (id, name, email, phone, location_city, location_state, location_country,
                current_company, current_title, seniority_level, years_of_experience,
                technical_skills, soft_skills, source, current_salary, desired_salary_min, desired_salary_max,
                linkedin_url, status, is_active, salary_currency,
                created_at, updated_at)
            VALUES (:id, :name, :email, :phone, :city, :state, 'Brasil',
                :company, :title, :seniority, :yrs,
                :tech, :soft, :source, :sal, :sal_min, :sal_max,
                :li, 'active', true, 'BRL',
                :created, :now)
        """), {
            "id": c["id"], "name": c["name"], "email": c["email"], "phone": c["phone"],
            "city": c["city"], "state": c["state"], "company": c["current_company"],
            "title": c["current_title"], "seniority": c["seniority"], "yrs": c["years_of_experience"],
            "tech": c["technical_skills"],
            "soft": c["soft_skills"],
            "source": c["source"], "sal": c["salary_current"],
            "sal_min": c["salary_min"], "sal_max": c["salary_max"],
            "li": c["linkedin_url"], "created": c["created_at"], "now": NOW,
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


async def clean_seed_data(db: AsyncSession):
    logger.info("Cleaning seed data...")

    await db.execute(text("DELETE FROM candidate_stage_history WHERE company_id = :cid"), {"cid": SEED_COMPANY_ID_STR})
    logger.info("  candidate_stage_history cleaned.")

    await db.execute(text("DELETE FROM vacancy_candidates WHERE company_id = :cid"), {"cid": SEED_COMPANY_ID_STR})
    logger.info("  vacancy_candidates cleaned.")

    await db.execute(text("DELETE FROM job_vacancies WHERE company_id = :cid"), {"cid": SEED_COMPANY_ID_STR})
    logger.info("  job_vacancies cleaned.")

    cand_ids_str = ", ".join(f"'{str(c['id'])}'" for c in CANDIDATES)
    if cand_ids_str:
        await db.execute(text(f"DELETE FROM candidate_experiences WHERE candidate_id::text IN ({cand_ids_str})"))
        logger.info("  candidate_experiences cleaned.")
        await db.execute(text(f"DELETE FROM candidate_education WHERE candidate_id::text IN ({cand_ids_str})"))
        logger.info("  candidate_education cleaned.")
        await db.execute(text(f"DELETE FROM candidates WHERE id::text IN ({cand_ids_str})"))
        logger.info("  candidates cleaned.")

    await db.execute(text("DELETE FROM recruitment_stages WHERE company_id = :cid"), {"cid": SEED_COMPANY_ID_STR})
    logger.info("  recruitment_stages cleaned.")

    await db.execute(text("DELETE FROM client_users WHERE company_id = :cid"), {"cid": SEED_COMPANY_ID})
    logger.info("  client_users cleaned.")

    await db.execute(text("DELETE FROM culture_values WHERE company_id = :cid"), {"cid": SEED_COMPANY_PROFILE_ID})
    logger.info("  culture_values cleaned.")
    await db.execute(text("DELETE FROM benefits WHERE company_id = :cid"), {"cid": SEED_COMPANY_PROFILE_ID})
    logger.info("  benefits cleaned.")
    await db.execute(text("DELETE FROM departments WHERE company_id = :cid"), {"cid": SEED_COMPANY_PROFILE_ID})
    logger.info("  departments cleaned.")

    await db.execute(text("DELETE FROM company_profiles WHERE id = :id"), {"id": SEED_COMPANY_PROFILE_ID})
    logger.info("  company_profiles cleaned.")

    await db.execute(text("DELETE FROM client_accounts WHERE id = :id"), {"id": SEED_COMPANY_ID})
    logger.info("  client_accounts cleaned.")

    logger.info("All seed data cleaned.")


async def run_seed():
    async with AsyncSessionLocal() as db:
        try:
            await seed_client_account(db)
            await seed_company_profile(db)
            await seed_departments(db)
            await seed_benefits(db)
            await seed_culture_values(db)
            await seed_client_users(db)
            await seed_recruitment_stages(db)
            await seed_job_vacancies(db)
            await seed_candidates(db)
            await seed_candidate_experiences(db)
            await seed_candidate_education(db)
            await seed_vacancy_candidates(db)
            await seed_stage_history(db)
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
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--seed", action="store_true", help="Insert all seed data")
    group.add_argument("--clean", action="store_true", help="Remove all seed data")
    group.add_argument("--reset", action="store_true", help="Clean + Seed")
    args = parser.parse_args()

    if args.seed:
        asyncio.run(run_seed())
    elif args.clean:
        asyncio.run(run_clean())
    elif args.reset:
        asyncio.run(run_reset())


if __name__ == "__main__":
    main()
