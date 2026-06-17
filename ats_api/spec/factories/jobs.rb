# spec/factories/jobs.rb
FactoryBot.define do
  factory :job do
    title { Faker::Job.title }
    description { Faker::Lorem.paragraph }

    association :user
    account { user.account }

    sequence(:provider) { |n| "provider_test_#{n}_#{SecureRandom.hex(4)}" }
    sequence(:provider_job_id) { |n| "job_id_test_#{n}_#{SecureRandom.hex(4)}" }

    company_id { nil }
    published_date { Faker::Date.backward(days: 30) }
    application_deadline { Faker::Date.forward(days: 30) }
    is_remote { Faker::Boolean.boolean }
    city { Faker::Address.city }
    state { Faker::Address.state_abbr }
    country { Faker::Address.country_code }
    job_url { Faker::Internet.url }
    career_page_id { Faker::Number.between(from: 1, to: 100) }
    career_page_name { Faker::Company.name }
    career_page_url { Faker::Internet.url }
    career_page_logo { Faker::Internet.url }
    friendly_badge { Faker::Boolean.boolean }
    disabilities { Faker::Boolean.boolean }
    is_urgent { false }
    workplace_type { [ 'on_site', 'hybrid', 'remote' ].sample }
  end
end
