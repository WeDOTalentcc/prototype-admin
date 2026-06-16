FactoryBot.define do
  factory :password_reset_token do
    association :user
    association :account
    ip_address { "127.0.0.1" }
    expires_at { 1.hour.from_now }
    used_at { nil }

    trait :expired do
      expires_at { 1.hour.ago }
    end

    trait :used do
      used_at { Time.current }
    end

    trait :from_different_ip do
      ip_address { "192.168.1.100" }
    end
  end
end
