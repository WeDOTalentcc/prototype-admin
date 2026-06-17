# frozen_string_literal: true

class CompensationPolicy < ApplicationRecord
  belongs_to :company_profile, foreign_key: :company_id

  validates :company_id, presence: true
end
