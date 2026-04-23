class ReplaceTagSerializer
  include JSONAPI::Serializer

  attributes :text, :tag
end
