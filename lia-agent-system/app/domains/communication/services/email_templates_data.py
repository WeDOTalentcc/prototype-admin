"""
Default email templates data.

Extracted from email_service.py for better modularity and maintainability.
Contains all DEFAULT_TEMPLATES used by EmailService for seeding and rendering.
"""
from typing import Dict, Any, List, Optional

DEFAULT_TEMPLATES = [
    {
        "name": "Convite para Entrevista",
        "subject": "Convite para Entrevista - {{job_title}} na {{company_name}}",
        "category": "interview",
        "channel": "email",
        "situation": "entrevista",
        "variables": ["candidate_name", "job_title", "company_name", "interview_date", "interview_time", "interview_location", "interviewer_name", "unsubscribe_url"],
        "body_html": """
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #2563eb;">Convite para Entrevista</h2>
    
    <p>Olá <strong>{{candidate_name}}</strong>,</p>
    
    <p>Ficamos muito felizes em informar que você foi selecionado(a) para uma entrevista para a posição de <strong>{{job_title}}</strong> na <strong>{{company_name}}</strong>!</p>
    
    <div style="background-color: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0;">
        <h3 style="margin-top: 0; color: #1f2937;">Detalhes da Entrevista:</h3>
        <ul style="list-style: none; padding: 0;">
            <li>📅 <strong>Data:</strong> {{interview_date}}</li>
            <li>🕐 <strong>Horário:</strong> {{interview_time}}</li>
            <li>📍 <strong>Local:</strong> {{interview_location}}</li>
            <li>👤 <strong>Entrevistador:</strong> {{interviewer_name}}</li>
        </ul>
    </div>
    
    <p>Por favor, confirme sua disponibilidade respondendo a este email.</p>
    
    <p>Boa sorte!</p>
    
    <p style="color: #6b7280; font-size: 14px; margin-top: 30px;">
        Atenciosamente,<br>
        Equipe de Recrutamento<br>
        {{company_name}}
    </p>
    <div style="margin-top: 40px; padding-top: 15px; border-top: 1px solid #e5e7eb; text-align: center;">
        <p style="color: #9ca3af; font-size: 12px;">
            Você está recebendo este email porque participou de um processo seletivo gerenciado pela Plataforma LIA.<br>
            Se não deseja mais receber comunicações, <a href="{{unsubscribe_url}}" style="color: #6b7280; text-decoration: underline;">clique aqui para cancelar</a> (LGPD Art. 8°, §5°).
        </p>
    </div>
</body>
</html>
""",
        "body_text": """
Convite para Entrevista

Olá {{candidate_name}},

Ficamos muito felizes em informar que você foi selecionado(a) para uma entrevista para a posição de {{job_title}} na {{company_name}}!

Detalhes da Entrevista:
- Data: {{interview_date}}
- Horário: {{interview_time}}
- Local: {{interview_location}}
- Entrevistador: {{interviewer_name}}

Por favor, confirme sua disponibilidade respondendo a este email.

Boa sorte!

Atenciosamente,
Equipe de Recrutamento
{{company_name}}

---
Se não deseja mais receber comunicações, acesse: {{unsubscribe_url}}
(LGPD Art. 8°, §5°)
"""
    },
    {
        "name": "Agradecimento pela Candidatura",
        "subject": "Recebemos sua candidatura - {{job_title}}",
        "category": "followup",
        "channel": "email",
        "situation": "triagem",
        "variables": ["candidate_name", "job_title", "company_name", "unsubscribe_url"],
        "body_html": """
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #2563eb;">Obrigado por se candidatar!</h2>
    
    <p>Olá <strong>{{candidate_name}}</strong>,</p>
    
    <p>Agradecemos pelo seu interesse na posição de <strong>{{job_title}}</strong> na <strong>{{company_name}}</strong>.</p>
    
    <p>Recebemos sua candidatura e ela está sendo analisada pela nossa equipe de recrutamento. Entraremos em contato em breve para informar sobre os próximos passos do processo seletivo.</p>
    
    <p>Enquanto isso, fique à vontade para conhecer mais sobre nossa empresa e cultura.</p>
    
    <p style="color: #6b7280; font-size: 14px; margin-top: 30px;">
        Atenciosamente,<br>
        Equipe de Recrutamento<br>
        {{company_name}}
    </p>
    <div style="margin-top: 40px; padding-top: 15px; border-top: 1px solid #e5e7eb; text-align: center;">
        <p style="color: #9ca3af; font-size: 12px;">
            Você está recebendo este email porque participou de um processo seletivo gerenciado pela Plataforma LIA.<br>
            Se não deseja mais receber comunicações, <a href="{{unsubscribe_url}}" style="color: #6b7280; text-decoration: underline;">clique aqui para cancelar</a> (LGPD Art. 8°, §5°).
        </p>
    </div>
</body>
</html>
""",
        "body_text": """
Obrigado por se candidatar!

Olá {{candidate_name}},

Agradecemos pelo seu interesse na posição de {{job_title}} na {{company_name}}.

Recebemos sua candidatura e ela está sendo analisada pela nossa equipe de recrutamento. Entraremos em contato em breve para informar sobre os próximos passos do processo seletivo.

Enquanto isso, fique à vontade para conhecer mais sobre nossa empresa e cultura.

Atenciosamente,
Equipe de Recrutamento
{{company_name}}

---
Se não deseja mais receber comunicações, acesse: {{unsubscribe_url}}
(LGPD Art. 8°, §5°)
"""
    },
    {
        "name": "Feedback Negativo (Humanizado)",
        "subject": "Atualização sobre sua candidatura - {{job_title}}",
        "category": "rejection",
        "channel": "email",
        "situation": "rejeicao",
        "variables": ["candidate_name", "job_title", "company_name", "feedback_message", "unsubscribe_url"],
        "body_html": """
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #2563eb;">Atualização sobre sua candidatura</h2>
    
    <p>Olá <strong>{{candidate_name}}</strong>,</p>
    
    <p>Primeiramente, gostaríamos de agradecer pelo tempo e esforço dedicados ao processo seletivo para a posição de <strong>{{job_title}}</strong> na <strong>{{company_name}}</strong>.</p>
    
    <p>Após uma análise cuidadosa, decidimos seguir com outros candidatos cujos perfis estão mais alinhados com as necessidades específicas desta posição neste momento.</p>
    
    <p>{{feedback_message}}</p>
    
    <p>Valorizamos muito seu interesse em fazer parte da nossa equipe. Seu perfil ficará em nosso banco de talentos e entraremos em contato caso surjam oportunidades compatíveis no futuro.</p>
    
    <p>Desejamos muito sucesso em sua jornada profissional!</p>
    
    <p style="color: #6b7280; font-size: 14px; margin-top: 30px;">
        Atenciosamente,<br>
        Equipe de Recrutamento<br>
        {{company_name}}
    </p>
    <div style="margin-top: 40px; padding-top: 15px; border-top: 1px solid #e5e7eb; text-align: center;">
        <p style="color: #9ca3af; font-size: 12px;">
            Você está recebendo este email porque participou de um processo seletivo gerenciado pela Plataforma LIA.<br>
            Se não deseja mais receber comunicações, <a href="{{unsubscribe_url}}" style="color: #6b7280; text-decoration: underline;">clique aqui para cancelar</a> (LGPD Art. 8°, §5°).
        </p>
    </div>
</body>
</html>
""",
        "body_text": """
Atualização sobre sua candidatura

Olá {{candidate_name}},

Primeiramente, gostaríamos de agradecer pelo tempo e esforço dedicados ao processo seletivo para a posição de {{job_title}} na {{company_name}}.

Após uma análise cuidadosa, decidimos seguir com outros candidatos cujos perfis estão mais alinhados com as necessidades específicas desta posição neste momento.

{{feedback_message}}

Valorizamos muito seu interesse em fazer parte da nossa equipe. Seu perfil ficará em nosso banco de talentos e entraremos em contato caso surjam oportunidades compatíveis no futuro.

Desejamos muito sucesso em sua jornada profissional!

Atenciosamente,
Equipe de Recrutamento
{{company_name}}

---
Se não deseja mais receber comunicações, acesse: {{unsubscribe_url}}
(LGPD Art. 8°, §5°)
"""
    },
    {
        "name": "Oferta de Trabalho",
        "subject": "🎉 Proposta de Trabalho - {{job_title}} na {{company_name}}",
        "category": "offer",
        "channel": "email",
        "situation": "proposta",
        "variables": ["candidate_name", "job_title", "company_name", "salary", "start_date", "benefits", "hiring_manager", "unsubscribe_url"],
        "body_html": """
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #16a34a;">🎉 Parabéns! Temos uma proposta para você!</h2>
    
    <p>Olá <strong>{{candidate_name}}</strong>,</p>
    
    <p>É com grande satisfação que comunicamos que você foi <strong>selecionado(a)</strong> para a posição de <strong>{{job_title}}</strong> na <strong>{{company_name}}</strong>!</p>
    
    <div style="background-color: #f0fdf4; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #16a34a;">
        <h3 style="margin-top: 0; color: #15803d;">Detalhes da Proposta:</h3>
        <ul style="list-style: none; padding: 0;">
            <li>💼 <strong>Cargo:</strong> {{job_title}}</li>
            <li>💰 <strong>Remuneração:</strong> {{salary}}</li>
            <li>📅 <strong>Data de Início:</strong> {{start_date}}</li>
            <li>🎁 <strong>Benefícios:</strong> {{benefits}}</li>
        </ul>
    </div>
    
    <p>Para discutir os detalhes da proposta e próximos passos, por favor entre em contato com <strong>{{hiring_manager}}</strong>.</p>
    
    <p>Estamos ansiosos para tê-lo(a) em nossa equipe!</p>
    
    <p style="color: #6b7280; font-size: 14px; margin-top: 30px;">
        Atenciosamente,<br>
        Equipe de Recrutamento<br>
        {{company_name}}
    </p>
    <div style="margin-top: 40px; padding-top: 15px; border-top: 1px solid #e5e7eb; text-align: center;">
        <p style="color: #9ca3af; font-size: 12px;">
            Você está recebendo este email porque participou de um processo seletivo gerenciado pela Plataforma LIA.<br>
            Se não deseja mais receber comunicações, <a href="{{unsubscribe_url}}" style="color: #6b7280; text-decoration: underline;">clique aqui para cancelar</a> (LGPD Art. 8°, §5°).
        </p>
    </div>
</body>
</html>
""",
        "body_text": """
🎉 Parabéns! Temos uma proposta para você!

Olá {{candidate_name}},

É com grande satisfação que comunicamos que você foi selecionado(a) para a posição de {{job_title}} na {{company_name}}!

Detalhes da Proposta:
- Cargo: {{job_title}}
- Remuneração: {{salary}}
- Data de Início: {{start_date}}
- Benefícios: {{benefits}}

Para discutir os detalhes da proposta e próximos passos, por favor entre em contato com {{hiring_manager}}.

Estamos ansiosos para tê-lo(a) em nossa equipe!

Atenciosamente,
Equipe de Recrutamento
{{company_name}}

---
Se não deseja mais receber comunicações, acesse: {{unsubscribe_url}}
(LGPD Art. 8°, §5°)
"""
    },
    {
        "name": "Convite para Avaliação Técnica",
        "subject": "Próxima etapa: Avaliação Técnica - {{job_title}}",
        "category": "screening",
        "channel": "email",
        "situation": "avaliacao_tecnica",
        "variables": ["candidate_name", "job_title", "company_name", "recruiter_name", "unsubscribe_url"],
        "body_html": """
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #2563eb;">Avaliação Técnica</h2>
    
    <p>Olá <strong>{{candidate_name}}</strong>,</p>
    
    <p>Parabéns por avançar no processo seletivo para <strong>{{job_title}}</strong>!</p>
    
    <p>Gostaríamos de convidá-lo(a) para a próxima etapa: uma avaliação técnica.</p>
    
    <div style="background-color: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0;">
        <h3 style="margin-top: 0; color: #1f2937;">📋 Sobre a avaliação:</h3>
        <ul>
            <li>Tipo: Avaliação técnica</li>
            <li>Objetivo: Avaliar suas competências técnicas para a posição</li>
        </ul>
    </div>
    
    <p>Aguardamos sua participação!</p>
    
    <p style="color: #6b7280; font-size: 14px; margin-top: 30px;">
        Atenciosamente,<br>
        {{recruiter_name}}<br>
        {{company_name}}
    </p>
    <div style="margin-top: 40px; padding-top: 15px; border-top: 1px solid #e5e7eb; text-align: center;">
        <p style="color: #9ca3af; font-size: 12px;">
            Você está recebendo este email porque participou de um processo seletivo gerenciado pela Plataforma LIA.<br>
            Se não deseja mais receber comunicações, <a href="{{unsubscribe_url}}" style="color: #6b7280; text-decoration: underline;">clique aqui para cancelar</a> (LGPD Art. 8°, §5°).
        </p>
    </div>
</body>
</html>
""",
        "body_text": """Avaliação Técnica

Olá {{candidate_name}},

Parabéns por avançar no processo seletivo para {{job_title}}!

Gostaríamos de convidá-lo(a) para a próxima etapa: uma avaliação técnica.

📋 Sobre a avaliação:
• Tipo: Avaliação técnica
• Objetivo: Avaliar suas competências técnicas para a posição

Aguardamos sua participação!

Atenciosamente,
{{recruiter_name}}
{{company_name}}

---
Se não deseja mais receber comunicações, acesse: {{unsubscribe_url}}
(LGPD Art. 8°, §5°)
"""
    },
    {
        "name": "Lembrete de Entrevista",
        "subject": "⏰ Lembrete: Sua entrevista amanhã - {{job_title}}",
        "category": "interview",
        "channel": "email",
        "situation": "agendamento",
        "variables": ["candidate_name", "job_title", "company_name", "interview_date", "interview_time", "interview_location", "interviewer_name", "preparation_tips", "unsubscribe_url"],
        "body_html": """
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #2563eb;">⏰ Lembrete de Entrevista</h2>
    
    <p>Olá <strong>{{candidate_name}}</strong>,</p>
    
    <p>Este é um lembrete amigável sobre sua entrevista agendada para a posição de <strong>{{job_title}}</strong> na <strong>{{company_name}}</strong>.</p>
    
    <div style="background-color: #fef3c7; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #f59e0b;">
        <h3 style="margin-top: 0; color: #92400e;">Detalhes:</h3>
        <ul style="list-style: none; padding: 0;">
            <li>📅 <strong>Data:</strong> {{interview_date}}</li>
            <li>🕐 <strong>Horário:</strong> {{interview_time}}</li>
            <li>📍 <strong>Local:</strong> {{interview_location}}</li>
            <li>👤 <strong>Entrevistador:</strong> {{interviewer_name}}</li>
        </ul>
    </div>
    
    <div style="background-color: #f3f4f6; padding: 15px; border-radius: 8px; margin: 20px 0;">
        <h4 style="margin-top: 0; color: #1f2937;">💡 Dicas de Preparação:</h4>
        <p>{{preparation_tips}}</p>
    </div>
    
    <p>Caso tenha algum imprevisto, por favor nos avise o mais breve possível.</p>
    
    <p>Boa sorte! Estamos torcendo por você! 🍀</p>
    
    <p style="color: #6b7280; font-size: 14px; margin-top: 30px;">
        Atenciosamente,<br>
        Equipe de Recrutamento<br>
        {{company_name}}
    </p>
    <div style="margin-top: 40px; padding-top: 15px; border-top: 1px solid #e5e7eb; text-align: center;">
        <p style="color: #9ca3af; font-size: 12px;">
            Você está recebendo este email porque participou de um processo seletivo gerenciado pela Plataforma LIA.<br>
            Se não deseja mais receber comunicações, <a href="{{unsubscribe_url}}" style="color: #6b7280; text-decoration: underline;">clique aqui para cancelar</a> (LGPD Art. 8°, §5°).
        </p>
    </div>
</body>
</html>
""",
        "body_text": """
⏰ Lembrete de Entrevista

Olá {{candidate_name}},

Este é um lembrete amigável sobre sua entrevista agendada para a posição de {{job_title}} na {{company_name}}.

Detalhes:
- Data: {{interview_date}}
- Horário: {{interview_time}}
- Local: {{interview_location}}
- Entrevistador: {{interviewer_name}}

Dicas de Preparação:
{{preparation_tips}}

Caso tenha algum imprevisto, por favor nos avise o mais breve possível.

Boa sorte! Estamos torcendo por você! 🍀

Atenciosamente,
Equipe de Recrutamento
{{company_name}}

---
Se não deseja mais receber comunicações, acesse: {{unsubscribe_url}}
(LGPD Art. 8°, §5°)
"""
    },
    {
        "name": "Convite de Usuário",
        "subject": "Você foi convidado para a Plataforma LIA",
        "category": "auth",
        "channel": "email",
        "situation": None,
        "variables": ["user_name", "invitation_link"],
        "body_html": """
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #2563eb;">🎉 Bem-vindo à Plataforma LIA!</h2>
    
    <p>Olá <strong>{{user_name}}</strong>,</p>
    
    <p>Você foi convidado para fazer parte da Plataforma LIA - sua nova ferramenta de recrutamento inteligente!</p>
    
    <p>Para ativar sua conta e criar sua senha, clique no botão abaixo:</p>
    
    <div style="text-align: center; margin: 30px 0;">
        <a href="{{invitation_link}}" style="background-color: #2563eb; color: white; padding: 14px 28px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">
            Aceitar Convite e Criar Senha
        </a>
    </div>
    
    <p style="color: #6b7280; font-size: 14px;">Este link expira em 24 horas. Se você não solicitou este convite, por favor ignore este email.</p>
    
    <p style="color: #6b7280; font-size: 14px; margin-top: 30px;">
        Atenciosamente,<br>
        Equipe LIA
    </p>
</body>
</html>
""",
        "body_text": """
🎉 Bem-vindo à Plataforma LIA!

Olá {{user_name}},

Você foi convidado para fazer parte da Plataforma LIA - sua nova ferramenta de recrutamento inteligente!

Para ativar sua conta e criar sua senha, acesse o link abaixo:
{{invitation_link}}

Este link expira em 24 horas. Se você não solicitou este convite, por favor ignore este email.

Atenciosamente,
Equipe LIA
"""
    },
    {
        "name": "Recuperação de Senha",
        "subject": "Redefinição de Senha - Plataforma LIA",
        "category": "auth",
        "channel": "email",
        "situation": None,
        "variables": ["user_name", "reset_link"],
        "body_html": """
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #2563eb;">🔐 Redefinição de Senha</h2>
    
    <p>Olá <strong>{{user_name}}</strong>,</p>
    
    <p>Recebemos uma solicitação para redefinir a senha da sua conta na Plataforma LIA.</p>
    
    <p>Para criar uma nova senha, clique no botão abaixo:</p>
    
    <div style="text-align: center; margin: 30px 0;">
        <a href="{{reset_link}}" style="background-color: #2563eb; color: white; padding: 14px 28px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">
            Redefinir Minha Senha
        </a>
    </div>
    
    <p style="color: #6b7280; font-size: 14px;">Este link expira em 24 horas. Se você não solicitou esta redefinição, por favor ignore este email - sua senha permanecerá a mesma.</p>
    
    <p style="color: #6b7280; font-size: 14px; margin-top: 30px;">
        Atenciosamente,<br>
        Equipe LIA
    </p>
</body>
</html>
""",
        "body_text": """
🔐 Redefinição de Senha

Olá {{user_name}},

Recebemos uma solicitação para redefinir a senha da sua conta na Plataforma LIA.

Para criar uma nova senha, acesse o link abaixo:
{{reset_link}}

Este link expira em 24 horas. Se você não solicitou esta redefinição, por favor ignore este email - sua senha permanecerá a mesma.

Atenciosamente,
Equipe LIA
"""
    },
    {
        "name": "Verificação de Email",
        "subject": "Verifique seu Email - Plataforma LIA",
        "category": "auth",
        "channel": "email",
        "situation": None,
        "variables": ["user_name", "verification_link"],
        "body_html": """
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #2563eb;">✉️ Verificação de Email</h2>
    
    <p>Olá <strong>{{user_name}}</strong>,</p>
    
    <p>Obrigado por se cadastrar na Plataforma LIA! Para completar seu registro, precisamos verificar seu endereço de email.</p>
    
    <p>Clique no botão abaixo para confirmar seu email:</p>
    
    <div style="text-align: center; margin: 30px 0;">
        <a href="{{verification_link}}" style="background-color: #16a34a; color: white; padding: 14px 28px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">
            Verificar Meu Email
        </a>
    </div>
    
    <p style="color: #6b7280; font-size: 14px;">Este link expira em 7 dias. Se você não criou uma conta na Plataforma LIA, por favor ignore este email.</p>
    
    <p style="color: #6b7280; font-size: 14px; margin-top: 30px;">
        Atenciosamente,<br>
        Equipe LIA
    </p>
</body>
</html>
""",
        "body_text": """
✉️ Verificação de Email

Olá {{user_name}},

Obrigado por se cadastrar na Plataforma LIA! Para completar seu registro, precisamos verificar seu endereço de email.

Para confirmar seu email, acesse o link abaixo:
{{verification_link}}

Este link expira em 7 dias. Se você não criou uma conta na Plataforma LIA, por favor ignore este email.

Atenciosamente,
Equipe LIA
"""
    },
    {
        "name": "Triagem WSI (WhatsApp)",
        "subject": None,
        "category": "interview",
        "channel": "whatsapp",
        "situation": "wsi_screening",
        "variables": ["candidate_name", "job_title", "company_name", "recruiter_name"],
        "body_html": """Olá {{candidate_name}}! 👋

Sou {{recruiter_name}} da {{company_name}}.

Estamos avançando no processo seletivo para a posição de *{{job_title}}* e você foi pré-selecionado(a)! 🎉

Antes da próxima etapa, gostaríamos de fazer algumas perguntas rápidas sobre sua experiência. Isso nos ajudará a conhecê-lo(a) melhor.

Podemos seguir agora ou prefere agendar outro momento?

Aguardo seu retorno! 😊""",
        "body_text": """Olá {{candidate_name}}! 👋

Sou {{recruiter_name}} da {{company_name}}.

Estamos avançando no processo seletivo para a posição de *{{job_title}}* e você foi pré-selecionado(a)! 🎉

Antes da próxima etapa, gostaríamos de fazer algumas perguntas rápidas sobre sua experiência. Isso nos ajudará a conhecê-lo(a) melhor.

Podemos seguir agora ou prefere agendar outro momento?

Aguardo seu retorno! 😊"""
    },
    {
        "name": "Contato Rápido (WhatsApp)",
        "subject": None,
        "category": "followup",
        "channel": "whatsapp",
        "situation": "triagem",
        "variables": ["candidate_name", "job_title", "company_name"],
        "body_html": """Olá {{candidate_name}}! 👋

Recebemos sua candidatura para a vaga de *{{job_title}}* na *{{company_name}}*.

Estamos analisando seu perfil e em breve entraremos em contato para os próximos passos. 📋

Enquanto isso, fique à vontade para nos perguntar qualquer coisa sobre a vaga!

Abraços! 🙌""",
        "body_text": """Olá {{candidate_name}}! 👋

Recebemos sua candidatura para a vaga de *{{job_title}}* na *{{company_name}}*.

Estamos analisando seu perfil e em breve entraremos em contato para os próximos passos. 📋

Enquanto isso, fique à vontade para nos perguntar qualquer coisa sobre a vaga!

Abraços! 🙌"""
    },
    {
        "name": "Lembrete de Entrevista (WhatsApp)",
        "subject": None,
        "category": "interview",
        "channel": "whatsapp",
        "situation": "agendamento",
        "variables": ["candidate_name", "job_title", "interview_date", "interview_time", "interview_location"],
        "body_html": """Olá {{candidate_name}}! 👋

Passando para lembrar da sua entrevista amanhã! 📅

📌 *Detalhes:*
• Vaga: {{job_title}}
• Data: {{interview_date}}
• Horário: {{interview_time}}
• Local: {{interview_location}}

Por favor, confirme sua presença respondendo esta mensagem. ✅

Qualquer imprevisto, nos avise o quanto antes!

Boa sorte! 🍀""",
        "body_text": """Olá {{candidate_name}}! 👋

Passando para lembrar da sua entrevista amanhã! 📅

📌 *Detalhes:*
• Vaga: {{job_title}}
• Data: {{interview_date}}
• Horário: {{interview_time}}
• Local: {{interview_location}}

Por favor, confirme sua presença respondendo esta mensagem. ✅

Qualquer imprevisto, nos avise o quanto antes!

Boa sorte! 🍀"""
    },
    {
        "name": "Acompanhamento (WhatsApp)",
        "subject": None,
        "category": "followup",
        "channel": "whatsapp",
        "situation": "follow_up",
        "variables": ["candidate_name", "job_title", "company_name", "next_steps"],
        "body_html": """Olá {{candidate_name}}! 👋

Gostaríamos de atualizar você sobre o processo seletivo para *{{job_title}}* na *{{company_name}}*.

{{next_steps}}

Fique tranquilo(a), estamos acompanhando de perto! 🤝

Qualquer dúvida, é só chamar.

Abraços! 😊""",
        "body_text": """Olá {{candidate_name}}! 👋

Gostaríamos de atualizar você sobre o processo seletivo para *{{job_title}}* na *{{company_name}}*.

{{next_steps}}

Fique tranquilo(a), estamos acompanhando de perto! 🤝

Qualquer dúvida, é só chamar.

Abraços! 😊"""
    },
    {
        "name": "Contato Inicial (Email)",
        "subject": "Oportunidade: {{job_title}} - {{company_name}}",
        "category": "followup",
        "channel": "email",
        "situation": "initial_contact",
        "variables": ["candidate_name", "job_title", "company_name", "job_challenge", "recruiter_name", "privacy_policy_url", "unsubscribe_url"],
        "body_html": """<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <p>Olá <strong>{{candidate_name}}</strong>,</p>
    
    <p>A {{company_name}} está em busca de um(a) <strong>{{job_title}}</strong> para integrar nosso time.</p>
    
    <p>Seu perfil chamou nossa atenção e acreditamos que você pode ser um excelente fit para esta posição.</p>
    
    {{job_challenge}}
    
    <h3 style="color: #2563eb;">PRÓXIMOS PASSOS:</h3>
    <p>Se tiver interesse, convidamos você a participar de uma triagem inicial com a LIA, nossa assistente de recrutamento com inteligência artificial.</p>
    
    <p>A LIA conduz entrevistas de forma:</p>
    <ul>
        <li>✅ Profissional e isenta (sem viés)</li>
        <li>✅ Humanizada e respeitosa</li>
        <li>✅ Com feedback construtivo ao final</li>
    </ul>
    
    <p>A conversa dura aproximadamente 15-20 minutos e pode ser feita por texto ou voz, no horário que preferir.</p>
    
    <p>Caso prefira conversar via WhatsApp, responda este email informando seu número.</p>
    
    <p style="font-size: 13px; color: #6b7280; margin-top: 20px;">
        📋 Ao participar, você concorda com nossa <a href="{{privacy_policy_url}}" style="color: #2563eb;">Política de Privacidade</a>. Caso não deseje participar do processo, basta responder este email informando.
    </p>
    
    <p style="color: #6b7280; font-size: 14px; margin-top: 30px;">
        Atenciosamente,<br>
        {{recruiter_name}}<br>
        {{company_name}}
    </p>
    <div style="margin-top: 40px; padding-top: 15px; border-top: 1px solid #e5e7eb; text-align: center;">
        <p style="color: #9ca3af; font-size: 12px;">
            Você está recebendo este email porque participou de um processo seletivo gerenciado pela Plataforma LIA.<br>
            Se não deseja mais receber comunicações, <a href="{{unsubscribe_url}}" style="color: #6b7280; text-decoration: underline;">clique aqui para cancelar</a> (LGPD Art. 8°, §5°).
        </p>
    </div>
</body>
</html>""",
        "body_text": """Olá {{candidate_name}},

A {{company_name}} está em busca de um(a) {{job_title}} para integrar nosso time.

Seu perfil chamou nossa atenção e acreditamos que você pode ser um excelente fit para esta posição.

{{job_challenge}}

PRÓXIMOS PASSOS:
Se tiver interesse, convidamos você a participar de uma triagem inicial com a LIA, nossa assistente de recrutamento com inteligência artificial.

A LIA conduz entrevistas de forma:
✅ Profissional e isenta (sem viés)
✅ Humanizada e respeitosa
✅ Com feedback construtivo ao final

A conversa dura aproximadamente 15-20 minutos e pode ser feita por texto ou voz, no horário que preferir.

Caso prefira conversar via WhatsApp, responda este email informando seu número.

📋 Ao participar, você concorda com nossa Política de Privacidade em {{privacy_policy_url}}. Caso não deseje participar do processo, basta responder este email informando.

Atenciosamente,
{{recruiter_name}}
{{company_name}}

---
Se não deseja mais receber comunicações, acesse: {{unsubscribe_url}}
(LGPD Art. 8°, §5°)"""
    },
    {
        "name": "Lembrete de Triagem (Email)",
        "subject": "Lembrete: Triagem pendente - {{job_title}}",
        "category": "followup",
        "channel": "email",
        "situation": "screening_reminder",
        "variables": ["candidate_name", "job_title", "hours_remaining", "unsubscribe_url"],
        "body_html": """<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <p>Olá <strong>{{candidate_name}}</strong>,</p>
    
    <p>Notei que você ainda não completou a triagem para a posição de <strong>{{job_title}}</strong>.</p>
    
    <p>Você tem mais <strong>{{hours_remaining}} horas</strong> para finalizar a conversa.</p>
    
    <p>Se tiver qualquer dificuldade ou dúvida, é só responder este email.</p>
    
    <p style="color: #6b7280; font-size: 14px; margin-top: 30px;">
        Atenciosamente,<br>
        LIA - Assistente de Recrutamento
    </p>
    <div style="margin-top: 40px; padding-top: 15px; border-top: 1px solid #e5e7eb; text-align: center;">
        <p style="color: #9ca3af; font-size: 12px;">
            Você está recebendo este email porque participou de um processo seletivo gerenciado pela Plataforma LIA.<br>
            Se não deseja mais receber comunicações, <a href="{{unsubscribe_url}}" style="color: #6b7280; text-decoration: underline;">clique aqui para cancelar</a> (LGPD Art. 8°, §5°).
        </p>
    </div>
</body>
</html>""",
        "body_text": """Olá {{candidate_name}},

Notei que você ainda não completou a triagem para a posição de {{job_title}}.

Você tem mais {{hours_remaining}} horas para finalizar a conversa.

Se tiver qualquer dificuldade ou dúvida, é só responder este email.

Atenciosamente,
LIA - Assistente de Recrutamento

---
Se não deseja mais receber comunicações, acesse: {{unsubscribe_url}}
(LGPD Art. 8°, §5°)"""
    },
    {
        "name": "Triagem Aprovada (Email)",
        "subject": "Parabéns! Você avançou no processo - {{job_title}}",
        "category": "approval",
        "channel": "email",
        "situation": "screening_passed",
        "variables": ["candidate_name", "job_title", "strengths", "company_name"],
        "body_html": """<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #16a34a;">Ótimas notícias! 🎉</h2>
    
    <p>Olá <strong>{{candidate_name}}</strong>,</p>
    
    <p>Você foi aprovado(a) na triagem para a posição de <strong>{{job_title}}</strong>!</p>
    
    <div style="background-color: #f0fdf4; padding: 20px; border-radius: 8px; margin: 20px 0;">
        <h3 style="margin-top: 0; color: #15803d;">PONTOS FORTES IDENTIFICADOS:</h3>
        <p>{{strengths}}</p>
    </div>
    
    <h3>PRÓXIMOS PASSOS:</h3>
    <p>Em breve entraremos em contato para agendar sua entrevista com a equipe.</p>
    
    <p>Se tiver alguma restrição de agenda, por favor nos avise respondendo este email.</p>
    
    <p>Parabéns e até breve!</p>
    
    <p style="color: #6b7280; font-size: 14px; margin-top: 30px;">
        Atenciosamente,<br>
        {{company_name}}
    </p>
</body>
</html>""",
        "body_text": """Ótimas notícias! 🎉

Olá {{candidate_name}},

Você foi aprovado(a) na triagem para a posição de {{job_title}}!

PONTOS FORTES IDENTIFICADOS:
{{strengths}}

PRÓXIMOS PASSOS:
Em breve entraremos em contato para agendar sua entrevista com a equipe.

Se tiver alguma restrição de agenda, por favor nos avise respondendo este email.

Parabéns e até breve!

Atenciosamente,
{{company_name}}"""
    },
    {
        "name": "Triagem Reprovada (Email)",
        "subject": "Resultado da triagem - {{job_title}}",
        "category": "rejection",
        "channel": "email",
        "situation": "screening_failed",
        "variables": ["candidate_name", "job_title", "strengths", "development_areas", "unsubscribe_url"],
        "body_html": """<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <p>Olá <strong>{{candidate_name}}</strong>,</p>
    
    <p>Obrigada por participar da triagem para a posição de <strong>{{job_title}}</strong>.</p>
    
    <p>Após uma análise cuidadosa, identificamos que outros candidatos apresentam maior aderência aos requisitos específicos desta posição.</p>
    
    <div style="background-color: #f0fdf4; padding: 15px; border-radius: 8px; margin: 20px 0;">
        <h4 style="margin-top: 0; color: #15803d;">PONTOS FORTES IDENTIFICADOS:</h4>
        <p>{{strengths}}</p>
    </div>
    
    <div style="background-color: #fef3c7; padding: 15px; border-radius: 8px; margin: 20px 0;">
        <h4 style="margin-top: 0; color: #92400e;">ÁREAS COM POTENCIAL DE DESENVOLVIMENTO:</h4>
        <p>{{development_areas}}</p>
    </div>
    
    <p>Esta decisão não diminui suas qualificações profissionais. Seu perfil permanece em nosso banco de talentos e entraremos em contato caso surjam oportunidades mais alinhadas ao seu perfil.</p>
    
    <p>Desejamos sucesso em sua jornada profissional!</p>
    
    <p style="color: #6b7280; font-size: 14px; margin-top: 30px;">
        Atenciosamente,<br>
        LIA - Assistente de Recrutamento
    </p>
    <div style="margin-top: 40px; padding-top: 15px; border-top: 1px solid #e5e7eb; text-align: center;">
        <p style="color: #9ca3af; font-size: 12px;">
            Você está recebendo este email porque participou de um processo seletivo gerenciado pela Plataforma LIA.<br>
            Se não deseja mais receber comunicações, <a href="{{unsubscribe_url}}" style="color: #6b7280; text-decoration: underline;">clique aqui para cancelar</a> (LGPD Art. 8°, §5°).
        </p>
    </div>
</body>
</html>""",
        "body_text": """Olá {{candidate_name}},

Obrigada por participar da triagem para a posição de {{job_title}}.

Após uma análise cuidadosa, identificamos que outros candidatos apresentam maior aderência aos requisitos específicos desta posição.

PONTOS FORTES IDENTIFICADOS:
{{strengths}}

ÁREAS COM POTENCIAL DE DESENVOLVIMENTO:
{{development_areas}}

Esta decisão não diminui suas qualificações profissionais. Seu perfil permanece em nosso banco de talentos e entraremos em contato caso surjam oportunidades mais alinhadas ao seu perfil.

Desejamos sucesso em sua jornada profissional!

Atenciosamente,
LIA - Assistente de Recrutamento

---
Se não deseja mais receber comunicações, acesse: {{unsubscribe_url}}
(LGPD Art. 8°, §5°)"""
    },
    {
        "name": "Rejeição Pós-Entrevista (Email)",
        "subject": "Resultado do processo - {{job_title}}",
        "category": "rejection",
        "channel": "email",
        "situation": "rejection_post_interview",
        "variables": ["candidate_name", "job_title", "feedback", "unsubscribe_url"],
        "body_html": """<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <p>Olá <strong>{{candidate_name}}</strong>,</p>
    
    <p>Agradecemos sua participação no processo seletivo para a posição de <strong>{{job_title}}</strong>.</p>
    
    <p>Após avaliação cuidadosa, decidimos seguir com outros candidatos que apresentaram maior aderência ao perfil buscado neste momento.</p>
    
    {{feedback}}
    
    <p>Seu perfil permanece em nosso banco de talentos e entraremos em contato caso surjam oportunidades alinhadas ao seu perfil.</p>
    
    <p>Desejamos sucesso em sua carreira!</p>
    
    <p style="color: #6b7280; font-size: 14px; margin-top: 30px;">
        Atenciosamente,<br>
        Equipe de Recrutamento
    </p>
    <div style="margin-top: 40px; padding-top: 15px; border-top: 1px solid #e5e7eb; text-align: center;">
        <p style="color: #9ca3af; font-size: 12px;">
            Você está recebendo este email porque participou de um processo seletivo gerenciado pela Plataforma LIA.<br>
            Se não deseja mais receber comunicações, <a href="{{unsubscribe_url}}" style="color: #6b7280; text-decoration: underline;">clique aqui para cancelar</a> (LGPD Art. 8°, §5°).
        </p>
    </div>
</body>
</html>""",
        "body_text": """Olá {{candidate_name}},

Agradecemos sua participação no processo seletivo para a posição de {{job_title}}.

Após avaliação cuidadosa, decidimos seguir com outros candidatos que apresentaram maior aderência ao perfil buscado neste momento.

{{feedback}}

Seu perfil permanece em nosso banco de talentos e entraremos em contato caso surjam oportunidades alinhadas ao seu perfil.

Desejamos sucesso em sua carreira!

Atenciosamente,
Equipe de Recrutamento

---
Se não deseja mais receber comunicações, acesse: {{unsubscribe_url}}
(LGPD Art. 8°, §5°)"""
    },
    {
        "name": "Processo Encerrado (Email)",
        "subject": "Encerramento do processo - {{job_title}}",
        "category": "rejection",
        "channel": "email",
        "situation": "process_closed",
        "variables": ["candidate_name", "job_title", "unsubscribe_url"],
        "body_html": """<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <p>Olá <strong>{{candidate_name}}</strong>,</p>
    
    <p>Gostaríamos de informar que a posição de <strong>{{job_title}}</strong> foi preenchida.</p>
    
    <p>Agradecemos sinceramente seu interesse e participação em nosso processo seletivo.</p>
    
    <p>Seu perfil ficará em nosso banco de talentos e entraremos em contato caso surjam novas oportunidades alinhadas ao seu perfil.</p>
    
    <p>Desejamos sucesso em sua carreira!</p>
    
    <p style="color: #6b7280; font-size: 14px; margin-top: 30px;">
        Atenciosamente,<br>
        LIA - Assistente de Recrutamento
    </p>
    <div style="margin-top: 40px; padding-top: 15px; border-top: 1px solid #e5e7eb; text-align: center;">
        <p style="color: #9ca3af; font-size: 12px;">
            Você está recebendo este email porque participou de um processo seletivo gerenciado pela Plataforma LIA.<br>
            Se não deseja mais receber comunicações, <a href="{{unsubscribe_url}}" style="color: #6b7280; text-decoration: underline;">clique aqui para cancelar</a> (LGPD Art. 8°, §5°).
        </p>
    </div>
</body>
</html>""",
        "body_text": """Olá {{candidate_name}},

Gostaríamos de informar que a posição de {{job_title}} foi preenchida.

Agradecemos sinceramente seu interesse e participação em nosso processo seletivo.

Seu perfil ficará em nosso banco de talentos e entraremos em contato caso surjam novas oportunidades alinhadas ao seu perfil.

Desejamos sucesso em sua carreira!

Atenciosamente,
LIA - Assistente de Recrutamento

---
Se não deseja mais receber comunicações, acesse: {{unsubscribe_url}}
(LGPD Art. 8°, §5°)"""
    },
    {
        "name": "Contato Inicial (WhatsApp)",
        "subject": None,
        "category": "followup",
        "channel": "whatsapp",
        "situation": "initial_contact",
        "variables": ["candidate_name", "job_title", "privacy_policy_url"],
        "body_html": """Olá {{candidate_name}}, tudo bem?
Estamos fazendo uma triagem inicial para a vaga de {{job_title}}.
Gostaríamos de confirmar seu interesse e seguir com algumas perguntas conduzidas pela LIA, nossa assistente de recrutamento com inteligência artificial.
Ao continuar, voce concorda com nossa Politica de Privacidade em {{privacy_policy_url}}. Responda 'NAO' se nao deseja participar.
Você pode responder agora?""",
        "body_text": """Olá {{candidate_name}}, tudo bem?
Estamos fazendo uma triagem inicial para a vaga de {{job_title}}.
Gostaríamos de confirmar seu interesse e seguir com algumas perguntas conduzidas pela LIA, nossa assistente de recrutamento com inteligência artificial.
Ao continuar, voce concorda com nossa Politica de Privacidade em {{privacy_policy_url}}. Responda 'NAO' se nao deseja participar.
Você pode responder agora?"""
    },
    {
        "name": "Início de Triagem (WhatsApp)",
        "subject": None,
        "category": "interview",
        "channel": "whatsapp",
        "situation": "screening_start",
        "variables": ["candidate_name", "job_title"],
        "body_html": """Ótimo, {{candidate_name}}! Vamos começar.

Esta triagem é para a posição de *{{job_title}}*.

Vou fazer algumas perguntas sobre sua experiência e competências. Você pode responder por texto ou áudio.

Pronto(a) para começar?""",
        "body_text": """Ótimo, {{candidate_name}}! Vamos começar.

Esta triagem é para a posição de *{{job_title}}*.

Vou fazer algumas perguntas sobre sua experiência e competências. Você pode responder por texto ou áudio.

Pronto(a) para começar?"""
    },
    {
        "name": "Lembrete de Triagem (WhatsApp)",
        "subject": None,
        "category": "followup",
        "channel": "whatsapp",
        "situation": "screening_reminder",
        "variables": ["candidate_name", "hours_remaining"],
        "body_html": """Oi {{candidate_name}}! 👋

Vi que nossa conversa ficou pausada. Você ainda tem *{{hours_remaining}}h* para completar a triagem.

Posso continuar de onde paramos quando estiver disponível. É só me chamar!""",
        "body_text": """Oi {{candidate_name}}! 👋

Vi que nossa conversa ficou pausada. Você ainda tem *{{hours_remaining}}h* para completar a triagem.

Posso continuar de onde paramos quando estiver disponível. É só me chamar!"""
    },
    {
        "name": "Triagem Aprovada (WhatsApp)",
        "subject": None,
        "category": "approval",
        "channel": "whatsapp",
        "situation": "screening_passed",
        "variables": ["candidate_name", "strengths"],
        "body_html": """Parabéns, {{candidate_name}}! 🎉

Você foi aprovado(a) na triagem!

*Seus pontos fortes:*
{{strengths}}

Vou conversar com o recrutador sobre seu perfil e em breve retorno com informações sobre a próxima etapa.

Qualquer dúvida, é só me chamar!""",
        "body_text": """Parabéns, {{candidate_name}}! 🎉

Você foi aprovado(a) na triagem!

*Seus pontos fortes:*
{{strengths}}

Vou conversar com o recrutador sobre seu perfil e em breve retorno com informações sobre a próxima etapa.

Qualquer dúvida, é só me chamar!"""
    },
    {
        "name": "Triagem Reprovada (WhatsApp)",
        "subject": None,
        "category": "rejection",
        "channel": "whatsapp",
        "situation": "screening_failed",
        "variables": ["candidate_name", "strengths", "development_areas"],
        "body_html": """Olá {{candidate_name}},

Obrigada por participar da triagem! Foi muito bom conversar com você.

*Pontos fortes:*
{{strengths}}

*Áreas para desenvolvimento:*
{{development_areas}}

Para esta posição específica, seguiremos com outros candidatos. Mas seu perfil fica em nosso banco e te aviso sobre outras oportunidades!

Sucesso! 🍀""",
        "body_text": """Olá {{candidate_name}},

Obrigada por participar da triagem! Foi muito bom conversar com você.

*Pontos fortes:*
{{strengths}}

*Áreas para desenvolvimento:*
{{development_areas}}

Para esta posição específica, seguiremos com outros candidatos. Mas seu perfil fica em nosso banco e te aviso sobre outras oportunidades!

Sucesso! 🍀"""
    },
    {
        "name": "Entrevista Agendada (WhatsApp)",
        "subject": None,
        "category": "interview",
        "channel": "whatsapp",
        "situation": "interview_scheduled",
        "variables": ["candidate_name", "interview_date", "interview_link"],
        "body_html": """Oi {{candidate_name}}! 📅

Sua entrevista está agendada:

*Data:* {{interview_date}}
*Link:* {{interview_link}}

Vou te lembrar no dia, tá?

Boa sorte! 🍀""",
        "body_text": """Oi {{candidate_name}}! 📅

Sua entrevista está agendada:

*Data:* {{interview_date}}
*Link:* {{interview_link}}

Vou te lembrar no dia, tá?

Boa sorte! 🍀"""
    },
    {
        "name": "Feedback de Rejeição (WhatsApp)",
        "subject": None,
        "category": "rejection",
        "channel": "whatsapp",
        "situation": "rejection_feedback",
        "variables": ["candidate_name", "custom_feedback"],
        "body_html": """Olá {{candidate_name}},

{{custom_feedback}}

Seu perfil fica em nosso banco de talentos. Te aviso sobre novas oportunidades!

Sucesso na sua jornada! 🍀""",
        "body_text": """Olá {{candidate_name}},

{{custom_feedback}}

Seu perfil fica em nosso banco de talentos. Te aviso sobre novas oportunidades!

Sucesso na sua jornada! 🍀"""
    },
    {
        "name": "Processo Encerrado (WhatsApp)",
        "subject": None,
        "category": "rejection",
        "channel": "whatsapp",
        "situation": "process_closed",
        "variables": ["candidate_name", "job_title"],
        "body_html": """Olá {{candidate_name}}! 👋

A posição de *{{job_title}}* foi preenchida.

Agradeço seu interesse! Seu perfil fica em nosso banco e te aviso sobre novas oportunidades.

Sucesso! 🍀""",
        "body_text": """Olá {{candidate_name}}! 👋

A posição de *{{job_title}}* foi preenchida.

Agradeço seu interesse! Seu perfil fica em nosso banco e te aviso sobre novas oportunidades.

Sucesso! 🍀"""
    },
    {
        "name": "Meta em Risco",
        "subject": "Alerta: Meta de {{goal_type}} em risco",
        "category": "alert",
        "channel": "email",
        "situation": "alerta",
        "variables": ["recruiter_name", "goal_type", "current_value", "target_value", "period", "days_remaining"],
        "body_html": """
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #dc2626;">⚠️ Alerta: Meta em Risco</h2>
    
    <p>Olá <strong>{{recruiter_name}}</strong>,</p>
    
    <p>Este é um alerta importante sobre sua meta de <strong>{{goal_type}}</strong> para o período de <strong>{{period}}</strong>.</p>
    
    <div style="background-color: #fef2f2; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #dc2626;">
        <h3 style="margin-top: 0; color: #991b1b;">Status Atual:</h3>
        <ul style="list-style: none; padding: 0;">
            <li>📊 <strong>Valor Atual:</strong> {{current_value}}</li>
            <li>🎯 <strong>Meta:</strong> {{target_value}}</li>
            <li>⏰ <strong>Dias Restantes:</strong> {{days_remaining}}</li>
        </ul>
    </div>
    
    <p>Com o ritmo atual, existe risco de não atingir a meta estabelecida. Recomendamos revisar as ações em andamento e identificar oportunidades para acelerar os resultados.</p>
    
    <p style="color: #6b7280; font-size: 14px; margin-top: 30px;">
        Atenciosamente,<br>
        LIA - Assistente de Recrutamento
    </p>
</body>
</html>
""",
        "body_text": """
⚠️ Alerta: Meta em Risco

Olá {{recruiter_name}},

Este é um alerta importante sobre sua meta de {{goal_type}} para o período de {{period}}.

Status Atual:
- Valor Atual: {{current_value}}
- Meta: {{target_value}}
- Dias Restantes: {{days_remaining}}

Com o ritmo atual, existe risco de não atingir a meta estabelecida. Recomendamos revisar as ações em andamento e identificar oportunidades para acelerar os resultados.

Atenciosamente,
LIA - Assistente de Recrutamento
"""
    },
    {
        "name": "Meta Não Atingida",
        "subject": "Relatório: Meta de {{goal_type}} não atingida",
        "category": "alert",
        "channel": "email",
        "situation": "alerta",
        "variables": ["recruiter_name", "goal_type", "final_value", "target_value", "period"],
        "body_html": """
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #dc2626;">📊 Relatório: Meta Não Atingida</h2>
    
    <p>Olá <strong>{{recruiter_name}}</strong>,</p>
    
    <p>Segue o resumo da meta de <strong>{{goal_type}}</strong> para o período de <strong>{{period}}</strong>.</p>
    
    <div style="background-color: #fef2f2; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #dc2626;">
        <h3 style="margin-top: 0; color: #991b1b;">Resultado Final:</h3>
        <ul style="list-style: none; padding: 0;">
            <li>📈 <strong>Valor Alcançado:</strong> {{final_value}}</li>
            <li>🎯 <strong>Meta Estabelecida:</strong> {{target_value}}</li>
        </ul>
    </div>
    
    <p>Infelizmente, a meta não foi atingida neste período. Recomendamos uma análise das causas e definição de planos de ação para o próximo ciclo.</p>
    
    <p>Entre em contato com seu gestor para discutir estratégias de melhoria.</p>
    
    <p style="color: #6b7280; font-size: 14px; margin-top: 30px;">
        Atenciosamente,<br>
        LIA - Assistente de Recrutamento
    </p>
</body>
</html>
""",
        "body_text": """
📊 Relatório: Meta Não Atingida

Olá {{recruiter_name}},

Segue o resumo da meta de {{goal_type}} para o período de {{period}}.

Resultado Final:
- Valor Alcançado: {{final_value}}
- Meta Estabelecida: {{target_value}}

Infelizmente, a meta não foi atingida neste período. Recomendamos uma análise das causas e definição de planos de ação para o próximo ciclo.

Entre em contato com seu gestor para discutir estratégias de melhoria.

Atenciosamente,
LIA - Assistente de Recrutamento
"""
    },
    {
        "name": "Resumo Semanal",
        "subject": "Seu resumo semanal - Semana {{week_number}}",
        "category": "report",
        "channel": "email",
        "situation": "relatorio",
        "variables": ["recruiter_name", "week_number", "candidates_screened", "interviews_scheduled", "offers_made", "conversion_rate", "top_job_title"],
        "body_html": """
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #2563eb;">📈 Resumo Semanal - Semana {{week_number}}</h2>
    
    <p>Olá <strong>{{recruiter_name}}</strong>,</p>
    
    <p>Confira seu resumo de performance desta semana:</p>
    
    <div style="background-color: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0;">
        <h3 style="margin-top: 0; color: #1f2937;">Suas Métricas:</h3>
        <ul style="list-style: none; padding: 0;">
            <li>👥 <strong>Candidatos Triados:</strong> {{candidates_screened}}</li>
            <li>📅 <strong>Entrevistas Agendadas:</strong> {{interviews_scheduled}}</li>
            <li>💼 <strong>Propostas Realizadas:</strong> {{offers_made}}</li>
            <li>📊 <strong>Taxa de Conversão:</strong> {{conversion_rate}}</li>
        </ul>
    </div>
    
    <div style="background-color: #f0fdf4; padding: 15px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #16a34a;">
        <p style="margin: 0;"><strong>🏆 Vaga em Destaque:</strong> {{top_job_title}}</p>
    </div>
    
    <p>Continue o excelente trabalho! Qualquer dúvida, estou aqui para ajudar.</p>
    
    <p style="color: #6b7280; font-size: 14px; margin-top: 30px;">
        Atenciosamente,<br>
        LIA - Assistente de Recrutamento
    </p>
</body>
</html>
""",
        "body_text": """
📈 Resumo Semanal - Semana {{week_number}}

Olá {{recruiter_name}},

Confira seu resumo de performance desta semana:

Suas Métricas:
- Candidatos Triados: {{candidates_screened}}
- Entrevistas Agendadas: {{interviews_scheduled}}
- Propostas Realizadas: {{offers_made}}
- Taxa de Conversão: {{conversion_rate}}

🏆 Vaga em Destaque: {{top_job_title}}

Continue o excelente trabalho! Qualquer dúvida, estou aqui para ajudar.

Atenciosamente,
LIA - Assistente de Recrutamento
"""
    },
    {
        "name": "SLA Violado",
        "subject": "Alerta SLA: {{candidate_name}} ultrapassou limite em {{stage_name}}",
        "category": "alert",
        "channel": "email",
        "situation": "alerta",
        "variables": ["recruiter_name", "candidate_name", "job_title", "stage_name", "sla_hours", "actual_hours"],
        "body_html": """
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #dc2626;">⏰ Alerta SLA Violado</h2>
    
    <p>Olá <strong>{{recruiter_name}}</strong>,</p>
    
    <p>O candidato <strong>{{candidate_name}}</strong> ultrapassou o tempo limite na etapa <strong>{{stage_name}}</strong>.</p>
    
    <div style="background-color: #fef2f2; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #dc2626;">
        <h3 style="margin-top: 0; color: #991b1b;">Detalhes:</h3>
        <ul style="list-style: none; padding: 0;">
            <li>👤 <strong>Candidato:</strong> {{candidate_name}}</li>
            <li>💼 <strong>Vaga:</strong> {{job_title}}</li>
            <li>📋 <strong>Etapa:</strong> {{stage_name}}</li>
            <li>⏱️ <strong>SLA Definido:</strong> {{sla_hours}} horas</li>
            <li>⚠️ <strong>Tempo Atual:</strong> {{actual_hours}} horas</li>
        </ul>
    </div>
    
    <p>Por favor, tome uma ação imediata para avançar este candidato no processo ou atualize o status conforme necessário.</p>
    
    <p style="color: #6b7280; font-size: 14px; margin-top: 30px;">
        Atenciosamente,<br>
        LIA - Assistente de Recrutamento
    </p>
</body>
</html>
""",
        "body_text": """
⏰ Alerta SLA Violado

Olá {{recruiter_name}},

O candidato {{candidate_name}} ultrapassou o tempo limite na etapa {{stage_name}}.

Detalhes:
- Candidato: {{candidate_name}}
- Vaga: {{job_title}}
- Etapa: {{stage_name}}
- SLA Definido: {{sla_hours}} horas
- Tempo Atual: {{actual_hours}} horas

Por favor, tome uma ação imediata para avançar este candidato no processo ou atualize o status conforme necessário.

Atenciosamente,
LIA - Assistente de Recrutamento
"""
    },
    {
        "name": "Aprovação Pendente",
        "subject": "Aprovação necessária: {{action_type}} para {{candidate_name}}",
        "category": "workflow",
        "channel": "email",
        "situation": "aprovacao",
        "variables": ["approver_name", "requester_name", "action_type", "candidate_name", "job_title", "approval_link"],
        "body_html": """
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #2563eb;">📋 Aprovação Pendente</h2>
    
    <p>Olá <strong>{{approver_name}}</strong>,</p>
    
    <p><strong>{{requester_name}}</strong> solicitou sua aprovação para a seguinte ação:</p>
    
    <div style="background-color: #fef3c7; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #f59e0b;">
        <h3 style="margin-top: 0; color: #92400e;">Detalhes da Solicitação:</h3>
        <ul style="list-style: none; padding: 0;">
            <li>📝 <strong>Ação:</strong> {{action_type}}</li>
            <li>👤 <strong>Candidato:</strong> {{candidate_name}}</li>
            <li>💼 <strong>Vaga:</strong> {{job_title}}</li>
        </ul>
    </div>
    
    <div style="text-align: center; margin: 30px 0;">
        <a href="{{approval_link}}" style="background-color: #2563eb; color: white; padding: 14px 28px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">
            Revisar e Aprovar
        </a>
    </div>
    
    <p>Por favor, revise a solicitação e tome uma decisão o mais breve possível.</p>
    
    <p style="color: #6b7280; font-size: 14px; margin-top: 30px;">
        Atenciosamente,<br>
        LIA - Assistente de Recrutamento
    </p>
</body>
</html>
""",
        "body_text": """
📋 Aprovação Pendente

Olá {{approver_name}},

{{requester_name}} solicitou sua aprovação para a seguinte ação:

Detalhes da Solicitação:
- Ação: {{action_type}}
- Candidato: {{candidate_name}}
- Vaga: {{job_title}}

Para revisar e aprovar, acesse:
{{approval_link}}

Por favor, revise a solicitação e tome uma decisão o mais breve possível.

Atenciosamente,
LIA - Assistente de Recrutamento
"""
    },
    {
        "name": "Candidato Não Compareceu",
        "subject": "No-show: {{candidate_name}} não compareceu à entrevista",
        "category": "alert",
        "channel": "email",
        "situation": "alerta",
        "variables": ["recruiter_name", "candidate_name", "job_title", "interview_date", "interview_time"],
        "body_html": """
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #dc2626;">❌ No-Show: Candidato Não Compareceu</h2>
    
    <p>Olá <strong>{{recruiter_name}}</strong>,</p>
    
    <p>Infelizmente, o candidato <strong>{{candidate_name}}</strong> não compareceu à entrevista agendada.</p>
    
    <div style="background-color: #fef2f2; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #dc2626;">
        <h3 style="margin-top: 0; color: #991b1b;">Detalhes da Entrevista:</h3>
        <ul style="list-style: none; padding: 0;">
            <li>👤 <strong>Candidato:</strong> {{candidate_name}}</li>
            <li>💼 <strong>Vaga:</strong> {{job_title}}</li>
            <li>📅 <strong>Data:</strong> {{interview_date}}</li>
            <li>🕐 <strong>Horário:</strong> {{interview_time}}</li>
        </ul>
    </div>
    
    <p>Sugestões de próximos passos:</p>
    <ul>
        <li>Tentar contato com o candidato para entender o motivo</li>
        <li>Reagendar a entrevista se houver justificativa válida</li>
        <li>Atualizar o status do candidato no sistema</li>
    </ul>
    
    <p style="color: #6b7280; font-size: 14px; margin-top: 30px;">
        Atenciosamente,<br>
        LIA - Assistente de Recrutamento
    </p>
</body>
</html>
""",
        "body_text": """
❌ No-Show: Candidato Não Compareceu

Olá {{recruiter_name}},

Infelizmente, o candidato {{candidate_name}} não compareceu à entrevista agendada.

Detalhes da Entrevista:
- Candidato: {{candidate_name}}
- Vaga: {{job_title}}
- Data: {{interview_date}}
- Horário: {{interview_time}}

Sugestões de próximos passos:
- Tentar contato com o candidato para entender o motivo
- Reagendar a entrevista se houver justificativa válida
- Atualizar o status do candidato no sistema

Atenciosamente,
LIA - Assistente de Recrutamento
"""
    },
    {
        "name": "Proposta Aceita",
        "subject": "Proposta aceita: {{candidate_name}} para {{job_title}}",
        "category": "offer",
        "channel": "email",
        "situation": "proposta",
        "variables": ["recruiter_name", "candidate_name", "job_title", "company_name", "start_date", "unsubscribe_url"],
        "body_html": """
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #16a34a;">🎉 Proposta Aceita!</h2>
    
    <p>Olá <strong>{{recruiter_name}}</strong>,</p>
    
    <p>Ótimas notícias! O candidato <strong>{{candidate_name}}</strong> aceitou a proposta para a posição de <strong>{{job_title}}</strong>!</p>
    
    <div style="background-color: #f0fdf4; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #16a34a;">
        <h3 style="margin-top: 0; color: #15803d;">Detalhes:</h3>
        <ul style="list-style: none; padding: 0;">
            <li>👤 <strong>Candidato:</strong> {{candidate_name}}</li>
            <li>💼 <strong>Vaga:</strong> {{job_title}}</li>
            <li>🏢 <strong>Empresa:</strong> {{company_name}}</li>
            <li>📅 <strong>Data de Início:</strong> {{start_date}}</li>
        </ul>
    </div>
    
    <p>Próximos passos recomendados:</p>
    <ul>
        <li>Iniciar processo de admissão</li>
        <li>Preparar documentação necessária</li>
        <li>Comunicar a equipe sobre o novo membro</li>
        <li>Planejar o onboarding</li>
    </ul>
    
    <p>Parabéns pelo excelente trabalho! 🏆</p>
    
    <p style="color: #6b7280; font-size: 14px; margin-top: 30px;">
        Atenciosamente,<br>
        LIA - Assistente de Recrutamento
    </p>
    <div style="margin-top: 40px; padding-top: 15px; border-top: 1px solid #e5e7eb; text-align: center;">
        <p style="color: #9ca3af; font-size: 12px;">
            Você está recebendo este email porque participou de um processo seletivo gerenciado pela Plataforma LIA.<br>
            Se não deseja mais receber comunicações, <a href="{{unsubscribe_url}}" style="color: #6b7280; text-decoration: underline;">clique aqui para cancelar</a> (LGPD Art. 8°, §5°).
        </p>
    </div>
</body>
</html>
""",
        "body_text": """
🎉 Proposta Aceita!

Olá {{recruiter_name}},

Ótimas notícias! O candidato {{candidate_name}} aceitou a proposta para a posição de {{job_title}}!

Detalhes:
- Candidato: {{candidate_name}}
- Vaga: {{job_title}}
- Empresa: {{company_name}}
- Data de Início: {{start_date}}

Próximos passos recomendados:
- Iniciar processo de admissão
- Preparar documentação necessária
- Comunicar a equipe sobre o novo membro
- Planejar o onboarding

Parabéns pelo excelente trabalho! 🏆

Atenciosamente,
LIA - Assistente de Recrutamento

---
Se não deseja mais receber comunicações, acesse: {{unsubscribe_url}}
(LGPD Art. 8°, §5°)
"""
    },
    {
        "name": "Proposta Recusada",
        "subject": "Proposta recusada: {{candidate_name}} declinou {{job_title}}",
        "category": "offer",
        "channel": "email",
        "situation": "proposta",
        "variables": ["recruiter_name", "candidate_name", "job_title", "rejection_reason", "unsubscribe_url"],
        "body_html": """
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #dc2626;">📋 Proposta Recusada</h2>
    
    <p>Olá <strong>{{recruiter_name}}</strong>,</p>
    
    <p>Infelizmente, o candidato <strong>{{candidate_name}}</strong> recusou a proposta para a posição de <strong>{{job_title}}</strong>.</p>
    
    <div style="background-color: #fef2f2; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #dc2626;">
        <h3 style="margin-top: 0; color: #991b1b;">Detalhes:</h3>
        <ul style="list-style: none; padding: 0;">
            <li>👤 <strong>Candidato:</strong> {{candidate_name}}</li>
            <li>💼 <strong>Vaga:</strong> {{job_title}}</li>
            <li>💬 <strong>Motivo:</strong> {{rejection_reason}}</li>
        </ul>
    </div>
    
    <p>Sugestões de próximos passos:</p>
    <ul>
        <li>Avaliar se há margem para negociação</li>
        <li>Considerar candidatos em segundo lugar</li>
        <li>Documentar o feedback para processos futuros</li>
    </ul>
    
    <p style="color: #6b7280; font-size: 14px; margin-top: 30px;">
        Atenciosamente,<br>
        LIA - Assistente de Recrutamento
    </p>
    <div style="margin-top: 40px; padding-top: 15px; border-top: 1px solid #e5e7eb; text-align: center;">
        <p style="color: #9ca3af; font-size: 12px;">
            Você está recebendo este email porque participou de um processo seletivo gerenciado pela Plataforma LIA.<br>
            Se não deseja mais receber comunicações, <a href="{{unsubscribe_url}}" style="color: #6b7280; text-decoration: underline;">clique aqui para cancelar</a> (LGPD Art. 8°, §5°).
        </p>
    </div>
</body>
</html>
""",
        "body_text": """
📋 Proposta Recusada

Olá {{recruiter_name}},

Infelizmente, o candidato {{candidate_name}} recusou a proposta para a posição de {{job_title}}.

Detalhes:
- Candidato: {{candidate_name}}
- Vaga: {{job_title}}
- Motivo: {{rejection_reason}}

Sugestões de próximos passos:
- Avaliar se há margem para negociação
- Considerar candidatos em segundo lugar
- Documentar o feedback para processos futuros

Atenciosamente,
LIA - Assistente de Recrutamento

---
Se não deseja mais receber comunicações, acesse: {{unsubscribe_url}}
(LGPD Art. 8°, §5°)
"""
    },
    {
        "name": "Boas-vindas ao Cliente",
        "subject": "Bem-vindo à WEDOTALENT - Configure seu Acesso SSO",
        "category": "onboarding",
        "channel": "email",
        "situation": "onboarding",
        "variables": ["company_name", "admin_name", "admin_portal_url", "support_email"],
        "body_html": """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;600;700&display=swap" rel="stylesheet">
</head>
<body style="margin: 0; padding: 0; font-family: 'Open Sans', Arial, Helvetica, sans-serif; background-color: #f4f4f5;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width: 600px; margin: 0 auto; background-color: #ffffff;">
        <tr>
            <td style="background: linear-gradient(135deg, #60BED1 0%, #4A9BAB 100%); padding: 40px 30px; text-align: center;">
                <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: 600;">WEDOTALENT</h1>
                <p style="margin: 10px 0 0 0; color: rgba(255,255,255,0.9); font-size: 14px;">Plataforma Inteligente de Recrutamento</p>
            </td>
        </tr>
        <tr>
            <td style="padding: 40px 30px;">
                <h2 style="margin: 0 0 20px 0; color: #1F2937; font-size: 24px; font-weight: 600;">
                    Bem-vindo à WEDOTALENT!
                </h2>
                
                <p style="margin: 0 0 20px 0; color: #1F2937; font-size: 16px; line-height: 1.6;">
                    Olá <strong>{{admin_name}}</strong>,
                </p>
                
                <p style="margin: 0 0 20px 0; color: #1F2937; font-size: 16px; line-height: 1.6;">
                    Estamos muito felizes em ter a <strong>{{company_name}}</strong> como nossa mais nova parceira! Sua conta está pronta e você pode começar a explorar todos os recursos da plataforma.
                </p>
                
                <div style="background-color: #f0f9fa; border-left: 4px solid #60BED1; padding: 20px; margin: 25px 0; border-radius: 0 8px 8px 0;">
                    <h3 style="margin: 0 0 15px 0; color: #1F2937; font-size: 18px;">Configure o Acesso SSO</h3>
                    <p style="margin: 0 0 15px 0; color: #1F2937; font-size: 14px; line-height: 1.6;">
                        Para garantir segurança e facilidade de acesso para sua equipe, recomendamos configurar o Single Sign-On (SSO) através do portal de administração.
                    </p>
                    <p style="margin: 0; color: #6b7280; font-size: 14px;">
                        <strong>Benefícios do SSO:</strong><br>
                        - Login único para todos os usuários<br>
                        - Maior segurança com autenticação corporativa<br>
                        - Gerenciamento centralizado de acessos
                    </p>
                </div>
                
                <div style="text-align: center; margin: 35px 0;">
                    <a href="{{admin_portal_url}}" style="display: inline-block; background-color: #60BED1; color: #ffffff; text-decoration: none; padding: 16px 40px; border-radius: 8px; font-size: 16px; font-weight: 600; box-shadow: 0 4px 6px rgba(96, 190, 209, 0.3);">
                        Acessar Portal de Administração
                    </a>
                </div>
                
                <div style="background-color: #f9fafb; padding: 20px; border-radius: 8px; margin: 25px 0;">
                    <h4 style="margin: 0 0 15px 0; color: #1F2937; font-size: 16px;">Próximos Passos:</h4>
                    <ol style="margin: 0; padding-left: 20px; color: #1F2937; font-size: 14px; line-height: 1.8;">
                        <li>Acesse o Portal de Administração</li>
                        <li>Configure as integrações de SSO (Azure AD, Google, Okta, etc.)</li>
                        <li>Convide os membros da sua equipe</li>
                        <li>Personalize as configurações da empresa</li>
                    </ol>
                </div>
                
                <p style="margin: 25px 0 0 0; color: #1F2937; font-size: 16px; line-height: 1.6;">
                    Qualquer dúvida, nossa equipe de suporte está à disposição!
                </p>
            </td>
        </tr>
        <tr>
            <td style="background-color: #1F2937; padding: 30px; text-align: center;">
                <p style="margin: 0 0 10px 0; color: #9ca3af; font-size: 14px;">
                    Precisa de ajuda? Entre em contato:
                </p>
                <a href="mailto:{{support_email}}" style="color: #60BED1; text-decoration: none; font-size: 14px; font-weight: 600;">
                    {{support_email}}
                </a>
                <p style="margin: 20px 0 0 0; color: #6b7280; font-size: 12px;">
                    © 2024 WEDOTALENT. Todos os direitos reservados.
                </p>
            </td>
        </tr>
    </table>
</body>
</html>
""",
        "body_text": """
Bem-vindo à WEDOTALENT!

Olá {{admin_name}},

Estamos muito felizes em ter a {{company_name}} como nossa mais nova parceira! Sua conta está pronta e você pode começar a explorar todos os recursos da plataforma.

CONFIGURE O ACESSO SSO
Para garantir segurança e facilidade de acesso para sua equipe, recomendamos configurar o Single Sign-On (SSO) através do portal de administração.

Benefícios do SSO:
- Login único para todos os usuários
- Maior segurança com autenticação corporativa
- Gerenciamento centralizado de acessos

Acesse o Portal de Administração:
{{admin_portal_url}}

PRÓXIMOS PASSOS:
1. Acesse o Portal de Administração
2. Configure as integrações de SSO (Azure AD, Google, Okta, etc.)
3. Convide os membros da sua equipe
4. Personalize as configurações da empresa

Qualquer dúvida, nossa equipe de suporte está à disposição!

Precisa de ajuda? Entre em contato: {{support_email}}

© 2024 WEDOTALENT. Todos os direitos reservados.
"""
    },
    {
        "name": "Convite para WEDOTALENT",
        "subject": "Você foi convidado para a plataforma WEDOTALENT - {{company_name}}",
        "category": "invite",
        "channel": "email",
        "situation": "convite",
        "variables": ["user_name", "company_name", "inviter_name", "accept_url", "role_name", "expires_at"],
        "body_html": """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;600;700&display=swap" rel="stylesheet">
</head>
<body style="margin: 0; padding: 0; font-family: 'Open Sans', Arial, Helvetica, sans-serif; background-color: #f4f4f5;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width: 600px; margin: 0 auto; background-color: #ffffff;">
        <tr>
            <td style="background: linear-gradient(135deg, #60BED1 0%, #4A9BAB 100%); padding: 40px 30px; text-align: center;">
                <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: 600;">WEDOTALENT</h1>
                <p style="margin: 10px 0 0 0; color: rgba(255,255,255,0.9); font-size: 14px;">Plataforma Inteligente de Recrutamento</p>
            </td>
        </tr>
        <tr>
            <td style="padding: 40px 30px;">
                <h2 style="margin: 0 0 20px 0; color: #1F2937; font-size: 24px; font-weight: 600;">
                    Você foi convidado!
                </h2>
                
                <p style="margin: 0 0 20px 0; color: #1F2937; font-size: 16px; line-height: 1.6;">
                    Olá <strong>{{user_name}}</strong>,
                </p>
                
                <p style="margin: 0 0 20px 0; color: #1F2937; font-size: 16px; line-height: 1.6;">
                    <strong>{{inviter_name}}</strong> convidou você para fazer parte da equipe <strong>{{company_name}}</strong> na plataforma WEDOTALENT!
                </p>
                
                <div style="background-color: #f0f9fa; border-radius: 12px; padding: 25px; margin: 25px 0; text-align: center;">
                    <p style="margin: 0 0 10px 0; color: #6b7280; font-size: 14px; text-transform: uppercase; letter-spacing: 1px;">
                        Seu perfil na plataforma
                    </p>
                    <p style="margin: 0; color: #1F2937; font-size: 20px; font-weight: 600;">
                        {{role_name}}
                    </p>
                </div>
                
                <div style="text-align: center; margin: 35px 0;">
                    <a href="{{accept_url}}" style="display: inline-block; background-color: #60BED1; color: #ffffff; text-decoration: none; padding: 18px 50px; border-radius: 8px; font-size: 18px; font-weight: 600; box-shadow: 0 4px 6px rgba(96, 190, 209, 0.3);">
                        Aceitar Convite
                    </a>
                </div>
                
                <div style="background-color: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px 20px; margin: 25px 0; border-radius: 0 8px 8px 0;">
                    <p style="margin: 0; color: #92400e; font-size: 14px;">
                        <strong>Atenção:</strong> Este convite expira em <strong>{{expires_at}}</strong>. Aceite o convite antes dessa data para garantir seu acesso.
                    </p>
                </div>
                
                <div style="background-color: #f9fafb; padding: 20px; border-radius: 8px; margin: 25px 0;">
                    <h4 style="margin: 0 0 15px 0; color: #1F2937; font-size: 16px;">O que você poderá fazer:</h4>
                    <ul style="margin: 0; padding-left: 20px; color: #1F2937; font-size: 14px; line-height: 1.8;">
                        <li>Triagem automatizada de candidatos com IA (LIA)</li>
                        <li>Análise inteligente de currículos e compatibilidade com vagas</li>
                        <li>Agendamento automático de entrevistas</li>
                        <li>Comunicação multicanal com candidatos (email, WhatsApp)</li>
                        <li>Busca semântica em base de 800M+ perfis profissionais</li>
                    </ul>
                </div>
                
                <p style="margin: 25px 0 0 0; color: #6b7280; font-size: 14px; line-height: 1.6;">
                    Se você não esperava este convite ou não conhece {{inviter_name}}, pode ignorar este email com segurança.
                </p>
            </td>
        </tr>
        <tr>
            <td style="background-color: #1F2937; padding: 30px; text-align: center;">
                <p style="margin: 0 0 10px 0; color: #9ca3af; font-size: 14px;">
                    Precisa de ajuda? Entre em contato:
                </p>
                <a href="mailto:suporte@wedotalent.com" style="color: #60BED1; text-decoration: none; font-size: 14px; font-weight: 600;">
                    suporte@wedotalent.com
                </a>
                <p style="margin: 20px 0 0 0; color: #6b7280; font-size: 12px;">
                    © 2024 WEDOTALENT. Todos os direitos reservados.
                </p>
            </td>
        </tr>
    </table>
</body>
</html>
""",
        "body_text": """
Você foi convidado!

Olá {{user_name}},

{{inviter_name}} convidou você para fazer parte da equipe {{company_name}} na plataforma WEDOTALENT!

SEU PERFIL NA PLATAFORMA: {{role_name}}

Para aceitar o convite, acesse o link abaixo:
{{accept_url}}

ATENÇÃO: Este convite expira em {{expires_at}}. Aceite o convite antes dessa data para garantir seu acesso.

O QUE VOCÊ PODERÁ FAZER:
- Triagem automatizada de candidatos com IA (LIA)
- Análise inteligente de currículos e compatibilidade com vagas
- Agendamento automático de entrevistas
- Comunicação multicanal com candidatos (email, WhatsApp)
- Busca semântica em base de 800M+ perfis profissionais

Se você não esperava este convite ou não conhece {{inviter_name}}, pode ignorar este email com segurança.

Precisa de ajuda? Entre em contato: suporte@wedotalent.com

© 2024 WEDOTALENT. Todos os direitos reservados.
"""
    },
    {
        "name": "Compartilhamento com Gestor",
        "subject": "{{recruiter_name}} compartilhou candidatos para {{job_title}}",
        "category": "sharing",
        "channel": "email",
        "situation": "share_with_manager",
        "variables": ["recruiter_name", "job_title", "candidate_count", "share_link", "otp_code", "expiry_date", "message", "company_name"],
        "body_html": """<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; background-color: #f9fafb; margin: 0; padding: 0;">
    <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff;">
        <div style="background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%); padding: 30px; text-align: center;">
            <h1 style="margin: 0; color: #ffffff; font-size: 22px; font-weight: 600;">Candidatos Compartilhados</h1>
        </div>
        <div style="padding: 30px;">
            <p>Olá,</p>
            <p><strong>{{recruiter_name}}</strong> da <strong>{{company_name}}</strong> compartilhou <strong>{{candidate_count}} candidato(s)</strong> para a posição de <strong>{{job_title}}</strong> com você.</p>

            <div style="background-color: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3 style="margin-top: 0; color: #1f2937;">Mensagem do Recrutador:</h3>
                <p style="margin-bottom: 0;">{{message}}</p>
            </div>

            <div style="background-color: #eff6ff; padding: 15px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #2563eb;">
                <p style="margin: 0;"><strong>Código de Acesso (OTP):</strong> {{otp_code}}</p>
                <p style="margin: 5px 0 0 0; font-size: 13px; color: #6b7280;">Válido até {{expiry_date}}</p>
            </div>

            <div style="text-align: center; margin: 30px 0;">
                <a href="{{share_link}}" style="background-color: #2563eb; color: white; padding: 14px 28px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">
                    Acessar Candidatos
                </a>
            </div>

            <p style="color: #6b7280; font-size: 13px;">Use o código OTP acima ao acessar o link para verificar sua identidade.</p>
        </div>
        <div style="background-color: #f9fafb; padding: 20px 30px; text-align: center; border-top: 1px solid #e5e7eb;">
            <p style="margin: 0; color: #9ca3af; font-size: 12px;">Este é um email automático enviado pela plataforma WEDOTALENT.</p>
        </div>
    </div>
</body>
</html>""",
        "body_text": """Candidatos Compartilhados

Olá,

{{recruiter_name}} da {{company_name}} compartilhou {{candidate_count}} candidato(s) para a posição de {{job_title}} com você.

Mensagem do Recrutador:
{{message}}

Código de Acesso (OTP): {{otp_code}}
Válido até: {{expiry_date}}

Acesse os candidatos: {{share_link}}

Use o código OTP acima ao acessar o link para verificar sua identidade.

Este é um email automático enviado pela plataforma WEDOTALENT.
"""
    },
    {
        "name": "Compartilhamento com Gestor (WhatsApp)",
        "subject": None,
        "category": "sharing",
        "channel": "whatsapp",
        "situation": "share_with_manager",
        "variables": ["recruiter_name", "job_title", "candidate_count", "share_link", "otp_code", "expiry_date", "message", "company_name"],
        "body_html": """Olá! 👋

*{{recruiter_name}}* da *{{company_name}}* compartilhou *{{candidate_count}} candidato(s)* para a vaga de *{{job_title}}* com você.

{{message}}

🔗 Acesse os candidatos:
{{share_link}}

🔑 Código de acesso: *{{otp_code}}*
📅 Válido até: {{expiry_date}}""",
        "body_text": """Olá! 👋

*{{recruiter_name}}* da *{{company_name}}* compartilhou *{{candidate_count}} candidato(s)* para a vaga de *{{job_title}}* com você.

{{message}}

🔗 Acesse os candidatos:
{{share_link}}

🔑 Código de acesso: *{{otp_code}}*
📅 Válido até: {{expiry_date}}"""
    },
]

