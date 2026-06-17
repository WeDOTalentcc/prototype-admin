# frozen_string_literal: true

module Llm
  module Adapters
    class Openai < Base
      BASE_URL = "https://api.openai.com/v1"
      DEFAULT_CHAT_MODEL = "gpt-4o-mini"
      DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"

      def chat(model:, messages:, temperature: 0.7, max_tokens: nil, response_format: nil, tracking: nil)
        model = DEFAULT_CHAT_MODEL if model.blank? || model.start_with?("gemini")

        body = {
          model: model,
          messages: messages.map { |m| { role: m[:role], content: m[:content] } },
          temperature: temperature
        }
        body[:max_tokens] = max_tokens if max_tokens

        response = connection.post("/v1/chat/completions") do |req|
          req.headers["Authorization"] = "Bearer #{api_key}"
          req.body = body
        end

        return handle_error_response(response, provider_name) unless response.success?

        data = response.body
        usage = data["usage"] || {}

        normalized_response(
          text: data.dig("choices", 0, "message", "content").to_s,
          prompt_tokens: usage["prompt_tokens"] || 0,
          completion_tokens: usage["completion_tokens"] || 0,
          total_tokens: usage["total_tokens"] || 0
        )
      end

      def embeddings(text:, model: nil, dimensions: 768, tracking: nil)
        model = DEFAULT_EMBEDDING_MODEL if model.blank? || model.start_with?("gemini")

        body = { model: model, input: text }
        body[:dimensions] = dimensions if dimensions

        response = connection.post("/v1/embeddings") do |req|
          req.headers["Authorization"] = "Bearer #{api_key}"
          req.body = body
        end

        return handle_error_response(response, provider_name) unless response.success?

        embedding = response.body.dig("data", 0, "embedding") || []
        normalized_embedding_response(embedding: embedding)
      end

      def provider_name
        "OpenAI"
      end

      private

      def connection
        @connection ||= build_connection(BASE_URL)
      end
    end
  end
end
