class CountrySerializer
  include JSONAPI::Serializer

  attributes :id, :name
end
