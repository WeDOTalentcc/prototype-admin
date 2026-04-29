module BulkImports
  class JobsImporterService < BaseService
    private

    def process_row(row, header_map)
      Apartment::Tenant.switch!(@account.tenant)
      attributes = build_attributes_from(row, header_map)
      attributes[:account_id] = @account.id

      job = Job.where(external_id: attributes[:external_id]).first

      if job.present?
        job.update(attributes)
        return job
      end

      job = Job.create(attributes)
      job.create_default_selective_processes if job.persisted? && job.selective_processes.empty?
      job
    end
  end
end
