"""
Default Templates models for managing system-wide communication templates.
These are templates that can be used by clients as starting points.
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, String, DateTime, Text, Integer, Index, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
import enum

from lia_config.database import Base


class TemplateCategory(str, enum.Enum):
    """Category of communication template."""
    EMAIL = "email"
    SMS = "sms"
    WHATSAPP = "whatsapp"
    PUSH = "push"


class TemplateStatus(str, enum.Enum):
    """Status of the template."""
    ACTIVE = "active"
    DRAFT = "draft"
    ARCHIVED = "archived"


class DefaultTemplate(Base):
    """
    Represents a system-wide default template for candidate communications.
    These templates serve as starting points that clients can copy and customize.
    """
    __tablename__ = "default_templates"
    __table_args__ = (
        Index('ix_default_templates_category_status', 'category', 'status'),
    {"extend_existing": True}, )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    category = Column(String(20), nullable=False, default="email", index=True)
    subject = Column(String(500), nullable=True)
    body = Column(Text, nullable=False)
    variables = Column(JSONB, default=list)
    status = Column(String(20), nullable=False, default="active", index=True)
    client_usage_count = Column(Integer, default=0)
    created_by = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<DefaultTemplate {self.id} - {self.name} ({self.category})>"
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "name": self.name,
            "category": self.category,
            "subject": self.subject,
            "body": self.body,
            "variables": self.variables or [],
            "status": self.status,
            "client_usage_count": self.client_usage_count,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


AVAILABLE_TEMPLATE_VARIABLES = [
    {
        "name": "candidate_name",
        "description": "Full name of the candidate",
        "example_value": "João Silva",
        "required": True
    },
    {
        "name": "candidate_first_name",
        "description": "First name of the candidate",
        "example_value": "João",
        "required": False
    },
    {
        "name": "candidate_email",
        "description": "Email address of the candidate",
        "example_value": "joao.silva@email.com",
        "required": False
    },
    {
        "name": "job_title",
        "description": "Title of the job position",
        "example_value": "Desenvolvedor Senior",
        "required": False
    },
    {
        "name": "company_name",
        "description": "Name of the hiring company",
        "example_value": "Tech Corp",
        "required": True
    },
    {
        "name": "recruiter_name",
        "description": "Name of the recruiter",
        "example_value": "Maria Santos",
        "required": False
    },
    {
        "name": "recruiter_email",
        "description": "Email of the recruiter",
        "example_value": "maria.santos@company.com",
        "required": False
    },
    {
        "name": "interview_date",
        "description": "Date of the interview",
        "example_value": "15 de Janeiro de 2025",
        "required": False
    },
    {
        "name": "interview_time",
        "description": "Time of the interview",
        "example_value": "14:00",
        "required": False
    },
    {
        "name": "interview_location",
        "description": "Location or link for the interview",
        "example_value": "https://meet.google.com/abc-123",
        "required": False
    },
    {
        "name": "screening_link",
        "description": "Link to the screening questionnaire",
        "example_value": "https://lia.app/screening/abc123",
        "required": False
    },
    {
        "name": "salary_range",
        "description": "Salary range for the position",
        "example_value": "R$ 12.000 - R$ 15.000",
        "required": False
    },
    {
        "name": "start_date",
        "description": "Expected start date",
        "example_value": "1 de Fevereiro de 2025",
        "required": False
    },
    {
        "name": "deadline",
        "description": "Deadline for response or action",
        "example_value": "20 de Janeiro de 2025",
        "required": False
    },
    {
        "name": "current_stage",
        "description": "Current stage in the recruitment process",
        "example_value": "Entrevista Técnica",
        "required": False
    },
    {
        "name": "next_steps",
        "description": "Description of next steps in the process",
        "example_value": "Aguardamos sua confirmação para agendar a próxima etapa.",
        "required": False
    },
]


DEFAULT_TEMPLATES_SEED = [
    {
        "name": "Confirmação de Candidatura",
        "category": "email",
        "subject": "Recebemos sua candidatura para {{job_title}} - {{company_name}}",
        "body": """Olá {{candidate_first_name}},

Agradecemos pelo seu interesse na vaga de {{job_title}} na {{company_name}}!

Recebemos sua candidatura e nossa equipe está analisando seu perfil. Entraremos em contato em breve com os próximos passos.

Enquanto isso, fique à vontade para conhecer mais sobre nossa empresa.

Atenciosamente,
{{recruiter_name}}
{{company_name}}""",
        "variables": ["candidate_first_name", "job_title", "company_name", "recruiter_name"],
        "status": "active"
    },
    {
        "name": "Convite para Triagem",
        "category": "email",
        "subject": "Próxima etapa: Triagem para {{job_title}} - {{company_name}}",
        "body": """Olá {{candidate_first_name}},

Ficamos muito felizes em informar que seu perfil foi selecionado para a próxima etapa do processo seletivo para {{job_title}}.

Gostaríamos de convidá-lo(a) para responder algumas perguntas de triagem. Isso nos ajudará a conhecer melhor você e suas experiências.

Acesse o link abaixo para iniciar:
{{screening_link}}

Por favor, complete a triagem até {{deadline}}.

Qualquer dúvida, estamos à disposição.

