# frozen_string_literal: true

class SchedulingSlot < ApplicationRecord
  belongs_to :scheduling_link

  validates :start_time, presence: true
  validates :end_time, presence: true
  validate :end_time_after_start_time

  scope :available, -> { where(is_available: true) }
  scope :unavailable, -> { where(is_available: false) }
  scope :future, -> { where("start_time > ?", Time.current) }
  scope :ordered, -> { order(start_time: :asc) }

  def available?
    is_available
  end

  def mark_as_unavailable!
    update!(is_available: false)
  end

  def duration_minutes
    ((end_time - start_time) / 60).to_i
  end

  private

  def end_time_after_start_time
    return if start_time.blank? || end_time.blank?
    return if end_time > start_time

    errors.add(:end_time, "must be after start_time")
  end
end
