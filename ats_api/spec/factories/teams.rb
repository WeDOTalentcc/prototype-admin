FactoryBot.define do
  factory :team do
    association :department
    account { department.account }
    name { "Team #{SecureRandom.hex(3)}" }
    description { "Team #{name}" }
    member_count { 0 }
    is_active { true }
  end
end
