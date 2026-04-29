# frozen_string_literal: true

FactoryBot.define do
  factory :background_agent do
    association :user
    association :job
    account { user.account }

    name { "Sourcing #{Faker::Job.title}" }
    criteria_text { Faker::Lorem.paragraph }
    criteria_structured { {} }
    calibration_state { "pending" }
    mode { "review" }
    status { "active" }
    daily_limit { 25 }
    min_score_threshold { 70.0 }
    auto_pause_days { 4 }
    sources { ["local"] }
    total_delivered { 0 }
    total_approved { 0 }
    total_rejected { 0 }

    trait :calibrated do
      calibration_state { "calibrated" }
      total_approved { 10 }
      total_rejected { 3 }
      total_delivered { 13 }
    end

    trait :learning do
      calibration_state { "learning" }
      total_approved { 2 }
      total_rejected { 1 }
      total_delivered { 3 }
    end

    trait :paused do
      status { "paused" }
      paused_at { Time.current }
    end

    trait :stopped do
      status { "stopped" }
      stopped_at { Time.current }
    end

    trait :deleted do
      is_deleted { true }
    end

    trait :auto_add do
      mode { "auto_add" }
    end

    trait :ran_today do
      last_run_at { Time.current }
    end

    trait :stale_interaction do
      last_interaction_at { 10.days.ago }
    end
  end
end
