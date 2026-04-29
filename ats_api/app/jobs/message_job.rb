class MessageJob < ApplicationJob
  queue_as :default
  sidekiq_options retry: false

  def perform(message_id, user_id)
    message = Message.find_by(id: message_id)
    user = User.find_by(id: user_id)
    return unless message && user
    MessageSampleService.call(message, user)
  rescue => e
    Rails.logger.error("MessageJob error message_id=#{message_id} user_id=#{user_id} #{e.class} #{e.message}")
  end
end
