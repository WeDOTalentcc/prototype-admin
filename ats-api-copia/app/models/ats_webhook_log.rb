# frozen_string_literal: true

class AtsWebhookLog < ApplicationRecord
  # ApplicationRecord already includes AccountScopable

  belongs_to :ats_connection, foreign_key: :connection_id
end
