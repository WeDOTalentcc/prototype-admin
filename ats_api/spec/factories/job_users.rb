# spec/factories/job_users.rb
FactoryBot.define do
  factory :job_user do
    transient do
      account { create(:account) }
    end

    user { create(:user, account: account) }
    job { create(:job, account: account, user: user) }
    account_id { account.id }

    person_function { Faker::Job.title }
    split { Faker::Number.between(from: 0, to: 100) }

    trait :with_zero_split do
      split { 0.0 }
    end

    trait :with_full_split do
      split { 100.0 }
    end

    trait :hiring_manager do
      person_function { "Hiring Manager" }
      split { 50.0 }
    end

    trait :recruiter_lead do
      person_function { "Recruiter Lead" }
      split { 30.0 }
    end
  end
end
