# frozen_string_literal: true

class SlaViolation < ApplicationRecord
  # ApplicationRecord already includes AccountScopable

  belongs_to :recruitment_sla, foreign_key: :sla_id

  validates :sla_id, presence: true
end
