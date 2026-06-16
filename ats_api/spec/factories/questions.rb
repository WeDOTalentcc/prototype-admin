# frozen_string_literal: true

FactoryBot.define do
  factory :question do
    title { Faker::Lorem.sentence }
    description { Faker::Lorem.paragraph }
    details { Faker::Lorem.word }
    number_retakers { Faker::Number.between(from: 0, to: 3) }
    time { Faker::Number.between(from: 30, to: 120) }
    evaluation
    response_type { Faker::Number.between(from: 1, to: 3) }
    position { Faker::Number.between(from: 1, to: 10) }
    is_deleted { false }
    selective_process_id { nil }
    choices { [ { label: "Option 1", value: 1 }, { label: "Option 2", value: 2 } ] }
    expected_response { Faker::Lorem.sentence }
    is_required { true }
    parent_question_id { nil }
    value_father { [] }
    extra_params { {} }
    wsi_reviewed { false }
    wsi_metadata { {} }
  end
end
