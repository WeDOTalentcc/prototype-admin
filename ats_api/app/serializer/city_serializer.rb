class CitySerializer
  include JSONAPI::Serializer

  attributes :id, :name, :state_id, :country_id

  attribute :state_name do |object|
    object.state&.name
  end

  attribute :country_name do |object|
    object.country&.name
  end

  belongs_to :state
  belongs_to :country

  attribute :city_state do |object|
    "#{object.name}, #{object.state&.name}"
  end
end
