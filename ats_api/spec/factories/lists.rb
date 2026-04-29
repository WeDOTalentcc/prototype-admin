FactoryBot.define do
  factory :list do
    name { Faker::Lorem.words(number: 3).join(' ') }
    is_public { false }
    association :user
    association :account

    trait :public do
      is_public { true }
    end

    trait :with_candidates do
      after(:create) do |list|
        3.times do
          create(:list_relationship, list: list, reference: create(:candidate), account: list.account)
        end
      end
    end

    trait :with_jobs do
      after(:create) do |list|
        2.times do
          create(:list_relationship, list: list, reference: create(:job), account: list.account)
        end
      end
    end
  end
end
