# frozen_string_literal: true

class NotificationSerializer
  include JSONAPI::Serializer

  set_type :notification

  attributes :title, :notification_type, :category, :priority,
             :proactive_type, :action_url, :action_label,
             :status, :channel, :alert_key, :metadata,
             :reference_type, :reference_id,
             :sent_at, :read_at, :created_at, :updated_at

  attribute :message do |record|
    record.content
  end

  attribute :content do |record|
    record.content
  end

  attribute :is_read do |record|
    record.read?
  end

  attribute :related_job_id do |record|
    record.related_job_id
  end

  attribute :related_candidate_id do |record|
    record.related_candidate_id
  end
end
