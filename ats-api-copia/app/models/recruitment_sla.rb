# frozen_string_literal: true

class RecruitmentSla < ApplicationRecord
  # ApplicationRecord already includes AccountScopable

  has_many :sla_violations, foreign_key: :sla_id, dependent: :destroy

  validates :company_id, :max_hours, presence: true
end
