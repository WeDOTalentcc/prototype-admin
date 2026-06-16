FactoryBot.define do
  factory :search_archetype do
    sequence(:uid) { |n| SecureRandom.uuid }
    sequence(:name) { |n| "Arquétipo #{n}" }
    emoji { [ '🎯', '💼', '🚀', '⚡', '🔥' ].sample }
    description { Faker::Lorem.paragraph }
    query { Faker::Job.title }

    seniority { SearchArchetype.seniorities.keys.sample }
    work_model { SearchArchetype.work_models.keys.sample }
    contract_type { SearchArchetype.contract_types.keys.sample }

    min_experience_years { rand(0..15) }
    industry { [ 'Tecnologia', 'Fintech', 'Saúde', 'E-commerce', 'Educação' ].sample }
    location { "#{Faker::Address.city}, #{Faker::Address.state_abbr}" }

    skills { Faker::Lorem.words(number: rand(3..8)) }
    tags { Faker::Lorem.words(number: rand(2..5)) }
    languages { [ 'Português', 'Inglês', 'Espanhol' ].sample(rand(1..3)) }

    local_filters { { keywords: Faker::Lorem.words(number: 3).join(' '), role_name: Faker::Job.title } }
    global_filters { { keywords: Faker::Lorem.words(number: 3).join(' ') } }

    is_default { false }
    is_public { false }
    is_deleted { false }
    usage_count { 0 }
    last_used_at { nil }

    association :account
    association :user

    trait :default do
      is_default { true }
      is_public { true }
      user { nil }
    end

    trait :public_archetype do
      is_public { true }
    end

    trait :deleted do
      is_deleted { true }
    end

    trait :with_usage do
      usage_count { rand(1..50) }
      last_used_at { rand(1..30).days.ago }
    end

    trait :tech_lead_python do
      name { 'Tech Lead Python' }
      emoji { '🐍' }
      query { 'Tech Lead Python Django AWS' }
      seniority { :lead }
      min_experience_years { 8 }
      industry { 'Tecnologia' }
      work_model { :remote }
      skills { [ 'Python', 'Django', 'AWS', 'Docker', 'PostgreSQL' ] }
      tags { [ 'backend', 'cloud', 'microservices' ] }
      languages { [ 'Português', 'Inglês' ] }
    end

    trait :junior_frontend do
      name { 'Desenvolvedor Frontend Júnior' }
      emoji { '💻' }
      query { 'Desenvolvedor Frontend React' }
      seniority { :junior }
      min_experience_years { 1 }
      work_model { :hybrid }
      skills { [ 'React', 'JavaScript', 'HTML', 'CSS' ] }
      tags { [ 'frontend', 'web' ] }
    end

    trait :intern do
      seniority { :intern }
    end

    trait :c_level do
      seniority { :c_level }
    end

    trait :clt do
      contract_type { :clt }
    end
  end
end
