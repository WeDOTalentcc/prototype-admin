# frozen_string_literal: true

FactoryBot.define do
  factory :evaluation do
    name { Faker::Company.catch_phrase }
    job
    selective_process
    user
    account { user.account }
    status { true }
    position { Faker::Number.between(from: 0, to: 10) }
    sub_status { Faker::Lorem.word }
    description { Faker::Lorem.paragraph }
    is_main { false }
    time { 90 }
    uid { SecureRandom.uuid }
    is_chatbot { false }
    ai_enabled { false }
  end
end
