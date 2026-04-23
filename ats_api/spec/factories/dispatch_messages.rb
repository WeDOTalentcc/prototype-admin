FactoryBot.define do
  factory :dispatch_message do
    account { dispatch.account }
    association :dispatch
    association :recipient, factory: :candidate
    recipient_address { Faker::Internet.email }
    status { :pending }
    attempts { 0 }
    sent_at { nil }
    provider_response { {} }
  end
end
