# frozen_string_literal: true

class TalentPoolCandidate < ApplicationRecord
  STAGES = %w[discovered contacted screening screened ready].freeze
  ORIGINS = %w[agent manual import search].freeze

  belongs_to :talent_pool, counter_cache: :candidates_count
  belongs_to :candidate

  validates :stage, inclusion: { in: STAGES }
  validates :origin, inclusion: { in: ORIGINS }
  validates :candidate_id, uniqueness: { scope: :talent_pool_id }

  scope :by_stage, ->(stage) { where(stage: stage) }
  scope :not_moved, -> { where(moved_to_job_id: nil) }
  scope :ready_to_move, -> { where(stage: "ready", moved_to_job_id: nil) }

  def moved?
    moved_to_job_id.present?
  end

  def advance_stage!
    current_idx = STAGES.index(stage)
    return if current_idx.nil? || current_idx >= STAGES.length - 1

    update!(stage: STAGES[current_idx + 1])
    talent_pool.update_counters!
  end

  def move_to_job!(job_id, target_stage)
    update!(
      moved_to_job_id: job_id,
      moved_at: Time.current,
      moved_to_stage: target_stage
    )
  end
end
