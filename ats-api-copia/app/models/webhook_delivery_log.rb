# frozen_string_literal: true

class WebhookDeliveryLog < ApplicationRecord
  # ApplicationRecord already includes AccountScopable

  belongs_to :webhook

  validates :webhook_id, presence: true
end
