"""
Seed script for Job Patterns and Embeddings.

Creates sample data for training the learning system:
- Job patterns from common roles
- Salary benchmarks
- Skill clusters
- Sample job embeddings

Run with: python -m app.scripts.seed_job_patterns
"""
import asyncio
import logging
import random
from uuid import uuid4

from app.core.database import AsyncSessionLocal
from app.models.job_pattern import JobEmbedding, JobPattern, SalaryBenchmark, SkillCluster

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SAMPLE_COMPANY_ID = "00000000-0000-0000-0000-000000000001"

SAMPLE_JOBS = [
    {
        "title": "Desenvolvedor Backend Senior",
        "department": "Tecnologia",
        "seniority": "senior",
        "location": "São Paulo, SP",
        "work_model": "hybrid",
        "skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "AWS", "Redis", "Celery"],
        "behavioral": ["Comunicação", "Liderança Técnica", "Resolução de Problemas"],
        "salary_min": 18000,
        "salary_max": 25000,
        "ttf_days": 35,
        "outcome": "filled"
    },
    {
        "title": "Desenvolvedor Frontend Pleno",
        "department": "Tecnologia",
        "seniority": "pleno",
        "location": "São Paulo, SP",
        "work_model": "remote",
        "skills": ["React", "TypeScript", "Next.js", "Tailwind CSS", "Jest", "Git"],
        "behavioral": ["Colaboração", "Atenção a Detalhes", "Proatividade"],
        "salary_min": 10000,
        "salary_max": 15000,
        "ttf_days": 28,
        "outcome": "filled"
    },
    {
        "title": "Product Manager",
        "department": "Produto",
        "seniority": "senior",
        "location": "São Paulo, SP",
        "work_model": "hybrid",
        "skills": ["Product Discovery", "Roadmap", "OKRs", "SQL", "Analytics", "Jira"],
        "behavioral": ["Comunicação", "Visão Estratégica", "Negociação", "Liderança"],
        "salary_min": 20000,
        "salary_max": 30000,
        "ttf_days": 45,
        "outcome": "filled"
    },
    {
        "title": "Analista de Dados Senior",
        "department": "Dados",
        "seniority": "senior",
        "location": "Rio de Janeiro, RJ",
        "work_model": "remote",
        "skills": ["Python", "SQL", "Power BI", "Tableau", "BigQuery", "Pandas"],
        "behavioral": ["Pensamento Analítico", "Comunicação", "Atenção a Detalhes"],
        "salary_min": 15000,
        "salary_max": 22000,
        "ttf_days": 32,
        "outcome": "filled"
    },
    {
        "title": "Engenheiro DevOps",
        "department": "Infraestrutura",
        "seniority": "pleno",
        "location": "Belo Horizonte, MG",
        "work_model": "remote",
        "skills": ["Kubernetes", "Docker", "Terraform", "AWS", "CI/CD", "Linux", "Python"],
        "behavioral": ["Resolução de Problemas", "Trabalho em Equipe", "Aprendizado Contínuo"],
        "salary_min": 14000,
        "salary_max": 20000,
        "ttf_days": 40,
        "outcome": "filled"
    },
    {
        "title": "Designer UX/UI Senior",
        "department": "Design",
        "seniority": "senior",
        "location": "São Paulo, SP",
        "work_model": "hybrid",
        "skills": ["Figma", "Design System", "User Research", "Prototipagem", "Usabilidade"],
        "behavioral": ["Criatividade", "Empatia", "Comunicação", "Colaboração"],
        "salary_min": 15000,
        "salary_max": 22000,
        "ttf_days": 30,
        "outcome": "filled"
    },
    {
        "title": "Analista de RH Pleno",
        "department": "Recursos Humanos",
        "seniority": "pleno",
        "location": "São Paulo, SP",
        "work_model": "hybrid",
        "skills": ["Recrutamento", "Entrevistas", "ATS", "Excel", "Onboarding"],
        "behavioral": ["Comunicação", "Organização", "Empatia", "Discrição"],
        "salary_min": 6000,
        "salary_max": 9000,
        "ttf_days": 25,
        "outcome": "filled"
    },
    {
        "title": "Gerente de Projetos",
        "department": "PMO",
        "seniority": "senior",
        "location": "Campinas, SP",
        "work_model": "hybrid",
        "skills": ["Scrum", "Kanban", "MS Project", "Jira", "Gestão de Riscos", "PMP"],
        "behavioral": ["Liderança", "Comunicação", "Negociação", "Organização"],
        "salary_min": 18000,
        "salary_max": 28000,
        "ttf_days": 50,
        "outcome": "filled"
    },
    {
        "title": "Analista de Marketing Digital",
        "department": "Marketing",
        "seniority": "pleno",
        "location": "São Paulo, SP",
        "work_model": "remote",
        "skills": ["Google Ads", "Facebook Ads", "SEO", "Analytics", "CRM", "Email Marketing"],
        "behavioral": ["Criatividade", "Análise de Dados", "Comunicação"],
        "salary_min": 7000,
        "salary_max": 11000,
        "ttf_days": 22,
        "outcome": "filled"
    },
    {
        "title": "Engenheiro de Machine Learning",
        "department": "Dados",
        "seniority": "senior",
        "location": "São Paulo, SP",
        "work_model": "remote",
        "skills": ["Python", "TensorFlow", "PyTorch", "MLOps", "SQL", "AWS SageMaker"],
        "behavioral": ["Pensamento Analítico", "Resolução de Problemas", "Comunicação Técnica"],
        "salary_min": 22000,
        "salary_max": 35000,
        "ttf_days": 55,
        "outcome": "filled"
    },
    {
        "title": "Analista Financeiro",
        "department": "Financeiro",
        "seniority": "pleno",
        "location": "São Paulo, SP",
        "work_model": "onsite",
        "skills": ["Excel Avançado", "SAP", "Power BI", "Contabilidade", "FP&A"],
        "behavioral": ["Atenção a Detalhes", "Organização", "Ética", "Comunicação"],
        "salary_min": 8000,
        "salary_max": 12000,
        "ttf_days": 28,
        "outcome": "filled"
    },
    {
        "title": "Desenvolvedor Mobile React Native",
        "department": "Tecnologia",
        "seniority": "pleno",
        "location": "Curitiba, PR",
        "work_model": "remote",
        "skills": ["React Native", "TypeScript", "Redux", "APIs REST", "Git", "Jest"],
        "behavioral": ["Proatividade", "Trabalho em Equipe", "Aprendizado Contínuo"],
        "salary_min": 11000,
        "salary_max": 16000,
        "ttf_days": 30,
        "outcome": "filled"
    },
]

