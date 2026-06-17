# frozen_string_literal: true

module Emails
  class CircuitOpen < StandardError
    attr_reader :retry_after

    def initialize(message = nil, retry_after: nil)
      @retry_after = retry_after
      super(message)
    end
  end
end
