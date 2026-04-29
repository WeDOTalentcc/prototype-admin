FactoryBot.define do
  factory :evaluation_candidate do
    association :evaluation
    association :candidate
    association :account
    association :user
    association :job
    association :apply
    date_expiration { 2.days.from_now }
    date_view { 1.day.from_now }
    completed { false }
  end
end
