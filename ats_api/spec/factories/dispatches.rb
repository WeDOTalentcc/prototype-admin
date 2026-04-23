FactoryBot.define do
  factory :dispatch do
    user
    account { user.account }
    channel_type { 'email' }
    status { :pending }
    name { "Dispatch #{SecureRandom.hex(4)}" }
    scheduled_for { nil }

    trait :with_job_reference do
      association :reference, factory: :job
    end

    trait :with_candidate_reference do
      association :reference, factory: :candidate
    end
  end
end
