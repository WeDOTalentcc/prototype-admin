# frozen_string_literal: true

class WebhookLog < ApplicationRecord
  # ApplicationRecord already includes AccountScopable

  belongs_to :webhook

  validates :webhook_id, presence: true
end
