# frozen_string_literal: true

FactoryBot.define do
  factory :entity_page do
    association :user
    association :account
    entity { "candidates" }
    type_view { "table" }
    link { "/candidates" }
    pages { { link: "/candidates", data: { current_page: 1 }, query: {} } }
  end
end
