class Evaluation < ApplicationRecord
  include Searchable

  enable_autocomplete :name

  belongs_to :user
  belongs_to :job, optional: true
  belongs_to :candidate, optional: true
  belongs_to :selective_process, optional: true
  belongs_to :approved_selective_process, class_name: "SelectiveProcess", foreign_key: "approved_selective_process_id", optional: true
  belongs_to :rejected_selective_process, class_name: "SelectiveProcess", foreign_key: "rejected_selective_process_id", optional: true
  belongs_to :account
  has_many :evaluation_candidates
  has_many :questions, dependent: :destroy
  has_many :interview_sessions, dependent: :destroy

  VALID_NOTIFICATION_CHANNELS = %w[internal voice phone whatsapp].freeze

  enum chatbot_channel: { internal: 0, whatsapp: 1 }
  enum notification_type: { per_candidate: 0, daily: 1, weekly: 2 }

  validate :validate_notification_channels

  validates :notification_hour,
    inclusion: { in: 9..18, message: "must be between 9 and 18 (business hours)" },
    allow_nil: true,
    if: :notification_enabled?

  validates :notification_days,
    presence: { message: "must have at least one day" },
    if: -> { notification_enabled? && (daily? || weekly?) }

  validate :validate_notification_days_range, if: -> { notification_enabled? && notification_days.present? }
  validate :validate_screening_selective_process, if: :is_screening?

  scope :screening, -> { where(is_screening: true) }
  scope :with_notifications_enabled, -> { where(notification_enabled: true) }
  scope :per_candidate_notifications, -> { with_notifications_enabled.where(notification_type: :per_candidate) }
  scope :daily_notifications_at, ->(hour) { with_notifications_enabled.where(notification_type: :daily, notification_hour: hour) }
  scope :weekly_notifications_at, ->(hour, day_of_week) {
    with_notifications_enabled
      .where(notification_type: :weekly, notification_hour: hour)
      .where("? = ANY(notification_days)", day_of_week)
  }

  def search_data
    {
      **attributes.deep_symbolize_keys,
      approved_selective_process_name: approved_selective_process_name,
      rejected_selective_process_name: rejected_selective_process_name,
      is_trigger: is_trigger
    }
  end

  def approved_selective_process_name
    approved_selective_process&.name
  end

  def rejected_selective_process_name
    rejected_selective_process&.name
  end

  def is_chatbot?
    attributes.key?("is_chatbot") ? self[:is_chatbot] : ai_enabled
  end

  def whatsapp_chatbot?
    is_chatbot? && respond_to?(:chatbot_channel) && chatbot_channel.to_s == "whatsapp"
  end

  def internal_chatbot?
    is_chatbot? && (!respond_to?(:chatbot_channel) || chatbot_channel.to_s == "internal")
  end

  def self.create_evaluation_by_job(previous_job_id, current_job)
    evaluations = Evaluation.where(job_id: previous_job_id)

    return if evaluations.empty?

    evaluations.each do |evaluation|
      selective_process_id = SelectiveProcess.find_by(
        job_id: current_job.id,
        status: evaluation&.selective_process&.status
      )&.id

      next if selective_process_id.nil?

      added_evalution = Evaluation.create(
        name: evaluation&.name,
        selective_process_id:,
        job_id: current_job.id,
        business_id: evaluation&.business_id,
        recruiter_id: evaluation&.recruiter_id,
        status: evaluation&.status,
        position: evaluation&.position,
        selective_process_sub_status_id: evaluation.selective_process_sub_status_id,
        sub_status: evaluation.sub_status,
        is_answered_by_recruiter: evaluation.is_answered_by_recruiter,
        notification_enabled: evaluation.notification_enabled,
        notification_type: evaluation.notification_type,
        notification_days: evaluation.notification_days,
        notification_hour: evaluation.notification_hour,
        is_screening: evaluation.is_screening,
        is_trigger: evaluation.is_trigger,
        chatbot_channel: evaluation.chatbot_channel,
        is_chatbot: evaluation.is_chatbot,
        ai_enabled: evaluation.ai_enabled,
        introduction_details: evaluation.introduction_details,
        notification_channels: evaluation.notification_channels,
      )

      questions = Question.where(evaluation_id: evaluation.id)

      next if questions.empty?

      questions.each do |question|
        selective_process_id = SelectiveProcess.find_by(
          job_id: current_job.id,
          status: question&.selective_process&.status
        )&.id

        Question.create(
          title: question&.title,
          description: question&.description,
          details: question&.details,
          number_retakers: question&.number_retakers,
          time: question&.time,
          evaluation_id: added_evalution.id,
          response_type: question&.response_type,
          position: question&.position,
          deleted: question&.deleted,
          selective_process_id:,
          choices: question&.choices
        )
      end
    end
  end

  def generate_questions_from_template(template_id)
    questions = Question.where(evaluation_id: template_id, is_deleted: false)

    return if questions.empty?

    questions.each do |question|
      Question.create(
        title: question.title,
        description: question.description,
        details: question.details,
        number_retakers: question.number_retakers,
        time: question.time,
        evaluation_id: self.id,
        response_type: question.response_type,
        position: question.position,
        choices: question.choices
      )
    end
  end

  def refresh_questions_hash!
    new_hash = Evaluations::QuestionsIntegrityHashBuilder.call(evaluation_id: id)
    update_column(:questions_hash, new_hash) if questions_hash != new_hash
  end

  def calculate_dashboard_stats
    questions_data = questions.where(is_deleted: false)
    candidates_data = evaluation_candidates

    total_candidates = candidates_data.count
    screened_count = candidates_data.where(completed: true).count

    {
      average_time: questions_data.average(:time)&.to_f&.round(2) || 0,
      questions_count: questions_data.count,
      total_candidates: total_candidates,
      screened_count: screened_count,
      approved_count: candidates_data.where("score >= ?", 5).count,
      rejected_count: candidates_data.where("score < ?", 5).count,
      average_score: candidates_data.average(:score)&.to_f&.round(2) || 0,
      completion_rate: calculate_completion_rate(total_candidates, screened_count),
      last_updated: updated_at
    }
  end

  private

  def calculate_completion_rate(total, screened)
    return 0 if total.zero?
    ((screened.to_f / total) * 100).round(2)
  end

  def validate_notification_days_range
    return if notification_days.blank?

    invalid_days = notification_days.reject { |day| day.between?(0, 6) }
    if invalid_days.any?
      errors.add(:notification_days, "contains invalid days: #{invalid_days.join(', ')}. Use 0 (sunday) to 6 (saturday)")
    end
  end

  def validate_screening_selective_process
    return if selective_process_id.blank?

    sp = SelectiveProcess.find_by(id: selective_process_id)
    return if sp&.screening?

    errors.add(:selective_process_id, "must belong to a screening stage when is_screening is true")
  end

  def validate_notification_channels
    return if notification_channels.blank?

    invalid = Array(notification_channels) - VALID_NOTIFICATION_CHANNELS
    return if invalid.empty?

    errors.add(:notification_channels, "contains invalid channels: #{invalid.join(', ')}. Valid: #{VALID_NOTIFICATION_CHANNELS.join(', ')}")
  end
end
