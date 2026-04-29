FactoryBot.define do
  factory :city do
    name { Faker::Address.city }
    association :state
    country { state.country }
  end
end
