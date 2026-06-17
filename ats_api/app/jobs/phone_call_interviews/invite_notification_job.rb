# frozen_string_literal: true

module PhoneCallInterviews
  class InviteNotificationJob < ApplicationJob
    include PhoneNormalizable

    queue_as :email_delivery

    def perform(evaluation_candidate_id, account_id, channels = %w[email whatsapp])
      account = Account.find_by(id: account_id)
      return unless account

      Apartment::Tenant.switch!(account.tenant)

      ec = EvaluationCandidate.find_by(id: evaluation_candidate_id)
      return unless ec&.scheduling_link

      candidate = ec.candidate
      return unless candidate

      link = ec.scheduling_link

      notify_via_email(candidate, link, ec, account) if channels.include?("email") && candidate.email.present?
      notify_via_whatsapp(candidate, link, ec, account) if channels.include?("whatsapp")
    end

    private

    def notify_via_email(candidate, link, ec, account)
      SchedulingMailer.scheduling_invite(
        candidate: candidate,
        link: link,
        user: ec.user,
        account: account
      ).deliver_now
    end

    def notify_via_whatsapp(candidate, link, ec, account)
      phone = normalize_phone(candidate.mobile_phone)
      return unless phone.present?

      candidate_name = candidate.name.to_s.split.first.presence || "Candidato"
      job_title = ec.job&.title || link.subject || "Entrevista"

      components = [ {
        type: "body",
        parameters: [
          { type: "text", text: candidate_name },
          { type: "text", text: job_title }
        ]
      } ]
      Meta::WhatsappService.send_message_by_template(phone, "entrevista", "pt_BR", components)

      sleep(10)

      scheduling_url = build_scheduling_url(account.uid, link.token)
      Meta::WhatsappService.send_link(
        phone: phone,
        body_text: ec.custom_invite_message.presence || "Clique no botão abaixo para agendar sua entrevista por telefone:",
        url: scheduling_url,
        button_text: "Agendar entrevista"
      )
    rescue StandardError => e
      Rails.logger.error "❌ [PhoneCallInterviews::InviteNotificationJob] WhatsApp failed: #{e.message}"
    end

    def build_scheduling_url(account_uid, token)
      base_url = ENV.fetch("FRONT_URL") do
        Rails.env.production? ? "https://wedotalent.cc" : "http://localhost:3000"
      end
      "#{base_url}/scheduling/#{account_uid}/#{token}"
    end
  end
end
