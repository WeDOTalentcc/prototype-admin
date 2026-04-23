# spec/factories/businesses.rb
FactoryBot.define do
  factory :business do
    name { Faker::Company.name }
    cnpj { Faker::Company.brazilian_company_number } # CNPJ
    email { Faker::Internet.email }
    phone { Faker::PhoneNumber.phone_number }
    website { Faker::Internet.url }
    industry { Faker::Company.industry }
    size { "#{Faker::Number.between(from: 1, to: 1000)} employees" }
    linkedin { "https://linkedin.com/company/#{name.parameterize}" }
    about { Faker::Lorem.paragraph }
    is_active { true }

    association :account
  end
end
