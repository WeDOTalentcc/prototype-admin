"""
Recruitment Email Templates Service.
Provides default templates for all recruitment pipeline stages.
"""
import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.job_management.repositories.recruitment_email_template_repository import RecruitmentEmailTemplateRepository

from lia_models.recruitment_email_template import RecruitmentEmailTemplate, RecruitmentStageName, TemplateType

logger = logging.getLogger(__name__)

COMMON_VARIABLES = [
    "candidate_name",
    "candidate_email",
    "job_title",
    "company_name",
    "recruiter_name",
    "recruiter_email",
]

DEFAULT_TEMPLATES: list[dict[str, Any]] = [
    {
        "stage_name": RecruitmentStageName.CANDIDATE_APPLIED.value,
        "template_type": TemplateType.CANDIDATE.value,
        "name": "Recebemos sua candidatura",
        "description": "Email enviado automaticamente quando um candidato se inscreve para uma vaga",
        "subject": "Recebemos sua candidatura para {{job_title}} - {{company_name}}",
        "variables": COMMON_VARIABLES + ["application_date"],
        "body_html": """
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto;">
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center;">
        <h1 style="color: white; margin: 0;">{{company_name}}</h1>
    </div>
    
    <div style="padding: 30px; background: #ffffff;">
        <h2 style="color: #2563eb; margin-top: 0;">Olá, {{candidate_name}}! 👋</h2>
        
        <p>Ficamos muito felizes em receber sua candidatura para a posição de <strong>{{job_title}}</strong>!</p>
        
        <div style="background-color: #f0f9ff; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #2563eb;">
            <p style="margin: 0;"><strong>📋 Próximos passos:</strong></p>
            <ol style="margin: 10px 0 0 0; padding-left: 20px;">
                <li>Nossa equipe analisará seu perfil com atenção</li>
                <li>Caso seu perfil seja compatível, entraremos em contato</li>
                <li>Você receberá uma resposta em até 7 dias úteis</li>
            </ol>
        </div>
        
        <p>Enquanto isso, aproveite para conhecer mais sobre nossa empresa e cultura.</p>
        
        <p>Obrigado por seu interesse em fazer parte do nosso time!</p>
    </div>
    
    <div style="background: #f3f4f6; padding: 20px; text-align: center; font-size: 14px; color: #6b7280;">
        <p style="margin: 0;">Atenciosamente,<br><strong>Equipe de Recrutamento</strong><br>{{company_name}}</p>
    </div>
</body>
</html>
""",
        "body_text": """
Olá, {{candidate_name}}!

Ficamos muito felizes em receber sua candidatura para a posição de {{job_title}}!

Próximos passos:
1. Nossa equipe analisará seu perfil com atenção
2. Caso seu perfil seja compatível, entraremos em contato
3. Você receberá uma resposta em até 7 dias úteis

Enquanto isso, aproveite para conhecer mais sobre nossa empresa e cultura.

Obrigado por seu interesse em fazer parte do nosso time!

Atenciosamente,
Equipe de Recrutamento
{{company_name}}
"""
    },
    {
        "stage_name": RecruitmentStageName.SCREENING_SCHEDULED.value,
        "template_type": TemplateType.CANDIDATE.value,
        "name": "Triagem agendada",
        "description": "Email enviado quando a triagem do candidato é agendada",
        "subject": "Triagem agendada para {{job_title}} - {{company_name}}",
        "variables": COMMON_VARIABLES + ["screening_date", "screening_time", "screening_type", "screening_link"],
        "body_html": """
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto;">
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center;">
        <h1 style="color: white; margin: 0;">{{company_name}}</h1>
    </div>
    
    <div style="padding: 30px; background: #ffffff;">
        <h2 style="color: #2563eb; margin-top: 0;">Sua triagem foi agendada! 📅</h2>
        
        <p>Olá <strong>{{candidate_name}}</strong>,</p>
        
        <p>Temos ótimas notícias! Sua candidatura para <strong>{{job_title}}</strong> avançou para a etapa de triagem.</p>
        
        <div style="background-color: #ecfdf5; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #10b981;">
            <h3 style="margin-top: 0; color: #059669;">📋 Detalhes da Triagem:</h3>
            <ul style="list-style: none; padding: 0; margin: 0;">
                <li style="padding: 5px 0;">📅 <strong>Data:</strong> {{screening_date}}</li>
                <li style="padding: 5px 0;">🕐 <strong>Horário:</strong> {{screening_time}}</li>
                <li style="padding: 5px 0;">💻 <strong>Formato:</strong> {{screening_type}}</li>
            </ul>
        </div>
        
        <div style="text-align: center; margin: 25px 0;">
            <a href="{{screening_link}}" style="background: #2563eb; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">Acessar Triagem</a>
        </div>
        
        <p><strong>Dicas para a triagem:</strong></p>
        <ul>
            <li>Esteja em um ambiente calmo e silencioso</li>
            <li>Tenha uma conexão de internet estável</li>
            <li>Mantenha seu currículo por perto para referência</li>
        </ul>
    </div>
    
    <div style="background: #f3f4f6; padding: 20px; text-align: center; font-size: 14px; color: #6b7280;">
        <p style="margin: 0;">Atenciosamente,<br><strong>{{recruiter_name}}</strong><br>{{company_name}}</p>
    </div>
</body>
</html>
""",
        "body_text": """
Sua triagem foi agendada!

Olá {{candidate_name}},

Temos ótimas notícias! Sua candidatura para {{job_title}} avançou para a etapa de triagem.

Detalhes da Triagem:
- Data: {{screening_date}}
- Horário: {{screening_time}}
- Formato: {{screening_type}}

Link de acesso: {{screening_link}}

Dicas para a triagem:
- Esteja em um ambiente calmo e silencioso
- Tenha uma conexão de internet estável
- Mantenha seu currículo por perto para referência

Atenciosamente,
{{recruiter_name}}
{{company_name}}
"""
    },
    {
        "stage_name": RecruitmentStageName.SCREENING_COMPLETED.value,
        "template_type": TemplateType.CANDIDATE.value,
        "name": "Triagem concluída",
        "description": "Email enviado após a conclusão da triagem do candidato",
        "subject": "Triagem concluída - {{job_title}} | {{company_name}}",
        "variables": COMMON_VARIABLES + ["next_steps"],
        "body_html": """
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto;">
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center;">
        <h1 style="color: white; margin: 0;">{{company_name}}</h1>
    </div>
    
    <div style="padding: 30px; background: #ffffff;">
        <h2 style="color: #2563eb; margin-top: 0;">Triagem concluída! ✅</h2>
        
        <p>Olá <strong>{{candidate_name}}</strong>,</p>
        
        <p>Agradecemos por participar da etapa de triagem para a vaga de <strong>{{job_title}}</strong>.</p>
        
        <p>Sua triagem foi concluída com sucesso e nossa equipe está analisando os resultados.</p>
        
        <div style="background-color: #f0f9ff; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #2563eb;">
            <p style="margin: 0;"><strong>⏳ O que acontece agora?</strong></p>
            <p style="margin: 10px 0 0 0;">{{next_steps}}</p>
        </div>
        
        <p>Em caso de dúvidas, fique à vontade para responder este email.</p>
    </div>
    
    <div style="background: #f3f4f6; padding: 20px; text-align: center; font-size: 14px; color: #6b7280;">
        <p style="margin: 0;">Atenciosamente,<br><strong>{{recruiter_name}}</strong><br>{{company_name}}</p>
    </div>
</body>
</html>
""",
        "body_text": """
Triagem concluída!

Olá {{candidate_name}},

Agradecemos por participar da etapa de triagem para a vaga de {{job_title}}.

Sua triagem foi concluída com sucesso e nossa equipe está analisando os resultados.

O que acontece agora?
{{next_steps}}

Em caso de dúvidas, fique à vontade para responder este email.

Atenciosamente,
{{recruiter_name}}
{{company_name}}
"""
    },
    {
        "stage_name": RecruitmentStageName.INTERVIEW_SCHEDULED.value,
        "template_type": TemplateType.CANDIDATE.value,
        "name": "Entrevista agendada",
        "description": "Email enviado quando uma entrevista é agendada",
        "subject": "🎯 Entrevista agendada - {{job_title}} | {{company_name}}",
        "variables": COMMON_VARIABLES + ["interview_date", "interview_time", "interview_type", "interview_location", "interviewer_name", "interviewer_role", "interview_link"],
        "body_html": """
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto;">
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center;">
        <h1 style="color: white; margin: 0;">{{company_name}}</h1>
    </div>
    
    <div style="padding: 30px; background: #ffffff;">
        <h2 style="color: #2563eb; margin-top: 0;">Sua entrevista está confirmada! 🎯</h2>
        
        <p>Olá <strong>{{candidate_name}}</strong>,</p>
        
        <p>Parabéns! Você avançou para a etapa de entrevista para a posição de <strong>{{job_title}}</strong>.</p>
        
        <div style="background-color: #ecfdf5; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #10b981;">
            <h3 style="margin-top: 0; color: #059669;">📋 Detalhes da Entrevista:</h3>
            <ul style="list-style: none; padding: 0; margin: 0;">
                <li style="padding: 5px 0;">📅 <strong>Data:</strong> {{interview_date}}</li>
                <li style="padding: 5px 0;">🕐 <strong>Horário:</strong> {{interview_time}}</li>
                <li style="padding: 5px 0;">💻 <strong>Formato:</strong> {{interview_type}}</li>
                <li style="padding: 5px 0;">📍 <strong>Local:</strong> {{interview_location}}</li>
                <li style="padding: 5px 0;">👤 <strong>Entrevistador:</strong> {{interviewer_name}} - {{interviewer_role}}</li>
            </ul>
        </div>
        
        <div style="text-align: center; margin: 25px 0;">
            <a href="{{interview_link}}" style="background: #2563eb; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">Acessar Entrevista</a>
        </div>
        
        <div style="background-color: #fef3c7; padding: 15px; border-radius: 8px; margin: 20px 0;">
            <p style="margin: 0;"><strong>💡 Dicas para a entrevista:</strong></p>
            <ul style="margin: 10px 0 0 0; padding-left: 20px;">
                <li>Pesquise sobre a empresa e a vaga</li>
                <li>Prepare exemplos de experiências relevantes</li>
                <li>Tenha perguntas prontas sobre a posição</li>
                <li>Teste sua câmera e microfone com antecedência</li>
            </ul>
        </div>
    </div>
    
    <div style="background: #f3f4f6; padding: 20px; text-align: center; font-size: 14px; color: #6b7280;">
        <p style="margin: 0;">Atenciosamente,<br><strong>{{recruiter_name}}</strong><br>{{company_name}}</p>
    </div>
</body>
</html>
""",
        "body_text": """
Sua entrevista está confirmada!

Olá {{candidate_name}},

Parabéns! Você avançou para a etapa de entrevista para a posição de {{job_title}}.

Detalhes da Entrevista:
- Data: {{interview_date}}
- Horário: {{interview_time}}
- Formato: {{interview_type}}
- Local: {{interview_location}}
- Entrevistador: {{interviewer_name}} - {{interviewer_role}}

Link de acesso: {{interview_link}}

Dicas para a entrevista:
- Pesquise sobre a empresa e a vaga
- Prepare exemplos de experiências relevantes
- Tenha perguntas prontas sobre a posição
- Teste sua câmera e microfone com antecedência

Atenciosamente,
{{recruiter_name}}
{{company_name}}
"""
    },
    {
        "stage_name": RecruitmentStageName.INTERVIEW_REMINDER.value,
        "template_type": TemplateType.CANDIDATE.value,
        "name": "Lembrete de entrevista",
        "description": "Lembrete enviado antes da entrevista",
        "subject": "⏰ Lembrete: Sua entrevista é amanhã - {{job_title}}",
        "variables": COMMON_VARIABLES + ["interview_date", "interview_time", "interview_type", "interview_location", "interviewer_name", "interview_link"],
        "body_html": """
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto;">
    <div style="background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); padding: 30px; text-align: center;">
        <h1 style="color: white; margin: 0;">⏰ Lembrete de Entrevista</h1>
    </div>
    
    <div style="padding: 30px; background: #ffffff;">
        <h2 style="color: #d97706; margin-top: 0;">Sua entrevista está chegando!</h2>
        
        <p>Olá <strong>{{candidate_name}}</strong>,</p>
        
        <p>Este é um lembrete amigável sobre sua entrevista para a posição de <strong>{{job_title}}</strong> na <strong>{{company_name}}</strong>.</p>
        
        <div style="background-color: #fef3c7; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #f59e0b;">
            <h3 style="margin-top: 0; color: #b45309;">📋 Detalhes:</h3>
            <ul style="list-style: none; padding: 0; margin: 0;">
                <li style="padding: 5px 0;">📅 <strong>Data:</strong> {{interview_date}}</li>
                <li style="padding: 5px 0;">🕐 <strong>Horário:</strong> {{interview_time}}</li>
                <li style="padding: 5px 0;">💻 <strong>Formato:</strong> {{interview_type}}</li>
                <li style="padding: 5px 0;">📍 <strong>Local:</strong> {{interview_location}}</li>
                <li style="padding: 5px 0;">👤 <strong>Entrevistador:</strong> {{interviewer_name}}</li>
            </ul>
        </div>
        
        <div style="text-align: center; margin: 25px 0;">
            <a href="{{interview_link}}" style="background: #f59e0b; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">Acessar Entrevista</a>
        </div>
        
        <p style="color: #6b7280;">Não esqueça de testar sua câmera e microfone antes da entrevista. Boa sorte! 🍀</p>
    </div>
    
    <div style="background: #f3f4f6; padding: 20px; text-align: center; font-size: 14px; color: #6b7280;">
        <p style="margin: 0;">Atenciosamente,<br><strong>Equipe de Recrutamento</strong><br>{{company_name}}</p>
    </div>
</body>
</html>
""",
        "body_text": """
Lembrete: Sua entrevista está chegando!

Olá {{candidate_name}},

Este é um lembrete amigável sobre sua entrevista para a posição de {{job_title}} na {{company_name}}.

Detalhes:
- Data: {{interview_date}}
- Horário: {{interview_time}}
- Formato: {{interview_type}}
- Local: {{interview_location}}
- Entrevistador: {{interviewer_name}}

Link de acesso: {{interview_link}}

Não esqueça de testar sua câmera e microfone antes da entrevista. Boa sorte!

Atenciosamente,
Equipe de Recrutamento
{{company_name}}
"""
    },
    {
        "stage_name": RecruitmentStageName.INTERVIEW_COMPLETED.value,
        "template_type": TemplateType.CANDIDATE.value,
        "name": "Entrevista realizada",
        "description": "Email de agradecimento após a entrevista",
        "subject": "Obrigado pela entrevista - {{job_title}} | {{company_name}}",
        "variables": COMMON_VARIABLES + ["interview_date", "next_steps", "feedback_timeline"],
        "body_html": """
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto;">
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center;">
        <h1 style="color: white; margin: 0;">{{company_name}}</h1>
    </div>
    
    <div style="padding: 30px; background: #ffffff;">
        <h2 style="color: #2563eb; margin-top: 0;">Obrigado pela entrevista! 🙏</h2>
        
        <p>Olá <strong>{{candidate_name}}</strong>,</p>
        
        <p>Agradecemos por dedicar seu tempo para conversar conosco sobre a posição de <strong>{{job_title}}</strong>.</p>
        
        <p>Foi um prazer conhecer mais sobre sua trajetória e experiências. Nossa equipe está avaliando todas as entrevistas realizadas.</p>
        
        <div style="background-color: #f0f9ff; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #2563eb;">
            <p style="margin: 0;"><strong>📅 Próximos passos:</strong></p>
            <p style="margin: 10px 0 0 0;">{{next_steps}}</p>
            <p style="margin: 10px 0 0 0;"><strong>⏱ Prazo para retorno:</strong> {{feedback_timeline}}</p>
        </div>
        
        <p>Se tiver alguma dúvida, fique à vontade para entrar em contato.</p>
    </div>
    
    <div style="background: #f3f4f6; padding: 20px; text-align: center; font-size: 14px; color: #6b7280;">
        <p style="margin: 0;">Atenciosamente,<br><strong>{{recruiter_name}}</strong><br>{{company_name}}</p>
    </div>
</body>
</html>
""",
        "body_text": """
Obrigado pela entrevista!

Olá {{candidate_name}},

Agradecemos por dedicar seu tempo para conversar conosco sobre a posição de {{job_title}}.

Foi um prazer conhecer mais sobre sua trajetória e experiências. Nossa equipe está avaliando todas as entrevistas realizadas.

Próximos passos:
{{next_steps}}

Prazo para retorno: {{feedback_timeline}}

Se tiver alguma dúvida, fique à vontade para entrar em contato.

Atenciosamente,
{{recruiter_name}}
{{company_name}}
"""
    },
    {
        "stage_name": RecruitmentStageName.OFFER_SENT.value,
        "template_type": TemplateType.CANDIDATE.value,
        "name": "Proposta enviada",
        "description": "Email com proposta de trabalho",
        "subject": "🎉 Proposta de Trabalho - {{job_title}} | {{company_name}}",
        "variables": COMMON_VARIABLES + ["salary", "start_date", "benefits", "contract_type", "offer_deadline", "offer_link"],
        "body_html": """
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto;">
    <div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); padding: 30px; text-align: center;">
        <h1 style="color: white; margin: 0;">🎉 Parabéns!</h1>
    </div>
    
    <div style="padding: 30px; background: #ffffff;">
        <h2 style="color: #059669; margin-top: 0;">Você recebeu uma proposta!</h2>
        
        <p>Olá <strong>{{candidate_name}}</strong>,</p>
        
        <p>É com grande satisfação que comunicamos que você foi <strong>selecionado(a)</strong> para a posição de <strong>{{job_title}}</strong> na <strong>{{company_name}}</strong>!</p>
        
        <div style="background-color: #ecfdf5; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #10b981;">
            <h3 style="margin-top: 0; color: #059669;">📋 Detalhes da Proposta:</h3>
            <ul style="list-style: none; padding: 0; margin: 0;">
                <li style="padding: 8px 0;">💼 <strong>Cargo:</strong> {{job_title}}</li>
                <li style="padding: 8px 0;">💰 <strong>Remuneração:</strong> {{salary}}</li>
                <li style="padding: 8px 0;">📅 <strong>Data de Início:</strong> {{start_date}}</li>
                <li style="padding: 8px 0;">📝 <strong>Tipo de Contrato:</strong> {{contract_type}}</li>
                <li style="padding: 8px 0;">🎁 <strong>Benefícios:</strong> {{benefits}}</li>
            </ul>
        </div>
        
        <div style="background-color: #fef3c7; padding: 15px; border-radius: 8px; margin: 20px 0;">
            <p style="margin: 0;"><strong>⏰ Prazo para resposta:</strong> {{offer_deadline}}</p>
        </div>
        
        <div style="text-align: center; margin: 25px 0;">
            <a href="{{offer_link}}" style="background: #10b981; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">Ver Proposta Completa</a>
        </div>
        
        <p>Estamos ansiosos para ter você em nosso time!</p>
    </div>
    
    <div style="background: #f3f4f6; padding: 20px; text-align: center; font-size: 14px; color: #6b7280;">
        <p style="margin: 0;">Atenciosamente,<br><strong>{{recruiter_name}}</strong><br>{{company_name}}</p>
    </div>
</body>
</html>
""",
        "body_text": """
Parabéns! Você recebeu uma proposta!

Olá {{candidate_name}},

É com grande satisfação que comunicamos que você foi selecionado(a) para a posição de {{job_title}} na {{company_name}}!

Detalhes da Proposta:
- Cargo: {{job_title}}
- Remuneração: {{salary}}
- Data de Início: {{start_date}}
- Tipo de Contrato: {{contract_type}}
- Benefícios: {{benefits}}

Prazo para resposta: {{offer_deadline}}

Ver proposta completa: {{offer_link}}

Estamos ansiosos para ter você em nosso time!

Atenciosamente,
{{recruiter_name}}
{{company_name}}
"""
    },
    {
        "stage_name": RecruitmentStageName.CANDIDATE_HIRED.value,
        "template_type": TemplateType.CANDIDATE.value,
        "name": "Parabéns! Você foi contratado",
        "description": "Email de confirmação de contratação",
        "subject": "🎊 Bem-vindo(a) à {{company_name}}!",
        "variables": COMMON_VARIABLES + ["start_date", "onboarding_date", "manager_name", "department", "welcome_link"],
        "body_html": """
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto;">
    <div style="background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%); padding: 30px; text-align: center;">
        <h1 style="color: white; margin: 0;">🎊 Bem-vindo(a) ao time!</h1>
    </div>
    
    <div style="padding: 30px; background: #ffffff;">
        <h2 style="color: #7c3aed; margin-top: 0;">Parabéns, {{candidate_name}}!</h2>
        
        <p>É com enorme alegria que confirmamos sua <strong>contratação</strong> para a posição de <strong>{{job_title}}</strong>!</p>
        
        <p>Estamos muito felizes em ter você como parte da família <strong>{{company_name}}</strong>.</p>
        
        <div style="background-color: #f5f3ff; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #8b5cf6;">
            <h3 style="margin-top: 0; color: #6d28d9;">📋 Informações Importantes:</h3>
            <ul style="list-style: none; padding: 0; margin: 0;">
                <li style="padding: 8px 0;">📅 <strong>Data de Início:</strong> {{start_date}}</li>
                <li style="padding: 8px 0;">🎓 <strong>Onboarding:</strong> {{onboarding_date}}</li>
                <li style="padding: 8px 0;">👤 <strong>Seu Gestor:</strong> {{manager_name}}</li>
                <li style="padding: 8px 0;">🏢 <strong>Departamento:</strong> {{department}}</li>
            </ul>
        </div>
        
        <div style="text-align: center; margin: 25px 0;">
            <a href="{{welcome_link}}" style="background: #8b5cf6; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">Acessar Portal de Boas-Vindas</a>
        </div>
        
        <p>Enviaremos mais informações sobre o seu primeiro dia em breve. Se tiver dúvidas, não hesite em nos contatar!</p>
    </div>
    
    <div style="background: #f3f4f6; padding: 20px; text-align: center; font-size: 14px; color: #6b7280;">
        <p style="margin: 0;">Com carinho,<br><strong>Equipe de Pessoas</strong><br>{{company_name}}</p>
    </div>
</body>
</html>
""",
        "body_text": """
Parabéns, {{candidate_name}}!

É com enorme alegria que confirmamos sua contratação para a posição de {{job_title}}!

Estamos muito felizes em ter você como parte da família {{company_name}}.

Informações Importantes:
- Data de Início: {{start_date}}
- Onboarding: {{onboarding_date}}
- Seu Gestor: {{manager_name}}
- Departamento: {{department}}

Acesse o Portal de Boas-Vindas: {{welcome_link}}

Enviaremos mais informações sobre o seu primeiro dia em breve. Se tiver dúvidas, não hesite em nos contatar!

Com carinho,
Equipe de Pessoas
{{company_name}}
"""
    },
    {
        "stage_name": RecruitmentStageName.CANDIDATE_REJECTED.value,
        "template_type": TemplateType.CANDIDATE.value,
        "name": "Feedback do processo",
        "description": "Email de feedback humanizado para candidatos não selecionados",
        "subject": "Atualização sobre sua candidatura - {{job_title}}",
        "variables": COMMON_VARIABLES + ["feedback_message", "strengths", "improvement_areas"],
        "body_html": """
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto;">
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center;">
        <h1 style="color: white; margin: 0;">{{company_name}}</h1>
    </div>
    
    <div style="padding: 30px; background: #ffffff;">
        <h2 style="color: #4b5563; margin-top: 0;">Atualização sobre sua candidatura</h2>
        
        <p>Olá <strong>{{candidate_name}}</strong>,</p>
        
        <p>Primeiramente, gostaríamos de agradecer pelo tempo e dedicação que você investiu no processo seletivo para a posição de <strong>{{job_title}}</strong>.</p>
        
        <p>Após uma análise cuidadosa, decidimos seguir com outros candidatos cujos perfis estão mais alinhados com as necessidades específicas desta posição neste momento.</p>
        
        <div style="background-color: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <p style="margin: 0 0 10px 0;"><strong>📝 Nosso feedback:</strong></p>
            <p style="margin: 0;">{{feedback_message}}</p>
        </div>
        
        <div style="background-color: #ecfdf5; padding: 15px; border-radius: 8px; margin: 15px 0;">
            <p style="margin: 0;"><strong>✨ Pontos fortes observados:</strong></p>
            <p style="margin: 5px 0 0 0;">{{strengths}}</p>
        </div>
        
        <div style="background-color: #fef3c7; padding: 15px; border-radius: 8px; margin: 15px 0;">
            <p style="margin: 0;"><strong>💡 Sugestões de desenvolvimento:</strong></p>
            <p style="margin: 5px 0 0 0;">{{improvement_areas}}</p>
        </div>
        
        <p>Seu perfil permanecerá em nosso banco de talentos e entraremos em contato caso surjam oportunidades mais alinhadas ao seu perfil.</p>
        
        <p>Desejamos muito sucesso em sua jornada profissional! 🍀</p>
    </div>
    
    <div style="background: #f3f4f6; padding: 20px; text-align: center; font-size: 14px; color: #6b7280;">
        <p style="margin: 0;">Atenciosamente,<br><strong>{{recruiter_name}}</strong><br>{{company_name}}</p>
    </div>
</body>
</html>
""",
        "body_text": """
Atualização sobre sua candidatura

Olá {{candidate_name}},

Primeiramente, gostaríamos de agradecer pelo tempo e dedicação que você investiu no processo seletivo para a posição de {{job_title}}.

Após uma análise cuidadosa, decidimos seguir com outros candidatos cujos perfis estão mais alinhados com as necessidades específicas desta posição neste momento.

Nosso feedback:
{{feedback_message}}

Pontos fortes observados:
{{strengths}}

Sugestões de desenvolvimento:
{{improvement_areas}}

Seu perfil permanecerá em nosso banco de talentos e entraremos em contato caso surjam oportunidades mais alinhadas ao seu perfil.

Desejamos muito sucesso em sua jornada profissional!

Atenciosamente,
{{recruiter_name}}
{{company_name}}
"""
    },
    {
        "stage_name": RecruitmentStageName.STAGE_CHANGED.value,
        "template_type": TemplateType.CANDIDATE.value,
        "name": "Atualização do seu processo",
        "description": "Email genérico para notificar mudança de etapa",
        "subject": "Atualização: Seu processo para {{job_title}} avançou!",
        "variables": COMMON_VARIABLES + ["previous_stage", "current_stage", "stage_description", "next_steps"],
        "body_html": """
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto;">
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center;">
        <h1 style="color: white; margin: 0;">{{company_name}}</h1>
    </div>
    
    <div style="padding: 30px; background: #ffffff;">
        <h2 style="color: #2563eb; margin-top: 0;">Atualização do seu processo! 📢</h2>
        
        <p>Olá <strong>{{candidate_name}}</strong>,</p>
        
        <p>Gostaríamos de informar que sua candidatura para a posição de <strong>{{job_title}}</strong> avançou no processo seletivo!</p>
        
        <div style="display: flex; align-items: center; justify-content: center; margin: 25px 0;">
            <div style="background: #e5e7eb; padding: 10px 20px; border-radius: 8px;">
                <p style="margin: 0; color: #6b7280; font-size: 14px;">Etapa anterior</p>
                <p style="margin: 5px 0 0 0; font-weight: bold;">{{previous_stage}}</p>
            </div>
            <div style="padding: 0 15px; font-size: 24px;">→</div>
            <div style="background: #dbeafe; padding: 10px 20px; border-radius: 8px; border: 2px solid #2563eb;">
                <p style="margin: 0; color: #2563eb; font-size: 14px;">Etapa atual</p>
                <p style="margin: 5px 0 0 0; font-weight: bold; color: #1d4ed8;">{{current_stage}}</p>
            </div>
        </div>
        
        <div style="background-color: #f0f9ff; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #2563eb;">
            <p style="margin: 0;"><strong>📋 Sobre esta etapa:</strong></p>
            <p style="margin: 10px 0 0 0;">{{stage_description}}</p>
        </div>
        
        <div style="background-color: #ecfdf5; padding: 15px; border-radius: 8px; margin: 20px 0;">
            <p style="margin: 0;"><strong>⏭ Próximos passos:</strong></p>
            <p style="margin: 5px 0 0 0;">{{next_steps}}</p>
        </div>
        
        <p>Parabéns pelo progresso! Continuaremos acompanhando seu processo.</p>
    </div>
    
    <div style="background: #f3f4f6; padding: 20px; text-align: center; font-size: 14px; color: #6b7280;">
        <p style="margin: 0;">Atenciosamente,<br><strong>{{recruiter_name}}</strong><br>{{company_name}}</p>
    </div>
</body>
</html>
""",
        "body_text": """
Atualização do seu processo!

Olá {{candidate_name}},

Gostaríamos de informar que sua candidatura para a posição de {{job_title}} avançou no processo seletivo!

Etapa anterior: {{previous_stage}}
Etapa atual: {{current_stage}}

Sobre esta etapa:
{{stage_description}}

Próximos passos:
{{next_steps}}

Parabéns pelo progresso! Continuaremos acompanhando seu processo.

Atenciosamente,
{{recruiter_name}}
{{company_name}}
"""
    },
]

