# frozen_string_literal: true

module Llm
  class TrackedGeminiClient
    def initialize(user: nil, account: nil, default_context: {})
      @client = Llm::ClientFactory.build(account: account)
      @user = user
      @account = account
      @default_context = default_context
    end

    def chat(model:, messages:, temperature: 0.7, max_tokens: nil, response_format: nil, context: {})
      tracker = UsageTracker.new(
        model: model,
        operation: "chat",
        user: @user,
        account: @account,
        context: @default_context.merge(context).merge(
          temperature: temperature,
          max_tokens: max_tokens,
          response_format: response_format,
          message_count: messages.size
        )
      )

      tracker.track do
        @client.chat(
          model: model,
          messages: messages,
          temperature: temperature,
          max_tokens: max_tokens,
          response_format: response_format
        )
      end
    end

    def embeddings(text:, model: Llm::ClientFactory.embedding_model, dimensions: 768, context: {})
      tracker = UsageTracker.new(
        model: model,
        operation: "embedding",
        user: @user,
        account: @account,
        context: context.merge(
          dimensions: dimensions,
          text_length: text.length
        )
      )

      tracker.track do
        result = @client.embeddings(text: text, model: model, dimensions: dimensions)

        estimated_tokens = CostCalculator.estimate_tokens(text)
        result["usage"] = {
          "prompt_tokens" => estimated_tokens,
          "completion_tokens" => 0,
          "total_tokens" => estimated_tokens
        }

        result
      end
    end
  end
end
