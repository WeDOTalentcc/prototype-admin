"""
Seed Service - Populates database with demo/test data.
All seed data is clearly marked with '[DEMO]' prefix for easy identification.
"""

# RAILS-DEPRECATED: This service performs CRUD for Rails-owned entities.
# Will be deleted after ats-api-rails handoff is complete.
# Do NOT migrate to a domain -- route through integrations_hub/rails_adapter instead.

import warnings
warnings.warn(
    "seed_service is deprecated and will be removed once Rails adapter routes are complete. "
    "Migrate callers to rails_adapter equivalents. "
    "See UC-P1-22 in the remediation plan (CROSS_CUTTING_AUDIT_AND_REMEDIATION_PLAN.md).",
    DeprecationWarning,
    stacklevel=2,
)

import logging
import random
import uuid
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.candidate import Candidate, CandidateEducation, CandidateExperience, VacancyCandidate
from lia_models.job_vacancy import JobVacancy

logger = logging.getLogger(__name__)

COMPANY_ID: str | None = None

def get_seed_company_id() -> str:
    if not COMPANY_ID:
        raise ValueError("COMPANY_ID must be set before seeding data. Set seed_service.COMPANY_ID = '<your_tenant_id>'")
    return COMPANY_ID


def generate_demo_job_vacancies() -> list[dict[str, Any]]:
    """Generate realistic demo job vacancies for different departments."""
    
    recruiters = [
        {"name": "Ana Paula Santos", "email": "ana.santos@wedotalent.com"},
        {"name": "Carlos Eduardo Lima", "email": "carlos.lima@wedotalent.com"},
        {"name": "Mariana Costa", "email": "mariana.costa@wedotalent.com"},
        {"name": "Rafael Oliveira", "email": "rafael.oliveira@wedotalent.com"},
    ]
    
    managers = [
        {"name": "João Paulo Silva", "email": "joao.silva@empresa.com", "dept": "Tecnologia"},
        {"name": "Fernanda Almeida", "email": "fernanda.almeida@empresa.com", "dept": "Tecnologia"},
        {"name": "Ricardo Mendes", "email": "ricardo.mendes@empresa.com", "dept": "Produto"},
        {"name": "Patrícia Souza", "email": "patricia.souza@empresa.com", "dept": "RH"},
        {"name": "Bruno Costa", "email": "bruno.costa@empresa.com", "dept": "Comercial"},
        {"name": "Camila Ferreira", "email": "camila.ferreira@empresa.com", "dept": "Marketing"},
    ]
    
    jobs = [
        {
            "title": "[DEMO] Desenvolvedor(a) Full Stack Sênior",
            "department": "Tecnologia",
            "location": "São Paulo, SP",
            "work_model": "Híbrido",
            "employment_type": "CLT",
            "seniority_level": "Sênior",
            "description": "Buscamos um desenvolvedor Full Stack Sênior para liderar projetos de alta complexidade, mentor de desenvolvedores júniors e participar das decisões técnicas do time.",
            "requirements": ["5+ anos de experiência", "React/Next.js", "Node.js/Python", "PostgreSQL", "Docker/Kubernetes", "CI/CD"],
            "technical_requirements": [
                {"category": "Frontend", "technology": "React", "level": "Avançado", "required": True},
                {"category": "Frontend", "technology": "Next.js", "level": "Avançado", "required": True},
                {"category": "Backend", "technology": "Node.js", "level": "Avançado", "required": True},
                {"category": "Backend", "technology": "Python", "level": "Intermediário", "required": False},
                {"category": "Database", "technology": "PostgreSQL", "level": "Avançado", "required": True},
            ],
            "languages": [{"language": "Inglês", "level": "Avançado", "required": True}],
            "behavioral_competencies": [
                {"competency": "Liderança Técnica", "weight": "Essencial"},
                {"competency": "Comunicação", "weight": "Importante"},
                {"competency": "Resolução de Problemas", "weight": "Essencial"},
            ],
            "salary_range": {"min": 18000, "max": 25000, "currency": "BRL"},
            "benefits": ["VR R$45/dia", "Plano de Saúde Unimed", "PLR", "Home Office 3x/semana", "Gympass"],
            "status": "Ativa",
            "stage": "Triagem",
            "priority": "alta",
            "urgency_level": 5,
            "nps": 85,
            "funnel_data": {"total": 48, "screening": 32, "interview": 12, "final": 4, "hired": 1},
            "screening_questions": [
                {"id": "1", "question": "Qual sua experiência com arquitetura de microsserviços?", "type": "text", "weight": 5},
                {"id": "2", "question": "Já liderou times técnicos? Quantas pessoas?", "type": "text", "weight": 4},
                {"id": "3", "question": "Qual sua pretensão salarial?", "type": "text", "weight": 3},
            ],
            "screening_config": {
                "channels": {"whatsapp": {"enabled": True, "label": "Principal"}, "chat_web": {"enabled": True, "label": "Website"}, "phone": {"enabled": False, "label": "Inativo"}},
                "settings": {"min_score": 75, "response_timeout_hours": 48},
                "metrics": {"screened_count": 156, "completion_rate": 82, "average_rating": 4.2},
                "scheduling": {"auto_enabled": True, "min_score_for_auto": 80, "calendar_provider": "Google", "available_hours": "9h-18h", "interview_duration_min": 60},
                "feedback_templates": {"approved": "Parabéns! Seu perfil está alinhado com a vaga.", "rejected": "Agradecemos seu interesse, mas optamos por outros perfis."}
            },
        },
        {
            "title": "[DEMO] Product Manager Pleno",
            "department": "Produto",
            "location": "São Paulo, SP",
            "work_model": "Remoto",
            "employment_type": "CLT",
            "seniority_level": "Pleno",
            "description": "Procuramos Product Manager para liderar a estratégia de produto da nossa plataforma B2B SaaS, trabalhando próximo ao time de engenharia e stakeholders.",
            "requirements": ["3+ anos como PM", "Metodologias ágeis", "Métricas de produto", "SQL básico", "Inglês fluente"],
            "technical_requirements": [
                {"category": "Ferramentas", "technology": "Jira/Trello", "level": "Avançado", "required": True},
                {"category": "Analytics", "technology": "Amplitude/Mixpanel", "level": "Intermediário", "required": True},
                {"category": "Data", "technology": "SQL", "level": "Básico", "required": False},
            ],
            "languages": [{"language": "Inglês", "level": "Fluente", "required": True}],
            "behavioral_competencies": [
                {"competency": "Visão Estratégica", "weight": "Essencial"},
                {"competency": "Comunicação", "weight": "Essencial"},
                {"competency": "Liderança sem Autoridade", "weight": "Importante"},
            ],
            "salary_range": {"min": 15000, "max": 20000, "currency": "BRL"},
            "benefits": ["VR R$40/dia", "Plano de Saúde", "PLR", "100% Remoto", "Budget de aprendizado"],
            "status": "Ativa",
            "stage": "Entrevistas",
            "priority": "alta",
            "urgency_level": 4,
            "nps": 78,
            "funnel_data": {"total": 35, "screening": 25, "interview": 8, "final": 3, "hired": 0},
            "screening_questions": [
                {"id": "1", "question": "Descreva um produto que você lançou do zero ao mercado.", "type": "text", "weight": 5},
                {"id": "2", "question": "Como você prioriza features no backlog?", "type": "text", "weight": 4},
            ],
            "screening_config": {
                "channels": {"whatsapp": {"enabled": True, "label": "Principal"}, "chat_web": {"enabled": True, "label": "Site Carreiras"}, "phone": {"enabled": True, "label": "Ativo"}},
                "settings": {"min_score": 70, "response_timeout_hours": 72},
                "metrics": {"screened_count": 89, "completion_rate": 78, "average_rating": 4.5},
                "scheduling": {"auto_enabled": True, "min_score_for_auto": 75, "calendar_provider": "Google", "available_hours": "10h-17h", "interview_duration_min": 45},
                "feedback_templates": {"approved": "Excelente! Você avançou para entrevistas.", "rejected": "Obrigado pelo interesse na posição."}
            },
        },
        {
            "title": "[DEMO] UX/UI Designer Sênior",
            "department": "Design",
            "location": "Rio de Janeiro, RJ",
            "work_model": "Híbrido",
            "employment_type": "CLT",
            "seniority_level": "Sênior",
            "description": "Designer sênior para criar experiências incríveis em nossa plataforma, trabalhando com pesquisa de usuário, prototipação e design system.",
            "requirements": ["5+ anos UX/UI", "Figma avançado", "Design Systems", "Pesquisa de usuário", "Portfólio online"],
            "technical_requirements": [
                {"category": "Design", "technology": "Figma", "level": "Avançado", "required": True},
                {"category": "Design", "technology": "Design Systems", "level": "Avançado", "required": True},
                {"category": "Research", "technology": "User Research", "level": "Intermediário", "required": True},
            ],
            "languages": [{"language": "Inglês", "level": "Intermediário", "required": False}],
            "behavioral_competencies": [
                {"competency": "Criatividade", "weight": "Essencial"},
                {"competency": "Empatia com Usuário", "weight": "Essencial"},
                {"competency": "Colaboração", "weight": "Importante"},
            ],
            "salary_range": {"min": 12000, "max": 18000, "currency": "BRL"},
            "benefits": ["VR R$35/dia", "Plano de Saúde", "Auxílio Home Office", "Gympass"],
            "status": "Ativa",
            "stage": "Publicada",
            "priority": "média",
            "urgency_level": 3,
            "nps": 92,
            "funnel_data": {"total": 28, "screening": 18, "interview": 6, "final": 2, "hired": 0},
            "screening_questions": [
                {"id": "1", "question": "Qual projeto no seu portfólio você mais se orgulha? Por quê?", "type": "text", "weight": 5},
                {"id": "2", "question": "Como você conduz pesquisas com usuários?", "type": "text", "weight": 4},
            ],
            "screening_config": {
                "channels": {"whatsapp": {"enabled": True, "label": "Principal"}, "chat_web": {"enabled": False, "label": "Desabilitado"}, "phone": {"enabled": False, "label": "Inativo"}},
                "settings": {"min_score": 65, "response_timeout_hours": 48},
                "metrics": {"screened_count": 67, "completion_rate": 85, "average_rating": 4.7},
                "scheduling": {"auto_enabled": True, "min_score_for_auto": 70, "calendar_provider": "Outlook", "available_hours": "9h-17h", "interview_duration_min": 30},
                "feedback_templates": {"approved": "Seu portfólio chamou nossa atenção!", "rejected": "Agradecemos a candidatura."}
            },
        },
        {
            "title": "[DEMO] Analista de Dados Pleno",
            "department": "Dados",
            "location": "São Paulo, SP",
            "work_model": "Remoto",
            "employment_type": "CLT",
            "seniority_level": "Pleno",
            "description": "Analista de dados para transformar dados em insights acionáveis, criar dashboards e apoiar decisões de negócio com análises avançadas.",
            "requirements": ["3+ anos análise de dados", "Python/R", "SQL avançado", "Power BI/Tableau", "Estatística"],
            "technical_requirements": [
                {"category": "Linguagem", "technology": "Python", "level": "Avançado", "required": True},
                {"category": "Database", "technology": "SQL", "level": "Avançado", "required": True},
                {"category": "Visualização", "technology": "Power BI", "level": "Avançado", "required": True},
            ],
            "languages": [{"language": "Inglês", "level": "Intermediário", "required": True}],
            "behavioral_competencies": [
                {"competency": "Pensamento Analítico", "weight": "Essencial"},
                {"competency": "Atenção a Detalhes", "weight": "Essencial"},
                {"competency": "Comunicação de Dados", "weight": "Importante"},
            ],
            "salary_range": {"min": 10000, "max": 14000, "currency": "BRL"},
            "benefits": ["VR R$35/dia", "Plano de Saúde", "PLR", "100% Remoto"],
            "status": "Ativa",
            "stage": "Triagem",
            "priority": "média",
            "urgency_level": 3,
            "nps": 75,
            "funnel_data": {"total": 52, "screening": 38, "interview": 10, "final": 3, "hired": 0},
            "screening_questions": [
                {"id": "1", "question": "Qual ferramenta de BI você domina melhor?", "type": "text", "weight": 4},
                {"id": "2", "question": "Descreva uma análise que gerou impacto real no negócio.", "type": "text", "weight": 5},
            ],
            "screening_config": {
                "channels": {"whatsapp": {"enabled": True, "label": "Principal"}, "chat_web": {"enabled": True, "label": "Website"}, "phone": {"enabled": False, "label": "Inativo"}},
                "settings": {"min_score": 70, "response_timeout_hours": 24},
                "metrics": {"screened_count": 134, "completion_rate": 74, "average_rating": 4.0},
                "scheduling": {"auto_enabled": True, "min_score_for_auto": 75, "calendar_provider": "Google", "available_hours": "8h-18h", "interview_duration_min": 45},
                "feedback_templates": {"approved": "Seus dados mostram grande potencial!", "rejected": "Obrigado pelo interesse."}
            },
        },
        {
            "title": "[DEMO] DevOps Engineer Sênior",
            "department": "Infraestrutura",
            "location": "São Paulo, SP",
            "work_model": "Híbrido",
            "employment_type": "CLT",
            "seniority_level": "Sênior",
            "description": "DevOps Engineer para otimizar nossa infraestrutura em nuvem, automação de deployments e garantir alta disponibilidade dos sistemas.",
            "requirements": ["5+ anos DevOps", "AWS/GCP", "Kubernetes", "Terraform", "CI/CD", "Monitoramento"],
            "technical_requirements": [
                {"category": "Cloud", "technology": "AWS", "level": "Avançado", "required": True},
                {"category": "Containers", "technology": "Kubernetes", "level": "Avançado", "required": True},
                {"category": "IaC", "technology": "Terraform", "level": "Avançado", "required": True},
            ],
            "languages": [{"language": "Inglês", "level": "Avançado", "required": True}],
            "behavioral_competencies": [
                {"competency": "Resolução de Problemas", "weight": "Essencial"},
                {"competency": "Proatividade", "weight": "Essencial"},
                {"competency": "Documentação", "weight": "Importante"},
            ],
            "salary_range": {"min": 20000, "max": 28000, "currency": "BRL"},
            "benefits": ["VR R$50/dia", "Plano de Saúde Premium", "PLR", "Stock Options", "Gympass"],
            "status": "Ativa",
            "stage": "Finalização",
            "priority": "alta",
            "urgency_level": 5,
            "nps": 88,
            "funnel_data": {"total": 22, "screening": 15, "interview": 5, "final": 2, "hired": 1},
            "screening_questions": [
                {"id": "1", "question": "Qual certificação AWS você possui?", "type": "text", "weight": 4},
                {"id": "2", "question": "Descreva como você implementaria zero-downtime deployment.", "type": "text", "weight": 5},
            ],
            "screening_config": {
                "channels": {"whatsapp": {"enabled": True, "label": "Preferencial"}, "chat_web": {"enabled": True, "label": "Website"}, "phone": {"enabled": True, "label": "Backup"}},
                "settings": {"min_score": 80, "response_timeout_hours": 48},
                "metrics": {"screened_count": 45, "completion_rate": 91, "average_rating": 4.8},
                "scheduling": {"auto_enabled": True, "min_score_for_auto": 85, "calendar_provider": "Google", "available_hours": "9h-19h", "interview_duration_min": 60},
                "feedback_templates": {"approved": "Sua expertise técnica é impressionante!", "rejected": "Agradecemos seu interesse na vaga."}
            },
        },
        {
            "title": "[DEMO] Executivo(a) de Contas Enterprise",
            "department": "Comercial",
            "location": "São Paulo, SP",
            "work_model": "Presencial",
            "employment_type": "CLT",
            "seniority_level": "Sênior",
            "description": "Executivo de vendas enterprise para conquistar grandes contas, com foco em vendas consultivas B2B de alto valor.",
            "requirements": ["5+ anos vendas B2B", "Experiência Enterprise", "Inglês fluente", "Histórico de quota 100%+"],
            "technical_requirements": [
                {"category": "CRM", "technology": "Salesforce", "level": "Avançado", "required": True},
                {"category": "Metodologia", "technology": "SPIN Selling", "level": "Intermediário", "required": False},
            ],
            "languages": [{"language": "Inglês", "level": "Fluente", "required": True}],
            "behavioral_competencies": [
                {"competency": "Negociação", "weight": "Essencial"},
                {"competency": "Resiliência", "weight": "Essencial"},
                {"competency": "Relacionamento", "weight": "Essencial"},
            ],
            "salary_range": {"min": 15000, "max": 25000, "currency": "BRL"},
            "benefits": ["VR R$45/dia", "Plano de Saúde", "Comissão agressiva", "Carro corporativo"],
            "status": "Ativa",
            "stage": "Aprovação",
            "priority": "alta",
            "urgency_level": 4,
            "nps": 70,
            "funnel_data": {"total": 18, "screening": 12, "interview": 5, "final": 2, "hired": 0},
            "screening_questions": [
                {"id": "1", "question": "Qual foi seu maior deal fechado? Valor e duração do ciclo.", "type": "text", "weight": 5},
                {"id": "2", "question": "Quanto atingiu da sua quota nos últimos 2 anos?", "type": "text", "weight": 5},
            ],
            "screening_config": {
                "channels": {"whatsapp": {"enabled": True, "label": "Principal"}, "chat_web": {"enabled": False, "label": "Desabilitado"}, "phone": {"enabled": True, "label": "Ativo"}},
                "settings": {"min_score": 70, "response_timeout_hours": 24},
                "metrics": {"screened_count": 52, "completion_rate": 68, "average_rating": 3.9},
                "scheduling": {"auto_enabled": False, "min_score_for_auto": 80, "calendar_provider": "Google", "available_hours": "10h-18h", "interview_duration_min": 45},
                "feedback_templates": {"approved": "Seu perfil comercial está alinhado!", "rejected": "Obrigado pela candidatura."}
            },
        },
        {
            "title": "[DEMO] Desenvolvedor(a) Backend Júnior",
            "department": "Tecnologia",
            "location": "Campinas, SP",
            "work_model": "Híbrido",
            "employment_type": "CLT",
            "seniority_level": "Júnior",
            "description": "Desenvolvedor(a) backend júnior para crescer em nosso time, aprendendo com devs sêniors e contribuindo em projetos reais.",
            "requirements": ["1+ ano programação", "Python ou Node.js", "Git básico", "SQL básico", "Vontade de aprender"],
            "technical_requirements": [
                {"category": "Backend", "technology": "Python", "level": "Básico", "required": True},
                {"category": "Database", "technology": "SQL", "level": "Básico", "required": True},
                {"category": "Versionamento", "technology": "Git", "level": "Básico", "required": True},
            ],
            "languages": [{"language": "Inglês", "level": "Básico", "required": False}],
            "behavioral_competencies": [
                {"competency": "Curiosidade", "weight": "Essencial"},
                {"competency": "Proatividade", "weight": "Importante"},
                {"competency": "Trabalho em Equipe", "weight": "Importante"},
            ],
            "salary_range": {"min": 4000, "max": 6000, "currency": "BRL"},
            "benefits": ["VR R$30/dia", "Plano de Saúde", "Mentoria sênior", "Cursos pagos"],
            "status": "Ativa",
            "stage": "Publicada",
            "priority": "média",
            "urgency_level": 2,
            "nps": 90,
            "funnel_data": {"total": 85, "screening": 60, "interview": 15, "final": 5, "hired": 0},
            "screening_questions": [
                {"id": "1", "question": "Qual linguagem de programação você mais gosta? Por quê?", "type": "text", "weight": 3},
                {"id": "2", "question": "Tem algum projeto pessoal para mostrar?", "type": "text", "weight": 4},
            ],
            "screening_config": {
                "channels": {"whatsapp": {"enabled": True, "label": "Principal"}, "chat_web": {"enabled": True, "label": "Website"}, "phone": {"enabled": False, "label": "Inativo"}},
                "settings": {"min_score": 60, "response_timeout_hours": 72},
                "metrics": {"screened_count": 245, "completion_rate": 72, "average_rating": 4.1},
                "scheduling": {"auto_enabled": True, "min_score_for_auto": 65, "calendar_provider": "Google", "available_hours": "9h-18h", "interview_duration_min": 30},
                "feedback_templates": {"approved": "Queremos conhecer mais sobre você!", "rejected": "Agradecemos o interesse."}
            },
        },
        {
            "title": "[DEMO] Coordenador(a) de RH",
            "department": "Recursos Humanos",
            "location": "São Paulo, SP",
            "work_model": "Híbrido",
            "employment_type": "CLT",
            "seniority_level": "Pleno",
            "description": "Coordenador de RH para liderar iniciativas de people, cultura organizacional e desenvolvimento de talentos.",
            "requirements": ["4+ anos RH", "Gestão de pessoas", "DHO", "R&S", "Inglês intermediário"],
            "technical_requirements": [
                {"category": "RH", "technology": "HRIS (Gupy/ADP)", "level": "Avançado", "required": True},
                {"category": "Analytics", "technology": "People Analytics", "level": "Intermediário", "required": False},
            ],
            "languages": [{"language": "Inglês", "level": "Intermediário", "required": True}],
            "behavioral_competencies": [
                {"competency": "Empatia", "weight": "Essencial"},
                {"competency": "Comunicação", "weight": "Essencial"},
                {"competency": "Organização", "weight": "Importante"},
            ],
            "salary_range": {"min": 10000, "max": 14000, "currency": "BRL"},
            "benefits": ["VR R$35/dia", "Plano de Saúde", "Desconto academia", "Day off aniversário"],
            "status": "Paralisada",
            "stage": "Triagem",
            "priority": "baixa",
            "urgency_level": 1,
            "nps": 65,
            "funnel_data": {"total": 42, "screening": 30, "interview": 8, "final": 2, "hired": 0},
            "screening_questions": [
                {"id": "1", "question": "Qual sua experiência com gestão de clima organizacional?", "type": "text", "weight": 4},
                {"id": "2", "question": "Como você mede o sucesso de iniciativas de RH?", "type": "text", "weight": 4},
            ],
            "screening_config": {
                "channels": {"whatsapp": {"enabled": True, "label": "Principal"}, "chat_web": {"enabled": True, "label": "Carreiras"}, "phone": {"enabled": True, "label": "Ativo"}},
                "settings": {"min_score": 65, "response_timeout_hours": 48},
                "metrics": {"screened_count": 98, "completion_rate": 80, "average_rating": 4.3},
                "scheduling": {"auto_enabled": True, "min_score_for_auto": 70, "calendar_provider": "Outlook", "available_hours": "9h-17h", "interview_duration_min": 45},
                "feedback_templates": {"approved": "Seu perfil de RH é interessante!", "rejected": "Obrigado pela candidatura."}
            },
        },
        {
            "title": "[DEMO] Tech Lead Mobile",
            "department": "Tecnologia",
            "location": "Florianópolis, SC",
            "work_model": "Remoto",
            "employment_type": "PJ",
            "seniority_level": "Especialista",
            "description": "Tech Lead para liderar nosso squad mobile, definindo arquitetura e mentorando desenvolvedores iOS e Android.",
            "requirements": ["6+ anos mobile", "React Native ou Flutter", "Liderança técnica", "Arquitetura mobile", "CI/CD mobile"],
            "technical_requirements": [
                {"category": "Mobile", "technology": "React Native", "level": "Avançado", "required": True},
                {"category": "Mobile", "technology": "Swift/Kotlin", "level": "Intermediário", "required": False},
                {"category": "Arquitetura", "technology": "Clean Architecture", "level": "Avançado", "required": True},
            ],
            "languages": [{"language": "Inglês", "level": "Avançado", "required": True}],
            "behavioral_competencies": [
                {"competency": "Liderança Técnica", "weight": "Essencial"},
                {"competency": "Mentoria", "weight": "Essencial"},
                {"competency": "Visão de Produto", "weight": "Importante"},
            ],
            "salary_range": {"min": 22000, "max": 30000, "currency": "BRL"},
            "benefits": ["100% Remoto", "Hardware fornecido", "Budget de aprendizado", "Flexibilidade horária"],
            "status": "Ativa",
            "stage": "Triagem",
            "priority": "alta",
            "urgency_level": 4,
            "nps": 82,
            "funnel_data": {"total": 15, "screening": 10, "interview": 4, "final": 1, "hired": 0},
            "screening_questions": [
                {"id": "1", "question": "Já liderou squad mobile? Quantas pessoas?", "type": "text", "weight": 5},
                {"id": "2", "question": "React Native ou Flutter? Justifique sua preferência.", "type": "text", "weight": 4},
            ],
            "screening_config": {
                "channels": {"whatsapp": {"enabled": True, "label": "Preferencial"}, "chat_web": {"enabled": True, "label": "Website"}, "phone": {"enabled": False, "label": "Inativo"}},
                "settings": {"min_score": 75, "response_timeout_hours": 48},
                "metrics": {"screened_count": 38, "completion_rate": 87, "average_rating": 4.6},
                "scheduling": {"auto_enabled": True, "min_score_for_auto": 80, "calendar_provider": "Google", "available_hours": "10h-19h", "interview_duration_min": 60},
                "feedback_templates": {"approved": "Sua liderança técnica é muito valorizada!", "rejected": "Agradecemos seu interesse."}
            },
        },
        {
            "title": "[DEMO] Gerente de Marketing Digital",
            "department": "Marketing",
            "location": "São Paulo, SP",
            "work_model": "Híbrido",
            "employment_type": "CLT",
            "seniority_level": "Sênior",
            "description": "Gerente de Marketing Digital para liderar estratégias de aquisição, branding e growth, gerenciando equipe multidisciplinar.",
            "requirements": ["5+ anos marketing digital", "Gestão de equipe", "Performance marketing", "Branding", "Budget management"],
            "technical_requirements": [
                {"category": "Marketing", "technology": "Google Ads", "level": "Avançado", "required": True},
                {"category": "Analytics", "technology": "Google Analytics 4", "level": "Avançado", "required": True},
                {"category": "Automação", "technology": "HubSpot/RD Station", "level": "Intermediário", "required": True},
            ],
            "languages": [{"language": "Inglês", "level": "Fluente", "required": True}],
            "behavioral_competencies": [
                {"competency": "Liderança", "weight": "Essencial"},
                {"competency": "Pensamento Estratégico", "weight": "Essencial"},
                {"competency": "Criatividade", "weight": "Importante"},
            ],
            "salary_range": {"min": 18000, "max": 25000, "currency": "BRL"},
            "benefits": ["VR R$45/dia", "Plano de Saúde Premium", "PLR", "Home Office 2x/semana"],
            "status": "Concluída",
            "stage": "Encerrada",
            "priority": "média",
            "urgency_level": 1,
            "nps": 95,
            "funnel_data": {"total": 45, "screening": 32, "interview": 10, "final": 3, "hired": 1},
            "screening_questions": [
                {"id": "1", "question": "Qual foi o maior budget que você gerenciou?", "type": "text", "weight": 4},
                {"id": "2", "question": "Descreva uma campanha de sucesso que você liderou.", "type": "text", "weight": 5},
            ],
            "screening_config": {
                "channels": {"whatsapp": {"enabled": True, "label": "Principal"}, "chat_web": {"enabled": True, "label": "Website"}, "phone": {"enabled": True, "label": "Ativo"}},
                "settings": {"min_score": 70, "response_timeout_hours": 48},
                "metrics": {"screened_count": 112, "completion_rate": 76, "average_rating": 4.4},
                "scheduling": {"auto_enabled": True, "min_score_for_auto": 75, "calendar_provider": "Google", "available_hours": "9h-18h", "interview_duration_min": 45},
                "feedback_templates": {"approved": "Sua experiência em marketing é impressionante!", "rejected": "Obrigado pelo interesse."}
            },
        },
        {
            "title": "[DEMO] Desenvolvedor Backend Python",
            "department": "Tecnologia",
            "location": "São Paulo, SP",
            "work_model": "Remoto",
            "employment_type": "CLT",
            "seniority_level": "Pleno",
            "description": "Desenvolvedor Backend Python para integrar time de produto, desenvolvendo APIs e sistemas escaláveis.",
            "requirements": ["3+ anos Python", "FastAPI/Django", "PostgreSQL", "Docker", "Testes automatizados"],
            "technical_requirements": [
                {"category": "Backend", "technology": "Python", "level": "Avançado", "required": True},
                {"category": "Backend", "technology": "FastAPI", "level": "Avançado", "required": True},
                {"category": "Database", "technology": "PostgreSQL", "level": "Intermediário", "required": True},
            ],
            "languages": [{"language": "Inglês", "level": "Intermediário", "required": True}],
            "behavioral_competencies": [
                {"competency": "Trabalho em Equipe", "weight": "Essencial"},
                {"competency": "Atenção a Detalhes", "weight": "Importante"},
            ],
            "salary_range": {"min": 12000, "max": 16000, "currency": "BRL"},
            "benefits": ["VR R$40/dia", "Plano de Saúde", "100% Remoto", "PLR"],
            "status": "Concluída",
            "stage": "Encerrada",
            "priority": "alta",
            "urgency_level": 2,
            "nps": 88,
            "funnel_data": {"total": 68, "screening": 52, "interview": 18, "final": 5, "hired": 2},
            "screening_questions": [
                {"id": "1", "question": "Qual framework Python você mais domina?", "type": "text", "weight": 5},
                {"id": "2", "question": "Descreva sua experiência com testes automatizados.", "type": "text", "weight": 4},
            ],
            "screening_config": {
                "channels": {"whatsapp": {"enabled": True, "label": "Principal"}, "chat_web": {"enabled": True, "label": "Website"}, "phone": {"enabled": False, "label": "Inativo"}},
                "settings": {"min_score": 70, "response_timeout_hours": 48},
                "metrics": {"screened_count": 187, "completion_rate": 79, "average_rating": 4.2},
                "scheduling": {"auto_enabled": True, "min_score_for_auto": 75, "calendar_provider": "Google", "available_hours": "9h-18h", "interview_duration_min": 45},
                "feedback_templates": {"approved": "Suas habilidades em Python são excelentes!", "rejected": "Agradecemos sua candidatura."}
            },
        },
        {
            "title": "[DEMO] Analista de BI Sênior",
            "department": "Dados",
            "location": "Rio de Janeiro, RJ",
            "work_model": "Híbrido",
            "employment_type": "CLT",
            "seniority_level": "Sênior",
            "description": "Analista de BI Sênior para liderar projetos de análise de dados e criação de dashboards estratégicos.",
            "requirements": ["5+ anos BI", "SQL Avançado", "Power BI/Tableau", "Data Modeling", "Storytelling"],
            "technical_requirements": [
                {"category": "BI", "technology": "Power BI", "level": "Avançado", "required": True},
                {"category": "Database", "technology": "SQL Server", "level": "Avançado", "required": True},
                {"category": "Data", "technology": "Data Modeling", "level": "Avançado", "required": True},
            ],
            "languages": [{"language": "Inglês", "level": "Avançado", "required": True}],
            "behavioral_competencies": [
                {"competency": "Pensamento Analítico", "weight": "Essencial"},
                {"competency": "Comunicação", "weight": "Essencial"},
            ],
            "salary_range": {"min": 14000, "max": 20000, "currency": "BRL"},
            "benefits": ["VR R$42/dia", "Plano de Saúde Premium", "PLR", "Gympass"],
            "status": "Concluída",
            "stage": "Encerrada",
            "priority": "média",
            "urgency_level": 2,
            "nps": 92,
            "funnel_data": {"total": 38, "screening": 28, "interview": 12, "final": 4, "hired": 1},
            "screening_questions": [
                {"id": "1", "question": "Qual dashboard você mais se orgulha de ter criado?", "type": "text", "weight": 5},
                {"id": "2", "question": "Como você aborda a modelagem de dados?", "type": "text", "weight": 4},
            ],
            "screening_config": {
                "channels": {"whatsapp": {"enabled": True, "label": "Principal"}, "chat_web": {"enabled": True, "label": "Website"}, "phone": {"enabled": False, "label": "Inativo"}},
                "settings": {"min_score": 72, "response_timeout_hours": 48},
                "metrics": {"screened_count": 94, "completion_rate": 83, "average_rating": 4.5},
                "scheduling": {"auto_enabled": True, "min_score_for_auto": 78, "calendar_provider": "Outlook", "available_hours": "10h-18h", "interview_duration_min": 45},
                "feedback_templates": {"approved": "Sua expertise em BI é muito valorizada!", "rejected": "Obrigado pelo interesse na vaga."}
            },
        },
        {
            "title": "[DEMO] Engenheiro de QA Pleno",
            "department": "Tecnologia",
            "location": "Curitiba, PR",
            "work_model": "Remoto",
            "employment_type": "CLT",
            "seniority_level": "Pleno",
            "description": "Engenheiro de QA para garantir qualidade de software através de automação de testes e processos de CI/CD.",
            "requirements": ["3+ anos QA", "Automação de Testes", "Cypress/Selenium", "CI/CD", "API Testing"],
            "technical_requirements": [
                {"category": "QA", "technology": "Cypress", "level": "Avançado", "required": True},
                {"category": "QA", "technology": "Postman/API Testing", "level": "Avançado", "required": True},
                {"category": "DevOps", "technology": "GitHub Actions", "level": "Intermediário", "required": False},
            ],
            "languages": [{"language": "Inglês", "level": "Intermediário", "required": True}],
            "behavioral_competencies": [
                {"competency": "Atenção a Detalhes", "weight": "Essencial"},
                {"competency": "Proatividade", "weight": "Importante"},
            ],
            "salary_range": {"min": 9000, "max": 13000, "currency": "BRL"},
            "benefits": ["VR R$35/dia", "Plano de Saúde", "100% Remoto", "Auxílio Home Office"],
            "status": "Concluída",
            "stage": "Encerrada",
            "priority": "média",
            "urgency_level": 2,
            "nps": 85,
            "funnel_data": {"total": 55, "screening": 42, "interview": 15, "final": 4, "hired": 1},
            "screening_questions": [
                {"id": "1", "question": "Qual ferramenta de automação você mais domina?", "type": "text", "weight": 5},
                {"id": "2", "question": "Como você prioriza quais testes automatizar?", "type": "text", "weight": 4},
            ],
            "screening_config": {
                "channels": {"whatsapp": {"enabled": True, "label": "Principal"}, "chat_web": {"enabled": True, "label": "Website"}, "phone": {"enabled": False, "label": "Inativo"}},
                "settings": {"min_score": 68, "response_timeout_hours": 48},
                "metrics": {"screened_count": 143, "completion_rate": 81, "average_rating": 4.3},
                "scheduling": {"auto_enabled": True, "min_score_for_auto": 72, "calendar_provider": "Google", "available_hours": "9h-18h", "interview_duration_min": 45},
                "feedback_templates": {"approved": "Sua experiência em QA é excelente!", "rejected": "Agradecemos sua candidatura."}
            },
        },
        {
            "title": "[DEMO] Especialista em Segurança da Informação",
            "department": "Tecnologia",
            "location": "São Paulo, SP",
            "work_model": "Híbrido",
            "employment_type": "CLT",
            "seniority_level": "Especialista",
            "description": "Especialista em Segurança da Informação para liderar iniciativas de cybersecurity e compliance.",
            "requirements": ["6+ anos Segurança", "CISSP/CEH", "Pentest", "LGPD/SOC2", "Cloud Security"],
            "technical_requirements": [
                {"category": "Security", "technology": "Pentest", "level": "Avançado", "required": True},
                {"category": "Cloud", "technology": "AWS Security", "level": "Avançado", "required": True},
                {"category": "Compliance", "technology": "LGPD", "level": "Avançado", "required": True},
            ],
            "languages": [{"language": "Inglês", "level": "Fluente", "required": True}],
            "behavioral_competencies": [
                {"competency": "Pensamento Crítico", "weight": "Essencial"},
                {"competency": "Ética", "weight": "Essencial"},
            ],
            "salary_range": {"min": 22000, "max": 30000, "currency": "BRL"},
            "benefits": ["VR R$50/dia", "Plano de Saúde Premium", "PLR", "Stock Options"],
            "status": "Concluída",
            "stage": "Encerrada",
            "priority": "alta",
            "urgency_level": 3,
            "nps": 90,
            "funnel_data": {"total": 25, "screening": 18, "interview": 8, "final": 3, "hired": 1},
            "screening_questions": [
                {"id": "1", "question": "Qual certificação de segurança você possui?", "type": "text", "weight": 5},
                {"id": "2", "question": "Descreva um incidente de segurança que você gerenciou.", "type": "text", "weight": 5},
            ],
            "screening_config": {
                "channels": {"whatsapp": {"enabled": True, "label": "Preferencial"}, "chat_web": {"enabled": True, "label": "Website"}, "phone": {"enabled": True, "label": "Backup"}},
                "settings": {"min_score": 80, "response_timeout_hours": 24},
                "metrics": {"screened_count": 62, "completion_rate": 88, "average_rating": 4.7},
                "scheduling": {"auto_enabled": True, "min_score_for_auto": 85, "calendar_provider": "Google", "available_hours": "9h-18h", "interview_duration_min": 60},
                "feedback_templates": {"approved": "Sua expertise em segurança é impressionante!", "rejected": "Obrigado pelo interesse."}
            },
        },
    ]
    
    result = []
    for i, job in enumerate(jobs):
        recruiter = random.choice(recruiters)
        matching_managers = [m for m in managers if m["dept"] == job["department"]]
        manager = random.choice(matching_managers) if matching_managers else random.choice(managers)
        
        open_date = datetime.utcnow() - timedelta(days=random.randint(5, 60))
        deadline = open_date + timedelta(days=random.randint(30, 90))
        
        closed_at = None
        if job["status"] == "Concluída":
            days_to_fill = random.randint(15, 35)
            closed_at = open_date + timedelta(days=days_to_fill)
        
        job_record = {
            "id": str(uuid.uuid4()),
            "company_id": get_seed_company_id(),
            "job_id": f"WDT-2025-{str(i+1).zfill(3)}",
            "title": job["title"],
            "department": job["department"],
            "location": job["location"],
            "work_model": job["work_model"],
            "employment_type": job["employment_type"],
            "seniority_level": job["seniority_level"],
            "description": job["description"],
            "requirements": job["requirements"],
            "technical_requirements": job["technical_requirements"],
            "languages": job["languages"],
            "behavioral_competencies": job["behavioral_competencies"],
            "salary_range": job["salary_range"],
            "salary": f"R$ {job['salary_range']['min']:,} - R$ {job['salary_range']['max']:,}".replace(",", "."),
            "benefits": job["benefits"],
            "status": job["status"],
            "stage": job["stage"],
            "priority": job["priority"],
            "urgency_level": job["urgency_level"],
            "nps": job["nps"],
            "funnel_data": job["funnel_data"],
            "screening_questions": job["screening_questions"],
            "screening_config": job.get("screening_config"),
            "manager": manager["name"],
            "manager_email": manager["email"],
            "recruiter": recruiter["name"],
            "recruiter_email": recruiter["email"],
            "created_by": recruiter["email"],
            "open_date": open_date,
            "deadline": deadline,
            "closed_at": closed_at,
            "created_at": open_date,
            "updated_at": datetime.utcnow(),
            "is_confidential": random.choice([False, False, False, True]),
            "is_affirmative": random.choice([False, False, True]),
            "published_linkedin": job["status"] in ["Ativa", "Concluída"],
            "published_website": job["status"] in ["Ativa", "Concluída"],
            "published_indeed": random.choice([True, False]) if job["status"] == "Ativa" else False,
            "approval_status": "aprovada" if job["status"] != "Rascunho" else "pendente",
            "tags": [job["department"], job["seniority_level"], job["work_model"]],
            "next_actions": ["Revisar candidatos", "Agendar entrevistas"] if job["status"] == "Ativa" else [],
        }
        result.append(job_record)
    
    return result


