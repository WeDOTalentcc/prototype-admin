FactoryBot.define do
  factory :scheduling_slot do
    association :scheduling_link
    start_time { 1.day.from_now.beginning_of_day + 9.hours }
    end_time { 1.day.from_now.beginning_of_day + 10.hours }
    is_available { true }

    trait :unavailable do
      is_available { false }
    end

    trait :past do
      start_time { 1.day.ago }
      end_time { 1.day.ago + 1.hour }
    end
  end
end
