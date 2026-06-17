# frozen_string_literal: true

module Notifications
  class DeliveryJob < ApplicationJob
    queue_as :default

    def perform(notification_id)
      notification = AgentNotification.find_by(id: notification_id)
      return unless notification

      Notifications::DeliveryService.new(notification).call
    end
  end
end
