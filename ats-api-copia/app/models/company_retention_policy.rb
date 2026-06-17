# frozen_string_literal: true

class CompanyRetentionPolicy < ApplicationRecord
  validates :company_id, :data_type, :retention_days, presence: true
end
