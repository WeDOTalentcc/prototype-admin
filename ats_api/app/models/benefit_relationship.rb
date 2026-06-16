class BenefitRelationship < ApplicationRecord
  include Searchable

  belongs_to :benefit, optional: true
  belongs_to :reference, polymorphic: true

  validates :reference_type, :reference_id, presence: true
  validates :name, presence: true
  validates :days_of_month, numericality: { only_integer: true, greater_than_or_equal_to: 0 }
  validates :dependents_count, numericality: { only_integer: true, greater_than_or_equal_to: 0 }, allow_nil: true

  def search_data
    {
      id: id,
      name: name,
      benefit_id: benefit_id,
      reference_type: reference_type,
      reference_id: reference_id,
      is_deleted: is_deleted,
      is_possible_extend_to_dependents: is_possible_extend_to_dependents,
      is_per_day: is_per_day,
      days_of_month: days_of_month,
      enable_value_editing: enable_value_editing,
      types: types,
      type_description: type_description,
      description: description,
      is_company: is_company,
      details: details,
      is_extendable_to_dependents: is_extendable_to_dependents,
      dependents_count: dependents_count,
      created_at: created_at,
      updated_at: updated_at
    }
  end
end
