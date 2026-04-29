# frozen_string_literal: true

module Emails
  module Delivery
    class MsGraphStrategy < BaseStrategy
      def deliver(to:, subject:, body:, dispatch:, message:)
        if Rails.env.development?
          deliver_via_mailpit(to: to, subject: subject, body: body, dispatch: dispatch)
        else
          deliver_via_microsoft_graph(to: to, subject: subject, body: body, dispatch: dispatch)
        end
      end

      private

      def deliver_via_mailpit(to:, subject:, body:, dispatch:)
        DispatchMailer.send_email(
          to: to,
          subject: subject,
          body: body,
          from: dispatch.user&.email.presence || ENV.fetch("MAILGUN_EMAIL", "contato@wedotalent.cc")
        ).deliver_now
        { success: true, provider: "mailpit", development: true }
      end

      def deliver_via_microsoft_graph(to:, subject:, body:, dispatch:)
        response = MicrosoftService::Mailer.send_to_address(
          user: dispatch.user,
          to: to,
          subject: subject,
          html: body,
          save_to_sent: true
        )
        { success: true, provider: "ms_graph", response: response }
      end
    end
  end
end
