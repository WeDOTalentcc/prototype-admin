# frozen_string_literal: true

FactoryBot.define do
  factory :embedding do
    association :reference, factory: :candidate

    embedding { Array.new(768) { rand(-1.0..1.0) } }

    trait :for_candidate do
      association :reference, factory: :candidate
    end

    trait :for_job do
      association :reference, factory: :job
    end

    trait :high_quality do
      # Embedding com valores mais distintos (simulando boa qualidade)
      embedding { Array.new(768) { rand(-0.8..0.8) } }
    end
  end
end
