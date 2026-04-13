# frozen_string_literal: true

require "bunny"
require "json"

# LIA-E03 (Rails mirror): Event publisher with version field for LIA Python integration
#
# Publishes events to RabbitMQ exchange  with proper versioning.
# Mirrors app/shared/messaging/rails_event_schemas.py and unified_event_publisher.py
# in the LIA Python repo.
#
# Usage:
#   LiaEvents::EventPublisher.new.publish(
#     event_type: "screening.completed",
#     company_id: company.id,
#     payload: { candidate_id: 123, score: 0.85 }
#   )
module LiaEvents
  class EventPublisher
    EXCHANGE_NAME = "lia_rails_events"
    SOURCE = "rails-ats-api"

    def initialize(rabbitmq_url: nil)
      @rabbitmq_url = rabbitmq_url || ENV.fetch("RABBITMQ_URL", "amqp://guest:guest@localhost:5672")
    end

    # Publish an event to the LIA Python backend.
    # @param event_type [String] Event type from EventRegistry::EVENT_VERSIONS
    # @param company_id [Integer, String] Tenant company ID
    # @param payload [Hash] Event-specific data
    # @return [Boolean] true on success, false on failure (fail-open)
    def publish(event_type:, company_id:, payload: {})
      unless LiaEvents::EventRegistry.known_event?(event_type)
        Rails.logger.warn("[LIA-E03] Unknown event_type: #{event_type}. Not publishing.")
        return false
      end

      envelope = {
        event_type: event_type,
        event_version: LiaEvents::EventRegistry.current_version(event_type),
        company_id: company_id,
        payload: payload,
        timestamp: Time.current.iso8601,
        source: SOURCE,
      }

      connection = nil
      begin
        connection = Bunny.new(@rabbitmq_url, automatically_recover: false)
        connection.start
        channel = connection.create_channel
        exchange = channel.direct(EXCHANGE_NAME, durable: true)
        exchange.publish(envelope.to_json, persistent: true, content_type: "application/json")

        Rails.logger.info(
          "[LIA-E03] Event published: type=#{event_type} company=#{company_id} version=#{envelope[:event_version]}"
        )
        true
      rescue StandardError => e
        Rails.logger.warn("[LIA-E03] Publish failed: type=#{event_type} err=#{e.message}")
        false
      ensure
        connection&.close
      end
    end
  end
end
