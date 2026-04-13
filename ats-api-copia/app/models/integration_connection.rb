# frozen_string_literal: true

class IntegrationConnection < ApplicationRecord
  # ApplicationRecord already includes AccountScopable

  belongs_to :integration_provider, foreign_key: :provider_id

  has_many :integration_sync_logs, foreign_key: :connection_id, dependent: :destroy
  has_many :integration_webhooks, foreign_key: :connection_id, dependent: :destroy

  validates :company_id, :provider_id, presence: true
end
