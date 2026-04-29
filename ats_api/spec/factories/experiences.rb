FactoryBot.define do
  factory :experience do
    work_here { false }
    start_date { 2.years.ago }
    end_date { 1.year.ago }
    reference_type { "Candidate" }
    reference_id { 1 }
    description { Faker::Lorem.paragraph }
    reasons_leaving { Faker::Lorem.sentence }
    contract_type { "CLT" }
    parse_language { "pt-BR" }
    is_deleted { false }

    association :account
    association :user
    association :occupation
    association :company

    trait :current_job do
      work_here { true }
      end_date { nil }
    end

    trait :deleted do
      is_deleted { true }
    end
  end
end
