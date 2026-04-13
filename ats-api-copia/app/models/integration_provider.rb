# frozen_string_literal: true

class IntegrationProvider < ApplicationRecord
  # ApplicationRecord already includes AccountScopable

  has_many :integration_connections, foreign_key: :provider_id, dependent: :destroy

  validates :name, presence: true
end
