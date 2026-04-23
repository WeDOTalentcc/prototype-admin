# frozen_string_literal: true

class RequestKey < ApplicationRecord
  validates :key, presence: true, uniqueness: true
  validates :expires_at, presence: true

  scope :expired, -> { where("expires_at < ?", Time.current) }

  # Atomically claim an idempotency key for a given TTL window.
  # Returns true when the key is newly claimed, false if it already exists.
  def self.claim!(key, ttl: 24.hours)
    create!(key: key, expires_at: ttl.from_now)
    true
  rescue ActiveRecord::RecordNotUnique
    false
  end
end
