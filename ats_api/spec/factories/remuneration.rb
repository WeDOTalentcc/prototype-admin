FactoryBot.define do
  factory :remuneration do
    name { "Base Salary" }
    description { "Full time" }
    account
    user { nil }
  end
end
