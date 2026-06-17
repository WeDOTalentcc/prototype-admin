# frozen_string_literal: true

FactoryBot.define do
  factory :calendar_event do
    association :organizer, factory: :user
    account { organizer.account }
    title { Faker::Lorem.sentence }
    provider { "microsoft" }
    event_type { "interview" }
    importance { "normal" }
    start_time { 1.hour.from_now }
    end_time { 2.hours.from_now }
    is_deleted { false }
    is_cancelled { false }
    is_all_day { false }

    trait :interview do
      event_type { "interview" }
    end

    trait :completed do
      sub_status { "completed" }
      start_time { 2.days.ago }
      end_time { 2.days.ago + 1.hour }
    end

    trait :no_show do
      sub_status { "no_show" }
    end

    trait :cancelled do
      is_cancelled { true }
    end
  end
end
