module BulkImports
  class CandidatesImporterService < BaseService
    private

    def process_row(row, header_map)
      Apartment::Tenant.switch!(@account.tenant)
      attributes = build_attributes_from(row, header_map)

      attributes[:account_id] = @account.id
      candidate = Candidate.where(external_id: attributes[:external_id]).first

      if candidate.present?
        candidate.update(attributes)
        return candidate
      end

      Candidate.create(attributes)
    end
  end
end
