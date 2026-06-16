# frozen_string_literal: true

module Scheduling
  class InviteNotificationWorker
    include Sidekiq::Worker
    include PhoneNormalizable

    sidekiq_options queue: :email_delivery, retry: 3

    def perform(link_id, account_id)
      account = Account.find_by(id: account_id)
      return unless account

      Apartment::Tenant.switch!(account.tenant)

      link = SchedulingLink.find_by(id: link_id)
      return unless link

      candidate = link.candidate
      return unless candidate.present?

      channels = link.channels.presence || %w[email]

      notify_via_email(candidate, link, account) if channels.include?("email") && candidate.email.present?
      notify_via_whatsapp(candidate, link, account) if channels.include?("whatsapp")
    end

    private

    def notify_via_email(candidate, link, account)
      SchedulingMailer.scheduling_invite(
        candidate: candidate,
        link: link,
        user: link.created_by,
        account: account
      ).deliver_now
    end

    def notify_via_whatsapp(candidate, link, account)
      phone = normalize_phone(candidate.mobile_phone)
      return unless phone.present?

      candidate_name = candidate.name.to_s.split.first.presence || "Candidato"
      job_title = link.job&.title || link.subject || "Entrevista"
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
        body_text: "Clique no botão abaixo para selecionar o horário da sua entrevista:",
        url: scheduling_url,
        button_text: "Agendar entrevista"
      )
    rescue StandardError => e
      Rails.logger.error "[InviteNotificationWorker] WhatsApp failed: #{e.message}"
    end

    def build_scheduling_url(account_uid, token)
      base_url = ENV.fetch("FRONT_URL") do
        Rails.env.production? ? "https://wedotalent.cc" : "http://localhost:3000"
      end
      "#{base_url}/scheduling/#{account_uid}/#{token}"
    end
  end
end
