class GenderSerializer
  include JSONAPI::Serializer

  attributes :id, :name, :specify
end
