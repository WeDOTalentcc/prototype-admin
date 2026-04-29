# frozen_string_literal: true

FactoryBot.define do
  factory :sector_relationship do
    association :sector
    association :account
    sector_name { sector.name }
    reference_type { "Job" }
    reference_id { create(:job).id }
    is_deleted { false }
  end
end
