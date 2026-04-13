# frozen_string_literal: true

class WebhookRegistration < ApplicationRecord
  # ApplicationRecord already includes AccountScopable

  validates :company_id, presence: true
end
