# frozen_string_literal: true

module Llm
  module Adapters
    class Anthropic < Base
      BASE_URL = "https://api.anthropic.com"
      API_VERSION = "2023-06-01"
      DEFAULT_CHAT_MODEL = "claude-sonnet-4-20250514"
      MAX_TOKENS_DEFAULT = 4096

      def chat(model:, messages:, temperature: 0.7, max_tokens: nil, response_format: nil, tracking: nil)
        model = DEFAULT_CHAT_MODEL if model.blank? || model.start_with?("gemini")

        system_message = extract_system_message(messages)
        filtered_messages = messages.reject { |m| m[:role] == "system" }
          .map { |m| { role: anthropic_role(m[:role]), content: m[:content] } }

        body = {
          model: model,
          messages: filtered_messages,
          max_tokens: max_tokens || MAX_TOKENS_DEFAULT,
          temperature: temperature
        }
        body[:system] = system_message if system_message

        response = connection.post("/v1/messages") do |req|
          req.headers["x-api-key"] = api_key
          req.headers["anthropic-version"] = API_VERSION
          req.body = body
        end

        return handle_error_response(response, provider_name) unless response.success?

        data = response.body
        usage = data["usage"] || {}
        text = data.dig("content", 0, "text").to_s

        normalized_response(
          text: text,
          prompt_tokens: usage["input_tokens"] || 0,
          completion_tokens: usage["output_tokens"] || 0,
          total_tokens: (usage["input_tokens"] || 0) + (usage["output_tokens"] || 0)
        )
      end

      def embeddings(text:, model: nil, dimensions: 768, tracking: nil)
        raise NotImplementedError, "Anthropic does not support embeddings. Use Gemini or OpenAI for embeddings."
      end

      def provider_name
        "Anthropic"
      end

      private

      def connection
        @connection ||= build_connection(BASE_URL)
      end

      def extract_system_message(messages)
        system_msg = messages.find { |m| m[:role] == "system" }
        system_msg&.dig(:content)
      end

      def anthropic_role(role)
        role == "assistant" || role == "model" ? "assistant" : "user"
      end
    end
  end
end
