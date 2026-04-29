FactoryBot.define do
  factory :role do
    sequence(:name) { |n| "role_#{n}" }
    description { "A description for the role." }

    trait :admin do
      name { 'admin' }
      description { 'Administrator role with broad permissions.' }
    end

    trait :super_admin do
      name { 'super_admin' }
      description { 'Super administrator with all permissions.' }
    end

    trait :regular_user do
      name { 'user' }
      description { 'Regular user with basic permissions.' }
    end
  end
end
