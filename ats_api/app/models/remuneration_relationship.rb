class RemunerationRelationship < ApplicationRecord
  include Searchable

  belongs_to :remuneration
  belongs_to :user, optional: true
  belongs_to :account

  validates :remuneration, presence: true
  validates :reference_type, :reference_id, presence: true

  validates :reference_id, uniqueness: {
    scope: [ :reference_type, :remuneration_id ],
    conditions: -> { where(is_deleted: false) },
    message: "Remuneration already linked to this reference"
  }

  PERIOD_VALUES = {
    "hourly" => 1,
    "daily" => 2,
    "weekly" => 3,
    "biweekly" => 4,
    "monthly" => 5,
    "yearly" => 6
  }.freeze

  CURRENCY_LIST = [
    { id: "BRL", name: "BRL" },
    { id: "USD", name: "USD" },
    { id: "EUR", name: "EUR" },
    { id: "GBP", name: "GBP" },
    { id: "JPY", name: "JPY" },
    { id: "AUD", name: "AUD" },
    { id: "CAD", name: "CAD" },
    { id: "CHF", name: "CHF" },
    { id: "CNY", name: "CNY" },
    { id: "INR", name: "INR" },
    { id: "RUB", name: "RUB" }
  ]

  CONTRACT_TYPE_LIST = [
    { id: "", name: "CLT" },
    { id: "PJ", name: "PJ" },
    { id: "Freelance", name: "Freelance" },
    { id: "Estágio", name: "Estágio" },
    { id: "Temporário", name: "Temporário" }
  ]

  class << self
    def normalize_period_value(value)
      return if value.blank?
      return value if value.is_a?(Integer)

      PERIOD_VALUES[value.to_s.downcase] || value
    end

    def period_label(value)
      return if value.blank?
      return value if value.is_a?(String)

      PERIOD_VALUES.key(value) || value
    end

    def normalize_contract_type(value)
      return if value.blank?

      normalized_values =
        if value.is_a?(Array)
          value
        elsif value.is_a?(String) && value.start_with?("{") && value.end_with?("}")
          value[1..-2].split(",")
        else
          Array(value)
        end

      normalized_values
        .map { |item| item.to_s.strip }
        .map { |item| item.gsub(/\?"+\A/, "").gsub(/\?"+\z/, "") }
        .reject(&:blank?)
        .first
    end
  end

  def period=(value)
    self[:period] = self.class.normalize_period_value(value)
  end

  def period
    self.class.period_label(self[:period])
  end

  def contract_type=(value)
    values = Array(value).reject(&:blank?)
    self[:contract_type] = values.presence
  end

  def contract_type
    stored = self[:contract_type]
    return stored if stored.is_a?(String)
    return stored.first if stored.is_a?(Array)

    stored
  end

  def self.create_remuneration_by(previous_id, reference_id, reference_type = "Job")
    remunerations = RemunerationRelationship.where(reference_type: reference_type, reference_id: previous_id)

    return if remunerations.empty?

    remunerations.each do |remuneration|
      new_remuneration = remuneration.dup
      new_remuneration.reference_id = reference_id
      new_remuneration.save
    end
  end
end