Atenciosamente,
{{recruiter_name}}
{{company_name}}""",
        "variables": ["candidate_first_name", "job_title", "company_name", "screening_link", "deadline", "recruiter_name"],
        "status": "active"
    },
    {
        "name": "Agendamento de Entrevista",
        "category": "email",
        "subject": "Convite para Entrevista - {{job_title}} na {{company_name}}",
        "body": """Olá {{candidate_first_name}},

Parabéns! Você foi selecionado(a) para a etapa de entrevista do processo seletivo para {{job_title}}.

Detalhes da Entrevista:
📅 Data: {{interview_date}}
🕐 Horário: {{interview_time}}
📍 Local/Link: {{interview_location}}

Por favor, confirme sua presença respondendo este email.

Dicas para a entrevista:
- Prepare-se para falar sobre suas experiências anteriores
- Pesquise sobre nossa empresa
- Tenha perguntas prontas para fazer

Aguardamos você!

Atenciosamente,
{{recruiter_name}}
{{company_name}}""",
        "variables": ["candidate_first_name", "job_title", "company_name", "interview_date", "interview_time", "interview_location", "recruiter_name"],
        "status": "active"
    },
    {
        "name": "Proposta de Emprego",
        "category": "email",
        "subject": "Oferta de Emprego - {{job_title}} na {{company_name}}",
        "body": """Olá {{candidate_name}},

É com grande satisfação que informamos que você foi aprovado(a) no processo seletivo para a posição de {{job_title}} na {{company_name}}!

Após avaliar cuidadosamente todos os candidatos, sua experiência e habilidades se destacaram.

Detalhes da Proposta:
💰 Faixa Salarial: {{salary_range}}
📅 Data de Início: {{start_date}}

Gostaríamos de receber sua resposta até {{deadline}}.

Estamos animados com a possibilidade de tê-lo(a) em nossa equipe!

Atenciosamente,
{{recruiter_name}}
{{company_name}}""",
        "variables": ["candidate_name", "job_title", "company_name", "salary_range", "start_date", "deadline", "recruiter_name"],
        "status": "active"
    },
    {
        "name": "Feedback Negativo - Não Selecionado",
        "category": "email",
        "subject": "Atualização sobre sua candidatura - {{company_name}}",
        "body": """Olá {{candidate_first_name}},

Agradecemos sinceramente seu interesse na vaga de {{job_title}} e pelo tempo dedicado ao nosso processo seletivo.

Após uma análise cuidadosa de todos os candidatos, decidimos seguir com outros perfis que estão mais alinhados com as necessidades específicas desta posição neste momento.

Esta decisão não diminui suas qualidades profissionais. Manteremos seu currículo em nosso banco de talentos para oportunidades futuras que possam ser compatíveis com seu perfil.

Desejamos sucesso em sua jornada profissional!

Atenciosamente,
{{recruiter_name}}
{{company_name}}""",
        "variables": ["candidate_first_name", "job_title", "company_name", "recruiter_name"],
        "status": "active"
    },
    {
        "name": "Lembrete de Triagem",
        "category": "whatsapp",
        "subject": None,
        "body": """Olá {{candidate_first_name}}! 👋

Este é um lembrete amigável para completar sua triagem para a vaga de {{job_title}} na {{company_name}}.

Acesse: {{screening_link}}

Prazo: {{deadline}}

Qualquer dúvida, estamos à disposição! 😊""",
        "variables": ["candidate_first_name", "job_title", "company_name", "screening_link", "deadline"],
        "status": "active"
    },
    {
        "name": "Confirmação de Entrevista",
        "category": "whatsapp",
        "subject": None,
        "body": """Olá {{candidate_first_name}}! 👋

Confirmando sua entrevista para {{job_title}}:

📅 {{interview_date}}
🕐 {{interview_time}}
📍 {{interview_location}}

Por favor, confirme sua presença respondendo esta mensagem.

Boa sorte! 🍀""",
        "variables": ["candidate_first_name", "job_title", "interview_date", "interview_time", "interview_location"],
        "status": "active"
    },
    {
        "name": "Lembrete de Entrevista SMS",
        "category": "sms",
        "subject": None,
        "body": """{{company_name}}: Lembrete - Sua entrevista para {{job_title}} é amanhã às {{interview_time}}. Local: {{interview_location}}""",
        "variables": ["company_name", "job_title", "interview_time", "interview_location"],
        "status": "active"
    },
    {
        "name": "Atualização de Status",
        "category": "email",
        "subject": "Atualização do seu processo seletivo - {{company_name}}",
        "body": """Olá {{candidate_first_name}},

Gostaríamos de atualizar você sobre o status do seu processo seletivo para {{job_title}}.

Status atual: {{current_stage}}

{{next_steps}}

Qualquer dúvida, estamos à disposição.

Atenciosamente,
{{recruiter_name}}
{{company_name}}""",
        "variables": ["candidate_first_name", "job_title", "current_stage", "next_steps", "recruiter_name", "company_name"],
        "status": "active"
    },
    {
        "name": "Boas-vindas ao Processo",
        "category": "push",
        "subject": "Bem-vindo(a) ao processo seletivo!",
        "body": """{{candidate_first_name}}, sua jornada com a {{company_name}} começou! Acompanhe aqui as próximas etapas.""",
        "variables": ["candidate_first_name", "company_name"],
        "status": "active"
    },
]