SKILL_CLUSTERS = [
    {
        "name": "Backend Python",
        "type": "technical",
        "core": ["Python", "FastAPI", "Django", "Flask"],
        "related": ["PostgreSQL", "Redis", "Docker", "AWS", "Celery", "SQLAlchemy"]
    },
    {
        "name": "Frontend React",
        "type": "technical",
        "core": ["React", "TypeScript", "JavaScript"],
        "related": ["Next.js", "Redux", "Tailwind CSS", "Jest", "Webpack", "Vite"]
    },
    {
        "name": "DevOps Cloud",
        "type": "technical",
        "core": ["Docker", "Kubernetes", "AWS", "Terraform"],
        "related": ["CI/CD", "Linux", "Ansible", "Prometheus", "Grafana"]
    },
    {
        "name": "Data Science",
        "type": "technical",
        "core": ["Python", "SQL", "Machine Learning"],
        "related": ["Pandas", "Scikit-learn", "TensorFlow", "Power BI", "Spark"]
    },
    {
        "name": "Liderança Técnica",
        "type": "behavioral",
        "core": ["Liderança", "Comunicação", "Mentoria"],
        "related": ["Gestão de Conflitos", "Delegação", "Feedback", "Visão Estratégica"]
    },
    {
        "name": "Colaboração",
        "type": "behavioral",
        "core": ["Trabalho em Equipe", "Comunicação", "Colaboração"],
        "related": ["Empatia", "Flexibilidade", "Respeito", "Escuta Ativa"]
    },
]


async def seed_job_patterns():
    """Create sample job patterns."""
    logger.info("Seeding job patterns...")
    
    async with AsyncSessionLocal() as session:
        for job in SAMPLE_JOBS:
            pattern = JobPattern(
                company_id=SAMPLE_COMPANY_ID,
                pattern_type="job_title",
                pattern_key=job["title"].lower().replace(" ", "_"),
                job_title_normalized=job["title"].lower(),
                department=job["department"],
                seniority=job["seniority"],
                location=job["location"],
                work_model=job["work_model"],
                sample_count=random.randint(3, 15),
                success_count=random.randint(2, 10),
                avg_salary_min=job["salary_min"],
                avg_salary_max=job["salary_max"],
                salary_percentile_25=job["salary_min"] * 0.9,
                salary_percentile_75=job["salary_max"] * 1.1,
                common_skills=job["skills"],
                skill_frequency={skill: random.randint(5, 15) for skill in job["skills"]},
                common_behavioral=job["behavioral"],
                behavioral_frequency={b: random.randint(3, 10) for b in job["behavioral"]},
                avg_time_to_fill=job["ttf_days"],
                median_time_to_fill=job["ttf_days"] - 3,
                is_active=True,
                confidence=0.7 + random.random() * 0.25
            )
            pattern.calculate_success_rate()
            session.add(pattern)
        
        await session.commit()
        logger.info(f"Created {len(SAMPLE_JOBS)} job patterns")


