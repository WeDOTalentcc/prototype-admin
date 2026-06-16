class LanguageRelationshipSerializer
  include JSONAPI::Serializer

  attributes :id, :language_id, :reference_type, :reference_id, :min_value, :max_value, :priority, :level, :is_required, :created_at, :updated_at

  attribute :language_name do |obj|
    obj.language&.name
  end

  attribute :language_name_ptbr do |obj|
    obj.language&.name_ptbr
  end
end
