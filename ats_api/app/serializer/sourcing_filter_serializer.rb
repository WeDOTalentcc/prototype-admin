class SourcingFilterSerializer
  include JSONAPI::Serializer

  attributes(
    :id,
    :uid,
    :name,
    :parameters,
    :usage_count,
    :last_used_at,
    :created_at,
    :updated_at
  )
end