def generate_demo_candidates() -> list[dict[str, Any]]:
    """Generate realistic demo candidates with complete professional profiles."""
    
    candidates = [
        {
            "name": "[DEMO] Lucas Mendes Silva",
            "email": "lucas.mendes.demo@email.com",
            "phone": "(11) 99999-0001",
            "avatar_url": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&h=150&fit=crop&crop=face",
            "current_title": "Desenvolvedor Full Stack",
            "current_company": "TechStartup Brasil",
            "seniority_level": "Sênior",
            "years_of_experience": 6,
            "technical_skills": ["React", "Node.js", "PostgreSQL", "Docker", "AWS"],
            "soft_skills": ["Liderança", "Comunicação", "Resolução de Problemas", "Trabalho em Equipe"],
            "location_city": "São Paulo",
            "location_state": "SP",
            "lia_score": 92.5,
            "skills_match_percentage": 95.0,
            "languages": {"Português": "Nativo", "Inglês": "Avançado", "Espanhol": "Intermediário"},
            "certifications": ["AWS Solutions Architect Associate", "Node.js Certified Developer"],
            "current_salary": 18000.0,
            "salary_expectation_clt": 22000.0,
            "linkedin_url": "https://linkedin.com/in/lucas-mendes-demo",
            "self_introduction": "Desenvolvedor Full Stack com 6 anos de experiência em startups de tecnologia. Especialista em arquiteturas escaláveis com React e Node.js, com forte background em AWS e DevOps. Apaixonado por criar produtos que impactam milhões de usuários.",
            "education": [
                {"institution": "Universidade de São Paulo (USP)", "degree": "Bacharelado", "field_of_study": "Ciência da Computação", "start_date": "2014", "end_date": "2018"},
                {"institution": "Alura", "degree": "Certificação", "field_of_study": "AWS Cloud Computing", "start_date": "2020", "end_date": "2020"},
            ],
            "work_experience": [
                {"company_name": "TechStartup Brasil", "title": "Desenvolvedor Full Stack Sênior", "start_date": "2021-03", "end_date": None, "is_current": True, "description": "Liderança técnica de squad de 5 desenvolvedores. Arquitetura de microsserviços em Node.js/React. Migração para AWS com redução de 40% em custos.", "industries": ["Tecnologia", "Fintech"]},
                {"company_name": "Empresa Digital LTDA", "title": "Desenvolvedor Full Stack Pleno", "start_date": "2019-01", "end_date": "2021-02", "is_current": False, "description": "Desenvolvimento de plataforma B2B SaaS com React e Node.js. Implementação de CI/CD com Docker e Jenkins.", "industries": ["E-commerce", "SaaS"]},
                {"company_name": "Agência Web SP", "title": "Desenvolvedor Frontend Jr", "start_date": "2017-06", "end_date": "2018-12", "is_current": False, "description": "Desenvolvimento de sites e aplicações web para clientes corporativos.", "industries": ["Agência Digital"]},
            ],
        },
        {
            "name": "[DEMO] Mariana Costa Oliveira",
            "email": "mariana.costa.demo@email.com",
            "phone": "(11) 99999-0002",
            "avatar_url": "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=150&h=150&fit=crop&crop=face",
            "current_title": "Senior Software Engineer",
            "current_company": "Banco Digital XP",
            "seniority_level": "Sênior",
            "years_of_experience": 7,
            "technical_skills": ["Python", "FastAPI", "React", "Kubernetes", "GCP"],
            "soft_skills": ["Pensamento Analítico", "Mentoria", "Adaptabilidade", "Proatividade"],
            "location_city": "São Paulo",
            "location_state": "SP",
            "lia_score": 88.0,
            "skills_match_percentage": 90.0,
            "languages": {"Português": "Nativo", "Inglês": "Fluente"},
            "certifications": ["Google Cloud Professional Developer", "Python Institute PCPP"],
            "current_salary": 22000.0,
            "salary_expectation_clt": 28000.0,
            "linkedin_url": "https://linkedin.com/in/mariana-costa-demo",
            "self_introduction": "Engenheira de Software com 7 anos de experiência em fintechs e bancos digitais. Especialista em Python e arquiteturas cloud-native. Mentora de desenvolvedores juniores e defensora de boas práticas de código.",
            "education": [
                {"institution": "Universidade Estadual de Campinas (UNICAMP)", "degree": "Bacharelado", "field_of_study": "Engenharia de Computação", "start_date": "2013", "end_date": "2017"},
                {"institution": "UNICAMP", "degree": "Mestrado", "field_of_study": "Inteligência Artificial", "start_date": "2018", "end_date": "2020"},
            ],
            "work_experience": [
                {"company_name": "Banco Digital XP", "title": "Senior Software Engineer", "start_date": "2022-01", "end_date": None, "is_current": True, "description": "Desenvolvimento de APIs de alta performance com FastAPI. Arquitetura de sistemas distribuídos em GCP. Mentoria de 3 desenvolvedores juniores.", "industries": ["Fintech", "Banco Digital"]},
                {"company_name": "Nubank", "title": "Software Engineer", "start_date": "2019-06", "end_date": "2021-12", "is_current": False, "description": "Desenvolvimento de microsserviços em Python. Implementação de pipelines de dados com Spark.", "industries": ["Fintech", "Banco Digital"]},
                {"company_name": "Consultoria Tech", "title": "Desenvolvedora Python", "start_date": "2017-03", "end_date": "2019-05", "is_current": False, "description": "Desenvolvimento de soluções backend para clientes do setor financeiro.", "industries": ["Consultoria", "Tecnologia"]},
            ],
        },
        {
            "name": "[DEMO] Pedro Henrique Alves",
            "email": "pedro.alves.demo@email.com",
            "phone": "(21) 99999-0003",
            "avatar_url": "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=150&h=150&fit=crop&crop=face",
            "current_title": "Product Manager",
            "current_company": "Fintech Scale",
            "seniority_level": "Pleno",
            "years_of_experience": 4,
            "technical_skills": ["Jira", "Amplitude", "SQL", "Figma"],
            "soft_skills": ["Visão Estratégica", "Comunicação", "Liderança sem Autoridade", "Negociação"],
            "location_city": "Rio de Janeiro",
            "location_state": "RJ",
            "lia_score": 85.0,
            "skills_match_percentage": 88.0,
            "languages": {"Português": "Nativo", "Inglês": "Fluente", "Francês": "Básico"},
            "certifications": ["Product Management Certificate - PM3", "Scrum Product Owner (PSPO I)"],
            "current_salary": 16000.0,
            "salary_expectation_clt": 20000.0,
            "linkedin_url": "https://linkedin.com/in/pedro-alves-demo",
            "self_introduction": "Product Manager com 4 anos de experiência em produtos digitais B2B e B2C. Histórico de lançamento de produtos do zero ao mercado com crescimento de 300% em base de usuários. Foco em métricas e decisões data-driven.",
            "education": [
                {"institution": "PUC-Rio", "degree": "Bacharelado", "field_of_study": "Administração de Empresas", "start_date": "2015", "end_date": "2019"},
                {"institution": "PM3", "degree": "Certificação", "field_of_study": "Product Management", "start_date": "2021", "end_date": "2021"},
            ],
            "work_experience": [
                {"company_name": "Fintech Scale", "title": "Product Manager", "start_date": "2022-06", "end_date": None, "is_current": True, "description": "Gestão de produto de pagamentos B2B. Crescimento de 150% em transações processadas. Coordenação de squad de 8 pessoas.", "industries": ["Fintech", "Pagamentos"]},
                {"company_name": "Startup Edtech", "title": "Associate Product Manager", "start_date": "2020-03", "end_date": "2022-05", "is_current": False, "description": "Lançamento de plataforma de cursos online. Crescimento de 50k para 200k usuários ativos.", "industries": ["Edtech", "Educação"]},
            ],
        },
        {
            "name": "[DEMO] Ana Beatriz Santos",
            "email": "ana.beatriz.demo@email.com",
            "phone": "(11) 99999-0004",
            "avatar_url": "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=150&h=150&fit=crop&crop=face",
            "current_title": "UX Designer Senior",
            "current_company": "Design Studio Premium",
            "seniority_level": "Sênior",
            "years_of_experience": 5,
            "technical_skills": ["Figma", "Design Systems", "User Research", "Prototyping"],
            "soft_skills": ["Criatividade", "Empatia", "Colaboração", "Atenção aos Detalhes"],
            "location_city": "São Paulo",
            "location_state": "SP",
            "lia_score": 90.5,
            "skills_match_percentage": 92.0,
            "languages": {"Português": "Nativo", "Inglês": "Avançado"},
            "certifications": ["Google UX Design Professional Certificate", "Nielsen Norman Group UX Certification"],
            "current_salary": 14000.0,
            "salary_expectation_clt": 18000.0,
            "linkedin_url": "https://linkedin.com/in/ana-beatriz-demo",
            "self_introduction": "UX Designer com 5 anos de experiência criando experiências digitais memoráveis. Especialista em Design Systems e pesquisa com usuários. Portfolio inclui projetos para empresas Fortune 500 e startups unicórnio.",
            "education": [
                {"institution": "ESPM", "degree": "Bacharelado", "field_of_study": "Design Gráfico", "start_date": "2015", "end_date": "2019"},
                {"institution": "Interaction Design Foundation", "degree": "Certificação", "field_of_study": "UX Design", "start_date": "2020", "end_date": "2020"},
            ],
            "work_experience": [
                {"company_name": "Design Studio Premium", "title": "UX Designer Senior", "start_date": "2021-09", "end_date": None, "is_current": True, "description": "Liderança de projetos de redesign para clientes enterprise. Criação de Design System utilizado por 50+ designers.", "industries": ["Agência de Design", "Consultoria"]},
                {"company_name": "Fintech Unicorn", "title": "UX Designer Pleno", "start_date": "2019-06", "end_date": "2021-08", "is_current": False, "description": "Design de produto mobile-first para app de investimentos. Aumento de 40% em conversão de onboarding.", "industries": ["Fintech", "Investimentos"]},
            ],
        },
        {
            "name": "[DEMO] Gabriel Ferreira Lima",
            "email": "gabriel.lima.demo@email.com",
            "phone": "(11) 99999-0005",
            "avatar_url": "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150&h=150&fit=crop&crop=face",
            "current_title": "Data Analyst",
            "current_company": "E-commerce Leader",
            "seniority_level": "Pleno",
            "years_of_experience": 3,
            "technical_skills": ["Python", "SQL", "Power BI", "Tableau", "Statistics"],
            "soft_skills": ["Pensamento Analítico", "Atenção a Detalhes", "Comunicação de Dados", "Curiosidade"],
            "location_city": "Campinas",
            "location_state": "SP",
            "lia_score": 78.0,
            "skills_match_percentage": 85.0,
            "languages": {"Português": "Nativo", "Inglês": "Intermediário"},
            "certifications": ["Google Data Analytics Professional Certificate", "Power BI Data Analyst Associate"],
            "current_salary": 9000.0,
            "salary_expectation_clt": 12000.0,
            "linkedin_url": "https://linkedin.com/in/gabriel-lima-demo",
            "self_introduction": "Analista de Dados com 3 anos de experiência transformando dados em insights acionáveis. Especialista em Power BI e Python para análise estatística. Histórico de projetos que geraram economia de R$ 2M+ para empresas.",
            "education": [
                {"institution": "UNICAMP", "degree": "Bacharelado", "field_of_study": "Estatística", "start_date": "2017", "end_date": "2021"},
                {"institution": "Data Science Academy", "degree": "Formação", "field_of_study": "Business Intelligence", "start_date": "2022", "end_date": "2022"},
            ],
            "work_experience": [
                {"company_name": "E-commerce Leader", "title": "Data Analyst", "start_date": "2022-03", "end_date": None, "is_current": True, "description": "Criação de dashboards estratégicos em Power BI. Análise de comportamento de compra com Python. Suporte a decisões de pricing.", "industries": ["E-commerce", "Varejo"]},
                {"company_name": "Consultoria Analytics", "title": "Data Analyst Jr", "start_date": "2021-02", "end_date": "2022-02", "is_current": False, "description": "Análise de dados para clientes de varejo e finanças. Automação de relatórios com Python.", "industries": ["Consultoria", "Analytics"]},
            ],
        },
        {
            "name": "[DEMO] Julia Nascimento Rosa",
            "email": "julia.rosa.demo@email.com",
            "phone": "(48) 99999-0006",
            "avatar_url": "https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=150&h=150&fit=crop&crop=face",
            "current_title": "DevOps Engineer",
            "current_company": "Cloud Native Co",
            "seniority_level": "Sênior",
            "years_of_experience": 6,
            "technical_skills": ["AWS", "Kubernetes", "Terraform", "Docker", "CI/CD"],
            "soft_skills": ["Resolução de Problemas", "Proatividade", "Documentação", "Trabalho sob Pressão"],
            "location_city": "Florianópolis",
            "location_state": "SC",
            "lia_score": 94.0,
            "skills_match_percentage": 96.0,
            "languages": {"Português": "Nativo", "Inglês": "Fluente"},
            "certifications": ["AWS Solutions Architect Professional", "Certified Kubernetes Administrator (CKA)", "HashiCorp Terraform Associate"],
            "current_salary": 24000.0,
            "salary_expectation_clt": 30000.0,
            "linkedin_url": "https://linkedin.com/in/julia-rosa-demo",
            "self_introduction": "DevOps Engineer com 6 anos de experiência em infraestrutura cloud e automação. Especialista em AWS e Kubernetes com certificações profissionais. Histórico de implementação de zero-downtime deployments e redução de custos cloud em 50%.",
            "education": [
                {"institution": "Universidade Federal de Santa Catarina (UFSC)", "degree": "Bacharelado", "field_of_study": "Sistemas de Informação", "start_date": "2014", "end_date": "2018"},
                {"institution": "Linux Foundation", "degree": "Certificação", "field_of_study": "Kubernetes Administration", "start_date": "2021", "end_date": "2021"},
            ],
            "work_experience": [
                {"company_name": "Cloud Native Co", "title": "DevOps Engineer Sênior", "start_date": "2021-01", "end_date": None, "is_current": True, "description": "Arquitetura de infraestrutura multi-cloud (AWS/GCP). Implementação de GitOps com ArgoCD. Redução de 60% em tempo de deploy.", "industries": ["Cloud", "Tecnologia"]},
                {"company_name": "Empresa SaaS", "title": "DevOps Engineer", "start_date": "2018-09", "end_date": "2020-12", "is_current": False, "description": "Migração de infraestrutura on-premise para AWS. Implementação de Kubernetes em produção.", "industries": ["SaaS", "Tecnologia"]},
            ],
        },
        {
            "name": "[DEMO] Rafael Moreira Costa",
            "email": "rafael.moreira.demo@email.com",
            "phone": "(11) 99999-0007",
            "avatar_url": "https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?w=150&h=150&fit=crop&crop=face",
            "current_title": "Account Executive",
            "current_company": "SaaS Enterprise",
            "seniority_level": "Sênior",
            "years_of_experience": 5,
            "technical_skills": ["Salesforce", "SPIN Selling", "Negotiation"],
            "soft_skills": ["Negociação", "Resiliência", "Relacionamento", "Orientação a Resultados"],
            "location_city": "São Paulo",
            "location_state": "SP",
            "lia_score": 82.0,
            "skills_match_percentage": 87.0,
            "languages": {"Português": "Nativo", "Inglês": "Fluente", "Espanhol": "Avançado"},
            "certifications": ["Salesforce Administrator", "SPIN Selling Certification"],
            "current_salary": 18000.0,
            "salary_expectation_clt": 25000.0,
            "linkedin_url": "https://linkedin.com/in/rafael-moreira-demo",
            "self_introduction": "Executivo de Contas Enterprise com 5 anos de experiência em vendas B2B de alto valor. Histórico consistente de 120%+ de quota. Especialista em vendas consultivas para C-level de empresas Fortune 500.",
            "education": [
                {"institution": "FGV", "degree": "Bacharelado", "field_of_study": "Administração de Empresas", "start_date": "2014", "end_date": "2018"},
                {"institution": "FGV", "degree": "MBA", "field_of_study": "Gestão Comercial", "start_date": "2020", "end_date": "2022"},
            ],
            "work_experience": [
                {"company_name": "SaaS Enterprise", "title": "Account Executive", "start_date": "2021-06", "end_date": None, "is_current": True, "description": "Vendas enterprise para contas acima de R$ 500k ARR. Fechamento de 15 deals em 2023 com ticket médio de R$ 800k.", "industries": ["SaaS", "Enterprise Software"]},
                {"company_name": "Tech Consulting", "title": "Inside Sales", "start_date": "2019-01", "end_date": "2021-05", "is_current": False, "description": "Prospecção e qualificação de leads enterprise. Quota atingida de 130% em 2020.", "industries": ["Consultoria", "Tecnologia"]},
            ],
        },
        {
            "name": "[DEMO] Camila Rodrigues Pinto",
            "email": "camila.pinto.demo@email.com",
            "phone": "(11) 99999-0008",
            "avatar_url": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&h=150&fit=crop&crop=face",
            "current_title": "Desenvolvedora Backend Jr",
            "current_company": "Startup Inovação",
            "seniority_level": "Júnior",
            "years_of_experience": 1,
            "technical_skills": ["Python", "Django", "SQL", "Git"],
            "soft_skills": ["Curiosidade", "Proatividade", "Trabalho em Equipe", "Vontade de Aprender"],
            "location_city": "Campinas",
            "location_state": "SP",
            "lia_score": 72.0,
            "skills_match_percentage": 78.0,
            "languages": {"Português": "Nativo", "Inglês": "Intermediário"},
            "certifications": ["Python Institute PCEP"],
            "current_salary": 4500.0,
            "salary_expectation_clt": 6000.0,
            "linkedin_url": "https://linkedin.com/in/camila-pinto-demo",
            "self_introduction": "Desenvolvedora Backend Jr com 1 ano de experiência em Python e Django. Formada pela UNICAMP com projeto de TCC premiado. Buscando oportunidades para crescer em ambiente de startup com mentoria de seniores.",
            "education": [
                {"institution": "UNICAMP", "degree": "Bacharelado", "field_of_study": "Ciência da Computação", "start_date": "2019", "end_date": "2023"},
                {"institution": "Rocketseat", "degree": "Bootcamp", "field_of_study": "Python Backend", "start_date": "2023", "end_date": "2023"},
            ],
            "work_experience": [
                {"company_name": "Startup Inovação", "title": "Desenvolvedora Backend Jr", "start_date": "2023-06", "end_date": None, "is_current": True, "description": "Desenvolvimento de APIs REST com Django. Manutenção de banco de dados PostgreSQL. Testes automatizados com Pytest.", "industries": ["Startup", "Tecnologia"]},
                {"company_name": "UNICAMP - Iniciação Científica", "title": "Bolsista de Pesquisa", "start_date": "2022-01", "end_date": "2023-05", "is_current": False, "description": "Pesquisa em Machine Learning aplicado a processamento de linguagem natural.", "industries": ["Pesquisa", "Universidade"]},
            ],
        },
        {
            "name": "[DEMO] Thiago Barbosa Souza",
            "email": "thiago.souza.demo@email.com",
            "phone": "(31) 99999-0009",
            "avatar_url": "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=150&h=150&fit=crop&crop=face",
            "current_title": "Mobile Developer",
            "current_company": "App Factory",
            "seniority_level": "Pleno",
            "years_of_experience": 4,
            "technical_skills": ["React Native", "Swift", "Kotlin", "Firebase"],
            "soft_skills": ["Atenção a Detalhes", "Resolução de Problemas", "Trabalho em Equipe", "Comunicação"],
            "location_city": "Belo Horizonte",
            "location_state": "MG",
            "lia_score": 86.5,
            "skills_match_percentage": 89.0,
            "languages": {"Português": "Nativo", "Inglês": "Avançado"},
            "certifications": ["Google Associate Android Developer", "Meta React Native Certificate"],
            "current_salary": 12000.0,
            "salary_expectation_clt": 16000.0,
            "linkedin_url": "https://linkedin.com/in/thiago-souza-demo",
            "self_introduction": "Desenvolvedor Mobile com 4 anos de experiência em apps iOS e Android. Especialista em React Native com apps publicados com 1M+ downloads. Experiência em apps fintech com alto padrão de segurança.",
            "education": [
                {"institution": "UFMG", "degree": "Bacharelado", "field_of_study": "Ciência da Computação", "start_date": "2016", "end_date": "2020"},
                {"institution": "Udacity", "degree": "Nanodegree", "field_of_study": "React Native", "start_date": "2021", "end_date": "2021"},
            ],
            "work_experience": [
                {"company_name": "App Factory", "title": "Mobile Developer", "start_date": "2022-01", "end_date": None, "is_current": True, "description": "Desenvolvimento de apps React Native para clientes enterprise. Liderança técnica de projetos mobile.", "industries": ["Agência Mobile", "Tecnologia"]},
                {"company_name": "Fintech MG", "title": "Mobile Developer Jr", "start_date": "2020-03", "end_date": "2021-12", "is_current": False, "description": "Desenvolvimento de app de pagamentos em React Native. Implementação de autenticação biométrica.", "industries": ["Fintech", "Pagamentos"]},
            ],
        },
        {
            "name": "[DEMO] Fernanda Lima Castro",
            "email": "fernanda.castro.demo@email.com",
            "phone": "(11) 99999-0010",
            "avatar_url": "https://images.unsplash.com/photo-1487412720507-e7ab37603c6f?w=150&h=150&fit=crop&crop=face",
            "current_title": "HR Business Partner",
            "current_company": "Multinacional Tech",
            "seniority_level": "Pleno",
            "years_of_experience": 4,
            "technical_skills": ["HRIS", "People Analytics", "Gestão de Clima"],
            "soft_skills": ["Empatia", "Comunicação", "Organização", "Influência"],
            "location_city": "São Paulo",
            "location_state": "SP",
            "lia_score": 80.0,
            "skills_match_percentage": 84.0,
            "languages": {"Português": "Nativo", "Inglês": "Avançado"},
            "certifications": ["SHRM-CP", "People Analytics Certificate - Wharton"],
            "current_salary": 12000.0,
            "salary_expectation_clt": 15000.0,
            "linkedin_url": "https://linkedin.com/in/fernanda-castro-demo",
            "self_introduction": "HR Business Partner com 4 anos de experiência em empresas de tecnologia. Especialista em People Analytics e gestão de clima organizacional. Histórico de redução de turnover em 25% através de programas de engajamento.",
            "education": [
                {"institution": "Mackenzie", "degree": "Bacharelado", "field_of_study": "Psicologia", "start_date": "2015", "end_date": "2019"},
                {"institution": "FIA", "degree": "Pós-Graduação", "field_of_study": "Gestão de Pessoas", "start_date": "2020", "end_date": "2021"},
            ],
            "work_experience": [
                {"company_name": "Multinacional Tech", "title": "HR Business Partner", "start_date": "2022-04", "end_date": None, "is_current": True, "description": "Parceria estratégica com 3 áreas de negócio (200+ colaboradores). Implementação de programa de desenvolvimento de líderes.", "industries": ["Tecnologia", "Multinacional"]},
                {"company_name": "Startup Scale", "title": "Analista de RH", "start_date": "2020-01", "end_date": "2022-03", "is_current": False, "description": "Estruturação de processos de R&S e onboarding. Gestão de benefícios e clima.", "industries": ["Startup", "Tecnologia"]},
            ],
        },
        {
            "name": "[DEMO] Bruno Carvalho Dias",
            "email": "bruno.dias.demo@email.com",
            "phone": "(11) 99999-0011",
            "avatar_url": "https://images.unsplash.com/photo-1560250097-0b93528c311a?w=150&h=150&fit=crop&crop=face",
            "current_title": "Tech Lead Mobile",
            "current_company": "Unicorn Startup",
            "seniority_level": "Especialista",
            "years_of_experience": 8,
            "technical_skills": ["React Native", "Flutter", "Swift", "Kotlin", "Clean Architecture"],
            "soft_skills": ["Liderança Técnica", "Mentoria", "Visão de Produto", "Tomada de Decisão"],
            "location_city": "São Paulo",
            "location_state": "SP",
            "lia_score": 96.0,
            "skills_match_percentage": 98.0,
            "languages": {"Português": "Nativo", "Inglês": "Fluente"},
            "certifications": ["Google Associate Android Developer", "AWS Mobile Specialty", "Apple Certified iOS Developer"],
            "current_salary": 28000.0,
            "salary_expectation_clt": 35000.0,
            "linkedin_url": "https://linkedin.com/in/bruno-dias-demo",
            "self_introduction": "Tech Lead Mobile com 8 anos de experiência liderando squads de alto desempenho. Especialista em arquitetura mobile escalável e mentoria de desenvolvedores. Apps desenvolvidos somam 50M+ de downloads globais.",
            "education": [
                {"institution": "ITA", "degree": "Bacharelado", "field_of_study": "Engenharia de Computação", "start_date": "2012", "end_date": "2016"},
                {"institution": "Stanford Online", "degree": "Especialização", "field_of_study": "Mobile Development", "start_date": "2019", "end_date": "2019"},
            ],
            "work_experience": [
                {"company_name": "Unicorn Startup", "title": "Tech Lead Mobile", "start_date": "2021-03", "end_date": None, "is_current": True, "description": "Liderança técnica de squad de 12 desenvolvedores mobile. Definição de arquitetura Flutter/React Native. Mentoria e desenvolvimento de carreira do time.", "industries": ["Startup Unicórnio", "Delivery"]},
                {"company_name": "Banco Digital", "title": "Senior Mobile Developer", "start_date": "2018-06", "end_date": "2021-02", "is_current": False, "description": "Desenvolvimento de app bancário com 10M+ usuários. Implementação de módulos de segurança e biometria.", "industries": ["Fintech", "Banco Digital"]},
                {"company_name": "Agência Apps", "title": "Mobile Developer", "start_date": "2016-01", "end_date": "2018-05", "is_current": False, "description": "Desenvolvimento de apps nativos iOS e Android para clientes corporativos.", "industries": ["Agência Mobile"]},
            ],
        },
        {
            "name": "[DEMO] Isabela Martins Ramos",
            "email": "isabela.ramos.demo@email.com",
            "phone": "(11) 99999-0012",
            "avatar_url": "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=150&h=150&fit=crop&crop=face",
            "current_title": "Marketing Manager",
            "current_company": "Agency Digital",
            "seniority_level": "Sênior",
            "years_of_experience": 6,
            "technical_skills": ["Google Ads", "Google Analytics", "HubSpot", "Meta Ads"],
            "soft_skills": ["Liderança", "Pensamento Estratégico", "Criatividade", "Gestão de Budget"],
            "location_city": "São Paulo",
            "location_state": "SP",
            "lia_score": 91.0,
            "skills_match_percentage": 93.0,
            "languages": {"Português": "Nativo", "Inglês": "Fluente", "Espanhol": "Intermediário"},
            "certifications": ["Google Ads Certification", "HubSpot Marketing Software", "Meta Blueprint Certification"],
            "current_salary": 18000.0,
            "salary_expectation_clt": 24000.0,
            "linkedin_url": "https://linkedin.com/in/isabela-ramos-demo",
            "self_introduction": "Marketing Manager com 6 anos de experiência em marketing digital e growth. Gerenciamento de budgets de até R$ 5M/ano. Histórico de campanhas com ROI de 400%+ em performance marketing.",
            "education": [
                {"institution": "ESPM", "degree": "Bacharelado", "field_of_study": "Publicidade e Propaganda", "start_date": "2014", "end_date": "2018"},
                {"institution": "ESPM", "degree": "MBA", "field_of_study": "Marketing Digital", "start_date": "2020", "end_date": "2022"},
            ],
            "work_experience": [
                {"company_name": "Agency Digital", "title": "Marketing Manager", "start_date": "2022-01", "end_date": None, "is_current": True, "description": "Gestão de equipe de 8 profissionais de marketing. Estratégia de aquisição para 15 clientes enterprise. Budget anual de R$ 3M.", "industries": ["Agência Digital", "Marketing"]},
                {"company_name": "E-commerce Fashion", "title": "Coordenadora de Marketing Digital", "start_date": "2019-06", "end_date": "2021-12", "is_current": False, "description": "Coordenação de campanhas de performance em Google e Meta. Crescimento de 200% em vendas online.", "industries": ["E-commerce", "Moda"]},
            ],
        },
        {
            "name": "[DEMO] André Luis Pereira",
            "email": "andre.pereira.demo@email.com",
            "phone": "(21) 99999-0013",
            "avatar_url": "https://images.unsplash.com/photo-1522075469751-3a6694fb2f61?w=150&h=150&fit=crop&crop=face",
            "current_title": "Backend Developer",
            "current_company": "Consulting IT",
            "seniority_level": "Pleno",
            "years_of_experience": 3,
            "technical_skills": ["Java", "Spring Boot", "PostgreSQL", "Docker"],
            "soft_skills": ["Trabalho em Equipe", "Atenção a Detalhes", "Aprendizado Contínuo", "Comunicação"],
            "location_city": "Rio de Janeiro",
            "location_state": "RJ",
            "lia_score": 75.0,
            "skills_match_percentage": 80.0,
            "languages": {"Português": "Nativo", "Inglês": "Intermediário"},
            "certifications": ["Oracle Certified Java Programmer", "Spring Professional Certification"],
            "current_salary": 10000.0,
            "salary_expectation_clt": 14000.0,
            "linkedin_url": "https://linkedin.com/in/andre-pereira-demo",
            "self_introduction": "Desenvolvedor Backend com 3 anos de experiência em Java e Spring Boot. Atuação em projetos de consultoria para grandes bancos e seguradoras. Foco em código limpo e boas práticas de desenvolvimento.",
            "education": [
                {"institution": "UFRJ", "degree": "Bacharelado", "field_of_study": "Sistemas de Informação", "start_date": "2017", "end_date": "2021"},
                {"institution": "Alura", "degree": "Formação", "field_of_study": "Java e Spring Boot", "start_date": "2021", "end_date": "2022"},
            ],
            "work_experience": [
                {"company_name": "Consulting IT", "title": "Backend Developer", "start_date": "2022-03", "end_date": None, "is_current": True, "description": "Desenvolvimento de APIs para cliente do setor bancário. Manutenção de sistemas legados em Java 8.", "industries": ["Consultoria", "Banking"]},
                {"company_name": "Empresa Seguros", "title": "Desenvolvedor Java Jr", "start_date": "2021-01", "end_date": "2022-02", "is_current": False, "description": "Desenvolvimento de módulos para sistema de gestão de apólices.", "industries": ["Seguros", "Financeiro"]},
            ],
        },
        {
            "name": "[DEMO] Carolina Vieira Nunes",
            "email": "carolina.nunes.demo@email.com",
            "phone": "(47) 99999-0014",
            "avatar_url": "https://images.unsplash.com/photo-1580489944761-15a19d654956?w=150&h=150&fit=crop&crop=face",
            "current_title": "Product Designer",
            "current_company": "Design Thinking Lab",
            "seniority_level": "Pleno",
            "years_of_experience": 3,
            "technical_skills": ["Figma", "Sketch", "Adobe XD", "InVision"],
            "soft_skills": ["Criatividade", "Empatia", "Colaboração", "Apresentação"],
            "location_city": "Joinville",
            "location_state": "SC",
            "lia_score": 83.0,
            "skills_match_percentage": 86.0,
            "languages": {"Português": "Nativo", "Inglês": "Avançado"},
            "certifications": ["Interaction Design Foundation Certificate", "Figma Professional Certificate"],
            "current_salary": 9000.0,
            "salary_expectation_clt": 12000.0,
            "linkedin_url": "https://linkedin.com/in/carolina-nunes-demo",
            "self_introduction": "Product Designer com 3 anos de experiência criando produtos digitais centrados no usuário. Especialista em design de interfaces e prototipagem. Portfolio inclui redesign de produtos com aumento de 50% em NPS.",
            "education": [
                {"institution": "UNIVILLE", "degree": "Bacharelado", "field_of_study": "Design", "start_date": "2017", "end_date": "2021"},
                {"institution": "IDEO U", "degree": "Certificação", "field_of_study": "Design Thinking", "start_date": "2022", "end_date": "2022"},
            ],
            "work_experience": [
                {"company_name": "Design Thinking Lab", "title": "Product Designer", "start_date": "2022-06", "end_date": None, "is_current": True, "description": "Design de produtos digitais para startups. Condução de workshops de Design Thinking.", "industries": ["Consultoria de Design", "Inovação"]},
                {"company_name": "Software House SC", "title": "UI Designer", "start_date": "2021-02", "end_date": "2022-05", "is_current": False, "description": "Criação de interfaces para sistemas web e mobile. Colaboração com equipe de desenvolvimento.", "industries": ["Software House", "Tecnologia"]},
            ],
        },
        {
            "name": "[DEMO] Diego Santos Machado",
            "email": "diego.machado.demo@email.com",
            "phone": "(51) 99999-0015",
            "avatar_url": "https://images.unsplash.com/photo-1539571696357-5a69c17a67c6?w=150&h=150&fit=crop&crop=face",
            "current_title": "Data Scientist",
            "current_company": "AI Solutions",
            "seniority_level": "Sênior",
            "years_of_experience": 5,
            "technical_skills": ["Python", "TensorFlow", "SQL", "Spark", "Machine Learning"],
            "soft_skills": ["Pensamento Analítico", "Resolução de Problemas", "Comunicação Técnica", "Inovação"],
            "location_city": "Porto Alegre",
            "location_state": "RS",
            "lia_score": 89.0,
            "skills_match_percentage": 91.0,
            "languages": {"Português": "Nativo", "Inglês": "Fluente"},
            "certifications": ["AWS Machine Learning Specialty", "TensorFlow Developer Certificate", "Google Cloud Professional Data Engineer"],
            "current_salary": 20000.0,
            "salary_expectation_clt": 26000.0,
            "linkedin_url": "https://linkedin.com/in/diego-machado-demo",
            "self_introduction": "Data Scientist com 5 anos de experiência em Machine Learning e IA. Especialista em modelos de NLP e Computer Vision. Projetos implementados geraram economia de R$ 10M+ para clientes enterprise.",
            "education": [
                {"institution": "UFRGS", "degree": "Bacharelado", "field_of_study": "Ciência da Computação", "start_date": "2015", "end_date": "2019"},
                {"institution": "UFRGS", "degree": "Mestrado", "field_of_study": "Machine Learning", "start_date": "2019", "end_date": "2021"},
            ],
            "work_experience": [
                {"company_name": "AI Solutions", "title": "Data Scientist Sênior", "start_date": "2022-01", "end_date": None, "is_current": True, "description": "Desenvolvimento de modelos de ML para detecção de fraude e recomendação. Liderança técnica de projetos de IA.", "industries": ["Inteligência Artificial", "Consultoria"]},
                {"company_name": "Banco Regional", "title": "Data Scientist", "start_date": "2020-03", "end_date": "2021-12", "is_current": False, "description": "Modelos de credit scoring e detecção de anomalias. Redução de 30% em fraudes.", "industries": ["Banking", "Financeiro"]},
            ],
        },
    ]
    
    result = []
    for candidate in candidates:
        candidate_record = {
            "id": str(uuid.uuid4()),
            "name": candidate["name"],
            "email": candidate["email"],
            "phone": candidate["phone"],
            "current_title": candidate["current_title"],
            "current_company": candidate["current_company"],
            "seniority_level": candidate["seniority_level"],
            "years_of_experience": candidate["years_of_experience"],
            "technical_skills": candidate["technical_skills"],
            "soft_skills": candidate.get("soft_skills", []),
            "location_city": candidate["location_city"],
            "location_state": candidate["location_state"],
            "location_country": "Brasil",
            "lia_score": candidate["lia_score"],
            "skills_match_percentage": candidate["skills_match_percentage"],
            "languages": candidate.get("languages", {}),
            "certifications": candidate.get("certifications", []),
            "current_salary": candidate.get("current_salary"),
            "salary_expectation_clt": candidate.get("salary_expectation_clt"),
            "linkedin_url": candidate.get("linkedin_url"),
            "self_introduction": candidate.get("self_introduction"),
            "education": candidate.get("education", []),
            "work_experience": candidate.get("work_experience", []),
            "source": "SEED_DATA",
            "status": "Ativo",
            "is_active": True,
            "communication_consent": True,
            "created_at": datetime.utcnow() - timedelta(days=random.randint(1, 30)),
            "updated_at": datetime.utcnow(),
        }
        result.append(candidate_record)
    
    return result


