# frozen_string_literal: true

module MessageService
  class EventPublisher
    def self.publish(payload)
      channel = ConnectionPool.channel
      exchange = channel.direct("messages_exchange", durable: true)

      exchange.publish(
        payload.to_json,
        routing_key: "messages_created",
        persistent: true
      )
    ensure
      channel&.close
    end
  end
end
