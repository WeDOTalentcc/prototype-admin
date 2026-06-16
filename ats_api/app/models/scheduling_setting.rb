# frozen_string_literal: true

class SchedulingSetting < ApplicationRecord
  VALID_DURATIONS = [ 15, 30, 45, 60, 90, 120 ].freeze

  belongs_to :user
  belongs_to :account

  validates :timezone, presence: true
  validates :work_hours_start, presence: true
  validates :work_hours_end, presence: true
  validates :default_duration_minutes, presence: true, inclusion: { in: VALID_DURATIONS }
  validates :buffer_minutes, numericality: { greater_than_or_equal_to: 0 }
  validates :lookahead_days, numericality: { greater_than: 0, less_than_or_equal_to: 60 }
  validates :user_id, uniqueness: true
  validate :work_hours_end_after_start

  private

  def work_hours_end_after_start
    return if work_hours_start.blank? || work_hours_end.blank?
    return if work_hours_end > work_hours_start

    errors.add(:work_hours_end, "must be after work_hours_start")
  end
end
