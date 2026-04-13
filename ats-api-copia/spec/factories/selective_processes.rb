FactoryBot.define do
  factory :selective_process do
    name { Faker::Job.title }
    position { Faker::Number.between(from: 1, to: 10) }
    status { Faker::Number.between(from: 0, to: 3) }
    uid { SecureRandom.uuid }
    sub_status { [ Faker::Lorem.word, Faker::Lorem.word ] }
    association :job
    account_id { create(:account).id }
  end
end
