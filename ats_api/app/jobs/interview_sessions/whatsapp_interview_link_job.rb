# frozen_string_literal: true

module InterviewSessions
  class WhatsappInterviewLinkJob < ApplicationJob
    queue_as :email_delivery
    sidekiq_options retry: 3

    def perform(phone, public_url)
      Meta::WhatsappService.send_link(
        phone: phone,
        body_text: "Click the button below to start your voice interview:",
        url: public_url,
        button_text: "Start Interview"
      )
    end
  end
end
