# spec/factories/jobs.rb (ou onde seu factory de Job estiver)
FactoryBot.define do
  factory :job do
    title { Faker::Job.title }
    description { Faker::Lorem.paragraph }

    # Associações obrigatórias
    association :user
    account { user.account }

    # Campos que exigem unicidade devido ao índice unique
    # Usamos `sequence` para garantir valores únicos a cada vez que um job é criado
    sequence(:provider) { |n| "provider_test_#{n}" }
    sequence(:provider_job_id) { |n| "job_id_test_#{n}" }

    # Outros campos do esquema, se você precisar deles para seus testes.
    # Se não forem cruciais para o cenário de teste atual e podem ser nulos/padrão,
    # você pode deixá-los de fora ou fornecer valores padrão.
    company_id { nil } # Exemplo, se puder ser nulo
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
    workplace_type { [ 'on_site', 'hybrid', 'remote' ].sample }
  end
end
