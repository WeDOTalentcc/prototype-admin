class ApplyStatusSerializer
  include JSONAPI::Serializer

  attributes(
    :id, :apply_id, :selective_process_id, :is_deleted, :account_id, :user_id, :status_name, :selective_process_name, :user_name, :created_at, :updated_at
  )
end
