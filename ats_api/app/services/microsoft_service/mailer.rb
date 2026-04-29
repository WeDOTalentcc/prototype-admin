# frozen_string_literal: true

module MicrosoftService
  class Mailer
    class << self
      def send_to_address(user:, to:, subject:, html: nil, text: nil, reply_to: nil, save_to_sent: true)
        content_type = html.present? ? "HTML" : "Text"
        content_body = html.presence || text.to_s
        body = build_send_mail_body(subject: subject, content: content_body, content_type: content_type, to: to, reply_to: reply_to, save_to_sent: save_to_sent)
        MicrosoftService::Api.post("/me/sendMail", user, body: body)
      end

      def send_dispatch_message(user:, message:, reply_to: nil, save_to_sent: true)
        content_type = "HTML"
        content_body = message.body.to_s
        body = build_send_mail_body(
          subject: message.subject.to_s,
          content: content_body,
          content_type: content_type,
          to: message.recipient_address.to_s,
          reply_to: reply_to,
          save_to_sent: save_to_sent
        )
        MicrosoftService::Api.post("/me/sendMail", user, body: body)
      end

      def build_send_mail_body(subject:, content:, content_type:, to:, reply_to: nil, save_to_sent: true)
        graph_body = {
          message: {
            subject: subject.to_s,
            body: { contentType: content_type, content: content.to_s },
            toRecipients: [ { emailAddress: { address: to.to_s } } ]
          },
          saveToSentItems: !!save_to_sent
        }
        if reply_to.present?
          graph_body[:message][:replyTo] = [ { emailAddress: { address: reply_to.to_s } } ]
        end
        graph_body
      end
    end
  end
end
