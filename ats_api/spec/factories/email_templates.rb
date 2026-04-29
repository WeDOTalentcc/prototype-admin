# frozen_string_literal: true

FactoryBot.define do
  factory :email_template do
    name { Faker::Lorem.sentence(word_count: 3) }
    subject { Faker::Lorem.sentence(word_count: 5) }
    content { Faker::Lorem.paragraph(sentence_count: 3) }
    category_id { 1 }
    association :account
    association :user
    is_deleted { false }

    trait :deleted do
      is_deleted { true }
    end

    trait :approval do
      category_id { 1 }
      name { "Email de Aprovação" }
      subject { "Parabéns! Você foi aprovado" }
      content { "Olá {{candidato_nome}}, você foi aprovado para a vaga {{vaga}}." }
    end

    trait :rejection do
      category_id { 2 }
      name { "Email de Rejeição" }
      subject { "Resultado do processo seletivo" }
      content { "Olá {{candidato_nome}}, infelizmente você não foi selecionado para a vaga {{vaga}}." }
    end

    trait :scheduling do
      category_id { 3 }
      name { "Email de Agendamento" }
      subject { "Agendamento de entrevista" }
      content { "Olá {{candidato_nome}}, gostaríamos de agendar uma entrevista para a vaga {{vaga}}." }
    end

    trait :post_interview do
      category_id { 7 }
      name { "Agradecimento Pós-Entrevista" }
      subject { "Obrigado pela entrevista — {{job_title}}" }
      content { "Olá {{candidate_name}}, obrigado pela entrevista para {{job_title}} em {{interview_date}}! Resposta em {{response_deadline}}." }
      is_automated { true }
      trigger_event { "interview_ended" }
      delay_hours { 2 }
      response_deadline_days { 7 }
    end
  end
end
