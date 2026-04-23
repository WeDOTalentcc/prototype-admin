FactoryBot.define do
  factory :institution do
    name { Faker::University.name }
    approved { false }
    reference_type { nil }
    reference_id { nil }
    # Note: This sets a default account_id. You'll likely override this in tests.
    account_id { [ create(:account).id ] }
  end
end