def generate_vacancy_candidates(job_ids: list[str], candidate_ids: list[str]) -> list[dict[str, Any]]:
    """Generate vacancy-candidate relationships with various stages."""
    
    stages = [
        "sourcing",
        "screening",
        "interview_hr",
        "interview_technical",
        "interview_manager",
        "offer",
        "hired",
        "rejected",
    ]

    STAGE_STATUS_MAP = {
        "hired": "hired",
        "rejected": "rejected",
        "sourcing": "active",
        "screening": "active",
        "interview_hr": "active",
        "interview_technical": "active",
        "interview_manager": "active",
        "offer": "active",
    }
    
    result = []
    
    for job_id in job_ids:
        num_candidates = random.randint(8, 15)
        selected_candidates = random.sample(candidate_ids, min(num_candidates, len(candidate_ids)))
        
        for candidate_id in selected_candidates:
            stage = random.choice(stages)
            lia_score = round(random.uniform(60, 98), 1)
            match_percentage = round(random.uniform(65, 99), 1)
            
            vacancy_candidate = {
                "id": str(uuid.uuid4()),
                "vacancy_id": job_id,
                "candidate_id": candidate_id,
                "company_id": get_seed_company_id(),
                "source": "SEED_DATA",
                "lia_score": lia_score,
                "match_percentage": match_percentage,
                "status": STAGE_STATUS_MAP.get(stage, "active"),
                "stage": stage,
                "added_by": "seed_service",
                "notes": f"Candidato adicionado via seed data. Etapa atual: {stage}",
                "created_at": datetime.utcnow() - timedelta(days=random.randint(1, 20)),
                "updated_at": datetime.utcnow(),
            }
            result.append(vacancy_candidate)
    
    return result


