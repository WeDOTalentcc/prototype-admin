# frozen_string_literal: true

FactoryBot.define do
  factory :llm_quota do
    association :account
    plan { "starter" }
    monthly_cost_limit_usd { 5.0 }
    monthly_request_limit { 5_000 }
    burst_rpm { 20 }
    extra_budget_usd { 0.0 }
    extra_budget_expires_at { nil }
    enabled { true }
    notify_at_percentage { 80 }
    hard_limit { true }
    metadata { {} }

    before(:create) do |quota|
      LlmQuota.where(account_id: quota.account_id).delete_all
    end

    trait :pro do
      plan { "pro" }
      monthly_cost_limit_usd { 25.0 }
      monthly_request_limit { 25_000 }
      burst_rpm { 50 }
    end

    trait :enterprise do
      plan { "enterprise" }
      monthly_cost_limit_usd { 100.0 }
      monthly_request_limit { 100_000 }
      burst_rpm { 100 }
    end

    trait :disabled do
      enabled { false }
    end

    trait :soft_limit do
      hard_limit { false }
    end

    trait :with_extra_budget do
      extra_budget_usd { 10.0 }
      extra_budget_expires_at { 30.days.from_now }
    end

    trait :with_expired_extra do
      extra_budget_usd { 10.0 }
      extra_budget_expires_at { 1.day.ago }
    end
  end
end
