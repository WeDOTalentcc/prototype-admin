# frozen_string_literal: true

module Emails
  module Delivery
    class MailgunStrategy < BaseStrategy
      def deliver(to:, subject:, body:, dispatch:, message:)
        response = DispatchMailer.send_email(
          to: to,
          subject: subject,
          body: body,
          from: sender_email(dispatch)
        ).deliver_now

        { success: true, provider: "mailgun", message_id: response.message_id }
      end

      private

      def sender_email(dispatch)
        dispatch.user&.email || ENV.fetch("MAILGUN_EMAIL", "contato@wedotalent.cc")
      end
    end
  end
end
