# frozen_string_literal: true

class IdealProfile < ApplicationRecord
  belongs_to :company_profile, foreign_key: :company_id
  belongs_to :department, optional: true

  validates :company_id, presence: true
end
