# frozen_string_literal: true

module Llm
  module Adapters
    class Base
      TIMEOUT_SECONDS = 120
      OPEN_TIMEOUT_SECONDS = 10

      attr_reader :api_key

      def initialize(api_key:)
        @api_key = api_key
      end

      def chat(model:, messages:, temperature: 0.7, max_tokens: nil, response_format: nil, tracking: nil)
        raise NotImplementedError
      end

      def embeddings(text:, model: nil, dimensions: 768, tracking: nil)
        raise NotImplementedError
      end

      def provider_name
        raise NotImplementedError
      end

      private

      def build_connection(base_url)
        Faraday.new(url: base_url) do |f|
          f.options.timeout = TIMEOUT_SECONDS
          f.options.open_timeout = OPEN_TIMEOUT_SECONDS
          f.request :json
          f.response :json
          f.adapter Faraday.default_adapter
        end
      end

      def normalized_response(text:, prompt_tokens: 0, completion_tokens: 0, total_tokens: 0)
        {
          "choices" => [{ "message" => { "content" => text } }],
          "usage" => {
            "prompt_tokens" => prompt_tokens,
            "completion_tokens" => completion_tokens,
            "total_tokens" => total_tokens
          }
        }
      end

      def normalized_embedding_response(embedding:)
        { "data" => [{ "embedding" => embedding }] }
      end

      def handle_error_response(response, provider)
        body = response.body
        error_msg = body.is_a?(Hash) ? (body.dig("error", "message") || body["error"] || body.to_json) : body.to_s
        Rails.logger.error "[#{provider}] API error (#{response.status}): #{error_msg}"
        raise "#{provider} API error (#{response.status}): #{error_msg}"
      end
    end
  end
end
