FactoryBot.define do
  factory :message do
    association :account
    association :reference, factory: :user

    content { Faker::Lorem.paragraph }
    entity { 0 }
    status { 0 }
    is_deleted { false }
  end
end
