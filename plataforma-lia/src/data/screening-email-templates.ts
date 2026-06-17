/**
 * Templates de email padrão para triagens por voz e entrevistas de vídeo
 * Compatível com DefaultTemplate do templates-service
 * 
 * @version 2.0.0
 * @updated 2026-01-13
 */

interface DefaultTemplate {
  id: string
  name: string
  category: string
  subject: string
  body: string
  variables?: string[]
  isActive?: boolean
  status?: string
  usedByClients?: number
  createdAt?: string
  updatedAt?: string
}

export type ScreeningTemplateType = 'screening' | 'interview' | 'feedback' | 'reminder' | 'offer'
export type TriggerEvent = 
  | 'screening_invite_sent'
  | 'screening_reminder_24h'
  | 'screening_completed'
  | 'video_interview_scheduled'
  | 'screening_approved'
  | 'screening_rejected'
  | 'interview_reminder_24h'
  | 'interview_reminder_1h'
  | 'offer_sent'
  | 'offer_accepted'
  | 'offer_declined'
  | 'offer_reminder'

export interface ScreeningTemplateMetadata {
  templateType: ScreeningTemplateType
  triggerEvent: TriggerEvent
  recipientType: 'candidate' | 'recruiter' | 'manager'
}

export interface ScreeningDefaultTemplate extends DefaultTemplate {
  metadata?: ScreeningTemplateMetadata
}

