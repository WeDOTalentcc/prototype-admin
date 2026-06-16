FactoryBot.define do
  factory :user do
    name { Faker::Name.name }
    email { Faker::Internet.unique.email }
    password { 'pass123' }
    association :account

    trait :without_account do
      account { nil }
    end

    transient do
      roles { [] }
    end

    after(:create) do |user, evaluator|
      evaluator.roles.each do |role_name|
        role = Role.find_or_create_by(name: role_name)
        user.roles << role
      end
    end

    trait :admin do
      after(:create) do |user|
        role = Role.find_or_create_by(name: 'admin')
        user.roles << role unless user.roles.include?(role)
      end
    end
  end
end
