class BenefitRelationshipSerializer
  include JSONAPI::Serializer

  attributes :id, :benefit_id, :name, :reference_type, :reference_id,
             :is_deleted, :is_possible_extend_to_dependents, :is_per_day,
             :days_of_month, :enable_value_editing, :types, :type_description,
             :description, :is_company, :details, :is_extendable_to_dependents,
             :dependents_count, :created_at, :updated_at, :category, :value
end
