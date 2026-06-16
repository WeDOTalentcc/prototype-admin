class MessageJob < ApplicationJob
  queue_as :default
  sidekiq_options retry: false

  def perform(message, user)
    MessageSampleService.call(message, user)
  end
end
