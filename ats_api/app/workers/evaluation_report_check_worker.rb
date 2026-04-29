class EvaluationReportCheckWorker
  include Sidekiq::Worker

  def perform(*args)
    Account.pluck(:tenant).each do |tenant|
      Apartment::Tenant.switch(tenant) do
        process_evaluations_for_tenant
      end
    end
  end

  private

  def process_evaluations_for_tenant
    evaluations = Evaluation.where.not(parent_evaluation_id: nil)
                           .where.not(job_id: nil)
                           .where(is_deleted: false)
                           .where(report_generated_at: nil)

    evaluations.find_each do |evaluation|
      process_evaluation(evaluation)
    end
  end

  def process_evaluation(evaluation)
    # Verificar se há evaluation_candidates completados para esta avaliação
    evaluation_candidates = EvaluationCandidate.where(
      evaluation_id: evaluation.id,
      job_id: evaluation.job_id,
      completed: true,
      is_deleted: false
    )

    # Se não há candidatos completados, pular esta avaliação
    return if evaluation_candidates.empty?

    # Verificar se passou o tempo necessário (report_date em dias) desde a criação
    return unless should_generate_report?(evaluation)

    # Gerar o relatório
    generate_report(evaluation)
  end

  def should_generate_report?(evaluation)
    return false unless evaluation.report_date.present?

    # Calcular a data limite baseada no report_date (em dias)
    days_ago = evaluation.report_date.days.ago

    # Verificar se a avaliação foi criada antes da data limite
    evaluation.created_at <= days_ago
  end

  def generate_report(evaluation)
    begin
      Rails.logger.info "[EvaluationReportCheckWorker] Gerando relatório para evaluation_id: #{evaluation.id}, job_id: #{evaluation.job_id}"

      report = EvaluationReportService.call(
        evaluation_id: evaluation.id,
        job_id: evaluation.job_id
      )

      if report.success?
        # Atualizar a data de geração do relatório
        evaluation.update(report_generated_at: Time.current)
        content = generate_html(evaluation, report)
        new_message = Message.create(
          content: content,
          reference_type: "User",
          reference_id: evaluation.user_id,
          entity: Message::ROLE_SYSTEM,
          status: Message::STATUS_NOT_ANSWERED,
          account_id: evaluation.account_id
        )
        ActionCable.server.broadcast("messages_user_#{evaluation.user_id}", {
          id: new_message.id,
          content: new_message.content,
          entity: new_message.entity,
          status: new_message.status,
          metadata: new_message.metadata,
          created_at: new_message.created_at
        })
        Rails.logger.info "[EvaluationReportCheckWorker] Relatório gerado com sucesso para evaluation_id: #{evaluation.id}"
      else
        Rails.logger.error "[EvaluationReportCheckWorker] Erro ao gerar relatório para evaluation_id: #{evaluation.id} - #{report.error}"
      end
    rescue StandardError => e
      Rails.logger.error "[EvaluationReportCheckWorker] Erro inesperado ao gerar relatório para evaluation_id: #{evaluation.id} - #{e.message}"
    end
  end

  def generate_html(evaluation, report)
    content = "<p class='f18'>Segue o relatório da avaliação '#{evaluation.name}' para a vaga '#{evaluation.job.title}':</p>"
    candidates = report.data["candidates"] || []

    if candidates.any?
      content += "<p class='f16'>Candidatos avaliados:</p>"
      content += "<ul class='f14'>"
      candidates.each do |candidate|
        content += "<li class='py-2'><strong>#{candidate['name']}</strong>: #{candidate['description']}</li>"
        content += "<hr />"
      end
      content += "</ul>"
    else
      content += "<p class='f14'>Nenhum candidato foi avaliado neste relatório.</p>"
    end

    content
  end
end
