FactoryBot.define do
  factory :company do
    name { Faker::Company.name }
    is_deleted { false }

    association :account
    association :user

    after(:build) do |company|
      company.logo.attach(
        io: File.open(Rails.root.join('spec/support/assets/test_image.png')),
        filename: 'test_image.png',
        content_type: 'image/png'
      )
    end
  end
end
