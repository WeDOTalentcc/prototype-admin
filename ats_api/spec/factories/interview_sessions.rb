# frozen_string_literal: true

FactoryBot.define do
  factory :interview_session do
    association :account
    association :evaluation
    association :candidate
    association :job
    association :created_by, factory: :user

    token { SecureRandom.uuid }
    status { "pending" }
    interview_type { "voice" }
    duration_minutes { 30 }
    language { "pt-BR" }
    expires_at { 7.days.from_now }
    questions_snapshot { [ { id: 1, title: "Tell me about yourself", description: nil, response_type: "open" } ] }
    job_context { { title: "Developer", description: "Rails developer" } }
    candidate_context { { name: "Test Candidate", email: "test@example.com" } }

    trait :active do
      status { "active" }
      started_at { Time.current }
    end

    trait :completed do
      status { "completed" }
      started_at { 1.hour.ago }
      completed_at { Time.current }
    end
  end
end
