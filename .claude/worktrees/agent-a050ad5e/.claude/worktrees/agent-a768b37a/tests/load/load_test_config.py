"""
Configurações para testes de carga com Locust.

Centraliza headers de autenticação, dados de teste e geradores de payload.
"""
import uuid
import random
from typing import Dict, Any, List

# ==================== AUTENTICAÇÃO ====================
AUTH_HEADERS = {
    "Content-Type": "application/json",
    "X-Company-ID": "admin_company",
    "X-User-ID": "admin_user",
    "X-User-Role": "admin",
}

# ==================== IDs DE TESTE ====================
# Em um ambiente real, estes IDs viriam de fixtures ou seed data.
# Para load tests, usar IDs que existam no ambiente de staging.
TEST_COMPANY_ID = "admin_company"
TEST_USER_ID = "admin_user"

# IDs de vagas para testes de pipeline (usar vagas reais do ambiente)
TEST_JOB_IDS = [
    "00000000-0000-0000-0000-000000000001",
    "00000000-0000-0000-0000-000000000002",
    "00000000-0000-0000-0000-000000000003",
]

# IDs de candidatos para testes de pipeline
TEST_CANDIDATE_IDS = [
    "00000000-0000-0000-0000-000000000101",
    "00000000-0000-0000-0000-000000000102",
    "00000000-0000-0000-0000-000000000103",
]

# IDs de VacancyCandidate para testes de transição de pipeline
TEST_VACANCY_CANDIDATE_IDS = [
    "00000000-0000-0000-0000-000000000201",
    "00000000-0000-0000-0000-000000000202",
]

# ==================== GERADORES DE PAYLOAD ====================

WIZARD_CONVERSATION_TURNS = [
    # Turno 1: Informar cargo
    [
        "Preciso criar uma vaga de {job_title} para a equipe de tecnologia",
        "A vaga é para trabalho {work_model}, {seniority_level}",
    ],
    # Turno 2: Confirmar e avançar
    ["sim, perfeito"],
    # Turno 3: Faixa salarial
    ["A faixa salarial é de R$ {salary_min} a R$ {salary_max}"],
    # Turno 4: Skills
    ["Skills principais: {skills}"],
]

JOB_TITLES = [
    "Desenvolvedor Backend Python",
    "Desenvolvedor Frontend React",
    "Engenheiro de Dados",
    "Analista de QA",
    "DevOps Engineer",
    "Product Manager",
    "UX Designer",
    "Analista de Negócios",
]

WORK_MODELS = ["remoto", "híbrido", "presencial"]
SENIORITY_LEVELS = ["Júnior", "Pleno", "Sênior"]

SKILLS_BY_ROLE = {
    "backend": ["Python", "FastAPI", "PostgreSQL", "Redis", "Docker"],
    "frontend": ["React", "TypeScript", "Next.js", "Tailwind CSS"],
    "dados": ["Python", "SQL", "Spark", "Airflow", "dbt"],
    "devops": ["Kubernetes", "Docker", "Terraform", "AWS", "CI/CD"],
    "default": ["comunicação", "trabalho em equipe", "resolução de problemas"],
}

PIPELINE_STAGES = ["sourcing", "screening", "shortlist", "interview", "offer"]


def generate_wizard_message() -> Dict[str, Any]:
    """Gera um payload de mensagem para o wizard."""
    job_title = random.choice(JOB_TITLES)
    work_model = random.choice(WORK_MODELS)
    seniority = random.choice(SENIORITY_LEVELS)
    salary_min = random.randint(5, 15) * 1000
    salary_max = salary_min + random.randint(2, 8) * 1000

    role_key = "backend"
    if "Frontend" in job_title or "UX" in job_title:
        role_key = "frontend"
    elif "Dados" in job_title:
        role_key = "dados"
    elif "DevOps" in job_title:
        role_key = "devops"

    skills = ", ".join(SKILLS_BY_ROLE.get(role_key, SKILLS_BY_ROLE["default"])[:3])

    turn_idx = random.randint(0, len(WIZARD_CONVERSATION_TURNS) - 1)
    messages = WIZARD_CONVERSATION_TURNS[turn_idx]
    message = random.choice(messages).format(
        job_title=job_title,
        work_model=work_model,
        seniority_level=seniority,
        salary_min=salary_min,
        salary_max=salary_max,
        skills=skills,
    )

    return {
        "message": message,
        "session_id": str(uuid.uuid4()),
        "company_id": TEST_COMPANY_ID,
        "user_id": TEST_USER_ID,
    }


def generate_pipeline_transition_payload() -> Dict[str, Any]:
    """Gera payload para transição de candidato no pipeline."""
    current_stage_idx = random.randint(0, len(PIPELINE_STAGES) - 2)
    current_stage = PIPELINE_STAGES[current_stage_idx]
    next_stage = PIPELINE_STAGES[current_stage_idx + 1]

    return {
        "vacancy_candidate_id": random.choice(TEST_VACANCY_CANDIDATE_IDS),
        "from_stage": current_stage,
        "to_stage": next_stage,
        "triggered_by": TEST_USER_ID,
        "notes": f"Load test transition: {current_stage} -> {next_stage}",
    }
