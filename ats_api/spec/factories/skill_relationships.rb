# frozen_string_literal: true

FactoryBot.define do
  factory :skill_relationship do
    association :skill
    association :account
    reference_type { 'Job' }
    reference_id { create(:job).id }
    level_skill { 3 }
    is_deleted { false }
  end
end
