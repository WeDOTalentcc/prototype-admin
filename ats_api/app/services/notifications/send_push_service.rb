# frozen_string_literal: true

module Notifications
  class SendPushService
    def initialize(user:, notification_type:, content:, channel: "web",
                   reference: nil, alert_key: nil, metadata: {},
                   title: nil, category: nil, priority: "normal",
                   proactive_type: nil, action_url: nil, action_label: nil)
      @user = user
      @notification_type = notification_type
      @content = content
      @channel = channel
      @reference = reference
      @alert_key = alert_key
      @metadata = metadata
      @title = title
      @category = category
      @priority = priority
      @proactive_type = proactive_type
      @action_url = action_url
      @action_label = action_label
    end

    def call
      return duplicate_result if duplicate?

      notification = build_notification
      return error("Failed to save notification") unless notification.save

      Notifications::DeliveryJob.perform_later(notification.id)
      success(notification)
    rescue StandardError => e
      Rails.logger.error "[#{self.class.name}] #{e.message}"
      error(e.message)
    end

    private

    attr_reader :user, :notification_type, :content, :channel, :reference,
                :alert_key, :metadata, :title, :category, :priority,
                :proactive_type, :action_url, :action_label

    def duplicate?
      alert_key.present? && AgentNotification.exists?(alert_key: alert_key)
    end

    def build_notification
      AgentNotification.new(
        user: user,
        notification_type: notification_type,
        channel: channel,
        content: content,
        reference: reference,
        alert_key: alert_key,
        metadata: metadata,
        status: "pending",
        title: title,
        category: category,
        priority: priority,
        proactive_type: proactive_type,
        action_url: action_url,
        action_label: action_label
      )
    end

    def success(notification) = { success: true, notification: notification }
    def error(message) = { success: false, error: message }
    def duplicate_result = { success: false, error: "duplicate", alert_key: alert_key }
  end
end
