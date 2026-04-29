# frozen_string_literal: true

module Scheduling
  class BookingNotificationWorker
    include Sidekiq::Worker
    include PhoneNormalizable

    sidekiq_options queue: :default, retry: 3

    def perform(link_id, meeting_id, account_id)
      account = Account.find_by(id: account_id)
      return unless account

      Apartment::Tenant.switch!(account.tenant)

      link = SchedulingLink.find_by(id: link_id)
      meeting = Meeting.find_by(id: meeting_id)
      return unless link && meeting

      user = link.created_by
      candidate = link.candidate

      notify_recruiter(user, meeting, link)
      notify_candidate(candidate, meeting, link) if candidate&.email.present?
      notify_candidate_whatsapp(candidate, meeting, link) if candidate.present?
    rescue StandardError => e
      Rails.logger.error "[BookingNotificationWorker] Error: #{e.message}"
      raise
    end

    private

    def notify_recruiter(user, meeting, link)
      return unless user&.email.present?

      SchedulingMailer.booking_confirmed_recruiter(
        user: user,
        meeting: meeting,
        link: link
      ).deliver_later
    end

    def notify_candidate(candidate, meeting, link)
      SchedulingMailer.booking_confirmed_candidate(
        candidate: candidate,
        meeting: meeting,
        link: link
      ).deliver_later
    end

    def notify_candidate_whatsapp(candidate, meeting, link)
      phone = normalize_phone(candidate.mobile_phone)
      return unless phone.present?

      tz = "America/Sao_Paulo"
      date = I18n.l(meeting.start_time.in_time_zone(tz).to_date, format: :long, locale: :"pt-BR")
      time_range = "#{meeting.start_time.in_time_zone(tz).strftime('%H:%M')} - #{meeting.end_time.in_time_zone(tz).strftime('%H:%M')}"
      meeting_link = meeting.join_url.presence || meeting.location.presence || "A confirmar"
      instructions = "Acesse o link na data e horário informados acima."

      components = [ {
        type: "body",
        parameters: [
          { type: "text", text: candidate.name.to_s.split.first.presence || "Candidato" },
          { type: "text", text: link.job&.title || link.subject || "Entrevista" },
          { type: "text", text: date },
          { type: "text", text: time_range },
          { type: "text", text: meeting_link },
          { type: "text", text: instructions }
        ]
      } ]

      template = ENV.fetch("META_WHATSAPP_TEMPLATE_SCHEDULING_CONFIRMED", "confirmacao_entrevista")
      Meta::WhatsappService.send_message_by_template(phone, template, "pt_BR", components)
    rescue StandardError => e
      Rails.logger.error "[BookingNotificationWorker] WhatsApp failed: #{e.message}"
    end
  end
end
