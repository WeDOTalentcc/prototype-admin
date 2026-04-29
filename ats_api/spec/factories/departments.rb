FactoryBot.define do
  factory :department do
    association :account
    name { "Dept #{SecureRandom.hex(4)}" }
    level { 0 }
    is_deleted { false }
  end
end
