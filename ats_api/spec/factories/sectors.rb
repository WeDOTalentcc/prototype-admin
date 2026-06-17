FactoryBot.define do
  factory :sector do
    sequence(:name) { |n| "Sector #{n}" }
    description { Faker::Lorem.sentence }
    icon { [ "🖥️", "💰", "🏥", "🛒", "🏭", "⚡", "🚚", "🎬", "🎓", "💼" ].sample }
    tags { [ "B2B", "B2C", "SaaS", "Cloud", "Tech" ].sample(2) }
    level { 0 }
    is_public { true }
    account_id { nil }
    is_deleted { false }
    parent_sector { nil }

    trait :with_parent do
      transient do
        parent { nil }
      end

      after(:build) do |sector, evaluator|
        sector.parent_sector = evaluator.parent || create(:sector, level: 0)
        sector.level = sector.parent_sector.level + 1
      end
    end

    trait :private do
      is_public { false }
      association :account
    end

    trait :with_children do
      after(:create) do |sector|
        create_list(:sector, 2, parent_sector: sector, level: sector.level + 1, is_public: sector.is_public, account_id: sector.account_id)
      end
    end

    trait :deleted do
      is_deleted { true }
    end

    trait :level_one do
      level { 1 }
      association :parent_sector, factory: :sector, level: 0
    end

    trait :level_two do
      level { 2 }
      association :parent_sector, factory: [ :sector, :level_one ]
    end
  end
end
