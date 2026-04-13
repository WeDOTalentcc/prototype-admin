# spec/factories/candidates.rb
FactoryBot.define do
  factory :candidate do
    uid { SecureRandom.uuid }
    name { "John" }
    surname { "Doe" }
    email { Faker::Internet.unique.email }
    secondary_email { Faker::Internet.email }
    mobile_phone { Faker::PhoneNumber.cell_phone }
    phone { Faker::PhoneNumber.phone_number }
    linkedin { Faker::Internet.url(host: 'linkedin.com') }
    github { Faker::Internet.url(host: 'github.com') }
    portfolio { Faker::Internet.url }
    current_company { Faker::Company.name }
    role_name { "Developer" }
    position_level { "Senior" }
    self_introduction { "Experienced developer with a focus on backend." }
    curriculum_text { "Curriculum content goes here." }
    date_birth { 30.years.ago }
    gender { 0 }
    nationality { "Brazilian" }
    marital_status { 1 }
    cpf { rand(000000..999999).to_s }
    street { "Main Street" }
    number { 123 }
    district { "Centro" }
    zip { "12345-678" }
    complement { "Apt 101" }
    clt_expectation { 8000 }
    pj_expectation { 12000 }
    freelance_expectation { 10000 }
    current_salary { 7000 }
    desired_salary { 15000 }
    remote_work { true }
    mobility { true }
    interests { "Technology, AI" }
    comments { "Candidate with potential." }
    source { "LinkedIn" }
    avatar_url { Faker::Avatar.image }
    curriculum_pdf_url { Faker::Internet.url }
    completed_register { true }
    accept_terms { true }
    account_id { create(:account).id }
  end
end
