FactoryBot.define do
  factory :job_journey do
    name { "Informações Básicas" }
    description { "Título, Confidencialidade, Área" }
    position { 1 }
    active { true }
    required { true }
    account
    job { nil }

    trait :inactive do
      active { false }
    end

    trait :optional do
      required { false }
    end

    trait :with_job do
      association :job
    end
  end
end
