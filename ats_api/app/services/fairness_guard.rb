# frozen_string_literal: true

module FairnessGuard
  BULK_REJECTION_THRESHOLD = 10

  DISCLAIMER = <<~MSG.freeze
    Aviso de Fairness: esta acao de rejeicao em massa e baseada em criterios tecnicos do processo seletivo. \
    Decisoes finais de selecao nao devem considerar atributos protegidos (genero, idade, raca, religiao, estado civil). \
    Recomenda-se revisao humana antes da comunicacao aos candidatos.
  MSG

  def self.audit_bulk_rejection(user_id:, job_id:, select_all_params:)
    Rails.logger.warn(
      "[FAIRNESS_AUDIT] bulk_rejection: user_id=#{user_id} job_id=#{job_id} " \
      "params=#{select_all_params.to_json}"
    )
  end

  def self.bulk_rejection_warning(select_all_params)
    filters = select_all_params.to_h
    has_broad_scope = filters.blank? ||
                      (filters.keys - %w[job_id account_id]).empty?

    return nil unless has_broad_scope

    "Atencao: voce esta rejeitando candidatos sem filtros especificos. #{DISCLAIMER}"
  end
end