export const screeningDefaultTemplates: ScreeningDefaultTemplate[] = [
  {
    id: 'tpl-voice-screening-invite',
    name: 'Convite para Triagem por Voz',
    category: 'email',
    subject: 'Próximo passo: Triagem por Voz para {{job_title}}',
    body: `<div style="font-family: 'Open Sans', sans-serif; color: #374151; line-height: 1.6;">
  <p>Olá <strong>{{candidate_name}}</strong>,</p>
  
  <p>Parabéns por avançar no processo seletivo para a vaga de <strong>{{job_title}}</strong> na <strong>{{company_name}}</strong>!</p>
  
  <p>O próximo passo é uma triagem por voz rápida, onde você poderá nos contar mais sobre sua experiência e motivações. A triagem leva aproximadamente 5-7 minutos e pode ser feita a qualquer momento.</p>
  
  <div style="background: #F0F9FA; border-left: 4px solid #60BED1; padding: 16px; margin: 20px 0; border-radius: 4px;">
    <strong style="color: #60BED1;">Para iniciar sua triagem:</strong>
    <ol style="margin: 10px 0 0 0; padding-left: 20px;">
      <li>Acesse o link: <a href="{{screening_link}}" style="color: #60BED1;">{{screening_link}}</a></li>
      <li>Certifique-se de estar em um ambiente silencioso</li>
      <li>Responda às {{total_questions}} perguntas com calma</li>
    </ol>
  </div>
  
  <p style="font-size: 13px; color: #2D2D2D;">Lembrando que suas respostas serão analisadas pela nossa IA para garantir um processo justo e eficiente.</p>
  
  <p>Caso tenha dúvidas, entre em contato conosco.</p>
  
  <p>Atenciosamente,<br/>
  <strong>{{recruiter_name}}</strong><br/>
  {{company_name}}</p>
</div>`,
    variables: ['candidate_name', 'job_title', 'company_name', 'screening_link', 'total_questions', 'recruiter_name'],
    status: 'active',
    usedByClients: 0,
    createdAt: '2026-01-13T00:00:00Z',
    updatedAt: '2026-01-13T00:00:00Z',
    metadata: {
      templateType: 'screening',
      triggerEvent: 'screening_invite_sent',
      recipientType: 'candidate'
    }
  },
  {
    id: 'tpl-voice-screening-reminder',
    name: 'Lembrete: Triagem por Voz Pendente',
    category: 'email',
    subject: 'Lembrete: Complete sua triagem por voz para {{job_title}}',
    body: `<div style="font-family: 'Open Sans', sans-serif; color: #374151; line-height: 1.6;">
  <p>Olá <strong>{{candidate_name}}</strong>,</p>
  
  <p>Notamos que você ainda não completou sua triagem por voz para a vaga de <strong>{{job_title}}</strong>.</p>
  
  <p>A triagem leva apenas 5-7 minutos e é um passo importante para continuarmos seu processo seletivo.</p>
  
  <div style="text-align: center; margin: 24px 0;">
    <a href="{{screening_link}}" style="display: inline-block; background: #60BED1; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: 600;">Completar Triagem</a>
  </div>
  
  <p style="font-size: 13px; color: #2D2D2D;">Se você tiver qualquer dificuldade técnica ou precisar de mais tempo, por favor nos avise.</p>
  
  <p>Atenciosamente,<br/>
  <strong>{{recruiter_name}}</strong><br/>
  {{company_name}}</p>
</div>`,
    variables: ['candidate_name', 'job_title', 'screening_link', 'recruiter_name', 'company_name'],
    status: 'active',
    usedByClients: 0,
    createdAt: '2026-01-13T00:00:00Z',
    updatedAt: '2026-01-13T00:00:00Z',
    metadata: {
      templateType: 'reminder',
      triggerEvent: 'screening_reminder_24h',
      recipientType: 'candidate'
    }
  },
  {
    id: 'tpl-voice-screening-completed',
    name: 'Triagem por Voz Concluída',
    category: 'email',
    subject: 'Triagem concluída - {{job_title}}',
    body: `<div style="font-family: 'Open Sans', sans-serif; color: #374151; line-height: 1.6;">
  <p>Olá <strong>{{candidate_name}}</strong>,</p>
  
  <p>Recebemos sua triagem por voz para a vaga de <strong>{{job_title}}</strong>. Obrigado por dedicar seu tempo!</p>
  
  <p>Nosso time analisará suas respostas e retornaremos em breve com os próximos passos do processo.</p>
  
  <div style="background: #F3F4F6; padding: 16px; border-radius: 8px; margin: 20px 0;">
    <div style="display: flex; justify-content: space-around; text-align: center;">
      <div>
        <div style="font-size: 20px; font-weight: 600; color: #60BED1;">{{screening_duration}}</div>
        <div style="font-size: 12px; color: #2D2D2D;">Duração</div>
      </div>
      <div>
        <div style="font-size: 20px; font-weight: 600; color: #10B981;">{{questions_answered}}/{{total_questions}}</div>
        <div style="font-size: 12px; color: #2D2D2D;">Perguntas</div>
      </div>
    </div>
  </div>
  
  <p style="font-size: 13px; color: #2D2D2D;">Fique atento ao seu email para atualizações.</p>
  
  <p>Atenciosamente,<br/>
  <strong>{{recruiter_name}}</strong><br/>
  {{company_name}}</p>
</div>`,
    variables: ['candidate_name', 'job_title', 'screening_duration', 'questions_answered', 'total_questions', 'recruiter_name', 'company_name'],
    status: 'active',
    usedByClients: 0,
    createdAt: '2026-01-13T00:00:00Z',
    updatedAt: '2026-01-13T00:00:00Z',
    metadata: {
      templateType: 'feedback',
      triggerEvent: 'screening_completed',
      recipientType: 'candidate'
    }
  },
  {
    id: 'tpl-video-interview-invite',
    name: 'Convite para Entrevista por Vídeo',
    category: 'email',
    subject: 'Convite: Entrevista por Vídeo para {{job_title}}',
    body: `<div style="font-family: 'Open Sans', sans-serif; color: #374151; line-height: 1.6;">
  <p>Olá <strong>{{candidate_name}}</strong>,</p>
  
  <p>Você foi selecionado(a) para a próxima etapa do processo seletivo para <strong>{{job_title}}</strong> na <strong>{{company_name}}</strong>.</p>
  
  <p>Gostaríamos de agendar uma entrevista por vídeo com você.</p>
  
  <div style="background: #F3F4F6; padding: 20px; border-radius: 8px; margin: 20px 0;">
    <div style="margin-bottom: 12px;">
      <span style="color: #2D2D2D; font-size: 12px;">📅 Data</span><br/>
      <strong>{{interview_date}}</strong>
    </div>
    <div style="margin-bottom: 12px;">
      <span style="color: #2D2D2D; font-size: 12px;">🕐 Horário</span><br/>
      <strong>{{interview_time}}</strong>
    </div>
    <div style="margin-bottom: 12px;">
      <span style="color: #2D2D2D; font-size: 12px;">⏱️ Duração</span><br/>
      <strong>{{interview_duration}}</strong>
    </div>
  </div>
  
  <div style="text-align: center; margin: 24px 0;">
    <a href="{{interview_link}}" style="display: inline-block; background: #60BED1; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: 600;">Acessar Entrevista</a>
  </div>
  
  <div style="background: #FEF3C7; padding: 16px; border-radius: 8px; margin: 20px 0;">
    <strong style="color: #D97706;">Dicas de preparação:</strong>
    <ul style="margin: 10px 0; padding-left: 20px; color: #92400E;">
      <li>Teste sua câmera e microfone com antecedência</li>
      <li>Escolha um ambiente bem iluminado e silencioso</li>
      <li>Tenha uma cópia do seu currículo por perto</li>
      <li>Prepare exemplos de suas realizações profissionais</li>
    </ul>
  </div>
  
  <p>Por favor, confirme sua participação respondendo a este email.</p>
  
  <p>Atenciosamente,<br/>
  <strong>{{recruiter_name}}</strong><br/>
  {{company_name}}</p>
</div>`,
    variables: ['candidate_name', 'job_title', 'company_name', 'interview_date', 'interview_time', 'interview_duration', 'interview_link', 'interviewers_list', 'recruiter_name'],
    status: 'active',
    usedByClients: 0,
    createdAt: '2026-01-13T00:00:00Z',
    updatedAt: '2026-01-13T00:00:00Z',
    metadata: {
      templateType: 'interview',
      triggerEvent: 'video_interview_scheduled',
      recipientType: 'candidate'
    }
  },
  {
    id: 'tpl-screening-result-approved',
    name: 'Resultado Triagem: Aprovado',
    category: 'email',
    subject: 'Boas notícias! Você avançou no processo - {{job_title}}',
    body: `<div style="font-family: 'Open Sans', sans-serif; color: #374151; line-height: 1.6;">
  <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #D1FAE5 0%, #A7F3D0 100%); border-radius: 8px; margin-bottom: 20px;">
    <span style="font-size: 48px;">🎉</span>
    <h2 style="color: #065F46; margin: 10px 0 0 0;">Parabéns!</h2>
  </div>
  
  <p>Olá <strong>{{candidate_name}}</strong>,</p>
  
  <p>Temos boas notícias! Após analisar sua triagem por voz para a vaga de <strong>{{job_title}}</strong>, você foi aprovado(a) para a próxima etapa do processo seletivo.</p>
  
  <div style="background: #F0FDF4; border-left: 4px solid #10B981; padding: 16px; margin: 20px 0; border-radius: 4px;">
    <strong style="color: #065F46;">Próximos passos:</strong>
    <p style="margin: 10px 0 0 0; color: #047857;">{{next_steps}}</p>
  </div>
  
  <p>Em breve entraremos em contato para agendar a próxima etapa.</p>
  
  <p>Atenciosamente,<br/>
  <strong>{{recruiter_name}}</strong><br/>
  {{company_name}}</p>
</div>`,
    variables: ['candidate_name', 'job_title', 'next_steps', 'recruiter_name', 'company_name'],
    status: 'active',
    usedByClients: 0,
    createdAt: '2026-01-13T00:00:00Z',
    updatedAt: '2026-01-13T00:00:00Z',
    metadata: {
      templateType: 'feedback',
      triggerEvent: 'screening_approved',
      recipientType: 'candidate'
    }
  },
  {
    id: 'tpl-screening-result-rejected',
    name: 'Resultado Triagem: Não Aprovado',
    category: 'email',
    subject: 'Atualização do seu processo - {{job_title}}',
    body: `<div style="font-family: 'Open Sans', sans-serif; color: #374151; line-height: 1.6;">
  <p>Olá <strong>{{candidate_name}}</strong>,</p>
  
  <p>Agradecemos seu interesse na vaga de <strong>{{job_title}}</strong> e pelo tempo dedicado ao nosso processo seletivo.</p>
  
  <p>Após análise cuidadosa, decidimos seguir com outros candidatos cujos perfis estão mais alinhados com os requisitos desta posição específica.</p>
  
  <div style="background: #F3F4F6; padding: 16px; border-radius: 8px; margin: 20px 0;">
    <p style="margin: 0; color: #4B5563; font-size: 14px;">
      💡 Isso não diminui suas qualificações. Encorajamos você a acompanhar novas oportunidades em nossa empresa.
    </p>
  </div>
  
  <p>Desejamos sucesso em sua jornada profissional.</p>
  
  <p>Atenciosamente,<br/>
  <strong>{{recruiter_name}}</strong><br/>
  {{company_name}}</p>
</div>`,
    variables: ['candidate_name', 'job_title', 'recruiter_name', 'company_name'],
    status: 'active',
    usedByClients: 0,
    createdAt: '2026-01-13T00:00:00Z',
    updatedAt: '2026-01-13T00:00:00Z',
    metadata: {
      templateType: 'feedback',
      triggerEvent: 'screening_rejected',
      recipientType: 'candidate'
    }
  },
  {
    id: 'tpl-video-interview-reminder-24h',
    name: 'Lembrete Entrevista 24h',
    category: 'email',
    subject: 'Lembrete: Sua entrevista amanhã - {{job_title}}',
    body: `<div style="font-family: 'Open Sans', sans-serif; color: #374151; line-height: 1.6;">
  <p>Olá <strong>{{candidate_name}}</strong>,</p>
  
  <p>Este é um lembrete de que sua entrevista por vídeo para a vaga de <strong>{{job_title}}</strong> está agendada para <strong>amanhã</strong>.</p>
  
  <div style="background: #EFF6FF; border: 1px solid #BFDBFE; padding: 16px; border-radius: 8px; margin: 20px 0;">
    <p style="margin: 0;"><strong>📅 {{interview_date}}</strong> às <strong>{{interview_time}}</strong></p>
  </div>
  
  <div style="text-align: center; margin: 20px 0;">
    <a href="{{interview_link}}" style="display: inline-block; background: #60BED1; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: 600;">Acessar Entrevista</a>
  </div>
  
  <p style="font-weight: 600;">Dicas finais:</p>
  <ul>
    <li>Teste sua conexão e equipamento hoje</li>
    <li>Prepare suas perguntas para os entrevistadores</li>
    <li>Descanse bem esta noite</li>
  </ul>
  
  <p>Boa sorte!</p>
  
  <p><strong>{{recruiter_name}}</strong><br/>
  {{company_name}}</p>
</div>`,
    variables: ['candidate_name', 'job_title', 'interview_date', 'interview_time', 'interview_link', 'recruiter_name', 'company_name'],
    status: 'active',
    usedByClients: 0,
    createdAt: '2026-01-13T00:00:00Z',
    updatedAt: '2026-01-13T00:00:00Z',
    metadata: {
      templateType: 'reminder',
      triggerEvent: 'interview_reminder_24h',
      recipientType: 'candidate'
    }
  },
  {
    id: 'tpl-video-interview-reminder-1h-whatsapp',
    name: 'Lembrete Entrevista 1h (WhatsApp)',
    category: 'whatsapp',
    subject: 'Lembrete: Entrevista em 1 hora',
    body: `Olá {{candidate_name}}! 👋

Sua entrevista para *{{job_title}}* começa em 1 hora.

🕐 {{interview_time}}
🔗 {{interview_link}}

Boa sorte! 🍀`,
    variables: ['candidate_name', 'job_title', 'interview_time', 'interview_link'],
    status: 'active',
    usedByClients: 0,
    createdAt: '2026-01-13T00:00:00Z',
    updatedAt: '2026-01-13T00:00:00Z',
    metadata: {
      templateType: 'reminder',
      triggerEvent: 'interview_reminder_1h',
      recipientType: 'candidate'
    }
  },
  {
    id: 'tpl-screening-complete-whatsapp',
    name: 'Triagem Concluída (WhatsApp)',
    category: 'whatsapp',
    subject: 'Triagem recebida',
    body: `Olá {{candidate_name}}! ✅

Recebemos sua triagem por voz para *{{job_title}}*.

Nosso time vai analisar e retornaremos em breve com os próximos passos.

Obrigado! 🙏`,
    variables: ['candidate_name', 'job_title'],
    status: 'active',
    usedByClients: 0,
    createdAt: '2026-01-13T00:00:00Z',
    updatedAt: '2026-01-13T00:00:00Z',
    metadata: {
      templateType: 'feedback',
      triggerEvent: 'screening_completed',
      recipientType: 'candidate'
    }
  },
  {
    id: 'tpl-offer-sent',
    name: 'Proposta Salarial Enviada',
    category: 'email',
    subject: 'Proposta de Trabalho - {{job_title}} na {{company_name}}',
    body: `<div style="font-family: 'Open Sans', sans-serif; color: #374151; line-height: 1.6; max-width: 600px; margin: 0 auto;">
  <div style="text-align: center; padding: 24px; background: linear-gradient(135deg, #60BED1 0%, #4BA3B5 100%); border-radius: 8px 8px 0 0;">
    <h1 style="color: white; margin: 0; font-size: 24px;">Proposta de Trabalho</h1>
  </div>
  
  <div style="padding: 24px; background: white; border: 1px solid #D4D4D4; border-top: none;">
    <p>Prezado(a) <strong>{{candidate_name}}</strong>,</p>
    
    <p>É com grande satisfação que formalizamos nossa proposta para a posição de <strong>{{job_title}}</strong> na <strong>{{company_name}}</strong>.</p>
    
    <p>Após cuidadosa avaliação de seu perfil profissional, temos a certeza de que você será uma adição valiosa à nossa equipe.</p>
    
    <div style="background: #F0F9FA; border: 2px solid #60BED1; border-radius: 8px; padding: 20px; margin: 24px 0; text-align: center;">
      <p style="margin: 0 0 8px 0; font-size: 14px; color: #2D2D2D;">Remuneração Mensal</p>
      <p style="margin: 0; font-size: 32px; font-weight: 700; color: #1F2937;">{{salary}}</p>
      {{#if bonus}}
      <p style="margin: 8px 0 0 0; font-size: 14px; color: #60BED1;">+ Bônus: {{bonus}}</p>
      {{/if}}
    </div>
    
    <h3 style="color: #1F2937; font-size: 16px; margin: 24px 0 12px 0; border-bottom: 2px solid #D4D4D4; padding-bottom: 8px;">Detalhes da Proposta</h3>
    
    <table style="width: 100%; border-collapse: collapse;">
      <tr>
        <td style="padding: 12px; background: #F9FAFB; border-bottom: 1px solid #D4D4D4; width: 40%;">
          <strong style="color: #2D2D2D;">Data de Início</strong>
        </td>
        <td style="padding: 12px; border-bottom: 1px solid #D4D4D4;">
          {{start_date}}
        </td>
      </tr>
      <tr>
        <td style="padding: 12px; background: #F9FAFB; border-bottom: 1px solid #D4D4D4;">
          <strong style="color: #2D2D2D;">Tipo de Contrato</strong>
        </td>
        <td style="padding: 12px; border-bottom: 1px solid #D4D4D4;">
          {{contract_type}}
        </td>
      </tr>
      <tr>
        <td style="padding: 12px; background: #F9FAFB; border-bottom: 1px solid #D4D4D4;">
          <strong style="color: #2D2D2D;">Modelo de Trabalho</strong>
        </td>
        <td style="padding: 12px; border-bottom: 1px solid #D4D4D4;">
          {{work_model}}
        </td>
      </tr>
      <tr>
        <td style="padding: 12px; background: #F9FAFB; border-bottom: 1px solid #D4D4D4;">
          <strong style="color: #2D2D2D;">Departamento</strong>
        </td>
        <td style="padding: 12px; border-bottom: 1px solid #D4D4D4;">
          {{department}}
        </td>
      </tr>
      <tr>
        <td style="padding: 12px; background: #F9FAFB;">
          <strong style="color: #2D2D2D;">Gestor Direto</strong>
        </td>
        <td style="padding: 12px;">
          {{manager_name}}
        </td>
      </tr>
    </table>
    
    <h3 style="color: #1F2937; font-size: 16px; margin: 24px 0 12px 0; border-bottom: 2px solid #D4D4D4; padding-bottom: 8px;">Pacote de Benefícios</h3>
    
    <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 20px;">
      {{benefits_list}}
    </div>
    
    <div style="background: #FEF3C7; border-left: 4px solid #F59E0B; padding: 16px; margin: 24px 0; border-radius: 4px;">
      <p style="margin: 0; color: #92400E;">
        <strong>Prazo para Resposta:</strong> {{response_deadline}}<br/>
        <span style="font-size: 13px;">Por favor, confirme sua aceitação ou entre em contato caso tenha dúvidas.</span>
      </p>
    </div>
    
    <div style="text-align: center; margin: 24px 0;">
      <a href="{{accept_link}}" style="display: inline-block; background: #60BED1; color: white; padding: 14px 32px; text-decoration: none; border-radius: 6px; font-weight: 600; margin-right: 12px;">Aceitar Proposta</a>
      <a href="{{contact_link}}" style="display: inline-block; background: white; color: #374151; padding: 14px 32px; text-decoration: none; border-radius: 6px; font-weight: 600; border: 1px solid #999999;">Tenho Dúvidas</a>
    </div>
    
    <p style="font-size: 13px; color: #2D2D2D; margin-top: 24px;">
      Esta proposta é confidencial e destinada exclusivamente ao destinatário. Os termos aqui apresentados estão sujeitos à aprovação final e formalização contratual.
    </p>
    
    <p>Aguardamos ansiosamente sua resposta positiva.</p>
    
    <p>Atenciosamente,<br/>
    <strong>{{recruiter_name}}</strong><br/>
    {{recruiter_title}}<br/>
    {{company_name}}</p>
  </div>
  
  <div style="padding: 16px; background: #F3F4F6; border-radius: 0 0 8px 8px; text-align: center;">
    <p style="margin: 0; font-size: 12px; color: #2D2D2D;">
      {{company_name}} | {{company_address}}<br/>
      Em caso de dúvidas: {{recruiter_email}} | {{recruiter_phone}}
    </p>
  </div>
</div>`,
    variables: ['candidate_name', 'job_title', 'company_name', 'salary', 'bonus', 'start_date', 'contract_type', 'work_model', 'department', 'manager_name', 'benefits_list', 'response_deadline', 'accept_link', 'contact_link', 'recruiter_name', 'recruiter_title', 'recruiter_email', 'recruiter_phone', 'company_address'],
    status: 'active',
    usedByClients: 0,
    createdAt: '2026-01-13T00:00:00Z',
    updatedAt: '2026-01-13T00:00:00Z',
    metadata: {
      templateType: 'offer',
      triggerEvent: 'offer_sent',
      recipientType: 'candidate'
    }
  },
  {
    id: 'tpl-offer-reminder',
    name: 'Lembrete: Resposta à Proposta Pendente',
    category: 'email',
    subject: 'Lembrete: Sua proposta de trabalho aguarda resposta - {{job_title}}',
    body: `<div style="font-family: 'Open Sans', sans-serif; color: #374151; line-height: 1.6;">
  <p>Olá <strong>{{candidate_name}}</strong>,</p>
  
  <p>Esperamos que esteja bem! Estamos entrando em contato para lembrar que sua proposta para a posição de <strong>{{job_title}}</strong> ainda aguarda resposta.</p>
  
  <div style="background: #F0F9FA; border: 1px solid #60BED1; border-radius: 8px; padding: 20px; margin: 20px 0; text-align: center;">
    <p style="margin: 0 0 8px 0; font-size: 14px; color: #2D2D2D;">Proposta</p>
    <p style="margin: 0; font-size: 24px; font-weight: 700; color: #1F2937;">{{salary}}</p>
    <p style="margin: 8px 0 0 0; font-size: 14px; color: #60BED1;">Início: {{start_date}}</p>
  </div>
  
  <p>O prazo para resposta é <strong>{{response_deadline}}</strong>.</p>
  
  <p>Se você tiver alguma dúvida sobre a proposta ou precisar de mais tempo para decidir, por favor entre em contato conosco. Estamos à disposição para esclarecer qualquer questão.</p>
  
  <div style="text-align: center; margin: 24px 0;">
    <a href="{{accept_link}}" style="display: inline-block; background: #60BED1; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: 600;">Responder à Proposta</a>
  </div>
  
  <p>Atenciosamente,<br/>
  <strong>{{recruiter_name}}</strong><br/>
  {{company_name}}</p>
</div>`,
    variables: ['candidate_name', 'job_title', 'salary', 'start_date', 'response_deadline', 'accept_link', 'recruiter_name', 'company_name'],
    status: 'active',
    usedByClients: 0,
    createdAt: '2026-01-13T00:00:00Z',
    updatedAt: '2026-01-13T00:00:00Z',
    metadata: {
      templateType: 'offer',
      triggerEvent: 'offer_reminder',
      recipientType: 'candidate'
    }
  },
  {
    id: 'tpl-offer-accepted-confirmation',
    name: 'Confirmação: Proposta Aceita',
    category: 'email',
    subject: 'Bem-vindo(a) à {{company_name}}! Próximos passos',
    body: `<div style="font-family: 'Open Sans', sans-serif; color: #374151; line-height: 1.6;">
  <div style="text-align: center; padding: 24px; background: linear-gradient(135deg, #60BED1 0%, #4BA3B5 100%); border-radius: 8px; margin-bottom: 20px;">
    <span style="font-size: 48px;">🎉</span>
    <h2 style="color: white; margin: 10px 0 0 0;">Bem-vindo(a) à equipe!</h2>
  </div>
  
  <p>Prezado(a) <strong>{{candidate_name}}</strong>,</p>
  
  <p>É com enorme alegria que confirmamos sua aceitação da proposta para a posição de <strong>{{job_title}}</strong>!</p>
  
  <p>Estamos muito felizes em tê-lo(a) como parte da nossa equipe. Sua jornada na <strong>{{company_name}}</strong> começa em <strong>{{start_date}}</strong>.</p>
  
  <div style="background: #F0F9FA; border-left: 4px solid #60BED1; padding: 16px; margin: 20px 0; border-radius: 4px;">
    <strong style="color: #60BED1;">Próximos Passos:</strong>
    <ol style="margin: 10px 0 0 0; padding-left: 20px;">
      <li>Você receberá o contrato formal em até 2 dias úteis</li>
      <li>Nossa equipe de RH entrará em contato para o onboarding</li>
      <li>Prepare a documentação necessária (lista em anexo)</li>
      <li>Aguarde o kit de boas-vindas</li>
    </ol>
  </div>
  
  <p>Se tiver qualquer dúvida antes do seu primeiro dia, não hesite em entrar em contato.</p>
  
  <p>Mais uma vez, seja muito bem-vindo(a)!</p>
  
  <p>Atenciosamente,<br/>
  <strong>{{recruiter_name}}</strong><br/>
  {{company_name}}</p>
</div>`,
    variables: ['candidate_name', 'job_title', 'company_name', 'start_date', 'recruiter_name'],
    status: 'active',
    usedByClients: 0,
    createdAt: '2026-01-13T00:00:00Z',
    updatedAt: '2026-01-13T00:00:00Z',
    metadata: {
      templateType: 'offer',
      triggerEvent: 'offer_accepted',
      recipientType: 'candidate'
    }
  },
  {
    id: 'tpl-offer-whatsapp',
    name: 'Proposta Enviada (WhatsApp)',
    category: 'whatsapp',
    subject: 'Proposta de trabalho enviada',
    body: `Olá {{candidate_name}}! 🎉

Temos uma ótima notícia! Sua proposta de trabalho para *{{job_title}}* foi enviada.

💰 *{{salary}}*
📅 Início: {{start_date}}
📄 Contrato: {{contract_type}}

Confira todos os detalhes no seu email e responda até {{response_deadline}}.

Qualquer dúvida, estamos à disposição! 💬`,
    variables: ['candidate_name', 'job_title', 'salary', 'start_date', 'contract_type', 'response_deadline'],
    status: 'active',
    usedByClients: 0,
    createdAt: '2026-01-13T00:00:00Z',
    updatedAt: '2026-01-13T00:00:00Z',
    metadata: {
      templateType: 'offer',
      triggerEvent: 'offer_sent',
      recipientType: 'candidate'
    }
  }
]

