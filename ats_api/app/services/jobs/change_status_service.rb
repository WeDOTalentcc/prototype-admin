# frozen_string_literal: true

module Jobs
  class ChangeStatusService
    ALLOWED_TRANSITIONS = {
      "Rascunho" => [ "Ativa", "Aguardando aprovação" ],
      "Aguardando aprovação" => [ "Aprovada", "Rascunho" ],
      "Aprovada" => [ "Ativa", "Rascunho" ],
      "Ativa" => [ "Paralisada", "Fechada (preenchida)", "Fechada (expirada)", "Cancelada", "Concluída" ],
      "Paralisada" => [ "Ativa", "Reaberta", "Cancelada" ],
      "Reaberta" => [ "Ativa", "Paralisada", "Cancelada" ],
      "Interna" => [ "Ativa", "Paralisada", "Cancelada" ],
      "Fechada (preenchida)" => [ "Reaberta", "Arquivada" ],
      "Fechada (expirada)" => [ "Reaberta", "Arquivada" ],
      "Cancelada" => [ "Reaberta", "Arquivada" ],
      "Concluída" => [ "Reaberta", "Arquivada" ],
      "Arquivada" => [ "Reaberta" ]
    }.freeze

    def initialize(job:, target_status_id:, reason: nil)
      @job = job
      @target_status_id = target_status_id
      @reason = reason
    end

    def call
      return error("Status de destino não encontrado") unless target_status
      return error("Status atual não encontrado") unless current_status_name

      unless transition_allowed?
        return error(
          "Transição não permitida de '#{current_status_name}' para '#{target_status.name}'",
          allowed: allowed_targets
        )
      end

      update_job
    end

    private

    attr_reader :job, :target_status_id, :reason

    def target_status
      @target_status ||= JobStatus.find_by(id: target_status_id)
    end

    def current_status_name
      @current_status_name ||= job.job_status&.name || initial_status_name
    end

    def initial_status_name
      return nil unless job.job_status_id.nil?

      "Rascunho"
    end

    def transition_allowed?
      allowed_targets.include?(target_status.name)
    end

    def allowed_targets
      ALLOWED_TRANSITIONS[current_status_name] || []
    end

    def update_job
      attrs = { job_status_id: target_status.id }
      attrs[:reason_for_pause] = reason if reason.present?
      attrs[:is_active] = resolve_is_active
      attrs[:is_archived] = target_status.name == "Arquivada"

      if job.update(attrs)
        success
      else
        error(job.errors.full_messages.join(", "))
      end
    end

    def resolve_is_active
      %w[Ativa Reaberta].include?(target_status.name)
    end

    def success
      { success: true, job: job, target_status: target_status }
    end

    def error(message, allowed: nil)
      result = { success: false, error: message }
      result[:allowed_transitions] = allowed if allowed.present?
      result
    end
  end
end
