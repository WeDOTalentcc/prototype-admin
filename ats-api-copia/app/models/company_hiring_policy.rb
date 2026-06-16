# frozen_string_literal: true

class CompanyHiringPolicy < ApplicationRecord
  validates :company_id, presence: true
end
