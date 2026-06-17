# frozen_string_literal: true

class DomainMessageChannel < ApplicationCable::Channel
  def self.broadcast_message(user_id:, domain:, domain_reference_id:, payload:)
    channel = "domain_messages_user_#{user_id}_#{domain}_#{domain_reference_id}"
    Rails.logger.info "🔔 [DomainMessageChannel] Broadcasting to: #{channel}"
    Rails.logger.info "🔔 [DomainMessageChannel] Payload keys: #{payload.keys}"
    ActionCable.server.broadcast(channel, payload)
  end

  private

  def after_authentication
    unless params[:domain].present?
      Rails.logger.warn "🔔 [DomainMessageChannel] REJECTED - no domain param"
      return reject
    end

    unless params[:domain_reference_id].present?
      Rails.logger.warn "🔔 [DomainMessageChannel] REJECTED - no domain_reference_id param"
      return reject
    end

    stream_from channel_name
  end

  def channel_name
    "domain_messages_user_#{current_user.id}_#{params[:domain]}_#{params[:domain_reference_id]}"
  end
end
