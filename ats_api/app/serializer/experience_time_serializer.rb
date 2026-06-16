class ExperienceTimeSerializer
  include JSONAPI::Serializer

  set_type :experience_time
  set_id :id
  attributes :name
end
