# frozen_string_literal: true

class Webhook < ApplicationRecord
  # ApplicationRecord already includes AccountScopable

  has_many :webhook_logs, dependent: :destroy
  has_many :webhook_delivery_logs, dependent: :destroy

  validates :company_id, :name, :url, presence: true
end
