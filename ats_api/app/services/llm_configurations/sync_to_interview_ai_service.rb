# frozen_string_literal: true

module LlmConfigurations
  class SyncToInterviewAiService
    TIMEOUT = 15
    OPEN_TIMEOUT = 5

    def initialize(llm_configuration:)
      @llm_configuration = llm_configuration
    end

    def call
      return error("INTERVIEW_AI_BASE_URL not configured") if base_url.blank?
      return error("LLM_CONFIG_SECRET not configured") if secret_token.blank?

      response = send_request
      handle_response(response)
    rescue Faraday::TimeoutError
      record_failure("Timeout connecting to Interview AI service")
    rescue Faraday::ConnectionFailed => e
      record_failure("Connection failed: #{e.message}")
    rescue StandardError => e
      Rails.logger.error "❌ [LlmConfigurations::SyncToInterviewAiService] #{e.message}"
      record_failure("Unexpected error: #{e.message}")
    end

    private

    attr_reader :llm_configuration

    def send_request
      connection.put("/api/v1/llm/configurations") do |req|
        req.body = {
          account_id: llm_configuration.account_id,
          provider: llm_configuration.provider,
          api_key: llm_configuration.api_key
        }
      end
    end

    def handle_response(response)
      return record_success if response.success?

      record_failure("HTTP #{response.status}: #{response.body}")
    end

    def record_success
      llm_configuration.update_columns(
        interview_ai_synced_at: Time.current,
        interview_ai_sync_error: nil
      )
      { success: true }
    end

    def record_failure(message)
      llm_configuration.update_columns(interview_ai_sync_error: message)
      error(message)
    end

    def error(message)
      { success: false, error: message }
    end

    def connection
      @connection ||= Faraday.new(url: base_url) do |f|
        f.request :json
        f.response :json
        f.headers["Authorization"] = "Bearer #{secret_token}"
        f.options.timeout = TIMEOUT
        f.options.open_timeout = OPEN_TIMEOUT
      end
    end

    def base_url
      ENV.fetch("INTERVIEW_AI_BASE_URL", nil)
    end

    def secret_token
      ENV.fetch("LLM_CONFIG_SECRET", nil)
    end
  end
end
