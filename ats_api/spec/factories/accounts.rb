FactoryBot.define do
  factory :account do
    name { Faker::Name.name }
    tenant { 'public' }
    setup_token { SecureRandom.hex(10) }
    setup_token_expires_at { 1.hour.from_now }
    staging_tenant { Faker::Name.name }
  end
end
