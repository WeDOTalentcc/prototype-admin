class SkillCategorySerializer
  include JSONAPI::Serializer

  attributes :id, :name, :description, :icon, :color, :is_deleted, :created_at, :updated_at

  attribute :skills_count do |object|
    object.skills.where(is_deleted: false).count
  end
end
