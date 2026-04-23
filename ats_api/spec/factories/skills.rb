FactoryBot.define do
  factory :skill do
    sequence(:name) { |n| "#{Faker::Job.key_skill} #{n}" }
    account
    skill_category { nil }
    is_deleted { false }

    trait :with_category do
      association :skill_category
    end

    trait :deleted do
      is_deleted { true }
    end

    trait :programming_language do
      skill_category { create(:skill_category, :programming) }
    end

    trait :backend_framework do
      skill_category { create(:skill_category, :backend) }
    end

    trait :soft_skill do
      skill_category { create(:skill_category, :soft_skills) }
    end
  end
end
