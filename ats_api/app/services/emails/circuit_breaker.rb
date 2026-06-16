# frozen_string_literal: true

module Emails
  class CircuitBreaker
    FAILURE_THRESHOLD = 5
    FAILURE_WINDOW = 60
    RECOVERY_TIMEOUT = 300

    class << self
      def check!(provider:, account_id:)
        state = current_state(provider, account_id)

        case state
        when :open
          raise Emails::CircuitOpen.new(
            "Circuit breaker OPEN for #{provider}/#{account_id}",
            retry_after: RECOVERY_TIMEOUT
          )
        when :half_open
          nil
        else
          nil
        end
      end

      def record_failure!(provider:, account_id:)
        k = failure_key(provider, account_id)

        redis do |conn|
          conn.multi do |m|
            m.incr(k)
            m.expire(k, FAILURE_WINDOW)
          end
        end

        count = redis { |c| c.get(k).to_i }
        open_circuit!(provider, account_id) if count >= FAILURE_THRESHOLD
      end

      def record_success!(provider:, account_id:)
        redis do |conn|
          conn.del(failure_key(provider, account_id))
          conn.del(circuit_key(provider, account_id))
        end
      end

      private

      def current_state(provider, account_id)
        opened_at = redis { |c| c.get(circuit_key(provider, account_id)) }
        return :closed unless opened_at

        elapsed = Time.current.to_f - opened_at.to_f
        elapsed > RECOVERY_TIMEOUT ? :half_open : :open
      end

      def open_circuit!(provider, account_id)
        redis do |conn|
          conn.set(circuit_key(provider, account_id), Time.current.to_f)
          conn.expire(circuit_key(provider, account_id), RECOVERY_TIMEOUT * 2)
        end

        Rails.logger.error("[CircuitBreaker] OPENED for #{provider}/#{account_id}")
      end

      def failure_key(provider, account_id) = "email:cb:fail:#{provider}:#{account_id}"
      def circuit_key(provider, account_id) = "email:cb:state:#{provider}:#{account_id}"
      def redis(&block) = Sidekiq.redis(&block)
    end
  end
end
