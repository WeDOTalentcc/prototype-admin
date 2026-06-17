# frozen_string_literal: true

class CultureValue < ApplicationRecord
  belongs_to :company_profile, foreign_key: :company_id

  validates :company_id, :name, presence: true
end
