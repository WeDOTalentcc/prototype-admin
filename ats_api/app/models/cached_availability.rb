# frozen_string_literal: true

class CachedAvailability < ApplicationRecord
  CACHE_TTL = 5.minutes

  belongs_to :user

  validates :date, presence: true
  validates :fetched_at, presence: true
  validates :date, uniqueness: { scope: :user_id }

  scope :for_date, ->(date) { where(date: date) }
  scope :fresh, -> { where("fetched_at > ?", CACHE_TTL.ago) }
  scope :stale, -> { where("fetched_at <= ?", CACHE_TTL.ago) }

  def fresh?
    fetched_at > CACHE_TTL.ago
  end

  def stale?
    !fresh?
  end

  def free_slots
    slots_data.fetch("slots", slots_data.fetch("free_slots", [])).select { |s| s["status"] == "available" }
  end

  def all_slots
    {
      slots: slots_data.fetch("slots", slots_data.fetch("free_slots", [])),
      busy_periods: slots_data.fetch("busy_periods", [])
    }
  end
end
