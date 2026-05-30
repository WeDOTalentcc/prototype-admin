# frozen_string_literal: true

module Emails
  module Delivery
    class StrategyResolver
      STRATEGIES = {
        "mailgun" => MailgunStrategy,
        "ms_graph" => MsGraphStrategy
      }.freeze

      # ms_graph é o provider primário para contas Microsoft 365.
      # Quando falha (token expirado, MS Graph unavailable), cai para mailgun
      # como fallback antes de deixar o Sidekiq retry subir o erro.
      FALLBACK_CHAIN = {
        "ms_graph" => "mailgun"
      }.freeze

      def self.for(dispatch)
        provider = dispatch.provider.to_s
        strategy_class = STRATEGIES[provider]
        raise ArgumentError, "Unknown provider: #{provider}" unless strategy_class

        strategy_class.new
      end

      def self.deliver_with_fallback(dispatch:, **delivery_args)
        provider = dispatch.provider.to_s
        strategy_class = STRATEGIES[provider]
        raise ArgumentError, "Unknown provider: #{provider}" unless strategy_class

        begin
          strategy_class.new.deliver(**delivery_args, dispatch: dispatch)
        rescue Emails::ProviderUnavailable, StandardError => primary_error
          fallback_provider = FALLBACK_CHAIN[provider]
          raise primary_error unless fallback_provider

          fallback_class = STRATEGIES[fallback_provider]
          raise primary_error unless fallback_class

          Rails.logger.warn(
            "[StrategyResolver] #{provider} falhou (#{primary_error.class}: #{primary_error.message}). " \
            "Tentando fallback: #{fallback_provider}"
          )

          begin
            result = fallback_class.new.deliver(**delivery_args, dispatch: dispatch)
            result.merge(fallback_used: true, primary_error: primary_error.message, fallback_provider: fallback_provider)
          rescue => fallback_error
            Rails.logger.error(
              "[StrategyResolver] Fallback #{fallback_provider} também falhou: #{fallback_error.message}"
            )
            raise primary_error
          end
        end
      end
    end
  end
end
