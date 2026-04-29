FactoryBot.define do
  factory :skill_category do
    sequence(:name) { |n| "#{Faker::Job.field} #{n}" }
    description { Faker::Lorem.sentence }
    icon { [ "💻", "⚙️", "🎨", "🗄️", "☁️", "📱", "🧪", "🎭", "🤖", "🔄" ].sample }
    color { [ "#3B82F6", "#10B981", "#8B5CF6", "#F59E0B", "#06B6D4", "#EC4899" ].sample }
    is_deleted { false }

    trait :deleted do
      is_deleted { true }
    end

    trait :programming do
      sequence(:name) { |n| "Linguagens de Programação #{n}" }
      description { "Linguagens de programação e scripting" }
      icon { "💻" }
      color { "#3B82F6" }
    end

    trait :backend do
      sequence(:name) { |n| "Frameworks Backend #{n}" }
      description { "Frameworks e bibliotecas para desenvolvimento backend" }
      icon { "⚙️" }
      color { "#10B981" }
    end

    trait :soft_skills do
      sequence(:name) { |n| "Soft Skills #{n}" }
      description { "Habilidades comportamentais e interpessoais" }
      icon { "🤝" }
      color { "#A855F7" }
    end
  end
end
