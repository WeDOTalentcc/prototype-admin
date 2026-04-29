# frozen_string_literal: true

class JobFieldTemplateSerializer
  include JSONAPI::Serializer

  set_type :job_field_template
  set_id :id

  attributes :name, :is_default, :fields, :created_at, :updated_at

  attribute :account_id
  attribute :fields_count do |object|
    object.fields&.count || 0
  end

  attribute :required_fields_count do |object|
    object.fields&.count { |f| f["is_required"] } || 0
  end

  attribute :optional_fields_count do |object|
    object.fields&.count { |f| !f["is_required"] } || 0
  end

  attribute :fields_by_journey_position do |object|
    next [] unless object.fields.is_a?(Array)

    object.fields.group_by { |f| f["job_journey_position"] || 0 }
                 .transform_values { |fields| fields.sort_by { |f| f["priority"] || 99 } }
  end

  attribute :fields_by_category do |object|
    next {} unless object.fields.is_a?(Array)

    object.fields.group_by { |f| f["category"] || "uncategorized" }
  end
end
