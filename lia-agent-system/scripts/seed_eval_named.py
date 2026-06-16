"""
Seed Eval Named Candidates — Populates specific named candidates and job vacancies
required by the LIA eval suite.

Eval suite references these by name; seed_full_platform.py's deterministic RNG
(seed=42) cannot generate "Pedro", "Lucas" (as candidate), so this script is
mandatory for eval accuracy.

Usage:
    python scripts/seed_eval_named.py

Idempotent: uses ON CONFLICT DO NOTHING and pre-checks by ID.
All records linked to SEED_COMPANY_ID = 00000000-0000-4000-a000-000000000001.
"""
import asyncio
import json
import logging
import os
import sys
import uuid
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import text

try:
    from lia_config.database import AsyncSessionLocal
except ImportError:
    from app.core.database import AsyncSessionLocal  # type: ignore[no-redef]

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ─── Constants ──────────────────────────────────────────────────────────────

SEED_COMPANY_ID_STR = "00000000-0000-4000-a000-000000000001"
SEED_NS = uuid.UUID("00000000-0000-4000-a000-ffffffffffff")

NOW = datetime.utcnow()


def _seed_uuid(label: str) -> uuid.UUID:
    """Deterministic UUID from label (same namespace as seed_full_platform.py)."""
    return uuid.uuid5(SEED_NS, label)


# ─── Named Candidates ────────────────────────────────────────────────────────
# Each entry is a real eval candidate referenced by name in eval_cases.yaml.
# IDs are deterministic so re-runs are idempotent.

EVAL_NAMED_CANDIDATES = [
    {
        "id": _seed_uuid("eval_candidate:joao_silva"),
        "name": "João Silva",
        "email": "joao.silva.eval@email.com",
        "phone": "+55 11 91234-5678",
        "city": "São Paulo",
        "state": "SP",
        "current_company": "TechBrasil S.A.",
        "current_title": "Desenvolvedor Full Stack Sênior",
        "seniority": "Sênior",
        "years_of_experience": 8,
        "technical_skills": ["Python", "JavaScript", "React", "Node.js", "PostgreSQL", "Docker", "AWS"],
        "soft_skills": ["Comunicação", "Liderança", "Resolução de problemas"],
        "current_salary": 18000.0,
        "desired_salary_min": 20000.0,
        "desired_salary_max": 28000.0,
        "linkedin_url": "https://linkedin.com/in/joaosilva-eval",
    },
    {
        "id": _seed_uuid("eval_candidate:ana_costa"),
        "name": "Ana Costa",
        "email": "ana.costa.eval@email.com",
        "phone": "+55 11 92345-6789",
        "city": "São Paulo",
        "state": "SP",
        "current_company": "DataInc",
        "current_title": "Analista de Dados Sênior",
        "seniority": "Sênior",
        "years_of_experience": 9,
        "technical_skills": ["Python", "SQL", "Power BI", "Pandas", "Tableau", "Spark"],
        "soft_skills": ["Pensamento crítico", "Comunicação", "Adaptabilidade"],
        "current_salary": 16000.0,
        "desired_salary_min": 18000.0,
        "desired_salary_max": 24000.0,
        "linkedin_url": "https://linkedin.com/in/anacosta-eval",
    },
    {
        "id": _seed_uuid("eval_candidate:pedro_santos"),
        "name": "Pedro Santos",
        "email": "pedro.santos.eval@email.com",
        "phone": "+55 11 93456-7890",
        "city": "Campinas",
        "state": "SP",
        "current_company": "CloudOps Ltda",
        "current_title": "DevOps Engineer Sênior",
        "seniority": "Sênior",
        "years_of_experience": 7,
        "technical_skills": ["Docker", "Kubernetes", "AWS", "Terraform", "CI/CD", "Linux", "Git"],
        "soft_skills": ["Proatividade", "Trabalho em equipe", "Resiliência"],
        "current_salary": 17000.0,
        "desired_salary_min": 18000.0,
        "desired_salary_max": 25000.0,
        "linkedin_url": "https://linkedin.com/in/pedrosantos-eval",
    },
    {
        "id": _seed_uuid("eval_candidate:lucas_ferreira"),
        "name": "Lucas Ferreira",
        "email": "lucas.ferreira.eval@email.com",
        "phone": "+55 11 94567-8901",
        "city": "São Paulo",
        "state": "SP",
        "current_company": "StartupX",
        "current_title": "Engenheiro de Software Pleno",
        "seniority": "Pleno",
        "years_of_experience": 4,
        "technical_skills": ["Python", "JavaScript", "Git", "Linux", "SQL"],
        "soft_skills": ["Aprendizado contínuo", "Comunicação", "Adaptabilidade"],
        "current_salary": 10000.0,
        "desired_salary_min": 12000.0,
        "desired_salary_max": 16000.0,
        "linkedin_url": "https://linkedin.com/in/lucasferreira-eval",
    },
    {
        "id": _seed_uuid("eval_candidate:maria_santos"),
        "name": "Maria Santos",
        "email": "maria.santos.eval@email.com",
        "phone": "+55 11 95678-9012",
        "city": "Rio de Janeiro",
        "state": "RJ",
        "current_company": "DesignStudio",
        "current_title": "UX Designer Pleno",
        "seniority": "Pleno",
        "years_of_experience": 5,
        "technical_skills": ["Figma", "Sketch", "Adobe XD", "Photoshop"],
        "soft_skills": ["Criatividade", "Empatia", "Comunicação"],
        "current_salary": 11000.0,
        "desired_salary_min": 12000.0,
        "desired_salary_max": 15000.0,
        "linkedin_url": "https://linkedin.com/in/mariasantos-eval",
    },
    {
        "id": _seed_uuid("eval_candidate:rafael_costa"),
        "name": "Rafael Costa",
        "email": "rafael.costa.eval@email.com",
        "phone": "+55 11 96789-0123",
        "city": "São Paulo",
        "state": "SP",
        "current_company": "InfraTech",
        "current_title": "Tech Lead Backend",
        "seniority": "Especialista",
        "years_of_experience": 12,
        "technical_skills": ["Python", "Go", "PostgreSQL", "Redis", "Docker", "Kubernetes", "AWS"],
        "soft_skills": ["Liderança", "Mentoria", "Visão estratégica"],
        "current_salary": 24000.0,
        "desired_salary_min": 26000.0,
        "desired_salary_max": 35000.0,
        "linkedin_url": "https://linkedin.com/in/rafaelcosta-eval",
    },
]

