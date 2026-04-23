# frozen_string_literal: true

module Llm
  module Adapters
    class Deepseek < Base
      BASE_URL = "https://api.deepseek.com"
      DEFAULT_CHAT_MODEL = "deepseek-chat"

      def chat(model:, messages:, temperature: 0.7, max_tokens: nil, response_format: nil, tracking: nil)
        model = DEFAULT_CHAT_MODEL if model.blank? || model.start_with?("gemini")

        body = {
          model: model,
          messages: messages.map { |m| { role: m[:role], content: m[:content] } },
          temperature: temperature
        }
        body[:max_tokens] = max_tokens if max_tokens

        response = connection.post("/chat/completions") do |req|
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
        raise NotImplementedError, "DeepSeek does not support embeddings. Use Gemini or OpenAI for embeddings."
      end

      def provider_name
        "DeepSeek"
      end

      private

      def connection
        @connection ||= build_connection(BASE_URL)
      end
    end
  end
end
