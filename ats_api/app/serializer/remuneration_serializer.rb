class RemunerationSerializer
  include JSONAPI::Serializer

  attributes(
    :id,
    :name,
    :description,
    :user_id,
    :account_id,
    :is_deleted,
    :created_at,
    :updated_at
  )
end
