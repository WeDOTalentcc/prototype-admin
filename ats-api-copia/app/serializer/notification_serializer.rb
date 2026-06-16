# frozen_string_literal: true

class NotificationSerializer
  include JSONAPI::Serializer

  attributes(
    :id,
    :user_id,
    :company_id,
    :notification_type,
    :title,
    :message,
    :status,
    :priority,
    :action_url,
    :metadata,
    :read_at,
    :dismissed_at,
    :created_at,
    :updated_at
  )
end
