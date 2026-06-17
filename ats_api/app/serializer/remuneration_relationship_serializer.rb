class RemunerationRelationshipSerializer
  include JSONAPI::Serializer
  attributes(
    :id,
    :remuneration_id,
    :account_id,
    :user_id,
    :reference_type,
    :reference_id,
    :is_deleted,
    :created_at,
    :updated_at,
    :currency,
    :period,
    :comments,
    :value,
    :amount,
    :contract_type
  )

  attribute :name do |object|
    object.remuneration&.name
  end
end