SAMPLE_DATA: dict[str, str] = {
    "candidate_name": "João Silva",
    "candidate_email": "joao.silva@email.com",
    "job_title": "Desenvolvedor Full Stack Senior",
    "company_name": "TechCorp Brasil",
    "recruiter_name": "Maria Santos",
    "recruiter_email": "maria.santos@techcorp.com.br",
    "application_date": "15/01/2026",
    "screening_date": "20/01/2026",
    "screening_time": "14:00",
    "screening_type": "Vídeo chamada",
    "screening_link": "https://meet.example.com/screening-123",
    "next_steps": "Aguarde o retorno da nossa equipe em até 5 dias úteis.",
    "interview_date": "25/01/2026",
    "interview_time": "10:00",
    "interview_type": "Entrevista técnica online",
    "interview_location": "Google Meet",
    "interviewer_name": "Carlos Oliveira",
    "interviewer_role": "Tech Lead",
    "interview_link": "https://meet.google.com/abc-defg-hij",
    "feedback_timeline": "5 dias úteis",
    "salary": "R$ 18.000,00",
    "start_date": "01/02/2026",
    "benefits": "Vale Refeição, Vale Transporte, Plano de Saúde, PLR, Gympass",
    "contract_type": "CLT",
    "offer_deadline": "22/01/2026",
    "offer_link": "https://portal.techcorp.com.br/proposta/123",
    "onboarding_date": "03/02/2026",
    "manager_name": "Ana Paula Costa",
    "department": "Engenharia de Software",
    "welcome_link": "https://portal.techcorp.com.br/boas-vindas",
    "feedback_message": "Você demonstrou boa comunicação e conhecimento técnico sólido.",
    "strengths": "Excelente capacidade de comunicação, experiência relevante em projetos similares.",
    "improvement_areas": "Recomendamos aprofundar conhecimentos em arquitetura de microsserviços.",
    "previous_stage": "Triagem",
    "current_stage": "Entrevista RH",
    "stage_description": "Nesta etapa, você conversará com nossa equipe de RH sobre sua trajetória e expectativas.",
}


