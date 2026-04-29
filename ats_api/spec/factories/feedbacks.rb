# frozen_string_literal: true

FactoryBot.define do
  factory :feedback do
    title { "Feedback técnico" }
    description { "O candidato demonstrou forte domínio técnico e boa comunicação." }
    name { "Recrutador João" }
    additional_text { "Possui potencial para liderar projetos no futuro." }
    is_deleted { false }

    association :account
    association :job
    association :selective_process
  end
end
