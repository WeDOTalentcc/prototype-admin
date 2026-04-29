# frozen_string_literal: true

module Emails
  class RateLimiter
    LIMITS = {
      mailgun: {
        per_minute: ENV.fetch("EMAIL_RATE_MAILGUN_PER_MINUTE", "5").to_i,
        per_hour: ENV.fetch("EMAIL_RATE_MAILGUN_PER_HOUR", "250").to_i,
        per_day: ENV.fetch("EMAIL_RATE_MAILGUN_PER_DAY", "5000").to_i
      },
      ms_graph: {
        per_minute: ENV.fetch("EMAIL_RATE_MSGRAPH_PER_MINUTE", "25").to_i,
        per_hour: ENV.fetch("EMAIL_RATE_MSGRAPH_PER_HOUR", "500").to_i,
        per_day: ENV.fetch("EMAIL_RATE_MSGRAPH_PER_DAY", "10000").to_i
      }
    }.freeze

    class << self
      def check!(provider:, account_id:)
        limits = LIMITS[provider.to_sym]
        raise ArgumentError, "Unknown provider: #{provider}" unless limits

        check_window!("#{key(provider, account_id)}:min", limits[:per_minute], 60)
        check_window!("#{key(provider, account_id)}:hour", limits[:per_hour], 3_600)
        check_window!("#{key(provider, account_id)}:day", limits[:per_day], 86_400)
      end

      def record_send!(provider:, account_id:)
        now = Time.current.to_f

        redis do |conn|
          %w[min hour day].each do |window|
            k = "#{key(provider, account_id)}:#{window}"
            conn.zadd(k, now, "#{now}-#{SecureRandom.hex(4)}")
          end
        end
      end

      def usage(provider:, account_id:)
        now = Time.current.to_f
        result = {}

        redis do |conn|
          { min: 60, hour: 3_600, day: 86_400 }.each do |window, seconds|
            k = "#{key(provider, account_id)}:#{window}"
            result[window] = conn.zcount(k, now - seconds, "+inf")
          end
        end

        result
      end

      private

      def check_window!(redis_key, limit, window_seconds)
        now = Time.current.to_f

        count = redis do |conn|
          conn.zremrangebyscore(redis_key, "-inf", now - window_seconds)
          conn.expire(redis_key, window_seconds + 60)
          conn.zcount(redis_key, now - window_seconds, "+inf")
        end

        if count >= limit
          raise Emails::RateLimitHit.new(
            "Rate limit exceeded: #{count}/#{limit} in #{window_seconds}s window",
            limit: limit, current: count, retry_after: window_seconds
          )
        end
      end

      def key(provider, account_id)
        "email:rate:#{provider}:#{account_id}"
      end

      def redis(&block)
        Sidekiq.redis(&block)
      end
    end
  end
end
