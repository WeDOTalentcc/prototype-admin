class SkillSerializer
  include JSONAPI::Serializer
  attributes :id, :name, :is_deleted, :account_id, :skill_category_id

  attribute :skill_category_name do |object|
    object.skill_category&.name
  end

  attribute :skill_category_icon do |object|
    object.skill_category&.icon
  end

  attribute :skill_category_color do |object|
    object.skill_category&.color
  end
end
