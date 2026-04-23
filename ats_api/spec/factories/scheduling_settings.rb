FactoryBot.define do
  factory :scheduling_setting do
    association :user
    association :account
    timezone { "America/Sao_Paulo" }
    work_hours_start { "09:00" }
    work_hours_end { "18:00" }
    default_duration_minutes { 60 }
    buffer_minutes { 15 }
    lookahead_days { 14 }
  end
end
