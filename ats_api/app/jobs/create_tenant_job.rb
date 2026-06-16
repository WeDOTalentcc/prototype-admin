# frozen_string_literal: true

class CreateTenantJob < ApplicationJob
  queue_as :default

  sidekiq_options retry: 1

  def perform(tenant)
    Apartment::Tenant.switch!("public")
    job_field_template = JobFieldTemplate.find_by(is_default: true)&.dup

    ensure_tenant!(tenant)
    return if Rails.env.test?

    Apartment::Tenant.switch!(tenant)

    begin
      account = Account.find_by(tenant: tenant)
      return unless account

      Searchkick.callbacks(false) do
        create_default_records(account, job_field_template)
      end

      reindex_tenant(tenant)
    ensure
      Apartment::Tenant.reset
    end
  rescue Sidekiq::Shutdown
    Rails.logger.warn "[CreateTenantJob] Job interrupted during shutdown, will retry"
    raise
  end

  private

  def create_default_records(account, job_field_template)
    apply_account_saturation_defaults(account)

    Business.find_or_create_by!(name: account.name, account: account)

    workflow_template = WorkflowTemplate.find_or_create_by!(
      name: "#{account.name} Workflow Template",
      account: account,
      is_main: true
    )

    create_selective_processes(account, workflow_template)
    link_selective_processes(workflow_template)

    JobStatus.create_default_statuses
    Remuneration.create_default_remunerations(account.id)
    JobJourney.create_default_journeys_for_account(account)
    Benefits::DefaultBenefitsCreator.create_for_account(account)
    Skills::DefaultCategoriesCreator.create_for_account(account)
    EmailTemplates::SeedDefaultsService.new(account: account).call

    return unless job_field_template

    job_field_template.account_id = account.id
    job_field_template.is_default = true
    job_field_template.save!
  end

  def create_selective_processes(account, workflow_template)
    selective_process_index = 1

    SelectiveProcess.default_process.each do |attrs|
      SelectiveProcess.find_or_create_by!(
        name: attrs[:name],
        position: attrs[:position],
        status: attrs[:status],
        color: attrs[:color],
        account: account,
        workflow_template_id: workflow_template.id,
        childrens: [ selective_process_index ],
        sub_status: attrs[:sub_status]
      )
      selective_process_index += 1
    end
  end

  def link_selective_processes(workflow_template)
    processes = SelectiveProcess.where(job_id: nil, workflow_template_id: workflow_template.id)

    web_submission_sp = processes.find(&:web_submission?)
    screening_sp = processes.find(&:screening?)
    interview_sp = processes.find(&:interview?)
    rejected_sp = processes.find(&:rejected?)

    return unless [ web_submission_sp, screening_sp, interview_sp, rejected_sp ].all?(&:present?)

    web_submission_sp.update(approved_process_id: screening_sp.id, rejected_process_id: rejected_sp.id)
    screening_sp.update(approved_process_id: interview_sp.id, rejected_process_id: rejected_sp.id)
    interview_sp.update(approved_process_id: nil, rejected_process_id: rejected_sp.id)
    rejected_sp.update(approved_process_id: nil, rejected_process_id: nil)
  end

  def apply_account_saturation_defaults(account)
    return unless account.respond_to?(:web_saturation_amount)

    defaults = Account::DEFAULT_SATURATION
    updates = defaults.select { |attr, value| account.read_attribute(attr).nil? || account.read_attribute(attr) == 0 }
    account.update_columns(updates) if updates.any?
  end

  def ensure_tenant!(tenant)
    unless ActiveRecord::Base.connection.schema_exists?(tenant)
      ApartmentService.create(tenant)
    end

    Apartment::Tenant.switch(tenant) do
      unless ActiveRecord::Base.connection.table_exists?("accounts")
        ActiveRecord::Base.connection.migration_context.migrate
        ActiveRecord::Base.connection.schema_cache.clear!
        ActiveRecord::Base.descendants.each(&:reset_column_information)
      end
    end
  end

  def reindex_tenant(tenant)
    excluded_model_names = Apartment.excluded_models

    Apartment::Tenant.switch(tenant) do
      tenant_models = ApplicationRecord.descendants.select do |model|
        next false unless model.included_modules.include?(Searchable)
        next false if excluded_model_names.include?(model.name)

        true
      end

      tenant_models.each do |model|
        next if model.count.zero?

        model.reindex
      rescue StandardError => e
        Rails.logger.error "[CreateTenantJob] Failed to reindex #{model.name}: #{e.message}"
      end
    end
  rescue StandardError => e
    Rails.logger.error "[CreateTenantJob] Reindex tenant #{tenant} failed: #{e.message}"
  end
end
