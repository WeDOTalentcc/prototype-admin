# frozen_string_literal: true

module MessageService
  # Singleton Bunny connection with automatic recovery.
  # Publishers obtain channels from this shared connection instead of
  # creating a new TCP connection per publish.
  #
  # Thread safety: each caller gets its own channel via create_channel.
  # Channels are NOT shared across threads.
  #
  # Usage:
  #   channel = MessageService::ConnectionPool.channel
  #   exchange = channel.direct("messages_exchange", durable: true)
  #   exchange.publish(payload, routing_key: "key")
  #   channel.close
  class ConnectionPool
    class << self
      def connection
        @mutex ||= Mutex.new
        @mutex.synchronize do
          if @connection.nil? || @connection.closed?
            @connection = Bunny.new(
              ENV.fetch("RABBITMQ_URL", "amqp://guest:guest@localhost:5672"),
              recover_from_connection_close: true,
              automatically_recover: true,
              recovery_attempts: 5,
              recovery_attempts_exhausted: -> { Rails.logger.error "[Bunny] Recovery attempts exhausted" },
              heartbeat: 30
            )
            @connection.start
            Rails.logger.info "[Bunny] Connection pool started"
          end
          @connection
        end
      end

      def channel
        connection.create_channel
      end

      def shutdown
        @mutex&.synchronize do
          if @connection && !@connection.closed?
            @connection.close
            Rails.logger.info "[Bunny] Connection pool closed"
          end
          @connection = nil
        end
      end
    end
  end
end
