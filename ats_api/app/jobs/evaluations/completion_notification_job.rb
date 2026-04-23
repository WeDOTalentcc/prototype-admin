# frozen_string_literal: true

module Evaluations
  class CompletionNotificationJob < ApplicationJob
    queue_as :default

    def perform(evaluation_candidate_id, account_id)
      return unless account_id

      account = Account.find_by(id: account_id)
      return unless account

      Apartment::Tenant.switch!(account.tenant)

      evaluation_candidate = EvaluationCandidate.find_by(id: evaluation_candidate_id)
      return unless evaluation_candidate
      return unless evaluation_candidate.completed?

      create_internal_message(evaluation_candidate)
      send_notification(evaluation_candidate)

      Rails.logger.info "✅ [CompletionNotificationJob] Notificação de conclusão enviada para evaluation_candidate #{evaluation_candidate_id}"
    rescue StandardError => e
      Rails.logger.error "❌ [CompletionNotificationJob] Error: #{e.class} - #{e.message}"
      Rails.logger.error e.backtrace.first(5).join("\n")
      raise e
    end

    private

    def create_internal_message(evaluation_candidate)
      user = evaluation_candidate.user
      return unless user.present?

      candidate = evaluation_candidate.candidate
      evaluation = evaluation_candidate.evaluation
      job = evaluation_candidate.job

      content = <<~HTML
        <p class='f14'>O candidato #{candidate&.name} concluiu a avaliação <strong>#{evaluation&.name}</strong>.</p>
        <p class='f12'>Vaga: #{job&.title}.</p>
      HTML

      Message.create(
        content: content.strip,
        reference_type: "User",
        reference_id: user.id,
        entity: Message::ROLE_SYSTEM,
        status: Message::STATUS_NOT_ANSWERED,
        account_id: user.account_id
      )
    end

    def send_notification(evaluation_candidate)
      user = evaluation_candidate.user
      return unless user.present?

      candidate = evaluation_candidate.candidate
      account = evaluation_candidate.account

      mail = EvaluationMailer.with(
        evaluation_candidate: evaluation_candidate,
        user: user
      ).completion_notification

      body_html = mail.html_part&.body&.to_s || mail.body.to_s

      dispatch_params = {
        account_id: account.id,
        user_id: user.id,
        reference_type: "User",
        reference_id: user.id,
        channel_type: "email",
        status: 0,
        name: "Candidato concluiu avaliação",
        target_type: "ids",
        target_payload: { ids: [ user.id ] },
        user_ids: [ user.id ],
        subject: "#{candidate&.name} concluiu a avaliação — #{evaluation_candidate.job&.title}",
        body: body_html
      }

      service = Dispatches::CreateService.new(
        user: user,
        account: account,
        params: dispatch_params
      )

      service.call if service
    end
  end
end