/**
 * English-language variants of the templates referenced by the static
 * preview pages under `/[locale]/triagem/preview/...`. They are intentionally
 * scoped to the previews so that production seeding (which still consumes
 * `screeningDefaultTemplates`) keeps shipping only the Portuguese defaults.
 *
 * If you add a new preview that depends on another template, add the
 * matching English version here so `getPreviewTemplate(id, 'en')` can find
 * it instead of silently falling back to Portuguese.
 */
export const screeningPreviewTemplatesEn: ScreeningDefaultTemplate[] = [
  {
    id: 'tpl-voice-screening-invite',
    name: 'Voice Screening Invitation',
    category: 'email',
    subject: 'Next step: voice screening for {{job_title}}',
    body: `<div style="font-family: 'Open Sans', sans-serif; color: #374151; line-height: 1.6;">
  <p>Hi <strong>{{candidate_name}}</strong>,</p>

  <p>Congratulations on advancing in the selection process for the <strong>{{job_title}}</strong> role at <strong>{{company_name}}</strong>!</p>

  <p>Your next step is a quick voice screening, where you can tell us more about your experience and motivations. The screening takes about 5–7 minutes and can be completed at any time.</p>

  <div style="background: #F0F9FA; border-left: 4px solid #60BED1; padding: 16px; margin: 20px 0; border-radius: 4px;">
    <strong style="color: #60BED1;">To start your screening:</strong>
    <ol style="margin: 10px 0 0 0; padding-left: 20px;">
      <li>Open the link: <a href="{{screening_link}}" style="color: #60BED1;">{{screening_link}}</a></li>
      <li>Make sure you are in a quiet environment</li>
      <li>Answer the {{total_questions}} questions at your own pace</li>
    </ol>
  </div>

  <p style="font-size: 13px; color: #2D2D2D;">Just so you know, your answers will be analysed by our AI to keep the process fair and efficient.</p>

  <p>If you have any questions, please reach out.</p>

  <p>Best regards,<br/>
  <strong>{{recruiter_name}}</strong><br/>
  {{company_name}}</p>
</div>`,
    variables: ['candidate_name', 'job_title', 'company_name', 'screening_link', 'total_questions', 'recruiter_name'],
    status: 'active',
    metadata: {
      templateType: 'screening',
      triggerEvent: 'screening_invite_sent',
      recipientType: 'candidate'
    }
  },
  {
    id: 'tpl-voice-screening-reminder',
    name: 'Reminder: Voice Screening Pending',
    category: 'email',
    subject: 'Reminder: complete your voice screening for {{job_title}}',
    body: `<div style="font-family: 'Open Sans', sans-serif; color: #374151; line-height: 1.6;">
  <p>Hi <strong>{{candidate_name}}</strong>,</p>

  <p>We noticed that you haven't finished your voice screening for the <strong>{{job_title}}</strong> role yet.</p>

  <p>The screening takes only 5–7 minutes and is an important step to keep your application moving forward.</p>

  <div style="text-align: center; margin: 24px 0;">
    <a href="{{screening_link}}" style="display: inline-block; background: #60BED1; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: 600;">Complete screening</a>
  </div>

  <p style="font-size: 13px; color: #2D2D2D;">If you run into any technical issues or need more time, please let us know.</p>

  <p>Best regards,<br/>
  <strong>{{recruiter_name}}</strong><br/>
  {{company_name}}</p>
</div>`,
    variables: ['candidate_name', 'job_title', 'screening_link', 'recruiter_name', 'company_name'],
    status: 'active',
    metadata: {
      templateType: 'reminder',
      triggerEvent: 'screening_reminder_24h',
      recipientType: 'candidate'
    }
  },
  {
    id: 'tpl-screening-complete-whatsapp',
    name: 'Screening Completed (WhatsApp)',
    category: 'whatsapp',
    subject: 'Screening received',
    body: `Hi {{candidate_name}}! ✅

We've received your voice screening for *{{job_title}}*.

Our team will review it and get back to you soon with the next steps.

Thank you! 🙏`,
    variables: ['candidate_name', 'job_title'],
    status: 'active',
    metadata: {
      templateType: 'feedback',
      triggerEvent: 'screening_completed',
      recipientType: 'candidate'
    }
  }
]

