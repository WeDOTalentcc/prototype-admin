FactoryBot.define do
  factory :remuneration_relationship do
    association :remuneration
    association :account
    user { create(:user, account: account) }

    reference_type { "Job" }
    reference_id { SecureRandom.random_number(1000) }

    currency { "BRL" }
    period { 1 }
    value { 5000.00 }
    amount { 1 }
    contract_type { [ "CLT" ] }
    comments { "Some comment" }
  end
end