async def seed_demo_data(db: AsyncSession) -> dict[str, Any]:
    """
    Seed the database with demo data.
    Clears existing demo data and creates fresh records.
    """
    logger.info("🌱 Starting seed process...")
    
    try:
        await db.execute(
            delete(VacancyCandidate).where(VacancyCandidate.source == "SEED_DATA")
        )
        await db.execute(
        # ADR-001-EXEMPT: Rails-owned Candidate table — seed/demo data teardown (test lifecycle)
            delete(Candidate).where(Candidate.source == "SEED_DATA")
        )
        await db.execute(
            delete(JobVacancy).where(JobVacancy.title.like("[DEMO]%"))
        )
        await db.commit()
        logger.info("🗑️  Cleared existing demo data")
    except Exception as e:
        await db.rollback()
        logger.warning(f"Could not clear existing demo data: {e}")
    
    jobs_data = generate_demo_job_vacancies()
    job_ids = []
    
    for job_data in jobs_data:
        job = JobVacancy(**job_data)
        db.add(job)
        job_ids.append(job_data["id"])
    
    await db.flush()
    logger.info(f"✅ Created {len(jobs_data)} demo job vacancies")
    
    candidates_data = generate_demo_candidates()
    candidate_ids = []
    education_count = 0
    experience_count = 0
    
    for candidate_data in candidates_data:
        education_list = candidate_data.pop("education", [])
        work_experience_list = candidate_data.pop("work_experience", [])
        
        candidate = Candidate(**candidate_data)
        db.add(candidate)
        candidate_ids.append(candidate_data["id"])
        
        for idx, edu in enumerate(education_list):
            edu_record = CandidateEducation(
                candidate_id=candidate_data["id"],
                institution=edu.get("institution"),
                degree=edu.get("degree"),
                field_of_study=edu.get("field_of_study"),
                start_date=edu.get("start_date"),
                end_date=edu.get("end_date"),
                is_completed=True,
                sequence_order=idx,
            )
            db.add(edu_record)
            education_count += 1
        
        for idx, exp in enumerate(work_experience_list):
            exp_record = CandidateExperience(
                candidate_id=candidate_data["id"],
                company_name=exp.get("company_name"),
                title=exp.get("title"),
                start_date=exp.get("start_date"),
                end_date=exp.get("end_date"),
                is_current=exp.get("is_current", False),
                description=exp.get("description"),
                industries=exp.get("industries", []),
                sequence_order=idx,
            )
            db.add(exp_record)
            experience_count += 1
    
    await db.flush()
    logger.info(f"✅ Created {len(candidates_data)} demo candidates with {education_count} education records and {experience_count} experience records")
    
    vacancy_candidates_data = generate_vacancy_candidates(job_ids, candidate_ids)
    
    for vc_data in vacancy_candidates_data:
        vc = VacancyCandidate(**vc_data)
        db.add(vc)
    
    await db.commit()
    logger.info(f"✅ Created {len(vacancy_candidates_data)} vacancy-candidate relationships")
    
    return {
        "success": True,
        "jobs_created": len(jobs_data),
        "candidates_created": len(candidates_data),
        "relationships_created": len(vacancy_candidates_data),
        "message": "Demo data seeded successfully. All records are marked with [DEMO] prefix."
    }