async def seed_default_templates(db: AsyncSession, company_id: str | None = None) -> list[RecruitmentEmailTemplate]:
    """
    Seed default recruitment email templates.
    If company_id is provided, creates templates for that company.
    If company_id is None, creates system-wide templates.
    """
    created_templates = []
    
    for template_data in DEFAULT_TEMPLATES:
        existing = await RecruitmentEmailTemplateRepository(db).find_by_stage_type_company(
            stage_name=template_data["stage_name"],
            template_type=template_data["template_type"],
            company_id=company_id,
        )

        if existing:
            continue
        
        template = RecruitmentEmailTemplate(
            company_id=company_id,
            stage_name=template_data["stage_name"],
            template_type=template_data["template_type"],
            name=template_data["name"],
            description=template_data.get("description"),
            subject=template_data["subject"],
            body_html=template_data["body_html"],
            body_text=template_data.get("body_text"),
            variables=template_data.get("variables", []),
            is_active=True,
            is_default=True,
            is_system=company_id is None,
        )
        
        db.add(template)
        created_templates.append(template)
    
    if created_templates:
        await db.commit()
        for t in created_templates:
            await db.refresh(t)
    
    return created_templates


async def get_template_for_stage(
    db: AsyncSession,
    stage_name: str,
    company_id: str | None = None,
    template_type: str = "candidate"
) -> RecruitmentEmailTemplate | None:
    """
    Get the active template for a specific stage.
    First looks for company-specific template, then falls back to system template.
    """
    repo = RecruitmentEmailTemplateRepository(db)
    if company_id:
        template = await repo.find_active_for_stage(
            stage_name=stage_name, template_type=template_type, company_id=company_id
        )
        if template:
            return template

    return await repo.find_active_system_for_stage(
        stage_name=stage_name, template_type=template_type
    )


