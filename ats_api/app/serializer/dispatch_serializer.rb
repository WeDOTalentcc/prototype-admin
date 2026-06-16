# frozen_string_literal: true

class DispatchSerializer
  include JSONAPI::Serializer

  attributes :channel_type, :subject, :status, :name, :created_at, :updated_at

  attribute :sent_at do |dispatch|
    dispatch.dispatch_messages.where(status: [ :sent, :delivered, :opened ]).minimum(:sent_at)
  end

  attribute :recipient_count do |dispatch|
    dispatch.dispatch_messages.size
  end

  attribute :opened_count do |dispatch|
    dispatch.dispatch_messages.where(status: :opened).size
  end

  attribute :delivered_count do |dispatch|
    dispatch.dispatch_messages.where(status: [ :delivered, :opened ]).size
  end

  attribute :failed_count do |dispatch|
    dispatch.dispatch_messages.where(status: :failed).size
  end

  attribute :recipients do |dispatch|
    dispatch.dispatch_messages.includes(:recipient).map do |dm|
      {
        name: dm.recipient&.try(:name),
        email: dm.recipient_address || dm.recipient&.try(:email),
        status: dm.status,
        sent_at: dm.sent_at,
        opened_at: dm.opened_at
      }
    end
  end
end
