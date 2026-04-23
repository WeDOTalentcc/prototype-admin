# frozen_string_literal: true

FactoryBot.define do
  factory :agent_notification do
    association :user
    notification_type { "alert_aging" }
    channel { "web" }
    status { "pending" }
    content { "Test notification content" }
    alert_key { "aging:apply:#{SecureRandom.hex(4)}:#{Date.current}" }

    trait :sent do
      status { "sent" }
      sent_at { Time.current }
    end

    trait :read do
      status { "read" }
      sent_at { 1.hour.ago }
      read_at { Time.current }
    end

    trait :failed do
      status { "failed" }
    end

    trait :briefing do
      notification_type { "briefing" }
    end

    trait :alert_deadline do
      notification_type { "alert_deadline" }
    end

    trait :via_whatsapp do
      channel { "whatsapp" }
    end

    trait :via_teams do
      channel { "teams" }
    end
  end
end
