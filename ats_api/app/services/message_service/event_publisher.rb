module MessageService
  class EventPublisher
    MAX_RETRIES = 3
    RETRY_DELAY = 0.5
    POOL_SIZE = 5
    POOL_TIMEOUT = 5

    def self.publish(payload, exchange_name: "messages_exchange", routing_key: "messages_created")
      retries = 0
      payload = ensure_account_id(payload)
      msg_id = payload[:message_id] || payload["message_id"]
      has_ott = (payload[:one_time_token] || payload["one_time_token"]).present?
      ott_preview = truncate_token(payload[:one_time_token] || payload["one_time_token"])
      account_id = payload[:account_id] || payload["account_id"]
      user_id = payload[:user_id] || payload["user_id"]

      Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      Rails.logger.info "🚀 [EventPublisher] Publishing to RabbitMQ"
      Rails.logger.info "   exchange=#{exchange_name} routing_key=#{routing_key}"
      Rails.logger.info "   message_id=#{msg_id} account_id=#{account_id} user_id=#{user_id}"
      Rails.logger.info "   has_ott=#{has_ott} ott_preview=#{ott_preview}"
      Rails.logger.info "   payload_keys=#{payload.keys.join(', ')}"
      Rails.logger.info "   rabbitmq_url_present=#{ENV['RABBITMQ_URL'].present?}"
      Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

      begin
        connection_pool.with do |connection|
          Rails.logger.info "🔌 [EventPublisher] Connection open=#{connection.open?} status=#{connection.status}"
          channel = connection.create_channel
          begin
            exchange = channel.direct(exchange_name, durable: true)

            json_payload = payload.to_json
            Rails.logger.info "📦 [EventPublisher] Payload size=#{json_payload.bytesize} bytes"

            exchange.publish(
              json_payload,
              routing_key: routing_key,
              persistent: true
            )

            Rails.logger.info "✅ [EventPublisher] Message published successfully message_id=#{msg_id} has_ott=#{has_ott}"
          ensure
            channel&.close rescue nil
          end
        end

        {
          status: :ok,
          payload: payload,
          exchange_name: exchange_name,
          routing_key: routing_key,
          message_id: msg_id
        }
      rescue Bunny::TCPConnectionFailed, Bunny::NetworkFailure, Bunny::ConnectionClosedError => e
        retries += 1
        if retries <= MAX_RETRIES
          Rails.logger.warn "[EventPublisher] Connection failed (attempt #{retries}/#{MAX_RETRIES}): #{e.message}. Retrying..."
          reset_pool!
          sleep(RETRY_DELAY * retries)
          retry
        end
        Rails.logger.error "[EventPublisher] Failed after #{MAX_RETRIES} retries: #{e.class} - #{e.message}"
        raise
      rescue StandardError => e
        Rails.logger.error "[EventPublisher] Unexpected error: #{e.class} - #{e.message}"
        raise
      end
    end

    def self.connection_pool
      @connection_pool ||= ConnectionPool.new(size: POOL_SIZE, timeout: POOL_TIMEOUT) do
        connection = Bunny.new(ENV.fetch("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672"))
        connection.start
        connection
      end
    end

    def self.reset_pool!
      @connection_pool&.shutdown { |conn| conn.close rescue nil }
      @connection_pool = nil
    end

    def self.truncate_token(token)
      return "nil" if token.blank?

      "#{token[0..15]}...#{token[-10..]}"
    end

    def self.ensure_account_id(payload)
      return payload if (payload[:account_id] || payload["account_id"]).present?

      account_id = Current.user&.account_id || Current.account&.id || account_id_from_tenant
      return payload unless account_id

      payload.is_a?(HashWithIndifferentAccess) || payload.keys.first.is_a?(String) ? payload.merge("account_id" => account_id) : payload.merge(account_id: account_id)
    end

    def self.account_id_from_tenant
      tenant = Apartment::Tenant.current
      return if tenant == "public"

      Account.find_by(tenant: tenant)&.id
    end
  end
end
