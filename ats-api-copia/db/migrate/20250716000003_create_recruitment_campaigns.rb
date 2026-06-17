# frozen_string_literal: true

class CreateRecruitmentCampaigns < ActiveRecord::Migration[7.1]
  def change
    create_table :recruitment_campaigns, id: :uuid do |t|
      t.references :account, null: false, foreign_key: true, type: :bigint
      t.references :created_by_user, foreign_key: { to_table: :users }, type: :bigint

      t.string  :name, null: false
      t.bigint  :job_id, null: true       # linked job (nullable for pool-only campaigns)
      t.references :talent_pool, foreign_key: true, type: :uuid, null: true

      t.string  :current_stage, null: false, default: "definition"
      # Stages: definition → sourcing → screening → wsi → interview → offer → placement

      t.string  :automation_level, null: false, default: "semi"
      # auto: advances without approval
      # semi: pauses at checkpoints
      # assisted: recruiter leads, agents suggest

      t.jsonb   :stages_config, default: {}  # per-stage overrides: { screening: { auto: true } }
      t.jsonb   :metadata, default: {}       # flexible metadata

      t.string  :status, null: false, default: "active"  # active, paused, completed, archived

      t.timestamps
    end

    add_index :recruitment_campaigns, [:account_id, :status]
    add_index :recruitment_campaigns, :job_id
    add_index :recruitment_campaigns, :talent_pool_id
    add_index :recruitment_campaigns, [:account_id, :current_stage]

    create_table :campaign_stage_events, id: :uuid do |t|
      t.references :recruitment_campaign, null: false, foreign_key: true, type: :uuid

      t.string  :stage, null: false           # which stage this event belongs to
      t.string  :event_type, null: false      # started, completed, checkpoint, error, agent_update
      t.jsonb   :event_data, default: {}      # flexible payload
      t.integer :candidates_count, default: 0  # candidates involved at this point
      t.string  :triggered_by                  # user_id, agent_id, or "system"

      t.datetime :completed_at
      t.timestamps
    end

    add_index :campaign_stage_events, [:recruitment_campaign_id, :stage]
    add_index :campaign_stage_events, :event_type
  end
end
