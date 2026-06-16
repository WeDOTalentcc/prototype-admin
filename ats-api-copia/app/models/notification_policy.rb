# frozen_string_literal: true

class NotificationPolicy < ApplicationRecord
  # ApplicationRecord already includes AccountScopable

  validates :company_id, :channel, :event_type, presence: true
end
