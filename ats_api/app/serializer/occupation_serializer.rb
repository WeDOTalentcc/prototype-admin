class OccupationSerializer
  include JSONAPI::Serializer
  attributes :id, :name, :description, :user_id, :account_id
end
