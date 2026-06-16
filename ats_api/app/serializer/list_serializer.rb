class ListSerializer
  include JSONAPI::Serializer

  attributes(
    :id,
    :name,
    :is_public,
    :user_id,
    :account_id,
    :candidates_count,
    :jobs_count,
    :applies_count,
    :selective_processes_count,
    :color,
    :description,
    :created_at,
    :updated_at
  )

  attribute :user_name do |list|
    list.user&.name
  end

  attribute :user_email do |list|
    list.user&.email
  end
end
