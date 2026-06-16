class LanguageRelationship < ApplicationRecord
  include Searchable

  belongs_to :language
  belongs_to :reference, polymorphic: true

  validates :language, presence: true
  validates :reference_type, presence: true
  validates :reference_id, presence: true
  validate :min_less_or_equal_max

  LEVELS = %w[básico intermediário avançado profissional fluente nativo].freeze
  validates :level, inclusion: { in: LEVELS, allow_blank: true, allow_nil: true }

  def search_data
    {
      id: id,
      language_id: language_id,
      language_name: language&.name,
      reference_type: reference_type,
      reference_id: reference_id,
      min_value: min_value,
      max_value: max_value,
      priority: priority,
      level: level,
      is_required: is_required,
      created_at:,
      updated_at:
    }
  end

  private

  def min_less_or_equal_max
    return if min_value.nil? || max_value.nil?

    errors.add(:min_value, "não pode ser maior que max_value") if min_value > max_value
  end
end
