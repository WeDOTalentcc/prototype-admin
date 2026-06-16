# frozen_string_literal: true

FactoryBot.define do
  factory :education do
    study_here { false }
    start_date { Faker::Date.backward(days: 1000) }
    end_date { Faker::Date.backward(days: 100) }
    formation_type { 1 }

    association :candidate
    association :account
    association :institution
    association :study_area
    association :city
  end
end
