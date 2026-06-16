class SkillLevelSerializer
  include JSONAPI::Serializer

  set_type :skill_level
  set_id :id
  attributes :name
end
