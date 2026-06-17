FactoryBot.define do
  factory :list_relationship do
    association :list
    association :account
    association :reference, factory: :candidate
    position { 0 }
    is_deleted { false }

    trait :with_job do
      association :reference, factory: :job
    end

    trait :with_apply do
      association :reference, factory: :apply
    end

    trait :with_comments do
      general_comments { Faker::Lorem.paragraph }
    end

    trait :with_score do
      score { rand(1..10) }
    end

    trait :deleted do
      is_deleted { true }
    end
  end
end
