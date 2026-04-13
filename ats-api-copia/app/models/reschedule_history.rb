# frozen_string_literal: true

class RescheduleHistory < ApplicationRecord
  # ApplicationRecord already includes AccountScopable

  self.table_name = "reschedule_history"

  belongs_to :interview

  validates :interview_id, presence: true
end
