class DepartmentSerializer
  include JSONAPI::Serializer

  attributes :id, :name, :description, :level, :is_deleted, :account_id, :manager_name, :manager_email, :manager_title, :color, :headcount, :order
  attribute :parent_department_id
  attribute :manager_id

  attribute :managers do |department|
    managers = department.department_relationships.managers.includes(:user)
    next [] if managers.empty? && department.manager_name.blank?

    if managers.any?
      managers.map do |rel|
        {
          id: rel.user_id,
          name: rel.user&.name || department.manager_name,
          email: rel.user&.email || department.manager_email,
          title: rel.title || department.manager_title,
          is_primary: rel.is_primary
        }
      end
    else
      [ {
        id: department.manager_id,
        name: department.manager_name,
        email: department.manager_email,
        title: department.manager_title,
        is_primary: true
      } ]
    end
  end

  attribute :children do |department|
    department.child_departments.order(:order, :name).map do |child|
      {
        id: child.id,
        name: child.name,
        level: child.level,
        color: child.color
      }
    end
  end

  attribute :members_count do |department|
    department.department_relationships.count
  end
end
