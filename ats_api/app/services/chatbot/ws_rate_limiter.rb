# frozen_string_literal: true

module Chatbot
  class WsRateLimitExceeded < StandardError
    attr_reader :limit, :current, :retry_after

    def initialize(message = nil, limit: nil, current: nil, retry_after: nil)
      @limit = limit
      @current = current
      @retry_after = retry_after
      super(message)
    end
  end

  class WsRateLimiter
    LIMIT = ENV.fetch("WS_RATE_LIMIT_PER_MINUTE", "60").to_i
    WINDOW = 60 # seconds

    class << self
      def check!(identifier)
        check_window!(redis_key(identifier), LIMIT, WINDOW)
      end

      def record!(identifier)
        now = Time.current.to_f

        redis do |conn|
          k = redis_key(identifier)
          conn.zadd(k, now, "#{now}-#{SecureRandom.hex(4)}")
          conn.expire(k, WINDOW + 60)
        end
      end

      def check_and_record!(identifier)
        now = Time.current.to_f
        k = redis_key(identifier)

        count, = redis do |conn|
          conn.multi do |m|
            m.zremrangebyscore(k, "-inf", now - WINDOW)
            m.zadd(k, now, "#{now}-#{SecureRandom.hex(4)}")
            m.expire(k, WINDOW + 60)
            m.zcount(k, now - WINDOW, "+inf")
          end
        end.last

        count > LIMIT
      end

      def exceeded?(identifier)
        now = Time.current.to_f

        count = redis do |conn|
          k = redis_key(identifier)
          conn.zcount(k, now - WINDOW, "+inf")
        end

        count >= LIMIT
      end

      def usage(identifier)
        now = Time.current.to_f

        redis do |conn|
          conn.zcount(redis_key(identifier), now - WINDOW, "+inf")
        end
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
          raise Chatbot::WsRateLimitExceeded.new(
            "WS rate limit exceeded: #{count}/#{limit} in #{window_seconds}s",
            limit: limit, current: count, retry_after: window_seconds
          )
        end
      end

      def redis_key(identifier)
        "ws:rate:triagem:#{identifier}"
      end

      def redis(&block)
        Sidekiq.redis(&block)
      end
    end
  end
end
