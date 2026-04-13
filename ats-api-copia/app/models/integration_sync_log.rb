# frozen_string_literal: true

class IntegrationSyncLog < ApplicationRecord
  # ApplicationRecord already includes AccountScopable

  belongs_to :integration_connection, foreign_key: :connection_id

  validates :connection_id, presence: true
end
