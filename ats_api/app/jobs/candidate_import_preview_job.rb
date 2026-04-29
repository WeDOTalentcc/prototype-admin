class CandidateImportPreviewJob < ApplicationJob
  queue_as :default

  def perform(data_file_ids:, user_id:)
    return unless (user = User.find_by(id: user_id))

    DataFile.where(id: data_file_ids).find_each do |data_file|
      next unless data_file.file.attached?

      import_candidate_from(data_file, user)
    end
  end

  private

  def import_candidate_from(data_file, user)
    text = extract_text(data_file)
    return if text.blank?

    candidate_data = RecruitAgentService.extract_candidate_data(text)
    return unless candidate_data

    Candidate.create(
      name: candidate_data.dig(:basics, :name) || "Candidato Importado ##{data_file.id}",
      account_id: user.account_id
    )

    Rails.logger.info ">>>>> JSON Recebido para DataFile ##{data_file.id}: #{candidate_data.inspect}"
  rescue => e
    Rails.logger.error "Falha ao importar candidato do DataFile ##{data_file.id}: #{e.message}"
    Rails.logger.error e.backtrace.join("\n")
  end

  def extract_text(data_file)
    io = StringIO.new(data_file.file.download)
    yomu = Yomu.new(io)
    yomu.text
  end
end
