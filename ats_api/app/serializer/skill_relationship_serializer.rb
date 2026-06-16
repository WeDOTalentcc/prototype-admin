class SkillRelationshipSerializer
  include JSONAPI::Serializer

  attributes(
    :id,
    :skill_id,
    :account_id,
    :user_id,
    :reference_type,
    :reference_id,
    :is_deleted,
    :priority,
    :min_value,
    :max_value,
    :description,
    :main,
    :experience_time,
    :level_skill,
    :created_at,
    :updated_at,
  )

  attribute :name do |object|
    object.skill&.name
  end

  attribute :skill_category_name do |object|
    object.skill&.skill_category&.name
  end

  attribute :skill_category_icon do |object|
    object.skill&.skill_category&.icon
  end

  attribute :experience_time_name do |object|
    experience_time_obj = ::SkillRelationship::EXPERIENCE_TIMES.find { |e| e[:id] == object.experience_time }
    experience_time_obj ? experience_time_obj[:name] : nil
  end

  attribute :level_skill_name do |object|
    skill_level_obj = ::SkillRelationship::SKILL_LEVELS.find { |s| s[:id] == object.level_skill }
    skill_level_obj ? skill_level_obj[:name] : nil
  end

  belongs_to :skill, serializer: SkillSerializer
end
