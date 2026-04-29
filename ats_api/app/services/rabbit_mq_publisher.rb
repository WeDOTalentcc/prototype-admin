require "connection_pool"
require "bunny"

module RabbitMqPublisher
  extend self

  def publish(exchange_name:, routing_key:, payload:, headers: {})
    enriched_payload = ensure_account_id(payload)

    pool.with do |connection|
      channel = connection.create_channel
      exchange = channel.direct(exchange_name, durable: true)

      exchange.publish(
        enriched_payload.to_json,
        routing_key: routing_key,
        persistent: true,
        headers: headers
      )
    end

    Rails.logger.info "✅ [RabbitMqPublisher] Published to '#{exchange_name}' routing_key='#{routing_key}' account_id=#{enriched_payload[:account_id] || enriched_payload['account_id']}"
    true
  rescue => e
    Rails.logger.error "❌ [RabbitMqPublisher] Failed: #{e.message}"
    false
  end

  private

  def ensure_account_id(payload)
    return payload if payload[:account_id].present? || payload["account_id"].present?

    account_id = resolve_account_id
    return payload unless account_id

    payload.merge(account_id: account_id)
  end

  def resolve_account_id
    Current.user&.account_id || Current.account&.id || account_id_from_tenant
  end

  def account_id_from_tenant
    tenant = Apartment::Tenant.current
    return if tenant == "public"

    Account.find_by(tenant: tenant)&.id
  end

  def pool
    @pool ||= ConnectionPool.new(size: 10, timeout: 5) do
      puts "🔌 Criando nova conexão com o RabbitMQ para o pool..."
      connection = Bunny.new(ENV.fetch("RABBITMQ_URL"))
      connection.start
      connection
    end
  end
end
