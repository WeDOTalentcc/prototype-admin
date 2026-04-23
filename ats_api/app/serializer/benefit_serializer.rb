class BenefitSerializer
  include JSONAPI::Serializer

  attributes :id, :name, :category, :is_deleted, :is_possible_extend_to_dependents, :is_per_day, :days_of_month, :enable_value_editing, :types, :created_at, :updated_at
end
