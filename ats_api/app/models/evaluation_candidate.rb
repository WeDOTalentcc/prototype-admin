class EvaluationCandidate < ApplicationRecord
  include Searchable
  include UidGeneratable
  include TracksJobAnalytics

  enum evaluation_type: { standard: 0, phone_call: 1 }
  enum session_status: { active: "active", timeout: "timeout", closed: "closed" }, _prefix: :session
  enum chatbot_channel: { internal: 0, whatsapp: 1 }

  PHONE_CALL_STATUSES = %w[pending_schedule scheduled calling in_progress completed failed cancelled].freeze

  scope :active_sessions, -> { where(session_status: [ nil, "active" ]) }
  scope :timed_out_pending_retry, -> {
    where(session_status: "timeout")
      .where("last_timeout_at < ?", 24.hours.ago)
      .where("retry_attempts < 1")
  }

  scope :declined, -> { where.not(declined_at: nil) }
  scope :phone_calls, -> { where(evaluation_type: :phone_call) }
  scope :pending_schedule, -> { phone_calls.where(phone_call_status: "pending_schedule") }
  scope :scheduled_calls, -> { phone_calls.where(phone_call_status: "scheduled") }

  belongs_to :evaluation
  belongs_to :candidate
  belongs_to :apply, optional: true
  belongs_to :job, optional: true
  belongs_to :user, optional: true
  belongs_to :account
  belongs_to :scheduling_link, optional: true
  belongs_to :interview_session, optional: true

  has_many :answers, ->(evaluation_candidate) {
    where(
      evaluation_id: evaluation_candidate.evaluation_id,
      candidate_id: evaluation_candidate.candidate_id
    )
  }, class_name: "Answer", primary_key: :candidate_id, foreign_key: :candidate_id

  validates :evaluation, presence: true
  validates :candidate, presence: true
  validates :account, presence: true

  before_validation :assign_account_from_sources
  before_validation :inherit_is_screening_from_evaluation
  before_validation :inherit_notification_channels, on: :create
  before_save :assign_answers_hash_when_completing, if: :marking_evaluation_completed?
  after_commit :sync_apply_evaluation_status, on: %i[create update]
  after_create :inherit_chatbot_channel_from_evaluation
  after_create_commit :trigger_whatsapp_chatbot_start, :create_evaluation_candidate_log
  after_create_commit :send_internal_evaluation_email, if: :should_send_invite_email?
  after_create_commit :mark_apply_screening_sent, if: :screening_evaluation_with_apply?
  after_update_commit :get_ai_feedback, if: :completed_changed_to_true?
  after_commit :schedule_f11_report_refresh, on: %i[create update]

  def search_data
    {
      **attributes.deep_symbolize_keys,
      candidate_name: candidate&.name&.downcase,
      candidate_email: candidate&.email&.downcase,
      evaluation_name: evaluation&.name&.downcase,
      evaluation_description: evaluation&.description&.downcase,
      score: score,
      evaluation_summary: evaluation_summary,
      wsi_classification: wsi_classification,
      wsi_level: wsi_level,
      wsi_summary: wsi_summary,
      is_screening: is_screening,
      is_expired: date_expiration.present? && date_expiration < Time.current,
      created_at: created_at,
      updated_at: updated_at
    }
  end

  def self.include_base
    joins(:candidate).joins(:evaluation).select(
      'evaluation_candidates.*,
      candidates.name AS candidate_name,
      candidates.email AS candidate_email,
      evaluations.name AS evaluation_name,
      evaluations.description AS evaluation_description'
    )
  end


  def send_completion_notifications
    final_account_id = account_id || account&.id
    return unless final_account_id

    Evaluations::CompletionNotificationJob.perform_later(id, final_account_id)
  end

  def create_finish_evaluation_candidate_log
    job = self.job
    evaluation = self.evaluation
    ActivityLog.log_change(
      self.candidate,
      user: self.user,
      action: "update",
      category: "evaluation_sent",
      changeset: { job: { id: job.id, title: job.title }, evaluation: { id: evaluation.id, name: evaluation.name } },
      account: self.account,
    )
  end

  F11_INTERNAL_ATTRS = %w[f11_report_json report_generated_at report_version f11_report_stale updated_at].freeze

  def schedule_f11_report_refresh
    return unless completed?
    return unless wsi_decision.is_a?(Hash) && wsi_decision["result"].present?
    return unless saved_changes_justify_f11_refresh?

    update_column(:f11_report_stale, true) if has_attribute?(:f11_report_stale)
    Wsi::ReportGenerationJob.perform_async(id, account_id) if account_id
  end

  def saved_changes_justify_f11_refresh?
    keys = previous_changes.keys
    (keys - F11_INTERNAL_ATTRS).any?
  end

  def get_evaluation_candidate_url
    base = ENV.fetch("FRONT_URL", "http://localhost:3000")
    acc_uid = account&.uid || account_id || "acc"
    return nil unless uid
    "#{base}/evaluations/#{acc_uid}/#{uid}"
  end

  def scheduling_url
    return unless scheduling_link&.token

    base = ENV.fetch("FRONT_URL", "http://localhost:3000")
    "#{base}/scheduling/#{account.uid}/#{scheduling_link.token}"
  end

  def phone_call_scheduled?
    phone_call? && scheduled_at.present? && phone_call_status == "scheduled"
  end

  def phone_call_callable?
    phone_call? && phone_call_status == "scheduled" && scheduled_at.present? && scheduled_at <= Time.current
  end

  def session_active_or_pending?
    session_status.nil? || session_active?
  end

  def pending_retry_next_day?
    session_timeout? && last_timeout_at.present? && last_timeout_at < 24.hours.ago && retry_attempts < 1
  end

  def declined?
    declined_at.present?
  end

  def decline!(reason = nil)
    return false if declined? || completed?

    update!(
      declined_at: Time.current,
      declined_reason: reason
    )

    final_account_id = account_id || account&.id
    Evaluations::DeclineNotificationJob.perform_later(id, final_account_id) if final_account_id

    true
  end

  private

  def sync_apply_evaluation_status
    return unless apply_id.present?

    new_status = completed? ? :answered : :sent

    Apply.where(id: apply_id)&.first&.update(
      evaluation_candidate_status: Apply.evaluation_candidate_statuses[new_status],
      updated_at: Time.current
    )
  end

  def assign_account_from_sources
    self.account_id ||= evaluation&.account_id
    self.account_id ||= candidate&.account_id
    self.account_id ||= apply&.account_id
  end

  def inherit_is_screening_from_evaluation
    return unless evaluation&.is_screening?

    self.is_screening = true
  end

  def inherit_chatbot_channel_from_evaluation
    return unless evaluation.present?
    return unless evaluation.respond_to?(:chatbot_channel)

    channel = evaluation.chatbot_channel
    return if channel.nil?

    db_value = Evaluation.chatbot_channels[channel.to_s]
    update_column(:chatbot_channel, db_value) if db_value.present?
  end

  def screening_evaluation_with_apply?
    evaluation&.is_screening? && apply_id.present?
  end

  def should_send_invite_email?
    return false unless candidate&.email.present?
    return false unless creator_user.present? && account_id.present?

    channels = resolve_notification_channels
    channels.any? { |c| c.in?([ :internal, :voice, :phone ]) }
  end

  def internal_evaluation_with_email?
    should_send_invite_email?
  end

  def send_internal_evaluation_email
    channels = resolve_notification_channels
    return if channels.empty?

    interview_sessions = create_interview_sessions_for_channels(channels)

    Evaluations::UnifiedInviteService.new(
      evaluation_candidate: self,
      user: creator_user,
      channels: channels,
      interview_sessions: interview_sessions
    ).call
  rescue StandardError => e
    Rails.logger.error "❌ [EvaluationCandidate] send_internal_evaluation_email error: #{e.class} #{e.message}"
    Rails.logger.error e.backtrace.first(5).join("\n")
  end

  def create_interview_sessions_for_channels(channels)
    InterviewSession.bulk_find_or_create_for_channels(
      evaluation_candidate: self,
      channels: channels,
      created_by: creator_user
    )
  end

  def inherit_notification_channels
    return if notification_channels.present?

    from_eval = Array(evaluation&.notification_channels)
    if from_eval.any?
      self.notification_channels = from_eval
      return
    end

    from_job = Array(job&.notification_channels)
    self.notification_channels = from_job if from_job.any?
  end

  def resolve_notification_channels
    stored = Array(notification_channels)
    return stored.map(&:to_sym) if stored.any?

    [ :internal ]
  end

  def creator_user
    user || job&.user || account&.users&.find_by(is_admin: true) || account&.users&.first
  end

  def mark_apply_screening_sent
    Apply.where(id: apply_id).update_all(is_screening_sent: true)
  end

  def trigger_whatsapp_chatbot_start
    channel_ok = evaluation.respond_to?(:whatsapp_chatbot?) ? evaluation.whatsapp_chatbot? : evaluation.is_chatbot?
    phone = candidate&.mobile_phone
    unless channel_ok
      return
    end
    unless apply_id.present? && phone.present?
      return
    end
    # return
    Chatbot::EvaluationStarterJob.perform_later(apply_id, evaluation_id, account_id)
  rescue => e
    Rails.logger.error("EvaluationCandidate trigger_whatsapp_chatbot_start error: #{e.class} #{e.message}")
  end

  def create_evaluation_candidate_log
    job = self.job
    evaluation = self.evaluation
    ActivityLog.log_change(
      self.candidate,
      user: self.user,
      action: "create",
      category: "evaluation_sent",
      changeset: { job: { id: job.id, title: job.title }, evaluation: { id: evaluation.id, name: evaluation.name } },
      account: self.account,
    )
  end

  def completed_changed_to_true?
    result = saved_change_to_completed? && completed?
    result
  end

  def marking_evaluation_completed?
    return false unless completed?

    return true if new_record? && completed?

    will_save_change_to_completed?
  end

  def assign_answers_hash_when_completing
    self.answers_hash = Evaluations::AnswersIntegrityHashBuilder.call(
      evaluation_id: evaluation_id,
      candidate_id: candidate_id
    )
  end

  def get_ai_feedback
    final_account_id = account_id || account&.id
    return unless final_account_id

    Evaluations::PerCandidateNotificationJob.perform_later(id, final_account_id)

    Rails.logger.info "✅ [EvaluationCandidate] Job enfileirado com sucesso para evaluation_candidate #{id} com account_id #{final_account_id}"
  rescue StandardError => e
    Rails.logger.error "❌ [EvaluationCandidate] Falha ao enfileirar job de análise AI: #{e.message}"
    Rails.logger.error "❌ [EvaluationCandidate] #{e.backtrace.first(3).join("\n")}"
  end
end
