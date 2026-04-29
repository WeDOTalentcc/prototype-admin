# frozen_string_literal: true

FactoryBot.define do
  factory :sourced_profile_sourcing do
    association :sourced_profile
    association :sourcing
    association :account
    association :user

    score { rand(50.0..100.0).round(2) }
    search_source { 'hybrid' }
    search_score { rand(50.0..100.0).round(2) }
    is_deleted { false }

    trait :high_score do
      score { rand(85.0..100.0).round(2) }
    end

    trait :low_score do
      score { rand(0.0..50.0).round(2) }
    end

    trait :deleted do
      is_deleted { true }
    end
  end
end
