# frozen_string_literal: true

FactoryBot.define do
  factory :sourcing do
    association :account
    association :user

    sequence(:uid) { |n| "sourcing_#{n}_#{SecureRandom.hex(8)}" }
    query { 'desenvolvedor ruby senior' }
    provider { 'pearch' }
    status { 'done' }
    is_deleted { false }
    searched_at { Time.current }
    results_count { 10 }
    parameters { {} }

    trait :processing do
      status { 'processing' }
    end

    trait :failed do
      status { 'failed' }
    end

    trait :deleted do
      is_deleted { true }
    end

    trait :with_results do
      results_count { 50 }
      total_estimate { 100 }
      local_results_count { 30 }
      global_results_count { 20 }
    end
  end
end
