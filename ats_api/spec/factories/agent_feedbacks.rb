# frozen_string_literal: true

FactoryBot.define do
  factory :agent_feedback do
    association :background_agent
    association :agent_cycle
    association :sourced_profile_sourcing

    action { "approved" }
    reason { nil }

    trait :approved do
      action { "approved" }
    end

    trait :rejected do
      action { "rejected" }
      reason { Faker::Lorem.sentence }
    end
  end
end
