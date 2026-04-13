FactoryBot.define do
  factory :account do
    name { Faker::Name.name }
    tenant { Faker::Name.name }
    staging_tenant { Faker::Name.name }
  end
end
