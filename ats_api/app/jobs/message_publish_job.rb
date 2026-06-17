# frozen_string_literal: true

class MessagePublishJob < ApplicationJob
  queue_as :critical
  sidekiq_options retry: 3

  def perform(message_id, tenant)
    Apartment::Tenant.switch(tenant) do
      message = Message.find_by(id: message_id)
      return unless message

      message.execute_publish_event
    end
  rescue => e
    Rails.logger.error "[MessagePublishJob] Error publishing message #{message_id}: #{e.class} - #{e.message}"
    Rails.logger.error e.backtrace&.first(5)&.join("\n")
    raise
  end
end
