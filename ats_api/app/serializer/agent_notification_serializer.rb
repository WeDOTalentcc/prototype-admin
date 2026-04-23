# frozen_string_literal: true

class AgentNotificationSerializer
  include JSONAPI::Serializer

  attributes :notification_type, :channel, :status, :content,
             :reference_type, :reference_id, :alert_key,
             :metadata, :sent_at, :read_at, :created_at

  attribute :read do |notification|
    notification.read?
  end
end
