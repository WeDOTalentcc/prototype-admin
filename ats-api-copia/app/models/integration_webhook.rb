# frozen_string_literal: true

class IntegrationWebhook < ApplicationRecord
  # ApplicationRecord already includes AccountScopable

  belongs_to :integration_connection, foreign_key: :connection_id

  validates :connection_id, presence: true
end
