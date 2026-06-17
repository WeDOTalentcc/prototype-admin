# frozen_string_literal: true

require "httparty"
require "ostruct"

module AtsSync
  class ApiClient
    include HTTParty

    class ApiError < StandardError; end
    class ConnectionError < ApiError; end
    class ValidationError < ApiError; end
    class AuthenticationError < ApiError; end
    class ServerError < ApiError; end
    class SyncError < ApiError; end

    def initialize
      self.class.base_uri AtsSync.config.api_url

      @options = {
        headers: {
          "Content-Type" => "application/json",
          "X-API-Key" => AtsSync.config.api_token
        },
        timeout: AtsSync.config.timeout
      }
    end

    def create_candidate(payload)
      request(:post, "/api/v1/candidates", payload)
    end

    def update_candidate(payload)
      request(:put, "/api/v1/candidates", payload)
    end

    def delete_candidate(payload)
      request(:delete, "/api/v1/candidates", payload)
    end

    def create_apply(payload)
      Rails.logger.info "🌐 [ApiClient] Sending CREATE_APPLY request"
      Rails.logger.debug "   Payload ats_references: #{payload[:ats_references].to_json}"
      request(:post, "/api/v1/applies", payload)
    end

    def update_apply(payload)
      Rails.logger.info "🌐 [ApiClient] Sending UPDATE_APPLY request"
      Rails.logger.debug "   Payload ats_references: #{payload[:ats_references].to_json}"
      request(:put, "/api/v1/applies", payload)
    end

    def delete_apply(payload)
      request(:delete, "/api/v1/applies", payload)
    end

    def health_check
      response = self.class.get("/api/v1/health", **@options)
      response.success?
    rescue StandardError
      false
    end

    private

    def request(method, path, payload)
      json_body = payload.to_json

      Rails.logger.debug "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      Rails.logger.debug "🌐 [ApiClient] HTTP Request"
      Rails.logger.debug "   Method: #{method.upcase}"
      Rails.logger.debug "   Path: #{path}"
      Rails.logger.debug "   JSON Body (ats_references only):"

      begin
        json_parsed = JSON.parse(json_body)
        if json_parsed["ats_references"]
          Rails.logger.debug "      ats_candidate_id: #{json_parsed["ats_references"]["ats_candidate_id"]}"
          Rails.logger.debug "      ats_job_id: #{json_parsed["ats_references"]["ats_job_id"]}"
          Rails.logger.debug "      ats_apply_id: #{json_parsed["ats_references"]["ats_apply_id"]}"
          Rails.logger.debug "      ats_selective_process_id: #{json_parsed["ats_references"]["ats_selective_process_id"]}"
        end
      rescue JSON::ParserError => e
        Rails.logger.error "   Failed to parse JSON: #{e.message}"
      end

      Rails.logger.debug "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

      response = self.class.public_send(method, path, body: json_body, **@options)
      handle_response(response)
    rescue Errno::ECONNREFUSED, SocketError, Net::OpenTimeout, Timeout::Error => e
      raise ConnectionError, "ATS unreachable (#{self.class.base_uri}): #{e.message}"
    end

    def handle_response(response)
      return parse_success_response(response) if response.success?

      raise_error_for_status(response)
    end

    def parse_success_response(response)
      body = JSON.parse(response.body)

      unless body["success"]
        errors = body["errors"]
        error_message = errors.is_a?(Array) ? errors.join(", ") : (errors || "Unknown error")
        raise SyncError, error_message
      end

      OpenStruct.new(
        success: true,
        ats_ids: body["ats_ids"] || {},
        warnings: body["warnings"] || [],
        message: body["message"]
      )
    rescue JSON::ParserError => e
      raise ApiError, "Invalid JSON response: #{e.message}"
    end

    def raise_error_for_status(response)
      error_handlers = {
        400 => ->(msg) { raise ValidationError, msg },
        401 => ->(_) { raise AuthenticationError, "Invalid token" },
        500 => ->(msg) { raise ServerError, msg }
      }

      handler = error_handlers[response.code] || ->(msg) { raise ApiError, msg }
      handler.call(parse_error_message(response))
    end

    def parse_error_message(response)
      body = JSON.parse(response.body)
      body["detail"] || body["message"] || response.body
    rescue JSON::ParserError
      "HTTP #{response.code}: #{response.body}"
    end
  end
end
