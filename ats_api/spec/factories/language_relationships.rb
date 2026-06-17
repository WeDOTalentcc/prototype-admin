FactoryBot.define do
  factory :language_relationship do
    association :language
    reference_type { 'Job' }
    reference_id { create(:job).id }
    min_value { 1 }
    max_value { 5 }
    priority { 1 }
    level { %w[basico intermediario avancado fluente nativo].sample }
  end
end
