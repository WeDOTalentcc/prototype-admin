# frozen_string_literal: true

module Llm
  class Gateway
    def self.chat(messages:, temperature: 0.7, max_tokens: nil, response_format: nil, tracking: nil, account: nil)
      execute(:chat, messages: messages, temperature: temperature, max_tokens: max_tokens,
              response_format: response_format, tracking: tracking, account: account)
    end

    def self.fast_chat(messages:, temperature: 0.7, max_tokens: nil, response_format: nil, tracking: nil, account: nil)
      execute(:fast, messages: messages, temperature: temperature, max_tokens: max_tokens,
              response_format: response_format, tracking: tracking, account: account)
    end

    def self.embed(text:, dimensions: 768, tracking: nil, account: nil)
      resolved = resolve_account(account)
      client = ClientFactory.build_for_embeddings(account: resolved)
      model = ClientFactory.embedding_model(account: resolved)

      tracked(:embedding, model: model, tracking: tracking, account: resolved) do
        client.embeddings(text: text, model: model, dimensions: dimensions, tracking: tracking)
      end
    end

    def self.execute(tier, messages:, temperature:, max_tokens:, response_format:, tracking:, account:)
      resolved = resolve_account(account)
      client = ClientFactory.build(account: resolved)
      model = tier == :fast ? ClientFactory.fast_model(account: resolved) : ClientFactory.chat_model(account: resolved)

      Rails.logger.info "🧠 [Llm::Gateway] provider=#{client.provider_name} model=#{model} operation=#{tracking&.dig(:operation)}"

      tracked(:chat, model: model, tracking: tracking, account: resolved) do
        client.chat(
          model: model,
          messages: messages,
          temperature: temperature,
          max_tokens: max_tokens,
          response_format: response_format,
          tracking: tracking
        )
      end
    end

    def self.tracked(operation_type, model:, tracking:, account:, &block)
      return yield unless tracking && account

      user = Current.user
      tracker = UsageTracker.new(
        model: model,
        operation: tracking[:operation] || operation_type.to_s,
        user: user,
        account: account,
        context: tracking.except(:operation)
      )

      tracker.track(&block)
    rescue StandardError
      yield
    end

    def self.resolve_account(account)
      account || Current.user&.account || Current.account
    end

    private_class_method :execute, :tracked, :resolve_account
  end
end
