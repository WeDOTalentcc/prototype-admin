class PositionAssignmentSerializer
  include JSONAPI::Serializer

  attributes :user_id, :organizational_position_id, :start_date, :end_date, :is_current, :employment_type, :account_id

  attribute :user_name do |assignment|
    assignment.user&.name
  end

  attribute :position_title do |assignment|
    assignment.organizational_position&.title
  end
end
