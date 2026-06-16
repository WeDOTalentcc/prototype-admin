# frozen_string_literal: true

class CampaignStageEvent < ApplicationRecord
  EVENT_TYPES = %w[started completed checkpoint error agent_update].freeze

  belongs_to :recruitment_campaign

  validates :stage, presence: true
  validates :event_type, inclusion: { in: EVENT_TYPES }

  scope :for_stage, ->(stage) { where(stage: stage) }
  scope :checkpoints, -> { where(event_type: "checkpoint") }
  scope :recent, -> { order(created_at: :desc) }
end
