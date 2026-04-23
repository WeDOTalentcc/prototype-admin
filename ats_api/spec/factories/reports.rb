# frozen_string_literal: true

FactoryBot.define do
  factory :report do
    name { Faker::Lorem.words(number: 2).join(' ') }
    is_deleted { false }
    is_main { true }
    description { Faker::Lorem.sentence }

    association :account
    association :user, factory: :user

    trait :deleted do
      is_deleted { true }
    end

    trait :not_main do
      is_main { false }
    end

    trait :performance_report do
      name { 'Performance Report' }
    end
  end
end
