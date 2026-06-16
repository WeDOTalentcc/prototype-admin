# frozen_string_literal: true

module InterviewSessions
  class InviteNotificationJob < ApplicationJob
    queue_as :email_delivery

    def perform(interview_session_id, account_id, channels)
      account = Account.find_by(id: account_id)
      return unless account

      Apartment::Tenant.switch!(account.tenant)

      session = InterviewSession.find_by(id: interview_session_id)
      return unless session

      candidate = session.candidate
      return unless candidate

      channels = Array(channels)

      notify_via_email(session) if channels.include?("email") && candidate.email.present?
      notify_via_whatsapp(session, candidate) if channels.include?("whatsapp") && candidate.mobile_phone.present?

      Rails.logger.info "🔄 [InterviewSessions::InviteNotificationJob] Notifications sent"
      Rails.logger.info "   Session: #{session.id} | Channels: #{channels.join(', ')}"
    rescue StandardError => e
      Rails.logger.error "❌ [InterviewSessions::InviteNotificationJob] Error: #{e.message}"
      Rails.logger.error e.backtrace.first(5).join("\n")
    end

    private

    def notify_via_email(session)
      evaluation_candidate = session.evaluation_candidate
      return unless evaluation_candidate

      evaluation = session.evaluation
      stored = Array(evaluation&.notification_channels)
      session_channel = session.interview_type == "phone" ? :phone : :voice
      channels = stored.any? ? stored.map(&:to_sym) : [ session_channel ]

      interview_sessions = InterviewSession.bulk_find_or_create_for_channels(
        evaluation_candidate: evaluation_candidate,
        channels: channels,
        created_by: session.created_by
      )
      interview_sessions[session_channel] ||= session

      Evaluations::UnifiedInviteService.new(
        evaluation_candidate: evaluation_candidate,
        user: session.created_by,
        channels: channels,
        interview_sessions: interview_sessions
      ).call
    end

    def notify_via_whatsapp(session, candidate)
      phone = normalize_phone(candidate.mobile_phone)
      return unless phone.present?

      candidate_name = candidate.name.to_s.split.first.presence || "Candidato"
      job_title = session.job_context["title"] || "Entrevista"

      components = [ {
        type: "body",
        parameters: [
          { type: "text", text: candidate_name },
          { type: "text", text: job_title }
        ]
      } ]

      Meta::WhatsappService.send_message_by_template(phone, "entrevista", "pt_BR", components)

      InterviewSessions::WhatsappInterviewLinkJob.perform_in(10.seconds, phone, session.public_url)
    end

    def normalize_phone(phone)
      return nil if phone.blank?

      cleaned = phone.gsub(/\D/, "")
      cleaned = "55#{cleaned}" unless cleaned.start_with?("55")
      cleaned
    end
  end
end