async def seed_salary_benchmarks():
    """Create sample salary benchmarks."""
    logger.info("Seeding salary benchmarks...")
    
    benchmarks_data = [
        ("desenvolvedor backend", "Tecnologia", "senior", "São Paulo, SP", 18000, 25000),
        ("desenvolvedor backend", "Tecnologia", "pleno", "São Paulo, SP", 12000, 18000),
        ("desenvolvedor backend", "Tecnologia", "junior", "São Paulo, SP", 5000, 8000),
        ("desenvolvedor frontend", "Tecnologia", "senior", "São Paulo, SP", 16000, 23000),
        ("desenvolvedor frontend", "Tecnologia", "pleno", "São Paulo, SP", 10000, 15000),
        ("product manager", "Produto", "senior", "São Paulo, SP", 20000, 30000),
        ("product manager", "Produto", "pleno", "São Paulo, SP", 12000, 18000),
        ("analista de dados", "Dados", "senior", "São Paulo, SP", 15000, 22000),
        ("designer ux", "Design", "senior", "São Paulo, SP", 15000, 22000),
        ("devops", "Infraestrutura", "senior", "São Paulo, SP", 18000, 28000),
    ]
    
    async with AsyncSessionLocal() as session:
        for title, dept, seniority, location, min_sal, max_sal in benchmarks_data:
            avg_sal = (min_sal + max_sal) / 2
            benchmark = SalaryBenchmark(
                company_id=SAMPLE_COMPANY_ID,
                job_title_normalized=title,
                department=dept,
                seniority=seniority,
                location=location,
                min_salary=min_sal,
                max_salary=max_sal,
                avg_salary=avg_sal,
                median_salary=avg_sal,
                percentile_10=min_sal * 0.85,
                percentile_25=min_sal * 0.95,
                percentile_50=avg_sal,
                percentile_75=max_sal * 0.95,
                percentile_90=max_sal * 1.05,
                sample_count=random.randint(5, 20)
            )
            session.add(benchmark)
        
        await session.commit()
        logger.info(f"Created {len(benchmarks_data)} salary benchmarks")


async def seed_skill_clusters():
    """Create sample skill clusters."""
    logger.info("Seeding skill clusters...")
    
    async with AsyncSessionLocal() as session:
        for cluster in SKILL_CLUSTERS:
            skill_cluster = SkillCluster(
                company_id=SAMPLE_COMPANY_ID,
                cluster_name=cluster["name"],
                cluster_type=cluster["type"],
                core_skills=cluster["core"],
                related_skills=cluster["related"],
                skill_cooccurrence={
                    skill: random.randint(3, 10) 
                    for skill in cluster["core"] + cluster["related"]
                },
                job_titles=[],
                departments=[],
                sample_count=random.randint(10, 50),
                is_active=True
            )
            session.add(skill_cluster)
        
        await session.commit()
        logger.info(f"Created {len(SKILL_CLUSTERS)} skill clusters")


async def seed_job_embeddings():
    """Create sample job embeddings (without actual vectors for now)."""
    logger.info("Seeding job embeddings...")
    
    async with AsyncSessionLocal() as session:
        for i, job in enumerate(SAMPLE_JOBS):
            embedding = JobEmbedding(
                company_id=SAMPLE_COMPANY_ID,
                job_id=str(uuid4()),
                job_title=job["title"],
                job_title_normalized=job["title"].lower(),
                department=job["department"],
                seniority=job["seniority"],
                location=job["location"],
                work_model=job["work_model"],
                skills=job["skills"],
                behavioral_competencies=job["behavioral"],
                outcome_status=job["outcome"],
                time_to_fill_days=job["ttf_days"],
                is_template=(i < 3),
                is_active=True,
                embedding_text=JobEmbedding.create_embedding_text(
                    job_title=job["title"],
                    department=job["department"],
                    seniority=job["seniority"],
                    location=job["location"],
                    skills=job["skills"],
                    behavioral=job["behavioral"]
                )
            )
            session.add(embedding)
        
        await session.commit()
        logger.info(f"Created {len(SAMPLE_JOBS)} job embeddings (vectors pending)")


async def main():
    """Run all seed operations."""
    logger.info("Starting seed process...")
    
    try:
        await seed_job_patterns()
        await seed_salary_benchmarks()
        await seed_skill_clusters()
        await seed_job_embeddings()
        
        logger.info("Seed process completed successfully!")
        logger.info("Note: Job embeddings were created without vectors.")
        logger.info("Use the /job-embeddings/batch-process endpoint to generate embeddings.")
        
    except Exception as e:
        logger.error(f"Seed process failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
