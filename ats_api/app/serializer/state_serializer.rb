class StateSerializer
  include JSONAPI::Serializer

  attributes :id, :name, :country_id

  belongs_to :country
end
