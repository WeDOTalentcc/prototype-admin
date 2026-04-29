# frozen_string_literal: true

module Evaluations
  class DeclineNotificationJob < ApplicationJob
    queue_as :default

    def perform(evaluation_candidate_id, account_id)
      return unless account_id

      account = Account.find_by(id: account_id)
      return unless account

      Apartment::Tenant.switch!(account.tenant)

      evaluation_candidate = EvaluationCandidate.find_by(id: evaluation_candidate_id)
      return unless evaluation_candidate
      return unless evaluation_candidate.declined?

      move_apply_to_rejected(evaluation_candidate)
      send_notification(evaluation_candidate)

      Rails.logger.info "✅ [DeclineNotificationJob] Notificação de recusa enviada para evaluation_candidate #{evaluation_candidate_id}"
    rescue StandardError => e
      Rails.logger.error "❌ [DeclineNotificationJob] Error: #{e.class} - #{e.message}"
      Rails.logger.error e.backtrace.first(5).join("\n")
      raise e
    end

    private

    def move_apply_to_rejected(evaluation_candidate)
      return unless evaluation_candidate.apply_id.present?

      current_apply = Apply.find_by(id: evaluation_candidate.apply_id)
      return unless current_apply&.job_id.present?

      rejected_process = SelectiveProcess.find_by(
        job_id: current_apply.job_id,
        status: SelectiveProcess.statuses[:rejected]
      )
      return unless rejected_process

      current_apply.update(
        selective_process_id: rejected_process.id,
        selective_process_status: "candidate_withdrew",
        sub_status: "candidate_withdrew",
        updated_at: Time.current
      )

      Rails.logger.info "📋 [DeclineNotificationJob] Apply ##{current_apply.id} movido para 'Reprovados' (candidate_withdrew)"
    end

    def send_notification(evaluation_candidate)
      user = evaluation_candidate.user
      return unless user.present?

      candidate = evaluation_candidate.candidate
      account = evaluation_candidate.account

      mail = EvaluationMailer.with(
        evaluation_candidate: evaluation_candidate,
        user: user
      ).decline_notification

      body_html = mail.html_part&.body&.to_s || mail.body.to_s

      dispatch_params = {
        account_id: account.id,
        user_id: user.id,
        reference_type: "User",
        reference_id: user.id,
        channel_type: "email",
        status: 0,
        name: "Candidato recusou participar da avaliação",
        target_type: "ids",
        target_payload: { ids: [ user.id ] },
        user_ids: [ user.id ],
        subject: "#{candidate&.name} recusou a avaliação — #{evaluation_candidate.job&.title}",
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
