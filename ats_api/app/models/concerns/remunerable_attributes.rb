# frozen_string_literal: true

module RemunerableAttributes
  extend ActiveSupport::Concern

  included do
    attr_reader :salary_from, :salary_to, :salary_currency, :salary_period, :salary_contract_type
    attr_reader :commission_from, :commission_to, :commission_currency, :commission_period
    attr_reader :bonus_from, :bonus_to, :bonus_currency, :bonus_period
  end

  def salary_from=(value)
    @salary_from = value
    @salary_from_changed = true
  end

  def salary_to=(value)
    @salary_to = value
    @salary_to_changed = true
  end

  def salary_currency=(value)
    @salary_currency = value
  end

  def salary_period=(value)
    @salary_period = value
  end

  def salary_contract_type=(value)
    @salary_contract_type = value
  end

  # Commission setters
  def commission_from=(value)
    @commission_from = value
    @commission_from_changed = true
  end

  def commission_to=(value)
    @commission_to = value
    @commission_to_changed = true
  end

  def commission_currency=(value)
    @commission_currency = value
  end

  def commission_period=(value)
    @commission_period = value
  end

  # Bonus setters
  def bonus_from=(value)
    @bonus_from = value
    @bonus_from_changed = true
  end

  def bonus_to=(value)
    @bonus_to = value
    @bonus_to_changed = true
  end

  def bonus_currency=(value)
    @bonus_currency = value
  end

  def bonus_period=(value)
    @bonus_period = value
  end

  # Load remuneration from database
  def load_remuneration_attributes
    return unless persisted?

    data = remuneration_relationships_data

    @salary_from = data[:salary_from]
    @salary_to = data[:salary_to]
    @salary_currency = data[:salary_currency]
    @salary_period = data[:salary_period]
    @salary_contract_type = data[:contract_types]&.first
  end
end
