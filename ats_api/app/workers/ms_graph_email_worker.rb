# frozen_string_literal: true

class MsGraphEmailWorker
  include Sidekiq::Worker

  sidekiq_options retry: 5, queue: :default

  def perform(message_id, user_id, options = {})
    user = User.find_by(id: user_id)
    account = user&.account
    Apartment::Tenant.switch!(account.tenant) if account

    message = DispatchMessage.find_by(id: message_id)
    return unless message && user
    return unless message.pending?

    message.update!(status: :processing, attempts: message.attempts + 1)

    if Rails.env.development?
      deliver_via_mailpit(message, user)
    else
      deliver_via_microsoft_graph(message, user, options)
    end

    message.update!(status: :sent, sent_at: Time.current)
  rescue => error
    message&.update!(status: :failed, provider_response: { error: { class: error.class.name, message: error.message } })
    raise error
  end

  private

  def deliver_via_mailpit(message, user)
    DispatchMailer.send_email(
      to: message.recipient_address,
      subject: message.subject,
      body: message.body,
      from: user.email.presence || ENV.fetch("MAILGUN_EMAIL", "contato@wedotalent.cc")
    ).deliver_now
  end

  def deliver_via_microsoft_graph(message, user, options)
    response = MicrosoftService::Mailer.send_dispatch_message(
      user: user,
      message: message,
      reply_to: options["reply_to"],
      save_to_sent: options["save_to_sent"].nil? ? true : !!options["save_to_sent"]
    )

    if response.is_a?(Hash)
      message.update!(provider_response: response)
    end
  end
end
