# frozen_string_literal: true

module Emails
  class RateLimitHit < StandardError
    attr_reader :limit, :current, :retry_after

    def initialize(message = nil, limit: nil, current: nil, retry_after: nil)
      @limit = limit
      @current = current
      @retry_after = retry_after
      super(message)
    end
  end
end
