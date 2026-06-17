# frozen_string_literal: true

class InterviewSession < ApplicationRecord
  STATUSES = %w[pending active completed scored expired cancelled].freeze
  INTERVIEW_TYPES = %w[voice video phone].freeze

  belongs_to :account
  belongs_to :evaluation
  belongs_to :evaluation_candidate, optional: true
  belongs_to :apply, optional: true
  belongs_to :candidate
  belongs_to :job
  belongs_to :created_by, class_name: "User"

  validates :token, presence: true, uniqueness: true
  validates :status, inclusion: { in: STATUSES }
  validates :interview_type, inclusion: { in: INTERVIEW_TYPES }

  before_validation :generate_token, on: :create
  before_validation :set_expiration, on: :create
  before_validation :snapshot_questions, on: :create
  before_validation :snapshot_contexts, on: :create

  scope :active_or_pending, -> { where(status: %w[pending active]) }
  scope :not_expired, -> { where("expires_at > ?", Time.current) }
  scope :accessible, -> { active_or_pending.not_expired }

  def self.find_or_create_for_channel(evaluation_candidate:, channel:, created_by:)
    existing = accessible.find_by(
      evaluation_candidate: evaluation_candidate,
      interview_type: channel.to_s,
      account_id: evaluation_candidate.account_id
    )
    return existing if existing

    create!(
      account: evaluation_candidate.account,
      evaluation: evaluation_candidate.evaluation,
      evaluation_candidate: evaluation_candidate,
      candidate: evaluation_candidate.candidate,
      job: evaluation_candidate.job,
      apply_id: evaluation_candidate.apply_id,
      created_by: created_by,
      interview_type: channel.to_s,
      duration_minutes: 30,
      language: "pt-BR"
    )
  end

  def self.bulk_find_or_create_for_channels(evaluation_candidate:, channels:, created_by:)
    voice_phone = channels.select { |c| c.to_sym.in?([ :voice, :phone ]) }
    return {} if voice_phone.empty?

    voice_phone.each_with_object({}) do |channel, sessions|
      sessions[channel.to_sym] = find_or_create_for_channel(
        evaluation_candidate: evaluation_candidate,
        channel: channel,
        created_by: created_by
      )
    end
  end

  def accessible?
    status.in?(%w[pending active]) && expires_at > Time.current
  end

  def public_url
    "#{ENV.fetch('FRONT_URL', 'http://localhost:3000')}/interviews/#{account.uid}/#{token}"
  end

  private

  def generate_token
    self.token ||= SecureRandom.uuid
  end

  def set_expiration
    self.expires_at ||= 7.days.from_now
  end

  def snapshot_questions
    return if questions_snapshot.present?

    self.questions_snapshot = evaluation.questions.order(:position).map do |q|
      {
        id: q.id,
        title: q.title,
        description: q.description,
        response_type: q.response_type,
        competence_type: q.competence_type,
        bloom_level: q.bloom_level,
        dreyfus_target: q.dreyfus_target,
        ocean_trait: q.ocean_trait,
        framework: q.framework,
        framework_weights: q.framework_weights,
        category: q.category,
        parent_question_id: q.parent_question_id,
        value_father: q.value_father || [],
        follow_up_limit: 2
      }
    end
  end

  def snapshot_contexts
    self.job_context = {
      title: job.title,
      description: job.description&.truncate(500),
      seniority: job.seniority,
      department: job.try(:department)&.try(:name),
      city: job.city,
      state: job.state,
      languages_data: job.language_relationships_data
    }.compact

    self.candidate_context = {
      name: candidate.name,
      email: candidate.email,
      mobile_phone: candidate.mobile_phone,
      current_company: candidate.current_company,
      role_name: candidate.role_name,
      position_level: candidate.position_level
    }.compact
  end
end
