# frozen_string_literal: true

module Emails
  module Delivery
    class BaseStrategy
      def deliver(to:, subject:, body:, dispatch:, message:)
        raise NotImplementedError, "#{self.class}#deliver must be implemented"
      end
    end
  end
end
