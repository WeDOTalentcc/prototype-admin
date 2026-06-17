class EvaluationSerializer
  include JSONAPI::Serializer

  attributes(
    :id,
    :name,
    :description,
    :is_main,
    :is_chatbot,
    :ai_enabled,
    :status,
    :report_date,
    :chatbot_channel,
    :time,
    :is_trigger,
    :notification_enabled,
    :notification_type,
    :notification_days,
    :notification_hour,
    :approved_selective_process_id,
    :rejected_selective_process_id,
    :approved_selective_process_name,
    :rejected_selective_process_name,
    :is_screening,
    :introduction_details,
    :notification_channels,
    :created_at,
    :updated_at,
    :questions_hash
  )

  attribute :job_title do |evaluation|
    evaluation.job&.title
  end

  attribute :user_name do |evaluation|
    evaluation.user&.name
  end
end
