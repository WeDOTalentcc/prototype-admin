module MessageService
  class EventPublisher
    def self.publish(payload)
      connection = Bunny.new(ENV["RABBITMQ_URL"])
      connection.start

      channel = connection.create_channel
      exchange = channel.direct("messages_exchange", durable: true)

      exchange.publish(
        payload.to_json,
        routing_key: "messages_created"
      )

      channel.close
      connection.close
    end
  end
end
