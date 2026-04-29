FactoryBot.define do
  factory :answer do
    title { "Answer #{SecureRandom.hex(4)}" }
    description { "Some description" }
    detail { "Detail" }
    time { 30 }
    time_taken { 25 }
    comments_response { "Comment" }
    choices { [ "A", "B" ] }
    association :user
    account { user.account }

    trait :with_question do
      association :question
    end

    trait :with_evaluation do
      association :evaluation
    end

    trait :with_candidate do
      association :candidate
    end

    trait :with_job do
      association :job
    end

    trait :with_apply do
      association :apply
    end
  end
end
