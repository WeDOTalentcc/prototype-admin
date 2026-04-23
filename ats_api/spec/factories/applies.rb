# spec/factories/applies.rb
FactoryBot.define do
  factory :apply do
    association :candidate
    association :job
    association :selective_process
    is_deleted { false }
    account_id { create(:account).id }
  end
end
