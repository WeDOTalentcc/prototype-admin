# frozen_string_literal: true

class RecruitmentCampaignSerializer
  include JSONAPI::Serializer

  attributes(
    :id,
    :name,
    :current_stage,
    :automation_level,
    :status,
    :job_id,
    :talent_pool_id,
    :created_at,
    :updated_at
  )

  attribute :created_by do |campaign|
    campaign.created_by_user&.name
  end

  attribute :stages do |campaign|
    campaign.stage_progress
  end

  attribute :pending_action do |campaign|
    checkpoint = campaign.campaign_stage_events
                         .where(event_type: "checkpoint")
                         .where(stage: campaign.current_stage)
                         .last
    if checkpoint
      {
        message: checkpoint.event_data&.dig("message"),
        candidates_count: checkpoint.candidates_count,
        created_at: checkpoint.created_at,
      }
    end
  end
end
