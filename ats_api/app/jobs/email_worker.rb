class EmailWorker < ApplicationJob
  queue_as :low
  sidekiq_options retry: 10

  def perform(dispatch_message_id, account_id)
    account = Account.find_by(id: account_id)
    return unless account

    Apartment::Tenant.switch(account.tenant) do
      message = DispatchMessage.find_by(id: dispatch_message_id)
      return unless message&.account
      if message.recipient_address.blank?
        Rails.logger.warn "⏸️ [EmailWorker] Skipping dispatch_message_id=#{dispatch_message_id} - recipient_address blank"
        return
      end
      return if message.sent? || message.processing?

      message.processing!

      begin
        mail = DispatchMailer.with(message: message).dispatch_email.deliver_now

        message.update!(
          status: :sent,
          sent_at: Time.current,
          provider_response: { message_id: mail.message_id }
        )
      rescue => e
        message.failed!
        message.update_column(:provider_response, { error: e.message })
        raise e
      end
    end
  end
end
