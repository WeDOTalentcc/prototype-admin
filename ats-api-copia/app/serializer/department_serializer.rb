# frozen_string_literal: true

class DepartmentSerializer
  include JSONAPI::Serializer

  attributes(
    :id,
    :company_id,
    :name,
    :code,
    :description,
    :parent_id,
    :manager_name,
    :manager_email,
    :manager_title,
    :manager_phone,
    :manager_id,
    :headcount,
    :budget_annual,
    :cost_center,
    :location,
    :is_active,
    :order,
    :hiring_priority,
    :created_at,
    :updated_at
  )
end
