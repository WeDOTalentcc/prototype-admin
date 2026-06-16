FactoryBot.define do
  factory :language do
    name { Faker::Nation.language + SecureRandom.hex(2) }
    acronym { Faker::Alphanumeric.alpha(number: 2).upcase }
    name_ptbr { "Língua #{Faker::Lorem.unique.word.capitalize}" }
  end
end
