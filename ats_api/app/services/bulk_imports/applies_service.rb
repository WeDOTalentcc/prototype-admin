module BulkImports
  class AppliesService
    def self.call
      BulkImports::CandidatesService.call.merge(
        external_job_id: { label: "ID Externo da Vaga", required: true },
        is_deleted: { label: "Aplicação Excluída? (true/false)", required: false }
      )
    end
  end
end
