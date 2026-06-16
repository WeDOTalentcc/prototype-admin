FactoryBot.define do
  factory :workflow_template do
    name { "#{Faker::Job.field} Process" }
    is_deleted { false }
    association :user
    account { user.account }
  end
end
