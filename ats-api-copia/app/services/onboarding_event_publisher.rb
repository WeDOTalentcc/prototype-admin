# frozen_string_literal: true

# Extension of MessageService::EventPublisher for onboarding events.
# Uses shared Bunny connection pool with a dedicated routing key.
#
# Usage:
#   OnboardingEventPublisher.publish("user_invited", { user_id: 1, ... })

class OnboardingEventPublisher
  EXCHANGE = "messages_exchange"
  ROUTING_KEY = "onboarding_events"

  def self.publish(event_type, payload)
    channel = MessageService::ConnectionPool.channel
    exchange = channel.direct(EXCHANGE, durable: true)

    message = {
      event_type: event_type,
      payload: payload,
      timestamp: Time.current.iso8601,
      source: "rails"
    }

    exchange.publish(
      message.to_json,
      routing_key: ROUTING_KEY,
      persistent: true
    )

    Rails.logger.info "[Onboarding] Published #{event_type} for user #{payload[:user_id]}"
  rescue StandardError => e
    Rails.logger.warn "[Onboarding] Event publish failed: #{e.message}"
  ensure
    channel&.close
  end
end