CANDIDATE_IDS = {c["name"]: c["id"] for c in EVAL_NAMED_CANDIDATES}

# ─── Named Job Vacancies ──────────────────────────────────────────────────────
# job_id strings match what the eval references: V0037 (DevOps), V0039 (Engenheiro SE)

EVAL_NAMED_JOBS = [
    {
        "id": _seed_uuid("eval_vacancy:V0037"),
        "job_id": "V0037",
        "title": "DevOps Engineer Sênior",
        "department": "Engineering",
        "location": "Remoto",
        "work_model": "remoto",
        "employment_type": "PJ",
        "seniority": "Sênior",
        "status": "Ativa",
        "priority": "alta",
        "urgency_level": 5,
        "salary_min": 16000,
        "salary_max": 24000,
        "description": (
            "Buscamos um DevOps Engineer Sênior para integrar nosso time de infraestrutura. "
            "Experiência obrigatória: Kubernetes, AWS, Terraform, CI/CD, Docker, Linux. "
            "Modelo de trabalho: 100% remoto. Contratação: PJ."
        ),
        "requirements": ["Kubernetes", "AWS", "Terraform", "CI/CD", "Docker"],
        "tech_requirements": [
            {"skill": "Kubernetes", "level": "avançado", "weight": 0.3},
            {"skill": "AWS", "level": "avançado", "weight": 0.25},
            {"skill": "Terraform", "level": "intermediário", "weight": 0.2},
            {"skill": "CI/CD", "level": "intermediário", "weight": 0.15},
            {"skill": "Docker", "level": "avançado", "weight": 0.1},
        ],
    },
    {
        "id": _seed_uuid("eval_vacancy:V0039"),
        "job_id": "V0039",
        "title": "Engenheiro de Software Sênior",
        "department": "Engineering",
        "location": "São Paulo, SP",
        "work_model": "híbrido",
        "employment_type": "CLT",
        "seniority": "Sênior",
        "status": "Ativa",
        "priority": "alta",
        "urgency_level": 5,
        "salary_min": 18000,
        "salary_max": 25000,
        "description": (
            "Vaga para Engenheiro(a) de Software Sênior no time de backend. "
            "Requisitos: Python, FastAPI, PostgreSQL, Docker, experiência em sistemas distribuídos. "
            "Modelo de trabalho: híbrido (3x presencial). Contratação: CLT."
        ),
        "requirements": ["Python", "FastAPI", "PostgreSQL", "Docker", "Sistemas distribuídos"],
        "tech_requirements": [
            {"skill": "Python", "level": "avançado", "weight": 0.3},
            {"skill": "FastAPI", "level": "avançado", "weight": 0.25},
            {"skill": "PostgreSQL", "level": "intermediário", "weight": 0.25},
            {"skill": "Docker", "level": "intermediário", "weight": 0.1},
            {"skill": "Redis", "level": "básico", "weight": 0.1},
        ],
    },
]

