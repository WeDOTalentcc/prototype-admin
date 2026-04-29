FactoryBot.define do
  factory :address_relationship do
    association :address
    association :account, factory: :account
    association :user, factory: :user # opcional, só será criado se você não passar nil

    reference_type { "TestType" }
    reference_id   { SecureRandom.random_number(1000) }
    is_deleted     { false }
  end
end
