# frozen_string_literal: true

module Notifications
  class DeliveryService
    CHANNEL_HANDLERS = {
      "web" => :deliver_web,
      "whatsapp" => :deliver_whatsapp,
      "teams" => :deliver_teams
    }.freeze

    def initialize(notification)
      @notification = notification
    end

    def call
      handler = CHANNEL_HANDLERS.fetch(notification.channel) { :deliver_web }
      send(handler)
      notification.mark_as_sent!
    rescue StandardError => e
      Rails.logger.error "[#{self.class.name}] Delivery failed on #{notification.channel}: #{e.message}"
      notification.mark_as_failed!
    end

    private

    attr_reader :notification

    def deliver_web
      ActionCable.server.broadcast(
        "notifications_user_#{notification.user_id}",
        {
          type: "agent_notification",
          data: NotificationSerializer.new(notification).serializable_hash
        }
      )
    end

    def deliver_whatsapp
      phone = notification.user.mobile_phone.presence || notification.user.phone
      return unless phone.present?

      Meta::WhatsappService.new.send_text_message(phone, notification.content)
    end

    def deliver_teams
      MicrosoftService::Teams.new(user: notification.user).send_message(
        user: notification.user,
        content: notification.content,
        content_type: "text"
      )
    end
  end
end
