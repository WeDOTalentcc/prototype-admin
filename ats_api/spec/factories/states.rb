# spec/factories/states.rb
FactoryBot.define do
  factory :state do
    name { Faker::Address.unique.state }
    association :country
  end
end
