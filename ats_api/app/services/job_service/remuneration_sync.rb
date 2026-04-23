# frozen_string_literal: true

module JobService
  class RemunerationSync
    REMUNERATION_TYPES = {
      salary: { from: "Salário (De)", to: "Salário (Até)" },
      commission: { from: "Comissão (De)", to: "Comissão (Até)" },
      bonus: { from: "Pacote de Bônus (De)", to: "Pacote de Bônus (Até)" }
    }.freeze

    attr_reader :job

    def initialize(job)
      @job = job
    end

    def call
      return unless valid_for_sync?

      ActiveRecord::Base.transaction do
        sync_salary if should_sync_salary?
        sync_commission if should_sync_commission?
        sync_bonus if should_sync_bonus?
      end
    rescue => e
      log_error(e)
    ensure
      reset_change_flags
    end

    private

    def valid_for_sync?
      return false if job.destroyed? || !job.persisted?
      return false unless job.account_id.present?

      job.account_id ||= job.user&.account_id
      job.account_id.present?
    end

    def should_sync_salary?
      job.instance_variable_get(:@salary_from_changed) ||
      job.instance_variable_get(:@salary_to_changed)
    end

    def should_sync_commission?
      job.instance_variable_get(:@commission_from_changed) ||
      job.instance_variable_get(:@commission_to_changed)
    end

    def should_sync_bonus?
      job.instance_variable_get(:@bonus_from_changed) ||
      job.instance_variable_get(:@bonus_to_changed)
    end

    def sync_salary
      sync_remuneration_range(
        type: :salary,
        value_from: job.salary_from,
        value_to: job.salary_to,
        currency: job.salary_currency,
        period: job.salary_period,
        contract_type: job.salary_contract_type
      )
    end

    def sync_commission
      sync_remuneration_range(
        type: :commission,
        value_from: job.commission_from,
        value_to: job.commission_to,
        currency: job.commission_currency,
        period: job.commission_period
      )
    end

    def sync_bonus
      sync_remuneration_range(
        type: :bonus,
        value_from: job.bonus_from,
        value_to: job.bonus_to,
        currency: job.bonus_currency,
        period: job.bonus_period
      )
    end

    def sync_remuneration_range(type:, value_from:, value_to:, currency: nil, period: nil, contract_type: nil)
      type_config = REMUNERATION_TYPES[type]
      return unless type_config

      default_currency = currency || "BRL"

      process_remuneration(type_config[:from], value_from, default_currency, period, contract_type)
      process_remuneration(type_config[:to], value_to, default_currency, period, contract_type)
    end

    def process_remuneration(type_name, value, currency, period, contract_type)
      if value.blank?
        remove_remuneration(type_name)
      else
        create_or_update_remuneration(type_name, value, currency, period, contract_type)
      end
    end

    def create_or_update_remuneration(type_name, value, currency, period, contract_type)
      remuneration = find_or_create_remuneration(type_name)
      relationship = find_or_initialize_relationship(remuneration.id)

      update_relationship_attributes(relationship, value, currency, period, contract_type)
      relationship.save!
    end

    def find_or_create_remuneration(type_name)
      Remuneration.find_or_create_by!(
        name: type_name,
        description: type_name,
        account_id: job.account_id,
        entity: "Job"
      )
    end

    def find_or_initialize_relationship(remuneration_id)
      job.remuneration_relationships.find_or_initialize_by(
        remuneration_id: remuneration_id,
        reference_type: "Job",
        reference_id: job.id
      )
    end

    def update_relationship_attributes(relationship, value, currency, period, contract_type)
      contract_type_array = normalize_contract_type(contract_type)

      relationship.assign_attributes(
        value: value.to_f,
        currency: currency,
        period: period,
        contract_type: contract_type_array,
        is_deleted: false,
        user_id: job.user_id,
        account_id: job.account_id
      )
    end

    def normalize_contract_type(contract_type)
      return [] if contract_type.blank?
      contract_type.is_a?(Array) ? contract_type : [ contract_type ].compact
    end

    def remove_remuneration(type_name)
      remuneration = Remuneration.find_by(
        name: type_name,
        account_id: job.account_id,
        entity: "Job"
      )

      return unless remuneration

      job.remuneration_relationships
         .where(remuneration_id: remuneration.id)
         .update_all(is_deleted: true)
    end

    def reset_change_flags
      job.instance_variable_set(:@salary_from_changed, false)
      job.instance_variable_set(:@salary_to_changed, false)
      job.instance_variable_set(:@commission_from_changed, false)
      job.instance_variable_set(:@commission_to_changed, false)
      job.instance_variable_set(:@bonus_from_changed, false)
      job.instance_variable_set(:@bonus_to_changed, false)
    end

    def log_error(error)
      Rails.logger.error "Failed to sync remuneration for Job #{job.id}: #{error.message}"
      Rails.logger.error error.backtrace.join("\n")
    end
  end
end