JOB_IDS = {j["job_id"]: j["id"] for j in EVAL_NAMED_JOBS}

# ─── Vacancy-Candidate Associations ─────────────────────────────────────────
# V0037 (DevOps): Pedro Santos (primary), Rafael Costa, Lucas Ferreira, João Silva
# V0039 (Engenheiro SE): João Silva, Ana Costa, Rafael Costa

EVAL_VACANCY_CANDIDATES = [
    # V0037 — DevOps: Pedro Santos at screening stage (primary for CM-004, SC-001)
    {
        "id": _seed_uuid("eval_vc:V0037:pedro_santos"),
        "vacancy_id": _seed_uuid("eval_vacancy:V0037"),
        "candidate_id": _seed_uuid("eval_candidate:pedro_santos"),
        "stage": "screening",
        "status": "screening",
        "lia_score": 72.5,
        "match_percentage": 78.0,
    },
    # V0037 — DevOps: Lucas Ferreira at screening stage (no score — for SC-001 "candidatos sem nota")
    {
        "id": _seed_uuid("eval_vc:V0037:lucas_ferreira"),
        "vacancy_id": _seed_uuid("eval_vacancy:V0037"),
        "candidate_id": _seed_uuid("eval_candidate:lucas_ferreira"),
        "stage": "screening",
        "status": "screening",
        "lia_score": None,
        "match_percentage": None,
    },
    # V0037 — DevOps: Rafael Costa at sourcing stage
    {
        "id": _seed_uuid("eval_vc:V0037:rafael_costa"),
        "vacancy_id": _seed_uuid("eval_vacancy:V0037"),
        "candidate_id": _seed_uuid("eval_candidate:rafael_costa"),
        "stage": "sourcing",
        "status": "sourced",
        "lia_score": 89.0,
        "match_percentage": 91.0,
    },
    # V0037 — DevOps: João Silva at sourcing
    {
        "id": _seed_uuid("eval_vc:V0037:joao_silva"),
        "vacancy_id": _seed_uuid("eval_vacancy:V0037"),
        "candidate_id": _seed_uuid("eval_candidate:joao_silva"),
        "stage": "sourcing",
        "status": "sourced",
        "lia_score": 65.0,
        "match_percentage": 60.0,
    },
    # V0039 — Engenheiro SE: João Silva at screening
    {
        "id": _seed_uuid("eval_vc:V0039:joao_silva"),
        "vacancy_id": _seed_uuid("eval_vacancy:V0039"),
        "candidate_id": _seed_uuid("eval_candidate:joao_silva"),
        "stage": "screening",
        "status": "screening",
        "lia_score": 85.0,
        "match_percentage": 88.0,
    },
    # V0039 — Engenheiro SE: Ana Costa at screening
    {
        "id": _seed_uuid("eval_vc:V0039:ana_costa"),
        "vacancy_id": _seed_uuid("eval_vacancy:V0039"),
        "candidate_id": _seed_uuid("eval_candidate:ana_costa"),
        "stage": "screening",
        "status": "screening",
        "lia_score": 79.0,
        "match_percentage": 76.0,
    },
    # V0039 — Engenheiro SE: Rafael Costa at interview_technical
    {
        "id": _seed_uuid("eval_vc:V0039:rafael_costa"),
        "vacancy_id": _seed_uuid("eval_vacancy:V0039"),
        "candidate_id": _seed_uuid("eval_candidate:rafael_costa"),
        "stage": "interview_technical",
        "status": "approved",
        "lia_score": 93.0,
        "match_percentage": 95.0,
    },
]


# ─── Seed Functions ───────────────────────────────────────────────────────────

