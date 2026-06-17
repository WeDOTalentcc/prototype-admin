# frozen_string_literal: true

module Llm
  module Adapters
    class Gemini < Base
      def chat(model:, messages:, temperature: 0.7, max_tokens: nil, response_format: nil, tracking: nil)
        client.chat(
          model: model, messages: messages, temperature: temperature,
          max_tokens: max_tokens, response_format: response_format, tracking: tracking
        )
      end

      def embeddings(text:, model: nil, dimensions: 768, tracking: nil)
        model ||= Llm::ClientFactory.embedding_model
        client.embeddings(text: text, model: model, dimensions: dimensions, tracking: tracking)
      end

      def provider_name
        "Gemini"
      end

      private

      def client
        @client ||= GeminiClient.new(api_key: api_key)
      end
    end
  end
end
