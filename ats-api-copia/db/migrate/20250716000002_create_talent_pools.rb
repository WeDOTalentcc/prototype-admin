# frozen_string_literal: true

class CreateTalentPools < ActiveRecord::Migration[7.1]
  def change
    create_table :talent_pools, id: :uuid do |t|
      t.references :account, null: false, foreign_key: true, type: :bigint
      t.references :ideal_profile, foreign_key: true, type: :uuid, null: true
      t.references :created_by_user, foreign_key: { to_table: :users }, type: :bigint

      t.string  :name, null: false
      t.text    :description
      t.string  :status, null: false, default: "active" # active, paused, archived

      # WSI screening config (Modo Compacto)
      t.jsonb   :screening_questions, default: []
      t.jsonb   :screening_config, default: {}  # mode: compact|full, weights, traits
      t.boolean :screening_approved, default: false

      # Agent sourcing
      t.boolean :agent_sourcing_enabled, default: false
      t.jsonb   :agent_config, default: {}  # candidates_per_day, channels, schedule, notify

      # Counters (denormalized for performance)
      t.integer :candidates_count, default: 0
      t.integer :screened_count, default: 0
      t.integer :ready_count, default: 0

      t.timestamps
    end

    add_index :talent_pools, :account_id
    add_index :talent_pools, :status
    add_index :talent_pools, [:account_id, :status]

    create_table :talent_pool_candidates, id: :uuid do |t|
      t.references :talent_pool, null: false, foreign_key: true, type: :uuid
      t.references :candidate, null: false, foreign_key: true, type: :bigint

      t.string  :stage, null: false, default: "discovered"
      # Stages: discovered → contacted → screening → screened → ready
      t.string  :origin, null: false, default: "manual"
      # Origins: agent, manual, import, search

      t.float   :fit_score        # 0-100, set by agent or LIA
      t.jsonb   :screening_data, default: {}  # answers, scores, timestamps
      t.jsonb   :match_criteria, default: {}  # why matched (for calibration card)

      # Migration tracking
      t.bigint  :moved_to_job_id   # FK to jobs, set when moved to a vaga
      t.datetime :moved_at
      t.string  :moved_to_stage    # which stage in the job pipeline

      t.text    :notes

      t.timestamps
    end

    add_index :talent_pool_candidates, [:talent_pool_id, :candidate_id], unique: true,
              name: "idx_tpc_pool_candidate_unique"
    add_index :talent_pool_candidates, :stage
    add_index :talent_pool_candidates, :origin
    add_index :talent_pool_candidates, [:talent_pool_id, :stage]
    add_index :talent_pool_candidates, :moved_to_job_id
  end
end
