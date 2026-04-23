FactoryBot.define do
  factory :cached_availability do
    association :user
    date { Date.current }
    slots_data { { "free_slots" => [] } }
    fetched_at { Time.current }
  end
end
