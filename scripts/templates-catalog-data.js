/* Dados do catalogo de templates (WEDO-3931).
   Gerado a partir de:
     ats-api/docs/communication_templates.yml   (inventario canonico)
     ats-api/app/views/*_mailer/*.html.erb      (corpo real dos e-mails)
     ats-api/app/services/cadence/message_builder.rb (texto da cadencia)
     ai-engine/app/templates/communication_templates.py (textos de WhatsApp)
   Tudo medido em origin/develop. Nao editar a mao. */

const CATALOGO = [
 {
  "key": "screening_invite",
  "name": "Convite para a triagem",
  "channel": "email",
  "category": "triagem",
  "audience": "candidato",
  "status": "active",
  "source": "ats-api app/mailers/evaluation_mailer.rb#unified_invitation",
  "subject": "{{company_name}} — Convite para triagem sobre {{job_title}}",
  "trigger": "Candidato entra na triagem, seja por criacao da candidatura, envio em massa pelo kanban ou convite manual.",
  "variables": [
   "company_name",
   "job_title",
   "candidate_name",
   "evaluation_url"
  ],
  "body": "Oportunidade — {{company_name}}\n\nOlá, {{candidate_name}}.\n\n{{custom_message_html}}\n\nMeu nome é {{recruiter_name}} e faço parte do time de recrutamento da {{company_name}}.\nIdentificamos seu perfil e gostaríamos de conversar sobre a vaga de\n{{job_title}}.\n\nPara dar início ao processo, convidamos você a uma conversa com a LIA\n— nossa assistente de inteligência artificial. É uma etapa breve e assíncrona, criada para que possamos conhecer\nsua trajetória e expectativas antes de qualquer entrevista formal.\n\nPara melhor experiência, escolha um momento tranquilo e verifique sua conexão à internet.\nCompatível com Chrome, Firefox e Edge.",
  "note": "",
  "hasText": false,
  "defaultSubject": "{{company_name}} — Convite para triagem sobre {{job_title}}",
  "defaultBody": "Oportunidade — {{company_name}}\n\nOlá, {{candidate_name}}.\n\n{{custom_message_html}}\n\nMeu nome é {{recruiter_name}} e faço parte do time de recrutamento da {{company_name}}.\nIdentificamos seu perfil e gostaríamos de conversar sobre a vaga de\n{{job_title}}.\n\nPara dar início ao processo, convidamos você a uma conversa com a LIA\n— nossa assistente de inteligência artificial. É uma etapa breve e assíncrona, criada para que possamos conhecer\nsua trajetória e expectativas antes de qualquer entrevista formal.\n\nPara melhor experiência, escolha um momento tranquilo e verifique sua conexão à internet.\nCompatível com Chrome, Firefox e Edge.",
  "customized": false,
  "customizedBy": null,
  "customizedAt": null,
  "otherClients": []
 },
 {
  "key": "screening_reminder",
  "name": "Lembrete de triagem pendente",
  "channel": "email",
  "category": "triagem",
  "audience": "candidato",
  "status": "active",
  "source": "ats-api app/mailers/evaluation_mailer.rb#escalation_continue_screening",
  "subject": "{{company_name}} — Continue sua triagem",
  "trigger": "Rotina diaria das 8h UTC, 48 horas depois do convite, se a triagem nao foi concluida.",
  "variables": [
   "company_name",
   "job_title",
   "candidate_name",
   "evaluation_url"
  ],
  "body": "Lembrete — {{company_name}}\n\nOlá, {{candidate_name}}.\n\nVocê ainda não concluiu a conversa com a LIA sobre a vaga de\n{{job_title}}.\n\nReserve alguns minutos para continuar. O processo é assíncrono — você pode pausar e retomar quando quiser.",
  "note": "",
  "hasText": false,
  "defaultSubject": "{{company_name}} — Continue sua triagem",
  "defaultBody": "Lembrete — {{company_name}}\n\nOlá, {{candidate_name}}.\n\nVocê ainda não concluiu a conversa com a LIA sobre a vaga de\n{{job_title}}.\n\nReserve alguns minutos para continuar. O processo é assíncrono — você pode pausar e retomar quando quiser.",
  "customized": false,
  "customizedBy": null,
  "customizedAt": null,
  "otherClients": []
 },
 {
  "key": "screening_last_chance",
  "name": "Última chance de triagem",
  "channel": "email",
  "category": "triagem",
  "audience": "candidato",
  "status": "active",
  "source": "ats-api app/mailers/evaluation_mailer.rb#escalation_last_chance",
  "subject": "{{company_name}} — Última chance: complete sua triagem",
  "trigger": "Mesma rotina diaria, 72 horas depois do convite.",
  "variables": [
   "company_name",
   "job_title",
   "candidate_name",
   "evaluation_url"
  ],
  "body": "Última chance — {{company_name}}\n\nOlá, {{candidate_name}}.\n\nEsta é nossa última tentativa de contato. A conversa com a LIA sobre a vaga de\n{{job_title}} ainda está pendente.\n\nSe você ainda tem interesse, complete a triagem agora. Caso contrário, entenderemos que não deseja seguir com o processo.",
  "note": "",
  "hasText": false,
  "defaultSubject": "{{company_name}} — Última chance: complete sua triagem",
  "defaultBody": "Última chance — {{company_name}}\n\nOlá, {{candidate_name}}.\n\nEsta é nossa última tentativa de contato. A conversa com a LIA sobre a vaga de\n{{job_title}} ainda está pendente.\n\nSe você ainda tem interesse, complete a triagem agora. Caso contrário, entenderemos que não deseja seguir com o processo.",
  "customized": false,
  "customizedBy": null,
  "customizedAt": null,
  "otherClients": [
   "Sodexo",
   "Localiza"
  ]
 },
 {
  "key": "cv_adherence_feedback",
  "name": "Retorno sobre o currículo",
  "channel": "email",
  "category": "feedback",
  "audience": "candidato",
  "status": "active",
  "source": "ats-api app/mailers/cv_adherence_feedback_mailer.rb#feedback_to_candidate",
  "subject": "Atualização sobre sua candidatura - {{job_title}}",
  "trigger": "Logo apos a analise do curriculo, quando a nota de aderencia fica em 50 ou menos. Nao sai para quem entrou por link direto de triagem.",
  "variables": [
   "candidate_name",
   "job_title",
   "feedback_body",
   "reaction_url"
  ],
  "body": "Processo seletivo\n\nOlá, {{candidate}}.\n\nSegue o retorno sobre sua candidatura à vaga de {{job}}:\n\n{{phrase}}\n\nAgradecemos seu interesse e o tempo dedicado ao processo. Ficamos à disposição para futuras oportunidades.",
  "note": "",
  "hasText": false,
  "defaultSubject": "Atualização sobre sua candidatura - {{job_title}}",
  "defaultBody": "Processo seletivo\n\nOlá, {{candidate}}.\n\nSegue o retorno sobre sua candidatura à vaga de {{job}}:\n\n{{phrase}}\n\nAgradecemos seu interesse e o tempo dedicado ao processo. Ficamos à disposição para futuras oportunidades.",
  "customized": false,
  "customizedBy": null,
  "customizedAt": null,
  "otherClients": []
 },
 {
  "key": "rejection_feedback",
  "name": "Feedback de reprovação",
  "channel": "email",
  "category": "feedback",
  "audience": "candidato",
  "status": "dynamic",
  "source": "ats-api app/mailers/reject_feedback_mailer.rb#feedback_to_candidate",
  "subject": "Atualização sobre sua candidatura - {{job_title}}",
  "trigger": "Reprovacao do candidato, disparo em massa do fechamento da vaga e retorno automatico apos a triagem.",
  "variables": [
   "candidate_name",
   "job_title",
   "feedback_body",
   "reaction_url"
  ],
  "body": "Processo seletivo\n\nOlá, {{candidate}}.\n\nSegue o retorno sobre sua candidatura à vaga de {{job}}:\n\n{{feedback_html}}\n\nAgradecemos seu interesse e o tempo dedicado ao processo. Desejamos sucesso em sua trajetória profissional e ficamos à disposição para futuras oportunidades.\n\nTime de Atração de Talentos do iFood",
  "note": "O recrutador pode escrever o titulo do feedback; o assunto do catalogo e o texto de reserva.",
  "hasText": false,
  "defaultSubject": "Atualização sobre sua candidatura - {{job_title}}",
  "defaultBody": "Processo seletivo\n\nOlá, {{candidate}}.\n\nSegue o retorno sobre sua candidatura à vaga de {{job}}:\n\n{{feedback_html}}\n\nAgradecemos seu interesse e o tempo dedicado ao processo. Desejamos sucesso em sua trajetória profissional e ficamos à disposição para futuras oportunidades.",
  "customized": true,
  "customizedBy": "Rodrigo Alfieri",
  "customizedAt": "05/09/2026",
  "otherClients": [
   "Localiza"
  ]
 },
 {
  "key": "scheduling_invite",
  "name": "Convite para escolher horário",
  "channel": "email",
  "category": "entrevista",
  "audience": "candidato",
  "status": "dynamic",
  "source": "ats-api app/mailers/scheduling_mailer.rb#scheduling_invite",
  "subject": "Escolha o horário da sua entrevista",
  "trigger": "Criacao de um link de agendamento e convite de entrevista por telefone.",
  "variables": [
   "candidate_name",
   "job_title",
   "scheduling_url",
   "slot_options"
  ],
  "body": "Agendamento de entrevista\n\n{{subject}}\n\nOlá, {{candidate}}.\n\n{{message}}\n\nVocê foi convidado(a) para agendar uma entrevista. Escolha o melhor horário para você.\n\nEscolha um horário disponível:\n\n{{option}}\n\nClique em um horário para confirmar sua presença.\n\nTime de Atração de Talentos do iFood",
  "note": "O assunto do catalogo so vale quando o recrutador deixa o campo em branco.",
  "hasText": false,
  "defaultSubject": "Escolha o horário da sua entrevista",
  "defaultBody": "Agendamento de entrevista\n\n{{subject}}\n\nOlá, {{candidate}}.\n\n{{message}}\n\nVocê foi convidado(a) para agendar uma entrevista. Escolha o melhor horário para você.\n\nEscolha um horário disponível:\n\n{{option}}\n\nClique em um horário para confirmar sua presença.",
  "customized": true,
  "customizedBy": "Rodrigo Alfieri",
  "customizedAt": "16/06/2026",
  "otherClients": []
 },
 {
  "key": "booking_confirmed_candidate",
  "name": "Entrevista confirmada (candidato)",
  "channel": "email",
  "category": "entrevista",
  "audience": "candidato",
  "status": "active",
  "source": "ats-api app/mailers/scheduling_mailer.rb#booking_confirmed_candidate",
  "subject": "Sua entrevista foi agendada: {{meeting_subject}}",
  "trigger": "Assim que o candidato escolhe um horario no link de agendamento.",
  "variables": [
   "candidate_name",
   "meeting_subject",
   "meeting_time",
   "interviewer_name"
  ],
  "body": "Entrevista confirmada\n\nOlá, {{candidate}}.\n\nSua entrevista foi confirmada com sucesso.\n\nLink da reunião\n\nNo horário, entre na sua entrevista por este link:\n\nEntrar na reunião\n\n{{meeting}}\n\nEstamos ansiosos para conhecê-lo(a)!",
  "note": "",
  "hasText": false,
  "defaultSubject": "Sua entrevista foi agendada: {{meeting_subject}}",
  "defaultBody": "Entrevista confirmada\n\nOlá, {{candidate}}.\n\nSua entrevista foi confirmada com sucesso.\n\nLink da reunião\n\nNo horário, entre na sua entrevista por este link:\n\nEntrar na reunião\n\n{{meeting}}\n\nEstamos ansiosos para conhecê-lo(a)!",
  "customized": false,
  "customizedBy": null,
  "customizedAt": null,
  "otherClients": []
 },
 {
  "key": "job_lifecycle_notice",
  "name": "Aviso de vaga pausada, retomada ou cancelada",
  "channel": "email",
  "category": "vaga",
  "audience": "candidato",
  "status": "active",
  "source": "ats-api app/jobs/lifecycle_candidate_notifier.rb",
  "subject": "A vaga {{job_title}} foi pausada temporariamente",
  "trigger": "Mudanca de status da vaga, depois que o recrutador confirma o aviso no chat.",
  "variables": [
   "candidate_name",
   "job_title",
   "lifecycle_state"
  ],
  "body": "",
  "note": "Tem tres variantes de assunto, pausada, retomada e cancelada. Cada variante vira uma chave propria no catalogo.",
  "hasText": false,
  "defaultSubject": "A vaga {{job_title}} foi pausada temporariamente",
  "defaultBody": "",
  "customized": false,
  "customizedBy": null,
  "customizedAt": null,
  "otherClients": []
 },
 {
  "key": "account_signup",
  "name": "Boas-vindas e cadastro da conta",
  "channel": "email",
  "category": "conta",
  "audience": "candidato",
  "status": "active",
  "source": "ats-api app/mailers/account_mailer.rb#signup_email",
  "subject": "Bem-vindo ao {{account_name}}! Complete seu cadastro",
  "trigger": "Criacao de conta com e-mail de cadastro preenchido.",
  "variables": [
   "account_name",
   "user_name",
   "signup_url"
  ],
  "body": "Novo acesso\n\nBem-vindo ao {{account_name}}!\n\n{{content}}\n\nOu copie e cole este link no seu navegador:\n\n{{setup_url}}",
  "note": "",
  "hasText": true,
  "defaultSubject": "Bem-vindo ao {{account_name}}! Complete seu cadastro",
  "defaultBody": "Novo acesso\n\nBem-vindo ao {{account_name}}!\n\n{{content}}\n\nOu copie e cole este link no seu navegador:\n\n{{setup_url}}",
  "customized": false,
  "customizedBy": null,
  "customizedAt": null,
  "otherClients": []
 },
 {
  "key": "evaluation_completed",
  "name": "Candidato concluiu a avaliação",
  "channel": "email",
  "category": "triagem",
  "audience": "recrutador",
  "status": "active",
  "source": "ats-api app/mailers/evaluation_mailer.rb#completion_notification",
  "subject": "{{candidate_name}} concluiu a avaliação — {{job_title}}",
  "trigger": "No instante em que a triagem do candidato e marcada como concluida.",
  "variables": [
   "candidate_name",
   "job_title",
   "wsi_score",
   "candidate_url"
  ],
  "body": "Avaliação concluída\n\n{{candidate_name}} finalizou a avaliação\n\nO candidato {{candidate_name}} concluiu a avaliação\n{{evaluation_name}}.",
  "note": "",
  "hasText": false,
  "defaultSubject": "{{candidate_name}} concluiu a avaliação — {{job_title}}",
  "defaultBody": "Avaliação concluída\n\n{{candidate_name}} finalizou a avaliação\n\nO candidato {{candidate_name}} concluiu a avaliação\n{{evaluation_name}}.",
  "customized": false,
  "customizedBy": null,
  "customizedAt": null,
  "otherClients": []
 },
 {
  "key": "evaluation_declined",
  "name": "Candidato recusou a avaliação",
  "channel": "email",
  "category": "triagem",
  "audience": "recrutador",
  "status": "active",
  "source": "ats-api app/mailers/evaluation_mailer.rb#decline_notification",
  "subject": "{{candidate_name}} recusou a avaliação — {{job_title}}",
  "trigger": "Candidato clica em nao tenho interesse ou a triagem e recusada.",
  "variables": [
   "candidate_name",
   "job_title",
   "candidate_url"
  ],
  "body": "Avaliação recusada\n\n{{candidate_name}} recusou a avaliação\n\nO candidato {{candidate_name}} recusou participar da avaliação\n{{evaluation_name}}.\n\nMotivo da recusa\n\n{{declined_reason}}",
  "note": "",
  "hasText": false,
  "defaultSubject": "{{candidate_name}} recusou a avaliação — {{job_title}}",
  "defaultBody": "Avaliação recusada\n\n{{candidate_name}} recusou a avaliação\n\nO candidato {{candidate_name}} recusou participar da avaliação\n{{evaluation_name}}.\n\nMotivo da recusa\n\n{{declined_reason}}",
  "customized": false,
  "customizedBy": null,
  "customizedAt": null,
  "otherClients": []
 },
 {
  "key": "evaluation_stalled_alert",
  "name": "Alerta de triagem não concluída",
  "channel": "email",
  "category": "triagem",
  "audience": "recrutador",
  "status": "active",
  "source": "ats-api app/mailers/evaluation_mailer.rb#escalation_alert_consultant",
  "subject": "Alerta: Triagem não concluída — {{candidate_name}} ({{job_title}})",
  "trigger": "Rotina diaria das 8h, 96 horas apos o convite. Junto com o e-mail o sistema encerra a triagem.",
  "variables": [
   "candidate_name",
   "job_title",
   "candidate_url"
  ],
  "body": "Alerta — Triagem não concluída\n\nCandidato não concluiu a triagem\n\nO candidato {{candidate_name}} não concluiu a avaliação\n{{evaluation_name}} após 96 horas.",
  "note": "",
  "hasText": false,
  "defaultSubject": "Alerta: Triagem não concluída — {{candidate_name}} ({{job_title}})",
  "defaultBody": "Alerta — Triagem não concluída\n\nCandidato não concluiu a triagem\n\nO candidato {{candidate_name}} não concluiu a avaliação\n{{evaluation_name}} após 96 horas.",
  "customized": false,
  "customizedBy": null,
  "customizedAt": null,
  "otherClients": []
 },
 {
  "key": "job_closed",
  "name": "Vaga encerrada",
  "channel": "email",
  "category": "vaga",
  "audience": "recrutador",
  "status": "active",
  "source": "ats-api app/mailers/job_closure_mailer.rb#closure_confirmation",
  "subject": "Vaga encerrada - {{job_title}}",
  "trigger": "Fechamento da vaga ou fim do disparo de feedback em massa, o que acontecer primeiro. Sai uma vez so.",
  "variables": [
   "job_title",
   "closed_by",
   "summary"
  ],
  "body": "Encerramento de vaga\n\nOlá, {{recipient}}.\n\nA vaga {{job}} foi encerrada.\n\n{{feedback_summary}}\n{{feedback_summary}} o feedback do processo.\n\nNão foi possível enviar para\n{{feedback_summary}}\n{{feedback_summary}}.\n\nTime de Atração de Talentos do iFood",
  "note": "",
  "hasText": false,
  "defaultSubject": "Vaga encerrada - {{job_title}}",
  "defaultBody": "Encerramento de vaga\n\nOlá, {{recipient}}.\n\nA vaga {{job}} foi encerrada.\n\n{{feedback_summary}}\n{{feedback_summary}} o feedback do processo.\n\nNão foi possível enviar para\n{{feedback_summary}}\n{{feedback_summary}}.",
  "customized": true,
  "customizedBy": "Paulo Moraes",
  "customizedAt": "12/09/2026",
  "otherClients": []
 },
 {
  "key": "job_closure_message_test",
  "name": "Prévia da mensagem de encerramento",
  "channel": "email",
  "category": "vaga",
  "audience": "recrutador",
  "status": "dynamic",
  "source": "ats-api app/mailers/job_closure_mailer.rb#closure_message_test",
  "subject": "[TESTE] {{subject}}",
  "trigger": "Botao de teste no modal de encerramento da vaga.",
  "variables": [
   "subject",
   "body",
   "candidate_name"
  ],
  "body": "Teste — não foi enviado a ninguém\n\nPrévia da mensagem de encerramento\n\nVaga {{job}}.\nAbaixo está exatamente o texto que o candidato receberia.\n\n{{body}}",
  "note": "",
  "hasText": false,
  "defaultSubject": "[TESTE] {{subject}}",
  "defaultBody": "Teste — não foi enviado a ninguém\n\nPrévia da mensagem de encerramento\n\nVaga {{job}}.\nAbaixo está exatamente o texto que o candidato receberia.\n\n{{body}}",
  "customized": false,
  "customizedBy": null,
  "customizedAt": null,
  "otherClients": [
   "Mappit"
  ]
 },
 {
  "key": "screening_issue_reported",
  "name": "Problema reportado na triagem",
  "channel": "email",
  "category": "triagem",
  "audience": "recrutador",
  "status": "active",
  "source": "ats-api app/mailers/issue_mailer.rb#screening_notification",
  "subject": "[Screening] Problema reportado por {{candidate_name}} - {{job_title}}",
  "trigger": "Candidato reporta um problema durante a triagem.",
  "variables": [
   "candidate_name",
   "job_title",
   "issue_description"
  ],
  "body": "Problema reportado\n\nProblema reportado no Screening",
  "note": "",
  "hasText": true,
  "defaultSubject": "[Screening] Problema reportado por {{candidate_name}} - {{job_title}}",
  "defaultBody": "Problema reportado\n\nProblema reportado no Screening",
  "customized": false,
  "customizedBy": null,
  "customizedAt": null,
  "otherClients": [
   "Grupo Boticário",
   "Sodexo"
  ]
 },
 {
  "key": "booking_confirmed_recruiter",
  "name": "Novo agendamento (recrutador)",
  "channel": "email",
  "category": "entrevista",
  "audience": "recrutador",
  "status": "active",
  "source": "ats-api app/mailers/scheduling_mailer.rb#booking_confirmed_recruiter",
  "subject": "Entrevista agendada: {{meeting_subject}}",
  "trigger": "Mesmo momento do aviso ao candidato, quando ele escolhe um horario.",
  "variables": [
   "candidate_name",
   "meeting_subject",
   "meeting_time"
  ],
  "body": "Novo agendamento\n\nUm candidato agendou uma entrevista\n\nUm candidato agendou uma entrevista através do seu link de agendamento.",
  "note": "",
  "hasText": false,
  "defaultSubject": "Entrevista agendada: {{meeting_subject}}",
  "defaultBody": "Novo agendamento\n\nUm candidato agendou uma entrevista\n\nUm candidato agendou uma entrevista através do seu link de agendamento.",
  "customized": false,
  "customizedBy": null,
  "customizedAt": null,
  "otherClients": [
   "Sodexo"
  ]
 },
 {
  "key": "notification_digest",
  "name": "Notificação por e-mail",
  "channel": "email",
  "category": "alertas",
  "audience": "recrutador",
  "status": "dynamic",
  "source": "ats-api app/mailers/notification_mailer.rb#digest_email",
  "subject": "Notificação WeDO",
  "trigger": "Notificacao do sistema que tem o e-mail como canal de entrega.",
  "variables": [
   "notification_title",
   "notification_body",
   "action_url"
  ],
  "body": "{{notification}}\n\n{{notification}}",
  "note": "O assunto do catalogo e o texto de reserva para quando a notificacao nao tem titulo.",
  "hasText": true,
  "defaultSubject": "Notificação WeDO",
  "defaultBody": "{{notification}}\n\n{{notification}}",
  "customized": false,
  "customizedBy": null,
  "customizedAt": null,
  "otherClients": [
   "Localiza",
   "Mappit"
  ]
 },
 {
  "key": "notification_grouped_alerts",
  "name": "Alertas agrupados",
  "channel": "email",
  "category": "alertas",
  "audience": "recrutador",
  "status": "active",
  "source": "ats-api app/mailers/notification_mailer.rb#grouped_alerts_email",
  "subject": "{{grouped_subject}}",
  "trigger": "Agrupamento de alertas do sistema para o recrutador.",
  "variables": [
   "grouped_subject",
   "alerts"
  ],
  "body": "{{notifications}} alertas das suas vagas\n\n{{title}} ({{grouped}})\n\n{{notification}}",
  "note": "",
  "hasText": true,
  "defaultSubject": "{{grouped_subject}}",
  "defaultBody": "{{notifications}} alertas das suas vagas\n\n{{title}} ({{grouped}})\n\n{{notification}}",
  "customized": false,
  "customizedBy": null,
  "customizedAt": null,
  "otherClients": [
   "Sodexo",
   "Localiza"
  ]
 },
 {
  "key": "insights_report",
  "name": "Relatório de insights",
  "channel": "email",
  "category": "relatorios",
  "audience": "recrutador",
  "status": "dynamic",
  "source": "ats-api app/services/jobs/insights_email_service.rb",
  "subject": "Relatório de Insights - {{jobs_count}} vaga(s)",
  "trigger": "Envio manual pela tela de insights das vagas.",
  "variables": [
   "jobs_count",
   "body",
   "recipient_name"
  ],
  "body": "",
  "note": "",
  "hasText": false,
  "defaultSubject": "Relatório de Insights - {{jobs_count}} vaga(s)",
  "defaultBody": "",
  "customized": false,
  "customizedBy": null,
  "customizedAt": null,
  "otherClients": []
 },
 {
  "key": "business_site_analysis_ready",
  "name": "Análise do site pronta para revisão",
  "channel": "email",
  "category": "onboarding",
  "audience": "recrutador",
  "status": "active",
  "source": "ats-api app/mailers/business_site_analysis_mailer.rb#ready_for_review",
  "subject": "Processamos as informações do site de {{company_name}}",
  "trigger": "Fim da analise automatica do site da empresa.",
  "variables": [
   "company_name",
   "confirm_url",
   "summary"
  ],
  "body": "Processamos as informações do site\n\nOlá {{user}},\n\nAnalisamos o site {{analysis}} e o LinkedIn da empresa\ne encontramos as informações abaixo.\n\n{{label}}\n\n{{value}}\n\nConfira os dados na plataforma: você pode editar o que precisar antes de confirmar.\n\nRevisar e confirmar\n\nSe o botão não funcionar, copie e cole este endereço no navegador:\n\n{{confirm_url}}\n\nNada é salvo na sua empresa até você confirmar.",
  "note": "",
  "hasText": true,
  "defaultSubject": "Processamos as informações do site de {{company_name}}",
  "defaultBody": "Processamos as informações do site\n\nOlá {{user}},\n\nAnalisamos o site {{analysis}} e o LinkedIn da empresa\ne encontramos as informações abaixo.\n\n{{label}}\n\n{{value}}\n\nConfira os dados na plataforma: você pode editar o que precisar antes de confirmar.\n\nRevisar e confirmar\n\nSe o botão não funcionar, copie e cole este endereço no navegador:\n\n{{confirm_url}}\n\nNada é salvo na sua empresa até você confirmar.",
  "customized": false,
  "customizedBy": null,
  "customizedAt": null,
  "otherClients": []
 },
 {
  "key": "manual_dispatch",
  "name": "Disparo manual do recrutador",
  "channel": "email",
  "category": "disparo",
  "audience": "candidato",
  "status": "dynamic",
  "source": "ats-api app/mailers/dispatch_mailer.rb#dispatch_email",
  "subject": "{{message_subject}}",
  "trigger": "Disparo em massa pelo chat e envio manual a partir do funil.",
  "variables": [
   "message_subject",
   "message_body",
   "candidate_name",
   "user_name"
  ],
  "body": "{{message}}\n\nNao desejo mais receber estes emails",
  "note": "E o unico caminho que o cliente ja edita hoje, pela tela de Templates.",
  "hasText": false,
  "defaultSubject": "{{message_subject}}",
  "defaultBody": "{{message}}\n\nNao desejo mais receber estes emails",
  "customized": false,
  "customizedBy": null,
  "customizedAt": null,
  "otherClients": [
   "Mappit"
  ]
 },
 {
  "key": "mfa_otp",
  "name": "Código de verificação",
  "channel": "email",
  "category": "seguranca",
  "audience": "usuario",
  "status": "active",
  "source": "ats-api app/mailers/mfa_mailer.rb#otp_email",
  "subject": "Seu código de verificação - WeDOTalent",
  "trigger": "Login com verificacao em duas etapas ligada e a cada reenvio de codigo, limite de 3.",
  "variables": [
   "user_name",
   "otp_code",
   "expires_in"
  ],
  "body": "Verificação de Segurança\n\nSeu código de acesso\n\nOlá, {{user}}!\nUse o código abaixo para completar seu login:\n\nCódigo de Verificação\n\n{{code}}\n\n⏱ Válido por {{expires_in}}\n\n✓\n\nCódigo expira em {{expires_in}}\n\n✓\n\nPode ser usado apenas uma vez\n\n✓\n\nNão compartilhe com ninguém\n\n⚠️\n\nNão solicitou este código? Ignore este email. Sua conta permanece segura.",
  "note": "",
  "hasText": false,
  "defaultSubject": "Seu código de verificação - WeDOTalent",
  "defaultBody": "Verificação de Segurança\n\nSeu código de acesso\n\nOlá, {{user}}!\nUse o código abaixo para completar seu login:\n\nCódigo de Verificação\n\n{{code}}\n\n⏱ Válido por {{expires_in}}\n\n✓\n\nCódigo expira em {{expires_in}}\n\n✓\n\nPode ser usado apenas uma vez\n\n✓\n\nNão compartilhe com ninguém\n\n⚠️\n\nNão solicitou este código? Ignore este email. Sua conta permanece segura.",
  "customized": false,
  "customizedBy": null,
  "customizedAt": null,
  "otherClients": []
 },
 {
  "key": "mfa_policy_required",
  "name": "Verificação em duas etapas obrigatória",
  "channel": "email",
  "category": "seguranca",
  "audience": "usuario",
  "status": "active",
  "source": "ats-api app/mailers/mfa_mailer.rb#policy_changed_to_required_for_all",
  "subject": "Verificação em duas etapas agora é obrigatória",
  "trigger": "Administrador da conta torna o MFA obrigatorio para todo mundo.",
  "variables": [
   "user_name",
   "account_name"
  ],
  "body": "Verificação em duas etapas agora é obrigatória\n\nOlá {{user}},\n\nA administração de {{company_name}} ativou a verificação em duas etapas (MFA)\ncomo obrigatória para todos os usuários. Esse controle está alinhado com NIST SP 800-63B AAL2,\nISO 27001 A.9.4.2 e SOC 2 CC6.1.\n\nNo seu próximo login você será solicitado a verificar sua identidade por um código enviado ao\nseu e-mail. Não é necessário cadastrar nada agora — o processo será apresentado automaticamente\npelo sistema.\n\nEm caso de dúvidas, fale com o administrador da sua conta ou acesse\n{{front_url}}.\n\nEsta é uma mensagem automática. Você está recebendo porque é usuário ativo da conta\n{{company_name}}.\n\nTime de Atração de Talentos do iFood",
  "note": "",
  "hasText": false,
  "defaultSubject": "Verificação em duas etapas agora é obrigatória",
  "defaultBody": "Verificação em duas etapas agora é obrigatória\n\nOlá {{user}},\n\nA administração de {{company_name}} ativou a verificação em duas etapas (MFA)\ncomo obrigatória para todos os usuários. Esse controle está alinhado com NIST SP 800-63B AAL2,\nISO 27001 A.9.4.2 e SOC 2 CC6.1.\n\nNo seu próximo login você será solicitado a verificar sua identidade por um código enviado ao\nseu e-mail. Não é necessário cadastrar nada agora — o processo será apresentado automaticamente\npelo sistema.\n\nEm caso de dúvidas, fale com o administrador da sua conta ou acesse\n{{front_url}}.\n\nEsta é uma mensagem automática. Você está recebendo porque é usuário ativo da conta\n{{company_name}}.",
  "customized": true,
  "customizedBy": "Paulo Moraes",
  "customizedAt": "05/09/2026",
  "otherClients": [
   "Mappit",
   "Sodexo"
  ]
 },
 {
  "key": "password_reset",
  "name": "Redefinição de senha",
  "channel": "email",
  "category": "seguranca",
  "audience": "usuario",
  "status": "active",
  "source": "ats-api app/mailers/password_reset_mailer.rb#reset_password_email",
  "subject": "Redefinição de senha - We Do Talent",
  "trigger": "Pedido de esqueci minha senha. O link vale 1 hora.",
  "variables": [
   "user_name",
   "reset_url",
   "expires_in"
  ],
  "body": "Redefinição de senha\n\nOlá, {{user}}!\n\nVocê solicitou a redefinição da sua senha no WeDOTalent.\n\nPara criar uma nova senha, clique no botão abaixo:\n\nOu copie e cole este link no seu navegador:\n\n{{reset_url}}",
  "note": "",
  "hasText": true,
  "defaultSubject": "Redefinição de senha - We Do Talent",
  "defaultBody": "Redefinição de senha\n\nOlá, {{user}}!\n\nVocê solicitou a redefinição da sua senha no WeDOTalent.\n\nPara criar uma nova senha, clique no botão abaixo:\n\nOu copie e cole este link no seu navegador:\n\n{{reset_url}}",
  "customized": false,
  "customizedBy": null,
  "customizedAt": null,
  "otherClients": []
 },
 {
  "key": "new_access_created",
  "name": "Novo acesso criado",
  "channel": "email",
  "category": "seguranca",
  "audience": "usuario",
  "status": "active",
  "source": "ats-api app/mailers/password_reset_mailer.rb#new_access_email",
  "subject": "Novo acesso criado - We Do Talent",
  "trigger": "Criacao de um usuario na plataforma. O link vale 7 dias.",
  "variables": [
   "user_name",
   "setup_url",
   "expires_in"
  ],
  "body": "Novo acesso criado\n\nOlá, {{user}}!\n\nUm novo acesso foi criado para você no WeDOTalent.\n\nPara definir sua senha e acessar o sistema, clique no botão abaixo:\n\nOu copie e cole este link no seu navegador:\n\n{{reset_url}}",
  "note": "",
  "hasText": true,
  "defaultSubject": "Novo acesso criado - We Do Talent",
  "defaultBody": "Novo acesso criado\n\nOlá, {{user}}!\n\nUm novo acesso foi criado para você no WeDOTalent.\n\nPara definir sua senha e acessar o sistema, clique no botão abaixo:\n\nOu copie e cole este link no seu navegador:\n\n{{reset_url}}",
  "customized": false,
  "customizedBy": null,
  "customizedAt": null,
  "otherClients": []
 },
 {
  "key": "login_alert",
  "name": "Alerta de acesso fora do padrão",
  "channel": "email",
  "category": "seguranca",
  "audience": "usuario",
  "status": "active",
  "source": "ats-api app/mailers/login_alert_mailer.rb#new_device_or_location",
  "subject": "Novo dispositivo detectado em sua conta",
  "trigger": "Login a partir de dispositivo ou local diferente dos ultimos acessos.",
  "variables": [
   "user_name",
   "device",
   "location",
   "access_time"
  ],
  "body": "Detectamos um acesso fora do padrão\n\nOlá {{user}},\n\nIdentificamos um novo login na sua conta com características diferentes das suas\núltimas sessões. Confira os detalhes:\n\nData e hora\n\n{{when}} (BRT)\n\nLocalização aproximada\n\n(diferente do habitual)\n\nNavegador\n\n{{device}}\n\nSistema\n\n{{device}}\n(dispositivo novo)\n\nEndereço IP\n\n{{ip}}\n\nFoi você? Se sim, pode ignorar este aviso.\n\nSe não foi você:\n\nAcesse {{front_url}}.\n\nTroque sua senha imediatamente.\n\nHabilite ou revise sua verificação em duas etapas (MFA).\n\nAvise o administrador da sua conta.\n\nEste alerta é automático. Geolocalização baseada em IP é aproximada e pode\nindicar a cidade do provedor de internet, não a sua localização exata.\n\nTime de Atração de Talentos do iFood",
  "note": "Tem tres variantes de assunto, dispositivo novo, local novo e os dois. Cada variante vira uma chave propria.",
  "hasText": true,
  "defaultSubject": "Novo dispositivo detectado em sua conta",
  "defaultBody": "Detectamos um acesso fora do padrão\n\nOlá {{user}},\n\nIdentificamos um novo login na sua conta com características diferentes das suas\núltimas sessões. Confira os detalhes:\n\nData e hora\n\n{{when}} (BRT)\n\nLocalização aproximada\n\n(diferente do habitual)\n\nNavegador\n\n{{device}}\n\nSistema\n\n{{device}}\n(dispositivo novo)\n\nEndereço IP\n\n{{ip}}\n\nFoi você? Se sim, pode ignorar este aviso.\n\nSe não foi você:\n\nAcesse {{front_url}}.\n\nTroque sua senha imediatamente.\n\nHabilite ou revise sua verificação em duas etapas (MFA).\n\nAvise o administrador da sua conta.\n\nEste alerta é automático. Geolocalização baseada em IP é aproximada e pode\nindicar a cidade do provedor de internet, não a sua localização exata.",
  "customized": true,
  "customizedBy": "Paulo Moraes",
  "customizedAt": "28/08/2026",
  "otherClients": [
   "Localiza",
   "Talenses"
  ]
 },
 {
  "key": "cadence_followup_email",
  "name": "Cadência de retomada (e-mail)",
  "channel": "email",
  "category": "cadencia",
  "audience": "candidato",
  "status": "active",
  "source": "ats-api app/services/cadence/message_builder.rb#email_body",
  "subject": "Sobre sua candidatura à vaga {{job_title}}",
  "trigger": "Toques 1, 2 e 3 da cadencia de retomada de contato.",
  "variables": [
   "candidate_name",
   "job_title",
   "touch_number",
   "opt_out_url"
  ],
  "body": "Toque 1: Olá! Seguimos com o seu processo seletivo e gostaríamos de dar continuidade ao seu contato.\n\nToque 2: Olá! Notamos que ainda não avançamos por aqui, seguimos à disposição para dar continuidade.\n\nToque 3: Olá! Este é um último lembrete sobre o seu processo seletivo.\n\nCaso não queira mais receber estes contatos, utilize o link de descadastramento ao final do email.",
  "note": "O corpo muda por toque. Tres chaves no catalogo, uma por toque.",
  "hasText": false,
  "defaultSubject": "Sobre sua candidatura à vaga {{job_title}}",
  "defaultBody": "Toque 1: Olá! Seguimos com o seu processo seletivo e gostaríamos de dar continuidade ao seu contato.\n\nToque 2: Olá! Notamos que ainda não avançamos por aqui, seguimos à disposição para dar continuidade.\n\nToque 3: Olá! Este é um último lembrete sobre o seu processo seletivo.\n\nCaso não queira mais receber estes contatos, utilize o link de descadastramento ao final do email.",
  "customized": false,
  "customizedBy": null,
  "customizedAt": null,
  "otherClients": []
 },
 {
  "key": "cadence_followup_whatsapp",
  "name": "Cadência de retomada (WhatsApp)",
  "channel": "whatsapp",
  "category": "cadencia",
  "audience": "candidato",
  "status": "active",
  "source": "ats-api app/services/cadence/message_builder.rb#whatsapp_body",
  "subject": "",
  "trigger": "Mesmos tres toques, pelo WhatsApp. Fora da janela de 24h exige template aprovado pela Meta.",
  "variables": [
   "candidate_name",
   "job_title",
   "touch_number"
  ],
  "body": "Toque 1: Olá! Seguimos com o seu processo seletivo e gostaríamos de dar continuidade ao seu contato.\n\nToque 2: Olá! Notamos que ainda não avançamos por aqui, seguimos à disposição para dar continuidade.\n\nToque 3: Olá! Este é um último lembrete sobre o seu processo seletivo.\n\nSe não quiser mais receber estes contatos, responda SAIR.",
  "note": "O aviso de opt out responda SAIR e exigencia de LGPD e nao pode sair do texto.",
  "hasText": false,
  "defaultSubject": "",
  "defaultBody": "Toque 1: Olá! Seguimos com o seu processo seletivo e gostaríamos de dar continuidade ao seu contato.\n\nToque 2: Olá! Notamos que ainda não avançamos por aqui, seguimos à disposição para dar continuidade.\n\nToque 3: Olá! Este é um último lembrete sobre o seu processo seletivo.\n\nSe não quiser mais receber estes contatos, responda SAIR.",
  "customized": false,
  "customizedBy": null,
  "customizedAt": null,
  "otherClients": []
 },
 {
  "key": "lia_user_invite",
  "name": "Convite de usuário (LIA)",
  "channel": "email",
  "category": "conta",
  "audience": "usuario",
  "status": "active",
  "source": "ai-engine send_user_notification",
  "subject": "Você foi convidado para a Plataforma LIA",
  "trigger": "Convite de usuario pelo motor de IA, criacao e reativacao de acesso.",
  "variables": [
   "user_name",
   "invite_url"
  ],
  "body": "",
  "note": "",
  "hasText": false,
  "defaultSubject": "Você foi convidado para a Plataforma LIA",
  "defaultBody": "",
  "customized": false,
  "customizedBy": null,
  "customizedAt": null,
  "otherClients": [
   "Mappit"
  ]
 },
 {
  "key": "lia_password_reset",
  "name": "Redefinição de senha (LIA)",
  "channel": "email",
  "category": "seguranca",
  "audience": "usuario",
  "status": "active",
  "source": "ai-engine send_user_notification",
  "subject": "Redefinição de Senha - Plataforma LIA",
  "trigger": "Pedido de nova senha pelo motor de IA. O link vale 24 horas, contra 1 hora do produto.",
  "variables": [
   "user_name",
   "reset_url"
  ],
  "body": "",
  "note": "O prazo diverge do password_reset do ats-api. Unificar na migracao.",
  "hasText": false,
  "defaultSubject": "Redefinição de Senha - Plataforma LIA",
  "defaultBody": "",
  "customized": true,
  "customizedBy": "Jader Ota",
  "customizedAt": "28/08/2026",
  "otherClients": []
 },
 {
  "key": "lia_email_verification",
  "name": "Verificação de e-mail (LIA)",
  "channel": "email",
  "category": "conta",
  "audience": "usuario",
  "status": "active",
  "source": "ai-engine send_user_notification",
  "subject": "Verifique seu Email - Plataforma LIA",
  "trigger": "Cadastro pelo motor de IA. Link de 7 dias.",
  "variables": [
   "user_name",
   "verification_url"
  ],
  "body": "",
  "note": "",
  "hasText": false,
  "defaultSubject": "Verifique seu Email - Plataforma LIA",
  "defaultBody": "",
  "customized": false,
  "customizedBy": null,
  "customizedAt": null,
  "otherClients": [
   "Grupo Boticário"
  ]
 },
 {
  "key": "interview_cancelled",
  "name": "Entrevista cancelada",
  "channel": "email",
  "category": "entrevista",
  "audience": "candidato",
  "status": "active",
  "source": "ai-engine pipeline_tool_registry",
  "subject": "Entrevista cancelada — {{job_title}}",
  "trigger": "Recrutador cancela a entrevista falando com a LIA no chat.",
  "variables": [
   "candidate_name",
   "job_title",
   "interview_date"
  ],
  "body": "",
  "note": "",
  "hasText": false,
  "defaultSubject": "Entrevista cancelada — {{job_title}}",
  "defaultBody": "",
  "customized": true,
  "customizedBy": "Rodrigo Alfieri",
  "customizedAt": "05/09/2026",
  "otherClients": [
   "Localiza",
   "Mappit"
  ]
 },
 {
  "key": "interview_rescheduled",
  "name": "Entrevista reagendada",
  "channel": "email",
  "category": "entrevista",
  "audience": "candidato",
  "status": "active",
  "source": "ai-engine pipeline_tool_registry",
  "subject": "Entrevista reagendada — {{job_title}}",
  "trigger": "Recrutador reagenda a entrevista falando com a LIA no chat.",
  "variables": [
   "candidate_name",
   "job_title",
   "interview_date"
  ],
  "body": "",
  "note": "",
  "hasText": false,
  "defaultSubject": "Entrevista reagendada — {{job_title}}",
  "defaultBody": "",
  "customized": false,
  "customizedBy": null,
  "customizedAt": null,
  "otherClients": [
   "Localiza"
  ]
 },
 {
  "key": "kpi_report",
  "name": "Relatório de KPIs",
  "channel": "email",
  "category": "relatorios",
  "audience": "recrutador",
  "status": "active",
  "source": "ai-engine communication domain",
  "subject": "Relatório de KPIs de Recrutamento",
  "trigger": "Recrutador pede o relatorio de KPIs pela LIA.",
  "variables": [
   "recipient_name",
   "period",
   "metrics"
  ],
  "body": "",
  "note": "",
  "hasText": false,
  "defaultSubject": "Relatório de KPIs de Recrutamento",
  "defaultBody": "",
  "customized": false,
  "customizedBy": null,
  "customizedAt": null,
  "otherClients": []
 },
 {
  "key": "initial_contact",
  "name": "Contato inicial",
  "channel": "whatsapp",
  "category": "motor de IA",
  "audience": "candidato",
  "status": "active",
  "source": "ai-engine app/templates/communication_templates.py#WhatsAppTemplates.initial_contact",
  "subject": "",
  "trigger": "Automação do motor de IA, disparada pelo fluxo de triagem e entrevista.",
  "variables": [
   "candidate_name",
   "job_title",
   "privacy_line"
  ],
  "body": "Olá {{candidate_name}}, tudo bem?\nEstamos fazendo uma triagem inicial para a vaga de {{job_title}}.\nGostaríamos de confirmar seu interesse e seguir com algumas perguntas conduzidas pela LIA, nossa assistente de recrutamento com inteligência artificial (IA). Esta conversa é processada via Twilio (sub-processador de dados — LGPD). {{privacy_line}}Responda 'NÃO' se não deseja participar.\nVocê pode responder agora?",
  "note": "Texto vive hoje no catálogo Python do motor de IA.",
  "hasText": false,
  "defaultSubject": "",
  "defaultBody": "Olá {{candidate_name}}, tudo bem?\nEstamos fazendo uma triagem inicial para a vaga de {{job_title}}.\nGostaríamos de confirmar seu interesse e seguir com algumas perguntas conduzidas pela LIA, nossa assistente de recrutamento com inteligência artificial (IA). Esta conversa é processada via Twilio (sub-processador de dados — LGPD). {{privacy_line}}Responda 'NÃO' se não deseja participar.\nVocê pode responder agora?",
  "customized": false,
  "customizedBy": null,
  "customizedAt": null,
  "otherClients": []
 },
 {
  "key": "screening_start",
  "name": "Início da triagem",
  "channel": "whatsapp",
  "category": "motor de IA",
  "audience": "candidato",
  "status": "active",
  "source": "ai-engine app/templates/communication_templates.py#WhatsAppTemplates.screening_start",
  "subject": "",
  "trigger": "Automação do motor de IA, disparada pelo fluxo de triagem e entrevista.",
  "variables": [
   "candidate_name",
   "job_title"
  ],
  "body": "Ótimo, {{candidate_name}}! Vamos começar.\n\nEsta triagem é para a posição de *{{job_title}}*.\n\nVou fazer algumas perguntas sobre sua experiência e competências. Você pode responder por texto ou áudio.\n\nPronto(a) para começar?",
  "note": "Texto vive hoje no catálogo Python do motor de IA.",
  "hasText": false,
  "defaultSubject": "",
  "defaultBody": "Ótimo, {{candidate_name}}! Vamos começar.\n\nEsta triagem é para a posição de *{{job_title}}*.\n\nVou fazer algumas perguntas sobre sua experiência e competências. Você pode responder por texto ou áudio.\n\nPronto(a) para começar?",
  "customized": false,
  "customizedBy": null,
  "customizedAt": null,
  "otherClients": []
 },
 {
  "key": "screening_reminder",
  "name": "Lembrete de triagem pendente",
  "channel": "whatsapp",
  "category": "motor de IA",
  "audience": "candidato",
  "status": "active",
  "source": "ai-engine app/templates/communication_templates.py#WhatsAppTemplates.screening_reminder",
  "subject": "",
  "trigger": "Automação do motor de IA, disparada pelo fluxo de triagem e entrevista.",
  "variables": [
   "candidate_name",
   "hours_remaining"
  ],
  "body": "Oi {{candidate_name}}! 👋\n\nVi que nossa conversa ficou pausada. Você ainda tem *{{hours_remaining}}h* para completar a triagem.\n\nPosso continuar de onde paramos quando estiver disponível. É só me chamar!",
  "note": "Texto vive hoje no catálogo Python do motor de IA.",
  "hasText": false,
  "defaultSubject": "",
  "defaultBody": "Oi {{candidate_name}}! 👋\n\nVi que nossa conversa ficou pausada. Você ainda tem *{{hours_remaining}}h* para completar a triagem.\n\nPosso continuar de onde paramos quando estiver disponível. É só me chamar!",
  "customized": false,
  "customizedBy": null,
  "customizedAt": null,
  "otherClients": []
 },
 {
  "key": "screening_passed",
  "name": "Triagem aprovada",
  "channel": "whatsapp",
  "category": "motor de IA",
  "audience": "candidato",
  "status": "active",
  "source": "ai-engine app/templates/communication_templates.py#WhatsAppTemplates.screening_passed",
  "subject": "",
  "trigger": "Automação do motor de IA, disparada pelo fluxo de triagem e entrevista.",
  "variables": [
   "candidate_name",
   "strengths_text"
  ],
  "body": "Parabéns, {{candidate_name}}! 🎉\n\nVocê foi aprovado(a) na triagem!\n\n*Seus pontos fortes:*\n{{strengths_text}}\n\nVou conversar com o recrutador sobre seu perfil e em breve retorno com informações sobre a próxima etapa.\n\nQualquer dúvida, é só me chamar!\n\nTime de Atração de Talentos do iFood",
  "note": "Texto vive hoje no catálogo Python do motor de IA.",
  "hasText": false,
  "defaultSubject": "",
  "defaultBody": "Parabéns, {{candidate_name}}! 🎉\n\nVocê foi aprovado(a) na triagem!\n\n*Seus pontos fortes:*\n{{strengths_text}}\n\nVou conversar com o recrutador sobre seu perfil e em breve retorno com informações sobre a próxima etapa.\n\nQualquer dúvida, é só me chamar!",
  "customized": true,
  "customizedBy": "Rodrigo Alfieri",
  "customizedAt": "16/06/2026",
  "otherClients": [
   "Sodexo"
  ]
 },
 {
  "key": "screening_failed",
  "name": "Triagem reprovada",
  "channel": "whatsapp",
  "category": "motor de IA",
  "audience": "candidato",
  "status": "active",
  "source": "ai-engine app/templates/communication_templates.py#WhatsAppTemplates.screening_failed",
  "subject": "",
  "trigger": "Automação do motor de IA, disparada pelo fluxo de triagem e entrevista.",
  "variables": [
   "candidate_name",
   "development_text",
   "strengths_text"
  ],
  "body": "Olá {{candidate_name}},\n\nObrigada por participar da triagem! Foi muito bom conversar com você.\n\n*Pontos fortes:*\n{{strengths_text}}\n\n*Áreas para desenvolvimento:*\n{{development_text}}\n\nPara esta posição específica, seguiremos com outros candidatos. Mas seu perfil fica em nosso banco e te aviso sobre outras oportunidades!\n\nSucesso! 🍀",
  "note": "Texto vive hoje no catálogo Python do motor de IA.",
  "hasText": false,
  "defaultSubject": "",
  "defaultBody": "Olá {{candidate_name}},\n\nObrigada por participar da triagem! Foi muito bom conversar com você.\n\n*Pontos fortes:*\n{{strengths_text}}\n\n*Áreas para desenvolvimento:*\n{{development_text}}\n\nPara esta posição específica, seguiremos com outros candidatos. Mas seu perfil fica em nosso banco e te aviso sobre outras oportunidades!\n\nSucesso! 🍀",
  "customized": false,
  "customizedBy": null,
  "customizedAt": null,
  "otherClients": [
   "Grupo Boticário"
  ]
 },
 {
  "key": "interview_scheduled",
  "name": "Entrevista agendada",
  "channel": "whatsapp",
  "category": "motor de IA",
  "audience": "candidato",
  "status": "active",
  "source": "ai-engine app/templates/communication_templates.py#WhatsAppTemplates.interview_scheduled",
  "subject": "",
  "trigger": "Automação do motor de IA, disparada pelo fluxo de triagem e entrevista.",
  "variables": [
   "candidate_name",
   "date_formatted",
   "interview_link"
  ],
  "body": "Oi {{candidate_name}}! 📅\n\nSua entrevista está agendada:\n\n*Data:* {{date_formatted}}\n*Link:* {{interview_link}}\n\nVou te lembrar no dia, tá?\n\nBoa sorte! 🍀",
  "note": "Texto vive hoje no catálogo Python do motor de IA.",
  "hasText": false,
  "defaultSubject": "",
  "defaultBody": "Oi {{candidate_name}}! 📅\n\nSua entrevista está agendada:\n\n*Data:* {{date_formatted}}\n*Link:* {{interview_link}}\n\nVou te lembrar no dia, tá?\n\nBoa sorte! 🍀",
  "customized": false,
  "customizedBy": null,
  "customizedAt": null,
  "otherClients": [
   "Sodexo"
  ]
 },
 {
  "key": "interview_reminder",
  "name": "Lembrete de entrevista",
  "channel": "whatsapp",
  "category": "motor de IA",
  "audience": "candidato",
  "status": "active",
  "source": "ai-engine app/templates/communication_templates.py#WhatsAppTemplates.interview_reminder",
  "subject": "",
  "trigger": "Automação do motor de IA, disparada pelo fluxo de triagem e entrevista.",
  "variables": [
   "candidate_name",
   "interview_link",
   "time_formatted"
  ],
  "body": "Oi {{candidate_name}}! 👋\n\nLembrete: sua entrevista é *hoje às {{time_formatted}}*!\n\n*Link:* {{interview_link}}\n\nDicas rápidas:\n✅ Teste áudio e vídeo\n✅ Ambiente tranquilo\n✅ Tenha seu currículo à mão\n\nBoa sorte! 🍀",
  "note": "Texto vive hoje no catálogo Python do motor de IA.",
  "hasText": false,
  "defaultSubject": "",
  "defaultBody": "Oi {{candidate_name}}! 👋\n\nLembrete: sua entrevista é *hoje às {{time_formatted}}*!\n\n*Link:* {{interview_link}}\n\nDicas rápidas:\n✅ Teste áudio e vídeo\n✅ Ambiente tranquilo\n✅ Tenha seu currículo à mão\n\nBoa sorte! 🍀",
  "customized": false,
  "customizedBy": null,
  "customizedAt": null,
  "otherClients": []
 },
 {
  "key": "rejection_feedback",
  "name": "Feedback de reprovação",
  "channel": "whatsapp",
  "category": "motor de IA",
  "audience": "candidato",
  "status": "active",
  "source": "ai-engine app/templates/communication_templates.py#WhatsAppTemplates.rejection_feedback",
  "subject": "",
  "trigger": "Automação do motor de IA, disparada pelo fluxo de triagem e entrevista.",
  "variables": [
   "candidate_name",
   "feedback"
  ],
  "body": "Olá {{candidate_name}},\n\n{{feedback}}\n\nSeu perfil fica em nosso banco de talentos. Te aviso sobre novas oportunidades!\n\nSucesso na sua jornada! 🍀",
  "note": "Texto vive hoje no catálogo Python do motor de IA.",
  "hasText": false,
  "defaultSubject": "",
  "defaultBody": "Olá {{candidate_name}},\n\n{{feedback}}\n\nSeu perfil fica em nosso banco de talentos. Te aviso sobre novas oportunidades!\n\nSucesso na sua jornada! 🍀",
  "customized": false,
  "customizedBy": null,
  "customizedAt": null,
  "otherClients": [
   "Mappit"
  ]
 },
 {
  "key": "process_closed",
  "name": "Processo encerrado",
  "channel": "whatsapp",
  "category": "motor de IA",
  "audience": "candidato",
  "status": "active",
  "source": "ai-engine app/templates/communication_templates.py#WhatsAppTemplates.process_closed",
  "subject": "",
  "trigger": "Automação do motor de IA, disparada pelo fluxo de triagem e entrevista.",
  "variables": [
   "candidate_name",
   "job_title"
  ],
  "body": "Olá {{candidate_name}}! 👋\n\nA posição de *{{job_title}}* foi preenchida.\n\nAgradeço seu interesse! Seu perfil fica em nosso banco e te aviso sobre novas oportunidades.\n\nSucesso! 🍀",
  "note": "Texto vive hoje no catálogo Python do motor de IA.",
  "hasText": false,
  "defaultSubject": "",
  "defaultBody": "Olá {{candidate_name}}! 👋\n\nA posição de *{{job_title}}* foi preenchida.\n\nAgradeço seu interesse! Seu perfil fica em nosso banco e te aviso sobre novas oportunidades.\n\nSucesso! 🍀",
  "customized": false,
  "customizedBy": null,
  "customizedAt": null,
  "otherClients": []
 },
 {
  "key": "interview_reminder_urgent",
  "name": "Lembrete urgente de entrevista",
  "channel": "whatsapp",
  "category": "motor de IA",
  "audience": "candidato",
  "status": "active",
  "source": "ai-engine app/templates/communication_templates.py#WhatsAppTemplates.interview_reminder_urgent",
  "subject": "",
  "trigger": "Automação do motor de IA, disparada pelo fluxo de triagem e entrevista.",
  "variables": [
   "candidate_name",
   "interview_link",
   "job_info",
   "time_formatted"
  ],
  "body": "⏰ {{candidate_name}}, sua entrevista{{job_info}} começa em *1 hora*!\n\n*Horário:* {{time_formatted}}\n*Link:* {{interview_link}}\n\nÚltimas dicas:\n✅ Verifique conexão de internet\n✅ Teste câmera e microfone agora\n✅ Tenha água por perto\n\nTe desejo muito sucesso! 🍀\n\nTime de Atração de Talentos do iFood",
  "note": "Texto vive hoje no catálogo Python do motor de IA.",
  "hasText": false,
  "defaultSubject": "",
  "defaultBody": "⏰ {{candidate_name}}, sua entrevista{{job_info}} começa em *1 hora*!\n\n*Horário:* {{time_formatted}}\n*Link:* {{interview_link}}\n\nÚltimas dicas:\n✅ Verifique conexão de internet\n✅ Teste câmera e microfone agora\n✅ Tenha água por perto\n\nTe desejo muito sucesso! 🍀",
  "customized": true,
  "customizedBy": "Paulo Moraes",
  "customizedAt": "05/09/2026",
  "otherClients": [
   "Sodexo"
  ]
 },
 {
  "key": "offer_deadline_reminder",
  "name": "Lembrete de prazo da proposta",
  "channel": "whatsapp",
  "category": "motor de IA",
  "audience": "candidato",
  "status": "active",
  "source": "ai-engine app/templates/communication_templates.py#WhatsAppTemplates.offer_deadline_reminder",
  "subject": "",
  "trigger": "Automação do motor de IA, disparada pelo fluxo de triagem e entrevista.",
  "variables": [
   "candidate_name",
   "deadline",
   "hours_remaining",
   "job_title",
   "link_section",
   "urgency"
  ],
  "body": "{{urgency}} Oi {{candidate_name}}!\n\nLembrete: sua proposta para *{{job_title}}* expira em *{{hours_remaining}}h* ({{deadline}}).\n\nPrecisa de mais tempo ou tem alguma dúvida? Me avisa que posso ajudar!\n{{link_section}}\nAguardo seu retorno! 😊",
  "note": "Texto vive hoje no catálogo Python do motor de IA.",
  "hasText": false,
  "defaultSubject": "",
  "defaultBody": "{{urgency}} Oi {{candidate_name}}!\n\nLembrete: sua proposta para *{{job_title}}* expira em *{{hours_remaining}}h* ({{deadline}}).\n\nPrecisa de mais tempo ou tem alguma dúvida? Me avisa que posso ajudar!\n{{link_section}}\nAguardo seu retorno! 😊",
  "customized": false,
  "customizedBy": null,
  "customizedAt": null,
  "otherClients": [
   "Mappit",
   "Talenses"
  ]
 },
 {
  "key": "follow_up",
  "name": "Acompanhamento de candidato inativo",
  "channel": "whatsapp",
  "category": "motor de IA",
  "audience": "candidato",
  "status": "active",
  "source": "ai-engine app/templates/communication_templates.py#WhatsAppTemplates.follow_up",
  "subject": "",
  "trigger": "Automação do motor de IA, disparada pelo fluxo de triagem e entrevista.",
  "variables": [
   "candidate_name",
   "days_inactive",
   "job_title"
  ],
  "body": "Oi {{candidate_name}}! 👋\n\nVi que sua triagem para *{{job_title}}* ficou pausada há {{days_inactive}} dias.\n\nPosso te ajudar a continuar? É só me chamar!\n\nAguardo seu retorno 😊",
  "note": "Texto vive hoje no catálogo Python do motor de IA.",
  "hasText": false,
  "defaultSubject": "",
  "defaultBody": "Oi {{candidate_name}}! 👋\n\nVi que sua triagem para *{{job_title}}* ficou pausada há {{days_inactive}} dias.\n\nPosso te ajudar a continuar? É só me chamar!\n\nAguardo seu retorno 😊",
  "customized": false,
  "customizedBy": null,
  "customizedAt": null,
  "otherClients": []
 },
 {
  "key": "no_show_first",
  "name": "Primeiro aviso de não comparecimento",
  "channel": "whatsapp",
  "category": "motor de IA",
  "audience": "candidato",
  "status": "active",
  "source": "ai-engine app/templates/communication_templates.py#WhatsAppTemplates.no_show_first",
  "subject": "",
  "trigger": "Automação do motor de IA, disparada pelo fluxo de triagem e entrevista.",
  "variables": [
   "candidate_name",
   "date_formatted",
   "job_title",
   "link_section"
  ],
  "body": "Oi {{candidate_name}}! 👋\n\nSentimos sua falta na entrevista de hoje ({{date_formatted}}) para *{{job_title}}*.\n\nImprevistos acontecem! Podemos reagendar para outro horário que funcione melhor para você?\n{{link_section}}\nMe avisa sua disponibilidade que eu ajudo a remarcar! 😊",
  "note": "Texto vive hoje no catálogo Python do motor de IA.",
  "hasText": false,
  "defaultSubject": "",
  "defaultBody": "Oi {{candidate_name}}! 👋\n\nSentimos sua falta na entrevista de hoje ({{date_formatted}}) para *{{job_title}}*.\n\nImprevistos acontecem! Podemos reagendar para outro horário que funcione melhor para você?\n{{link_section}}\nMe avisa sua disponibilidade que eu ajudo a remarcar! 😊",
  "customized": false,
  "customizedBy": null,
  "customizedAt": null,
  "otherClients": []
 },
 {
  "key": "no_show_final",
  "name": "Aviso final de não comparecimento",
  "channel": "whatsapp",
  "category": "motor de IA",
  "audience": "candidato",
  "status": "active",
  "source": "ai-engine app/templates/communication_templates.py#WhatsAppTemplates.no_show_final",
  "subject": "",
  "trigger": "Automação do motor de IA, disparada pelo fluxo de triagem e entrevista.",
  "variables": [
   "candidate_name",
   "job_title",
   "no_show_count"
  ],
  "body": "Oi {{candidate_name}},\n\nInfelizmente você não compareceu às entrevistas agendadas para *{{job_title}}* ({{no_show_count}} ausências).\n\nCaso ainda tenha interesse, por favor entre em contato conosco nas próximas *48 horas*.\n\nSe não conseguir, seu processo será encerrado. Desejamos sucesso na sua jornada! 🍀",
  "note": "Texto vive hoje no catálogo Python do motor de IA.",
  "hasText": false,
  "defaultSubject": "",
  "defaultBody": "Oi {{candidate_name}},\n\nInfelizmente você não compareceu às entrevistas agendadas para *{{job_title}}* ({{no_show_count}} ausências).\n\nCaso ainda tenha interesse, por favor entre em contato conosco nas próximas *48 horas*.\n\nSe não conseguir, seu processo será encerrado. Desejamos sucesso na sua jornada! 🍀",
  "customized": false,
  "customizedBy": null,
  "customizedAt": null,
  "otherClients": [
   "Localiza"
  ]
 },
 {
  "key": "job_paused",
  "name": "Vaga pausada",
  "channel": "whatsapp",
  "category": "motor de IA",
  "audience": "candidato",
  "status": "active",
  "source": "ai-engine app/templates/communication_templates.py#WhatsAppTemplates.job_paused",
  "subject": "",
  "trigger": "Automação do motor de IA, disparada pelo fluxo de triagem e entrevista.",
  "variables": [
   "candidate_name",
   "job_title"
  ],
  "body": "Olá {{candidate_name}}! 👋\n\nInformamos que o processo para *{{job_title}}* está temporariamente pausado. Não se preocupe, isso não tem relação com seu desempenho.\n\nAssim que tivermos novidades, entraremos em contato. Seu perfil continua sendo considerado.\n\nAgradecemos sua paciência! 🙏\n\nTime de Atração de Talentos do iFood",
  "note": "Texto vive hoje no catálogo Python do motor de IA.",
  "hasText": false,
  "defaultSubject": "",
  "defaultBody": "Olá {{candidate_name}}! 👋\n\nInformamos que o processo para *{{job_title}}* está temporariamente pausado. Não se preocupe, isso não tem relação com seu desempenho.\n\nAssim que tivermos novidades, entraremos em contato. Seu perfil continua sendo considerado.\n\nAgradecemos sua paciência! 🙏",
  "customized": true,
  "customizedBy": "Paulo Moraes",
  "customizedAt": "05/09/2026",
  "otherClients": [
   "Localiza"
  ]
 },
 {
  "key": "job_reactivated",
  "name": "Vaga retomada",
  "channel": "whatsapp",
  "category": "motor de IA",
  "audience": "candidato",
  "status": "active",
  "source": "ai-engine app/templates/communication_templates.py#WhatsAppTemplates.job_reactivated",
  "subject": "",
  "trigger": "Automação do motor de IA, disparada pelo fluxo de triagem e entrevista.",
  "variables": [
   "candidate_name",
   "job_title"
  ],
  "body": "Oi {{candidate_name}}! 🎉\n\nBoas notícias! O processo para *{{job_title}}* foi reativado e você continua sendo considerado(a)!\n\nCaso tenha mudanças na sua disponibilidade, é só me avisar.\n\nObrigado pela paciência! 😊",
  "note": "Texto vive hoje no catálogo Python do motor de IA.",
  "hasText": false,
  "defaultSubject": "",
  "defaultBody": "Oi {{candidate_name}}! 🎉\n\nBoas notícias! O processo para *{{job_title}}* foi reativado e você continua sendo considerado(a)!\n\nCaso tenha mudanças na sua disponibilidade, é só me avisar.\n\nObrigado pela paciência! 😊",
  "customized": false,
  "customizedBy": null,
  "customizedAt": null,
  "otherClients": [
   "Mappit"
  ]
 },
 {
  "key": "job_cancelled",
  "name": "Vaga cancelada",
  "channel": "whatsapp",
  "category": "motor de IA",
  "audience": "candidato",
  "status": "active",
  "source": "ai-engine app/templates/communication_templates.py#WhatsAppTemplates.job_cancelled",
  "subject": "",
  "trigger": "Automação do motor de IA, disparada pelo fluxo de triagem e entrevista.",
  "variables": [
   "candidate_name",
   "job_title"
  ],
  "body": "Olá {{candidate_name}}! 👋\n\nInformamos que o processo para *{{job_title}}* foi encerrado. Essa decisão não tem relação com seu desempenho.\n\nSeu perfil permanece em nosso banco de talentos e entraremos em contato sobre novas oportunidades.\n\nDesejamos sucesso! 🍀",
  "note": "Texto vive hoje no catálogo Python do motor de IA.",
  "hasText": false,
  "defaultSubject": "",
  "defaultBody": "Olá {{candidate_name}}! 👋\n\nInformamos que o processo para *{{job_title}}* foi encerrado. Essa decisão não tem relação com seu desempenho.\n\nSeu perfil permanece em nosso banco de talentos e entraremos em contato sobre novas oportunidades.\n\nDesejamos sucesso! 🍀",
  "customized": false,
  "customizedBy": null,
  "customizedAt": null,
  "otherClients": []
 }
];

const CATALOGO_MORTOS = [
 {
  "source": "ats-api app/mailers/evaluation_mailer.rb#invitation",
  "reason": "Substituido pelo unified_invitation. O texto continua no codigo e nao e enviado."
 },
 {
  "source": "ats-api app/mailers/evaluation_mailer.rb#microsoft_invitation",
  "reason": "Mesma substituicao."
 },
 {
  "source": "ats-api app/mailers/interview_session_mailer.rb#invite",
  "reason": "Assunto Voice Interview Invitation, em ingles, sem nenhum ponto de disparo."
 },
 {
  "source": "ats-api app/mailers/interview_session_mailer.rb#completed",
  "reason": "Assunto Interview Completed, em ingles, sem nenhum ponto de disparo."
 },
 {
  "source": "ats-api app/mailers/test_mailer.rb#hello_email",
  "reason": "Diagnostico do Mailgun, roda so por comando manual."
 }
];
