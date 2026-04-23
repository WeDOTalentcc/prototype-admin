# frozen_string_literal: true

FactoryBot.define do
  factory :shortlist do
    name { Faker::Lorem.words(number: 2).join(' ') }
    description { Faker::Lorem.sentence }
    is_deleted { false }

    association :account
    association :user, factory: :user

    trait :deleted do
      is_deleted { true }
    end
  end
end
