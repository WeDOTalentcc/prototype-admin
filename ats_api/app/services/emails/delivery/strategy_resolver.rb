# frozen_string_literal: true

module Emails
  module Delivery
    class StrategyResolver
      STRATEGIES = {
        "mailgun" => MailgunStrategy,
        "ms_graph" => MsGraphStrategy
      }.freeze

      def self.for(dispatch)
        provider = dispatch.provider.to_s
        strategy_class = STRATEGIES[provider]
        raise ArgumentError, "Unknown provider: #{provider}" unless strategy_class

        strategy_class.new
      end
    end
  end
end
