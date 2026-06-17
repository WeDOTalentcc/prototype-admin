# frozen_string_literal: true

FactoryBot.define do
  factory :agent_cycle do
    association :background_agent
    association :sourcing

    sequence(:cycle_number) { |n| n }
    status { "running" }
    candidates_delivered { 0 }
    candidates_total_found { 0 }

    trait :delivered do
      status { "delivered" }
      candidates_delivered { 10 }
      candidates_total_found { 50 }
      delivered_at { Time.current }
      expires_at { 48.hours.from_now }
    end

    trait :reviewed do
      status { "reviewed" }
      candidates_delivered { 10 }
      reviewed_at { Time.current }
    end

    trait :expired do
      status { "delivered" }
      delivered_at { 3.days.ago }
      expires_at { 1.day.ago }
    end

    trait :cancelled do
      status { "cancelled" }
    end
  end
end
