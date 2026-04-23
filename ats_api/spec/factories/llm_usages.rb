# frozen_string_literal: true

FactoryBot.define do
  factory :llm_usage do
    association :user
    association :account

    model { [ "gemini-2.5-flash", "gemini-1.5-pro", "gpt-4o", "text-embedding-3-small" ].sample }
    operation { [ "chat", "embedding" ].sample }
    input_tokens { rand(100..10000) }
    output_tokens { rand(50..5000) }
    total_tokens { input_tokens + output_tokens }
    cost_usd { rand(0.0001..0.5).round(8) }
    latency_ms { rand(100..3000).round(2) }
    success { true }
    error_message { nil }
    context { {} }

    trait :chat do
      operation { "chat" }
      model { "gemini-2.5-flash" }
      output_tokens { rand(500..2000) }
    end

    trait :embedding do
      operation { "embedding" }
      model { "gemini-embedding-001" }
      output_tokens { 0 }
    end

    trait :failed do
      success { false }
      error_message { "API rate limit exceeded" }
      cost_usd { 0.0 }
    end

    trait :expensive do
      model { "gemini-1.5-pro" }
      input_tokens { 50000 }
      output_tokens { 20000 }
      cost_usd { 1.25 }
    end

    trait :cheap do
      model { "gemini-2.5-flash" }
      input_tokens { 100 }
      output_tokens { 50 }
      cost_usd { 0.000015 }
    end

    trait :slow do
      latency_ms { 5000.0 }
    end

    trait :fast do
      latency_ms { 150.0 }
    end
  end
end
