# frozen_string_literal: true

FactoryBot.define do
  factory :meeting do
    association :organizer, factory: :user
    account { organizer.account }
    subject { Faker::Lorem.sentence }
    provider { "microsoft_teams" }
    start_time { 1.hour.from_now }
    end_time { 2.hours.from_now }
    is_deleted { false }

    trait :completed do
      sub_status { "completed" }
      start_time { 2.days.ago }
      end_time { 2.days.ago + 1.hour }
    end

    trait :no_show do
      sub_status { "no_show" }
      start_time { 1.day.ago }
      end_time { 1.day.ago + 1.hour }
    end

    trait :scheduled do
      sub_status { "scheduled" }
    end

    trait :deleted do
      is_deleted { true }
    end
  end
end
