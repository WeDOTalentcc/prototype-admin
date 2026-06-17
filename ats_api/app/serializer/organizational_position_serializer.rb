class OrganizationalPositionSerializer
  include JSONAPI::Serializer

  attributes :title, :description, :department_id, :reports_to_id, :level, :position_type, :is_active, :account_id

  attribute :department_name do |position|
    position.department&.name
  end

  attribute :reports_to_title do |position|
    position.reports_to&.title
  end

  attribute :current_holder do |position|
    position.current_user&.name
  end
end
