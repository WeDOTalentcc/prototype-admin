# frozen_string_literal: true

FactoryBot.define do
  factory :llm_quota_usage do
    association :account
    period { Date.current.strftime("%Y-%m") }
    total_cost_usd { 0.0 }
    total_requests { 0 }
    total_tokens { 0 }
    cost_by_model { {} }
    cost_by_operation { {} }
    last_synced_at { nil }

    trait :with_usage do
      total_cost_usd { 12.50 }
      total_requests { 500 }
      total_tokens { 1_500_000 }
      cost_by_model { { "gemini-2.5-flash" => 10.0, "gemini-embedding-001" => 2.5 } }
      cost_by_operation { { "search.query_analysis" => 5.0, "embeddings.encode" => 7.5 } }
    end
  end
end
