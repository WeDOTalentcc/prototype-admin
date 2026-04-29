# spec/factories/apply_statuses.rb
FactoryBot.define do
  factory :apply_status do
    association :apply
    association :selective_process
    association :user
    association :account, factory: :account

    status_id { Faker::Number.between(from: 1, to: 5) }
    status_name { Faker::Lorem.word }
    comment { Faker::Lorem.sentence }
    is_deleted { false }
  end
end
