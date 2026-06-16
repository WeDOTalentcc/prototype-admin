class AddressRelationshipSerializer
  include JSONAPI::Serializer

  attributes :id, :reference_type, :reference_id, :is_deleted, :address_id, :account_id, :user_id, :created_at, :updated_at
end
