class AnswerSerializer
  include JSONAPI::Serializer

  attributes(
    :id,
    :title,
    :question_id,
    :evaluation_id,
    :candidate_id,
    :job_id,
    :time,
    :description,
    :detail,
    :apply_id,
    :user_id,
    :choices,
    :time_taken,
    :represent_field,
    :comments_response,
    :analysis_data,
    :final_skill_score,
    :reference_id,
    :reference_type,
    :account_id,
    :source,
    :self_declaration_score,
    :eligibility_answer,
    :final_skill_score,
    :created_at,
    :updated_at
  )

  attribute :question_title do |object|
    object.try(:question_title) || object.question&.title
  end

  attribute :question_description do |object|
    object.try(:question_description) || object.question&.description
  end

  attribute :question_details do |object|
    object.try(:question_details) || object.question&.details
  end

  attribute :question_competence_type do |object|
    object.try(:question_competence_type) || object.question&.competence_type
  end

  attribute :question_bloom_level do |object|
    object.try(:question_bloom_level) || object.question&.bloom_level
  end

  attribute :question_dreyfus_target do |object|
    object.try(:question_dreyfus_target) || object.question&.dreyfus_target
  end

  attribute :question_ocean_trait do |object|
    raw = object.try(:question_ocean_trait) || object.question&.ocean_trait
    Wsi::OceanTraitCanonical.to_api(raw)
  end

  attribute :question_framework_weights do |object|
    object.try(:question_framework_weights) || object.question&.framework_weights
  end

  attribute :question_validation_type_weight do |object|
    object.try(:question_validation_type_weight) || object.question&.validation_type_weight
  end

  attribute :question_framework do |object|
    object.try(:question_framework) || object.question&.framework
  end

  attribute :audio_url do |answer|
    next nil unless answer.audio_file.attached?

    prefix = ENV.fetch("API_URL", "http://localhost:8080")
    prefix + Rails.application.routes.url_helpers.rails_blob_url(answer.audio_file, only_path: true)
  end

  attribute :has_audio do |answer|
    answer.audio_file.attached?
  end

  attribute :audio_mime_type do |answer|
    next nil unless answer.audio_file.attached?

    answer.audio_file.content_type
  end

  attribute :comments_response do |object|
    raw = object.comments_response
    next nil if raw.blank?

    begin
      next raw if raw.is_a?(Hash)

      safe_str = raw
        .gsub(/([,{]\s*)([a-zA-Z0-9_]+)\s*:/, '\1"\2":')
        .gsub("=>", ":")
        .gsub(/\bnil\b/, "null")
        .gsub(/\btrue\b/, "true")
        .gsub(/\bfalse\b/, "false")
        .gsub(/\\\"/, '"')
        .gsub(/:(\s*)(?=[}\]])/, '\1null')

      JSON.parse(safe_str)
    rescue JSON::ParserError => e
      Rails.logger.error "❌ Erro parseando comments_response #{object.id}: #{e.message}"
      { error: "parse_error", message: e.message, original: raw }
    rescue => e
      Rails.logger.error "❌ Erro inesperado ao parsear comments_response #{object.id}: #{e.message}"
      { error: "unexpected_error", message: e.message, original: raw }
    end
  end
end
