class EmailFollowupStatus < ApplicationRecord
  self.table_name = "email_followup_status"

  belongs_to :dispatch
  belongs_to :candidate
  belongs_to :account, optional: true

  MAX_ATTEMPTS = 7
  INTERVAL_HOURS = 24

  validates :status, presence: true

  enum status: {
    pending: "pending",
    completed: "completed",
    stopped: "stopped"
  }

  scope :due_for_retry, -> { where(status: :pending).where("next_attempt_at <= ?", Time.current) }
  scope :for_candidate, ->(candidate_id) { where(candidate_id: candidate_id) }

  def can_retry?
    pending? && attempt_count < MAX_ATTEMPTS
  end

  def schedule_next_attempt!
    return unless can_retry?

    self.attempt_count += 1
    self.last_attempt_at = Time.current
    self.next_attempt_at = INTERVAL_HOURS.hours.from_now
    self.status = "stopped" if attempt_count >= MAX_ATTEMPTS
    save!
  end

  def complete!(reason = "responded")
    update!(
      status: :completed,
      completed_at: Time.current,
      stop_reason: reason
    )
  end
end
