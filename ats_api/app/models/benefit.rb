class Benefit < ApplicationRecord
  include Searchable

  enable_autocomplete :name

  validates :name, presence: true
  validates :days_of_month, numericality: { only_integer: true, greater_than_or_equal_to: 0 }

  def search_data
    {
      id: id,
      name: name,
      types: types,
      category: category,
      is_deleted: is_deleted,
      is_possible_extend_to_dependents: is_possible_extend_to_dependents,
      is_per_day: is_per_day,
      days_of_month: days_of_month,
      enable_value_editing: enable_value_editing,
      created_at: created_at,
      updated_at: updated_at
    }
  end

  def self.agg_search_array(_params = {})
    {
      category: { field: "category", limit: 50 },
      is_deleted: { field: "is_deleted", limit: 2 }
    }
  end

  def self.search_fields
    [ :name, :category ]
  end
end
