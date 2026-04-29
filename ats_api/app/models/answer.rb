class Answer < ApplicationRecord
  include Searchable
  belongs_to :question, optional: true
  belongs_to :evaluation, optional: true
  belongs_to :candidate, optional: true
  belongs_to :job, optional: true
  belongs_to :apply, optional: true
  belongs_to :user, optional: true
  belongs_to :account, optional: true
  belongs_to :reference, polymorphic: true, optional: true

  has_one_attached :audio_file

  SOURCE_WHATSAPP = "whatsapp"
  SOURCE_INTERNAL = "internal"
  SOURCE_VOICE = "voice"
  SOURCES = [ SOURCE_WHATSAPP, SOURCE_INTERNAL, SOURCE_VOICE ].freeze

  def self.source_from_message(message)
    message&.metadata&.dig("source").present? ? message&.metadata&.dig("source") : SOURCE_INTERNAL
  end

  AUDIO_MAX_SIZE = 25.megabytes
  AUDIO_CONTENT_TYPES = %w[
    audio/webm audio/ogg audio/mp4 audio/mpeg
    audio/wav audio/x-wav audio/mp3
  ].freeze

  validates :title, presence: true, allow_blank: true
  validates :final_skill_score, numericality: { greater_than_or_equal_to: 0, less_than_or_equal_to: 10 }, allow_nil: true
  validates :self_declaration_score, inclusion: { in: 1..5 }, allow_nil: true
  validate :analysis_data_must_be_hash
  validate :audio_file_valid, if: -> { audio_file.attached? }

  before_validation :clear_wsi_fields_for_question_kind
  after_commit :invalidate_linked_f11_reports, on: %i[create update]

  def self.include_base
    joins(:question).select(
      'answers.*,
      questions.title AS question_title,
      questions.description AS question_description,
      questions.details AS question_details,
      questions.competence_type AS question_competence_type,
      questions.bloom_level AS question_bloom_level,
      questions.dreyfus_target AS question_dreyfus_target,
      questions.ocean_trait AS question_ocean_trait,
      questions.framework_weights AS question_framework_weights,
      questions.validation_type_weight AS question_validation_type_weight,
      questions.framework AS question_framework'
    )
  end

  def attach_audio_from_base64(base64_data, content_type: "audio/webm")
    return false if base64_data.blank?

    decoded = Base64.decode64(base64_data)
    extension = content_type.split("/").last.sub("mpeg", "mp3")
    filename = "answer_#{id}_#{Time.current.to_i}.#{extension}"

    audio_file.attach(
      io: StringIO.new(decoded),
      filename: filename,
      content_type: content_type
    )

    audio_file.attached?
  end

  def audio_url
    return nil unless audio_file.attached?

    prefix = ENV.fetch("API_URL", "http://localhost:8080")
    prefix + Rails.application.routes.url_helpers.rails_blob_url(audio_file, only_path: true)
  end

  def candidate_content_locked?
    description.present?
  end

  def candidate_forbidden_content_change?(permitted_answer_params)
    return false unless candidate_content_locked?

    attrs = permitted_answer_params.to_h.with_indifferent_access
    if attrs.key?(:description) && attrs[:description].to_s != description.to_s
      return true
    end
    return false unless attrs.key?(:choices)

    normalize_json(attrs[:choices]) != normalize_json(choices)
  end

  private

  def invalidate_linked_f11_reports
    return if evaluation_id.blank? || candidate_id.blank?

    EvaluationCandidate.where(evaluation_id: evaluation_id, candidate_id: candidate_id).find_each do |ec|
      next unless ec.completed?
      next unless ec.wsi_decision.is_a?(Hash) && ec.wsi_decision["result"].present?

      ec.update_column(:f11_report_stale, true) if ec.has_attribute?(:f11_report_stale)
      Wsi::ReportGenerationJob.perform_async(ec.id, ec.account_id) if ec.account_id
    end
  end

  def normalize_json(value)
    return nil if value.nil?

    value.to_json
  end

  def clear_wsi_fields_for_question_kind
    return unless question

    case question.competence_type.to_s
    when "technical"
      self.eligibility_answer = nil
    when "eligibility"
      self.self_declaration_score = nil
    else
      self.self_declaration_score = nil
      self.eligibility_answer = nil
    end
  end

  def analysis_data_must_be_hash
    return if analysis_data.is_a?(Hash)

    errors.add(:analysis_data, "must be a JSON object")
  end

  def audio_file_valid
    return unless audio_file.attached?

    unless AUDIO_CONTENT_TYPES.include?(audio_file.content_type)
      errors.add(:audio_file, "unsupported audio format")
    end

    return unless audio_file.byte_size > AUDIO_MAX_SIZE

    errors.add(:audio_file, "max size is #{AUDIO_MAX_SIZE / 1.megabyte}MB")
  end
end
