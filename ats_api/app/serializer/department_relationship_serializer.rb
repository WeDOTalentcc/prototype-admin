class DepartmentRelationshipSerializer
  include JSONAPI::Serializer

  attributes :id, :department_id, :user_id, :reference_type, :reference_id,
             :role, :title, :is_primary, :is_deleted, :account_id,
             :created_at, :updated_at

  attribute :department do |relationship|
    next unless relationship.department

    {
      id: relationship.department.id,
      name: relationship.department.name
    }
  end

  attribute :user do |relationship|
    next unless relationship.user

    {
      id: relationship.user.id,
      name: relationship.user.name,
      email: relationship.user.email
    }
  end
end
