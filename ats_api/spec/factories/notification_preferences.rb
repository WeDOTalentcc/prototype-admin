# frozen_string_literal: true

FactoryBot.define do
  factory :notification_preference do
    association :user
    briefing_enabled { true }
    briefing_time { "08:00" }
    briefing_channel { "web" }
    alert_aging_enabled { true }
    alert_deadline_enabled { true }
    alert_no_show_enabled { true }
    alert_evaluation_enabled { true }
    alert_strong_fit_enabled { true }
    alert_stale_job_enabled { true }
    aging_threshold_days { 3 }
    alert_channels { [ "web" ] }
    timezone { "America/Sao_Paulo" }
  end
end
