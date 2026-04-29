FactoryBot.define do
  factory :scheduling_link do
    association :account
    association :created_by, factory: :user
    token { SecureRandom.urlsafe_base64(32) }
    status { "active" }
    duration_minutes { 60 }
    subject { "Interview" }

    trait :booked do
      status { "booked" }
      booked_at { Time.current }
    end

    trait :expired do
      status { "expired" }
    end

    trait :cancelled do
      status { "cancelled" }
    end

    trait :with_expiry do
      expires_at { 7.days.from_now }
    end

    trait :with_slots do
      after(:create) do |link|
        3.times do |i|
          start_time = 1.day.from_now.beginning_of_day + 9.hours + (i * 90).minutes
          create(:scheduling_slot, scheduling_link: link, start_time: start_time, end_time: start_time + 60.minutes)
        end
      end
    end
  end
end
