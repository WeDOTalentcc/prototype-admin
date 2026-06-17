FactoryBot.define do
  factory :study_area do
    name { Faker::Educator.course_name }
    approved { false }
    association :account
  end
end
