# frozen_string_literal: true

class CalendarAvailability < ApplicationRecord
  # ApplicationRecord already includes AccountScopable

  self.table_name = "calendar_availability"

  belongs_to :user

  validates :user_id, presence: true
end