async def clear_demo_data(db: AsyncSession) -> dict[str, Any]:
    """Clear all demo data from the database."""
    logger.info("🗑️  Clearing demo data...")
    
    try:
        from sqlalchemy import func
        
        vc_count = await db.scalar(
            select(func.count()).where(VacancyCandidate.source == "SEED_DATA")
        )
        await db.execute(
            delete(VacancyCandidate).where(VacancyCandidate.source == "SEED_DATA")
        )
        
        c_count = await db.scalar(
            select(func.count()).where(Candidate.source == "SEED_DATA")
        )
        await db.execute(
        # ADR-001-EXEMPT: Rails-owned Candidate table — seed/demo data teardown (test lifecycle)
            delete(Candidate).where(Candidate.source == "SEED_DATA")
        )
        
        j_count = await db.scalar(
            select(func.count()).where(JobVacancy.title.like("[DEMO]%"))
        )
        await db.execute(
            delete(JobVacancy).where(JobVacancy.title.like("[DEMO]%"))
        )
        
        await db.commit()
        
        return {
            "success": True,
            "jobs_deleted": j_count or 0,
            "candidates_deleted": c_count or 0,
            "relationships_deleted": vc_count or 0,
            "message": "Demo data cleared successfully."
        }
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to clear demo data: {e}")
        return {
            "success": False,
            "error": str(e)
        }



