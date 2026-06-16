# frozen_string_literal: true

class AuditRetentionPolicy < ApplicationRecord
  validates :company_id, :log_type, :retention_days, presence: true
end