async def seed_candidates(db) -> int:
    count = 0
    for c in EVAL_NAMED_CANDIDATES:
        existing = await db.execute(
            text("SELECT id FROM candidates WHERE id = :id"), {"id": c["id"]}
        )
        if existing.fetchone():
            logger.info(f"  Candidate {c['name']} already exists, skipping.")
            continue
        await db.execute(text("""
            INSERT INTO candidates (
                id, company_id, name, email, phone,
                location_city, location_state, location_country,
                current_company, current_title, seniority_level, years_of_experience,
                technical_skills, soft_skills, source,
                current_salary, desired_salary_min, desired_salary_max,
                linkedin_url, status, is_active, salary_currency,
                created_at, updated_at
            ) VALUES (
                :id, :cid, :name, :email, :phone,
                :city, :state, 'Brasil',
                :company, :title, :seniority, :yrs,
                :tech, :soft, 'eval_seed',
                :sal, :sal_min, :sal_max,
                :li, 'active', true, 'BRL',
                :now, :now
            )
            ON CONFLICT (id) DO NOTHING
        """), {
            "id": c["id"],
            "cid": SEED_COMPANY_ID_STR,
            "name": c["name"],
            "email": c["email"],
            "phone": c["phone"],
            "city": c["city"],
            "state": c["state"],
            "company": c["current_company"],
            "title": c["current_title"],
            "seniority": c["seniority"],
            "yrs": c["years_of_experience"],
            "tech": c["technical_skills"],
            "soft": c["soft_skills"],
            "sal": c["current_salary"],
            "sal_min": c["desired_salary_min"],
            "sal_max": c["desired_salary_max"],
            "li": c["linkedin_url"],
            "now": NOW,
        })
        logger.info(f"  Created candidate: {c['name']}")
        count += 1
    return count


async def seed_job_vacancies(db) -> int:
    count = 0
    for j in EVAL_NAMED_JOBS:
        existing = await db.execute(
            text("SELECT id FROM job_vacancies WHERE id = :id"), {"id": j["id"]}
        )
        if existing.fetchone():
            logger.info(f"  Job {j['job_id']} already exists, skipping.")
            continue

        # Also check by job_id string to avoid duplicates from other seeds
        existing_by_jid = await db.execute(
            text("SELECT id FROM job_vacancies WHERE company_id = :cid AND job_id = :jid"),
            {"cid": SEED_COMPANY_ID_STR, "jid": j["job_id"]},
        )
        if existing_by_jid.fetchone():
            logger.info(f"  Job {j['job_id']} already exists by job_id, skipping.")
            continue

        open_date = NOW - timedelta(days=20)
        deadline = NOW + timedelta(days=40)
        salary_json = json.dumps({"min": j["salary_min"], "max": j["salary_max"], "currency": "BRL"})

        await db.execute(text("""
            INSERT INTO job_vacancies (
                id, company_id, job_id, title, department, location, work_model,
                employment_type, seniority_level, description, salary_range,
                status, stage, priority, urgency_level,
                open_date, deadline, recruiter_email, manager, created_by, visibility,
                requirements, technical_requirements, behavioral_competencies,
                created_at, updated_at, is_pipeline_customized
            ) VALUES (
                :id, :cid, :jid, :title, :dept, :loc, :model,
                :etype, :sen, :desc, cast(:salary as jsonb),
                :status, :stage, :pri, :urg,
                :open, :dead, :rec, :mgr, :cb, 'public',
                :reqs, cast(:tech_reqs as json), cast(:behav as json),
                :created, :now, false
            )
            ON CONFLICT (id) DO NOTHING
        """), {
            "id": j["id"],
            "cid": SEED_COMPANY_ID_STR,
            "jid": j["job_id"],
            "title": j["title"],
            "dept": j["department"],
            "loc": j["location"],
            "model": j["work_model"],
            "etype": j["employment_type"],
            "sen": j["seniority"],
            "desc": j["description"],
            "salary": salary_json,
            "status": j["status"],
            "stage": "Publicada",
            "pri": j["priority"],
            "urg": j["urgency_level"],
            "open": open_date,
            "dead": deadline,
            "rec": "rafael.mendes@wedotalent.cc",
            "mgr": "Lucas Ferreira",
            "cb": "ana.costa@wedotalent.cc",
            "reqs": j["requirements"],
            "tech_reqs": json.dumps(j["tech_requirements"]),
            "behav": json.dumps([]),
            "created": open_date,
            "now": NOW,
        })
        logger.info(f"  Created job: {j['job_id']} — {j['title']}")
        count += 1
    return count


