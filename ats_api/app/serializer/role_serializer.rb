# app/serializers/role_serializer.rb
class RoleSerializer
  include JSONAPI::Serializer

  attributes :id, :name, :description, :created_at, :updated_at
end
