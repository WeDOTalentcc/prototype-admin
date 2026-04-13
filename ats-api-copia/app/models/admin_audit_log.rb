# frozen_string_literal: true

class AdminAuditLog < ApplicationRecord
  validates :admin_user_id, :action, :created_at, presence: true
end
