# frozen_string_literal: true

class AuditLog < ApplicationRecord
  validates :created_at, presence: true
end