async def list_templates(
    db: AsyncSession,
    company_id: str | None = None,
    stage_name: str | None = None,
    template_type: str | None = None,
    is_active: bool | None = None
) -> list[RecruitmentEmailTemplate]:
    """
    List recruitment email templates with optional filtering.
    Returns company templates plus system templates.
    """
    return await RecruitmentEmailTemplateRepository(db).list_templates(
        company_id=company_id,
        stage_name=stage_name,
        template_type=template_type,
        is_active=is_active,
    )


def render_template(template: RecruitmentEmailTemplate, variables: dict[str, str]) -> dict[str, str]:
    """
    Render a template with the provided variables.
    Returns both HTML and text versions.
    """
    subject = template.subject
    body_html = template.body_html
    body_text = template.body_text or ""
    
    for key, value in variables.items():
        placeholder = "{{" + key + "}}"
        subject = subject.replace(placeholder, str(value))
        body_html = body_html.replace(placeholder, str(value))
        body_text = body_text.replace(placeholder, str(value))
    
    return {
        "subject": subject,
        "body_html": body_html,
        "body_text": body_text,
    }


def preview_template(template: RecruitmentEmailTemplate) -> dict[str, str]:
    """
    Preview a template with sample data.
    """
    return render_template(template, SAMPLE_DATA)


async def clone_templates_for_company(
    db: AsyncSession,
    company_id: str,
    created_by: str | None = None
) -> list[RecruitmentEmailTemplate]:
    """
    Clone system templates for a specific company.
    """
    repo = RecruitmentEmailTemplateRepository(db)
    system_templates_list = await repo.list_system_templates()

    created_templates = []

    for system_template in system_templates_list:
        existing = await repo.find_by_stage_type_company(
            stage_name=system_template.stage_name,
            template_type=system_template.template_type,
            company_id=company_id,
        )

        if existing:
            continue
        
        new_template = RecruitmentEmailTemplate(
            company_id=company_id,
            stage_name=system_template.stage_name,
            template_type=system_template.template_type,
            name=system_template.name,
            description=system_template.description,
            subject=system_template.subject,
            body_html=system_template.body_html,
            body_text=system_template.body_text,
            variables=system_template.variables,
            is_active=True,
            is_default=False,
            is_system=False,
            created_by=created_by,
        )
        
        db.add(new_template)
        created_templates.append(new_template)
    
    if created_templates:
        await db.commit()
        for t in created_templates:
            await db.refresh(t)
    
    return created_templates
