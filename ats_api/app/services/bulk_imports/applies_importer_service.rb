module BulkImports
  class AppliesImporterService < BaseService
    private

    def process_row(row, header_map)
      Apartment::Tenant.switch!(@account.tenant)

      attributes = build_attributes_from(row, header_map)
      attributes[:account_id] = @account.id

      candidate = find_or_initialize_candidate(attributes)

      permitted_attrs = attributes.stringify_keys.slice(*Candidate.column_names)
      candidate.assign_attributes(permitted_attrs)
      candidate.account_id ||= @account.id
      candidate.save

      external_job_id = attributes["external_job_id"]
      raise "Vaga não pôde ser localizada: 'external_job_id' está ausente" if external_job_id.blank?

      job = Job.find_by(external_id: external_job_id)
      raise "Vaga com external_id '#{external_job_id}' não encontrada" if job.nil?

      selective_process = job.selective_processes.first
      raise "Vaga sem processo seletivo vinculado" if selective_process.nil?

      apply = Apply.find_or_initialize_by(candidate: candidate, job: job, selective_process: selective_process)
      apply.assign_attributes(
        attributes.slice(:is_deleted).merge(
          external_candidate_id: attributes[:external_candidate_id],
          external_job_id: external_job_id,
          account_id: @account.id
        )
      )
      apply.save
    end


    def find_or_initialize_candidate(attributes)
      return Candidate.find_or_initialize_by(external_id: attributes["external_candidate_id"]) if attributes["external_candidate_id"].present?
      return Candidate.find_or_initialize_by(email: attributes["email"]) if attributes["email"].present?
      return Candidate.find_or_initialize_by(mobile_phone: attributes["mobile_phone"]) if attributes["mobile_phone"].present?

      raise "Candidato não pôde ser identificado: forneça ao menos 'external_id', 'email' ou 'mobile_phone'"
    end
  end
end
