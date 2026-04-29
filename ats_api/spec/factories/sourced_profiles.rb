# frozen_string_literal: true

FactoryBot.define do
  factory :sourced_profile do
    association :account
    sourcing { nil }
    candidate { nil }

    sequence(:uid) { |n| "sourced_profile_#{n}" }
    sequence(:external_id) { |n| "ext_#{n}" }
    provider { 'pearch' }
    status { 'new' }
    name { Faker::Name.name }
    is_deleted { false }

    trait :with_candidate do
      association :candidate
    end

    trait :with_sourcing do
      association :sourcing
    end

    trait :viewed do
      status { 'viewed' }
    end

    trait :interested do
      status { 'interested' }
    end

    trait :with_rating do
      rating { rand(1..5) }
    end
  end
end
