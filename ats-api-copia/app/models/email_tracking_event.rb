# frozen_string_literal: true

class EmailTrackingEvent < ApplicationRecord
  belongs_to :email_log

  validates :email_log_id, :event_type, :event_at, presence: true
end
