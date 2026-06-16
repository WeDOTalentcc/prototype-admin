class Chatbot::ReplyProcessorJob < ApplicationJob
  queue_as :default

  # Desabilita retry automático do Sidekiq
  sidekiq_options retry: false

  def perform(message_id, account_id = nil)
    return if account_id.nil?

    account = Account.find_by(id: account_id)
    return if account.nil?

    Apartment::Tenant.switch!(account.tenant)
    begin
      Chatbot::Evaluation::ReplyProcessor.new(message_id, account).call
    ensure
      Apartment::Tenant.reset if account_id
    end
  end
end
