class FeedbackSerializer
  include JSONAPI::Serializer

  attributes(
    :id,
    :name,
    :title,
    :description,
    :additional_text,
    :is_deleted,
    :job_id,
    :selective_process_id,
    :account_id,
    :created_at,
    :updated_at,
  )
end
