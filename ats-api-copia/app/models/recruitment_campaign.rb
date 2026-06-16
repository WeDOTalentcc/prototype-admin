# frozen_string_literal: true

class RecruitmentCampaign < ApplicationRecord
  STAGES = %w[definition sourcing screening wsi interview offer placement].freeze
  AUTOMATION_LEVELS = %w[auto semi assisted].freeze
  STATUSES = %w[active paused completed archived].freeze

  belongs_to :account
  belongs_to :created_by_user, class_name: "User", optional: true
  belongs_to :job, optional: true
  belongs_to :talent_pool, optional: true

  has_many :campaign_stage_events, dependent: :destroy

  validates :name, presence: true
  validates :current_stage, inclusion: { in: STAGES }
  validates :automation_level, inclusion: { in: AUTOMATION_LEVELS }
  validates :status, inclusion: { in: STATUSES }

  scope :active, -> { where(status: "active") }
  scope :for_account, ->(account_id) { where(account_id: account_id) }

  def advance_stage!
    idx = STAGES.index(current_stage)
    return false if idx.nil? || idx >= STAGES.length - 1

    next_stage = STAGES[idx + 1]
    update!(current_stage: next_stage)

    campaign_stage_events.create!(
      stage: next_stage,
      event_type: "started",
      triggered_by: "system"
    )

    broadcast_update!
    true
  end

  def complete_current_stage!(candidates_count: 0, triggered_by: "system")
    campaign_stage_events.create!(
      stage: current_stage,
      event_type: "completed",
      candidates_count: candidates_count,
      completed_at: Time.current,
      triggered_by: triggered_by
    )

    broadcast_update!
  end

  def add_checkpoint!(message, candidates_count: 0)
    campaign_stage_events.create!(
      stage: current_stage,
      event_type: "checkpoint",
      event_data: { message: message },
      candidates_count: candidates_count,
      triggered_by: "system"
    )

    broadcast_update!
  end

  def stage_progress
    # Eager-load all events once to avoid N+1 (was 14+ queries, now 1)
    events_by_stage = campaign_stage_events.group_by(&:stage)

    STAGES.map do |stage|
      events = events_by_stage[stage] || []
      completed = events.any? { |e| e.event_type == "completed" }
      is_current = current_stage == stage
      max_candidates = events.map(&:candidates_count).compact.max || 0
      checkpoint = events.select { |e| e.event_type == "checkpoint" }.last&.event_data&.dig("message")

      {
        stage: stage,
        label: stage_label(stage),
        status: completed ? "completed" : (is_current ? "in_progress" : "pending"),
        candidates_count: max_candidates,
        checkpoint: checkpoint,
      }
    end
  end

  def broadcast_update!
    return unless created_by_user

    ActionCable.server.broadcast(
      "workflow_user_#{created_by_user.id}",
      {
        type: "campaign_update",
        campaign_id: id,
        name: name,
        current_stage: current_stage,
        status: status,
        stages: stage_progress,
        job_id: job_id,
        talent_pool_id: talent_pool_id,
      }
    )
  end

  private

  def stage_label(stage)
    {
      "definition" => "Definição",
      "sourcing" => "Sourcing",
      "screening" => "Triagem",
      "wsi" => "WSI",
      "interview" => "Entrevista",
      "offer" => "Oferta",
      "placement" => "Placement",
    }[stage] || stage.capitalize
  end
end
