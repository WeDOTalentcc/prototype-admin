FactoryBot.define do
  factory :benefit do
    name { "Benefit #{Faker::Commerce.product_name}" }
    category { %w[saude alimentacao transporte educacao lazer outros].sample }
    is_deleted { false }
    is_possible_extend_to_dependents { [ true, false ].sample }
    is_per_day { [ true, false ].sample }
    days_of_month { rand(0..31) }
    enable_value_editing { true }
    types { %w[meal transport health].sample(2) }
  end
end