/**
 * Returns the screening template matching `id` for the given locale, used by
 * the static preview pages. Falls back to the Portuguese default when no
 * English variant has been authored for the requested template.
 */
export function getPreviewTemplate(
  id: string,
  locale: string
): ScreeningDefaultTemplate | undefined {
  if (locale === 'en') {
    const enTemplate = screeningPreviewTemplatesEn.find((t) => t.id === id)
    if (enTemplate) return enTemplate
  }
  return screeningDefaultTemplates.find((t) => t.id === id)
}

export const screeningTemplateCategories: Record<ScreeningTemplateType, { label: string; color: string; icon: string }> = {
  screening: { label: 'Triagem', color: 'var(--wedo-cyan)', icon: '🎤' },
  interview: { label: 'Entrevista', color: 'var(--wedo-cyan)', icon: '🎥' },
  feedback: { label: 'Feedback', color: 'var(--wedo-cyan)', icon: '✉️' },
  reminder: { label: 'Lembrete', color: 'var(--wedo-cyan)', icon: '⏰' },
  offer: { label: 'Proposta', color: 'var(--wedo-cyan)', icon: '💼' }
}

export function getTemplateByEvent(event: TriggerEvent): ScreeningDefaultTemplate | undefined {
  return screeningDefaultTemplates.find(t => t.metadata?.triggerEvent === event)
}

export function getTemplatesByType(templateType: ScreeningTemplateType): ScreeningDefaultTemplate[] {
  return screeningDefaultTemplates.filter(t => t.metadata?.templateType === templateType)
}

export function getTemplatesByChannel(channel: DefaultTemplate['category']): ScreeningDefaultTemplate[] {
  return screeningDefaultTemplates.filter(t => t.category === channel)
}

export function renderTemplate(template: ScreeningDefaultTemplate, variables: Record<string, string>): { subject: string; body: string } {
  let subject = template.subject || ''
  let body = template.body

  for (const [key, value] of Object.entries(variables)) {
    const regex = new RegExp(`\\{\\{${key}\\}\\}`, 'g')
    subject = subject.replace(regex, value)
    body = body.replace(regex, value)
  }

  return { subject, body }
}

export function convertToDefaultTemplate(template: ScreeningDefaultTemplate): DefaultTemplate {
  const { metadata, ...defaultTemplate } = template
  return defaultTemplate
}

export function getScreeningTemplatesForSeeding(): DefaultTemplate[] {
  return screeningDefaultTemplates.map(convertToDefaultTemplate)
}

export default screeningDefaultTemplates
