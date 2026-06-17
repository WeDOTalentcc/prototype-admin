FactoryBot.define do
  factory :benefit_relationship do
    name { "BenefitRel #{Faker::Commerce.product_name}" }
    association :benefit
    reference_type { 'Job' }
    reference_id { create(:job).id }
    is_deleted { false }
    is_possible_extend_to_dependents { [ true, false ].sample }
    is_per_day { [ true, false ].sample }
    days_of_month { rand(0..31) }
    enable_value_editing { true }
    types { %w[meal transport health].sample(2) }
    type_description { 'Tipo custom' }
    description { 'Descrição customizada' }
    is_company { [ true, false ].sample }
    details { 'Detalhes opcionais' }
    is_extendable_to_dependents { [ true, false ].sample }
    dependents_count { rand(0..3) }
  end
end
