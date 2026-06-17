# frozen_string_literal: true

FactoryBot.define do
  factory :llm_configuration do
    association :account
    provider { "gemini" }
    api_key { "test-api-key-#{SecureRandom.hex(8)}" }
    active { true }
    metadata { {} }

    trait :openai do
      provider { "openai" }
    end

    trait :anthropic do
      provider { "anthropic" }
    end

    trait :inactive do
      active { false }
    end
  end
end