# ---------------------------------------------------------------------------
# Demo company profile seed helpers (Task #819)
# ---------------------------------------------------------------------------

#: Canonical culture/size data for the demo tenant.
#: ``website`` is intentionally absent — preserving the ``analyze_company_website``
#: offer (contract §5.1). Tests assert on "industry" and "company_size" fields.
_DEMO_CULTURE_PROFILE: dict = {
    "industry": "Tecnologia",
    "company_size": "51-200",
    "description": "Empresa de tecnologia demonstrativa para testes e onboarding.",
}


async def _ensure_demo_company_profile(db) -> bool:
    """Idempotently seed the canonical company_profiles row for the demo tenant.

    Uses an ``INSERT … ON CONFLICT DO UPDATE`` (upsert) so that:

    * **New row**: inserts ``name``, ``industry``, and ``company_size``.
    * **Existing row**: backfills any NULL columns (does not overwrite
      admin-entered values because we use ``COALESCE`` for each field).
    * **website** is deliberately excluded — keeping it NULL preserves the
      ``analyze_company_website`` onboarding offer (contract §5.1).

    Args:
        db: An async SQLAlchemy session.

    Returns:
        ``True`` when the row was freshly inserted (``xmax = 0``),
        ``False`` when the row already existed (DO UPDATE path).
    """
    from sqlalchemy import text as sa_text
    from app.core.tenant import DEMO_COMPANY_UUID

    sql = sa_text(
        "INSERT INTO company_profiles (id, name, industry, company_size) "
        "VALUES (:cid, :name, :industry, :company_size) "
        "ON CONFLICT (id) DO UPDATE SET "
        "  name         = COALESCE(company_profiles.name,         EXCLUDED.name), "
        "  industry     = COALESCE(company_profiles.industry,     EXCLUDED.industry), "
        "  company_size = COALESCE(company_profiles.company_size, EXCLUDED.company_size) "
        "RETURNING (xmax = 0) AS inserted"
    )
    params = {
        "cid": DEMO_COMPANY_UUID,
        "name": "WeDO Talent Demo",
        "industry": _DEMO_CULTURE_PROFILE["industry"],
        "company_size": _DEMO_CULTURE_PROFILE["company_size"],
    }
    result = await db.execute(sql, params)
    row = result.first()
    return bool(row[0]) if row else True
