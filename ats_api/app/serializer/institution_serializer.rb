class InstitutionSerializer
  include JSONAPI::Serializer

  attributes :id, :name, :approved, :reference_type, :reference_id, :account_id
end
