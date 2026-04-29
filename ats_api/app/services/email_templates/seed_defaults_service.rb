# frozen_string_literal: true

module EmailTemplates
  class SeedDefaultsService
    TEMPLATES = [
      {
        name: "Aprovação - Próxima Etapa",
        subject: "Parabéns! Você avançou no processo seletivo - {{job_title}}",
        category_id: 1,
        content: <<~HTML
          <p>Olá {{candidate_name}},</p>
          <p>Temos uma ótima notícia! Você foi aprovado(a) na etapa atual do processo seletivo para a vaga de <strong>{{job_title}}</strong>.</p>
          <p>Em breve entraremos em contato com mais detalhes sobre a próxima etapa.</p>
          <p>Caso tenha alguma dúvida, fique à vontade para responder este e-mail.</p>
          <p>Atenciosamente,<br>{{user_name}}</p>
        HTML
      },
      {
        name: "Rejeição - Feedback Construtivo",
        subject: "Atualização sobre o processo seletivo - {{job_title}}",
        category_id: 2,
        content: <<~HTML
          <p>Olá {{candidate_name}},</p>
          <p>Agradecemos muito seu interesse e participação no processo seletivo para a vaga de <strong>{{job_title}}</strong>.</p>
          <p>Após cuidadosa avaliação, decidimos seguir com outros candidatos cujo perfil está mais alinhado com os requisitos específicos desta posição neste momento.</p>
          <p>Gostaríamos de manter seu currículo em nosso banco de talentos para futuras oportunidades que possam ser compatíveis com seu perfil.</p>
          <p>Desejamos sucesso em sua jornada profissional!</p>
          <p>Atenciosamente,<br>{{user_name}}</p>
        HTML
      },
      {
        name: "Agendamento - Entrevista",
        subject: "Agendamento de Entrevista - {{job_title}}",
        category_id: 3,
        content: <<~HTML
          <p>Olá {{candidate_name}},</p>
          <p>Gostaríamos de convidá-lo(a) para uma entrevista referente à vaga de <strong>{{job_title}}</strong>.</p>
          <p>Por favor, confirme sua disponibilidade respondendo este e-mail com os melhores horários para você.</p>
          <p>Detalhes da vaga:</p>
          <p>{{job_description}}</p>
          <p>Aguardamos seu retorno!</p>
          <p>Atenciosamente,<br>{{user_name}}</p>
        HTML
      },
      {
        name: "Follow-up - Retorno Pendente",
        subject: "Acompanhamento - Processo Seletivo {{job_title}}",
        category_id: 4,
        content: <<~HTML
          <p>Olá {{candidate_name}},</p>
          <p>Estamos entrando em contato para dar continuidade ao processo seletivo da vaga de <strong>{{job_title}}</strong>.</p>
          <p>Gostaríamos de saber se você ainda tem interesse na posição e se possui alguma dúvida sobre as próximas etapas.</p>
          <p>Ficamos no aguardo do seu retorno.</p>
          <p>Atenciosamente,<br>{{user_name}}</p>
        HTML
      },
      {
        name: "Feedback - Pós-Entrevista",
        subject: "Feedback da Entrevista - {{job_title}}",
        category_id: 5,
        content: <<~HTML
          <p>Olá {{candidate_name}},</p>
          <p>Gostaríamos de agradecer pela sua participação na entrevista para a vaga de <strong>{{job_title}}</strong>.</p>
          <p>Foi um prazer conhecer mais sobre sua trajetória profissional e suas experiências.</p>
          <p>Estamos finalizando as avaliações e retornaremos em breve com um posicionamento sobre os próximos passos.</p>
          <p>Caso tenha alguma dúvida, não hesite em nos contatar.</p>
          <p>Atenciosamente,<br>{{user_name}}</p>
        HTML
      },
      {
        name: "Contato Inicial - Apresentação de Vaga",
        subject: "Oportunidade Profissional - {{job_title}}",
        category_id: 6,
        content: <<~HTML
          <p>Olá {{candidate_name}},</p>
          <p>Encontramos seu perfil e acreditamos que ele pode ser um ótimo match para uma oportunidade que temos em aberto.</p>
          <p><strong>Vaga: {{job_title}}</strong></p>
          <p>{{job_description}}</p>
          <p>Caso tenha interesse, ficaremos felizes em conversar mais sobre esta oportunidade.</p>
          <p>Aguardamos seu retorno!</p>
          <p>Atenciosamente,<br>{{user_name}}</p>
        HTML
      },
      {
        name: "Agradecimento Pós-Entrevista",
        subject: "Obrigado pela entrevista — {{job_title}}",
        category_id: 7,
        is_automated: true,
        trigger_event: "interview_ended",
        delay_hours: 24,
        response_deadline_days: 7,
        content: <<~HTML
          <p>Olá {{candidate_name}},</p>
          <p>Obrigado por participar da entrevista para a vaga de <strong>{{job_title}}</strong> em {{interview_date}}!</p>
          <p>Foi um prazer conhecer você melhor. 🙂</p>
          <p><strong>Próximos passos:</strong></p>
          <ul>
            <li>Nosso time irá avaliar os candidatos finalistas</li>
            <li>Você receberá uma resposta em até {{response_deadline}}</li>
          </ul>
          <p>Enquanto isso, fique à vontade para nos enviar dúvidas.</p>
          <p>Atenciosamente,<br>{{user_name}}</p>
        HTML
      }
    ].freeze

    def initialize(account:)
      @account = account
    end

    def call
      user = find_default_user
      return if user.blank?

      templates_created = []

      TEMPLATES.each do |template_attrs|
        next if EmailTemplate.exists?(
          account_id: @account.id,
          name: template_attrs[:name]
        )

        template = EmailTemplate.create!(
          name: template_attrs[:name],
          subject: template_attrs[:subject],
          content: template_attrs[:content].strip,
          category_id: template_attrs[:category_id],
          account_id: @account.id,
          user_id: user.id,
          is_automated: template_attrs[:is_automated] || false,
          trigger_event: template_attrs[:trigger_event],
          delay_hours: template_attrs[:delay_hours],
          response_deadline_days: template_attrs[:response_deadline_days]
        )

        templates_created << template
      end

      Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      Rails.logger.info "✅ [EmailTemplates::SeedDefaultsService] Templates created: #{templates_created.size}"
      Rails.logger.info "   Account: #{@account.name} (ID: #{@account.id})"
      Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

      templates_created
    end

    private

    def find_default_user
      @account.users.order(:created_at).first
    end
  end
end
