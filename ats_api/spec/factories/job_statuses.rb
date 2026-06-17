FactoryBot.define do
  factory :job_status do
    name { Faker::Job.unique.employment_type + SecureRandom.hex(2) }
    color { Faker::Color.hex_color }
  end
end
