FactoryBot.define do
  factory :organizational_position do
    association :department
    account { department.account }
    title { "Position #{SecureRandom.hex(3)}" }
    level { 0 }
    is_active { true }
  end
end
