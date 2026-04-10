# frozen_string_literal: true

class OnboardingMessage < ApplicationRecord
  belongs_to :onboarding_session

  CHANNELS = %w[whatsapp email web].freeze
  DIRECTIONS = %w[inbound outbound].freeze

  validates :channel, inclusion: { in: CHANNELS }
  validates :direction, inclusion: { in: DIRECTIONS }

  scope :by_channel, ->(ch) { where(channel: ch) }
  scope :inbound, -> { where(direction: "inbound") }
  scope :outbound, -> { where(direction: "outbound") }
  scope :chronological, -> { order(created_at: :asc) }
end
