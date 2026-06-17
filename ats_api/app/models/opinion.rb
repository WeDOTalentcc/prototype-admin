class Opinion < ApplicationRecord
  include UidGeneratable

  STATUSES = %w[active pending_review approved archived].freeze

  belongs_to :candidate
  belongs_to :job, optional: true
  belongs_to :user
  belongs_to :account

  validates :content, presence: true
  validates :status, inclusion: { in: STATUSES }

  scope :active, -> { where(is_deleted: false) }
  scope :general, -> { where(job_id: nil) }
  scope :for_job, ->(job_id) { where(job_id: job_id) }
  scope :by_candidate, ->(candidate_id) { where(candidate_id: candidate_id) }
  scope :pending_review, -> { active.where(status: "pending_review") }
end