async def seed_vacancy_candidates(db) -> int:
    count = 0
    for vc in EVAL_VACANCY_CANDIDATES:
        existing = await db.execute(
            text("SELECT id FROM vacancy_candidates WHERE id = :id"), {"id": vc["id"]}
        )
        if existing.fetchone():
            continue

        # Also guard against duplicate (vacancy_id, candidate_id) pairs
        existing_pair = await db.execute(
            text("""
                SELECT id FROM vacancy_candidates
                WHERE vacancy_id = :vid AND candidate_id = :cid AND company_id = :co
            """),
            {"vid": vc["vacancy_id"], "cid": vc["candidate_id"], "co": SEED_COMPANY_ID_STR},
        )
        if existing_pair.fetchone():
            continue

        added_at = NOW - timedelta(days=10)
        await db.execute(text("""
            INSERT INTO vacancy_candidates (
                id, vacancy_id, candidate_id, company_id,
                source, origin, lia_score, match_percentage,
                status, stage, added_by,
                created_at, updated_at, stage_entered_at
            ) VALUES (
                :id, :vid, :cid, :comp,
                'eval_seed', 'web', :score, :match,
                :status, :stage, 'eval_seed_script',
                :created, :now, :entered
            )
            ON CONFLICT (id) DO NOTHING
        """), {
            "id": vc["id"],
            "vid": vc["vacancy_id"],
            "cid": vc["candidate_id"],
            "comp": SEED_COMPANY_ID_STR,
            "score": vc["lia_score"],
            "match": vc["match_percentage"],
            "status": vc["status"],
            "stage": vc["stage"],
            "created": added_at,
            "now": NOW,
            "entered": added_at,
        })
        count += 1
    return count


async def run_seed():
    logger.info("=" * 60)
    logger.info("seed_eval_named.py — seeding eval named candidates & jobs")
    logger.info(f"SEED_COMPANY_ID: {SEED_COMPANY_ID_STR}")
    logger.info("=" * 60)

    async with AsyncSessionLocal() as db:
        # 1. Candidates
        logger.info("\n[1/3] Seeding named candidates...")
        n_cands = await seed_candidates(db)
        await db.commit()
        logger.info(f"  → {n_cands} new candidates created")

        # 2. Job vacancies
        logger.info("\n[2/3] Seeding eval job vacancies (V0037, V0039)...")
        n_jobs = await seed_job_vacancies(db)
        await db.commit()
        logger.info(f"  → {n_jobs} new job vacancies created")

        # 3. Vacancy-candidate associations
        logger.info("\n[3/3] Seeding vacancy-candidate associations...")
        n_vc = await seed_vacancy_candidates(db)
        await db.commit()
        logger.info(f"  → {n_vc} new associations created")

    logger.info("\n" + "=" * 60)
    logger.info("✅ seed_eval_named.py complete")
    logger.info(f"   Candidates: {n_cands} new | Jobs: {n_jobs} new | Assoc: {n_vc} new")
    logger.info("=" * 60)

    # Verification
    logger.info("\nVerification — checking DB...")
    async with AsyncSessionLocal() as db:
        for c in EVAL_NAMED_CANDIDATES:
            row = await db.execute(
                text("SELECT name FROM candidates WHERE id = :id"), {"id": c["id"]}
            )
            r = row.fetchone()
            status = "✅" if r else "❌ MISSING"
            logger.info(f"  {status} Candidate: {c['name']}")

        for j in EVAL_NAMED_JOBS:
            row = await db.execute(
                text("SELECT title, job_id FROM job_vacancies WHERE job_id = :jid AND company_id = :cid"),
                {"jid": j["job_id"], "cid": SEED_COMPANY_ID_STR},
            )
            r = row.fetchone()
            status = "✅" if r else "❌ MISSING"
            logger.info(f"  {status} Job: {j['job_id']} — {r[0] if r else 'not found'}")

        # Count vacancy_candidates for V0037
        row = await db.execute(
            text("""
                SELECT COUNT(*) FROM vacancy_candidates vc
                JOIN job_vacancies jv ON vc.vacancy_id = jv.id
                WHERE jv.job_id = 'V0037' AND vc.company_id = :cid
            """),
            {"cid": SEED_COMPANY_ID_STR},
        )
        count_v37 = row.scalar()
        logger.info(f"  {'✅' if count_v37 > 0 else '❌'} V0037 candidates: {count_v37}")


if __name__ == "__main__":
    asyncio.run(run_seed())
