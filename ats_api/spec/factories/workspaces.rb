FactoryBot.define do
  factory :workspace do
    name { Faker::Lorem.words(number: 2).join(' ').titleize }
    association :user
    association :account
    is_deleted { false }
    last_message_date { nil }

    trait :deleted do
      is_deleted { true }
    end

    trait :with_messages do
      after(:create) do |workspace|
        create_list(:message, 3, workspace: workspace, reference: workspace.user)
        workspace.update!(last_message_date: Time.current)
      end
    end
  end
end
