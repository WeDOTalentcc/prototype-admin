# frozen_string_literal: true

require "uri"
require "net/http"
require "json"
require "timeout"

module MicrosoftService
  class Auth
    TOKEN_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
    GRAPH_BASE = "https://graph.microsoft.com/v1.0"
    REQUEST_TIMEOUT = 10 # seconds
    MAX_TOKEN_PREVIEW_LENGTH = 8

    class AuthenticationError < StandardError; end
    class TokenValidationError < StandardError; end
    class GraphApiError < StandardError; end

    class << self
      def domain
        return "http://localhost:8080/v1/" if Rails.env.development?

        host = ENV.fetch("APP_HOST", "http://localhost:8080")
        return "#{host}/v1/" if host.start_with?("http://", "https://")

        "https://#{host}/v1/"
      end

      # Exchange authorization code for access token
      def token(code = nil, redirect_uri: nil)
        raise ArgumentError, "Authorization code is required" if code.blank?

        if redirect_uri.present?
          return exchange_code_for_token(code: code, redirect_uri: redirect_uri)
        end

        exchange_code_for_token(
          code: code,
          redirect_uri: "#{domain}auth/microsoft_graph_auth/callback"
        )
      end

      # Refresh an access token using refresh token
      def refresh_token(refresh_token, redirect_uri: nil)
        raise ArgumentError, "Refresh token is required" if refresh_token.blank?

        if redirect_uri.present?
          return refresh_access_token(refresh_token: refresh_token, redirect_uri: redirect_uri)
        end

        refresh_access_token(
          refresh_token: refresh_token,
          redirect_uri: "#{domain}auth/microsoft_graph_auth/callback"
        )
      end

      # Get user profile from Microsoft Graph API
      def get_me(access_token)
        raise TokenValidationError, "Access token is required" if access_token.blank?

        Rails.logger.info("Microsoft Graph API: Fetching user profile")

        response = make_graph_request(access_token, "/me")

        if response[:success]
          Rails.logger.info("Microsoft Graph API: User profile retrieved successfully")
          response[:data]
        else
          Rails.logger.error("Microsoft Graph API: Failed to retrieve user profile - #{response[:error]}")
          raise GraphApiError, response[:error]
        end
      rescue => e
        Rails.logger.error("Microsoft Graph API: Exception - #{e.message}")
        nil
      end

      # Validate if access token is still valid
      def validate_token(access_token)
        return false if access_token.blank?

        response = make_graph_request(access_token, "/me")
        response[:success]
      end

      # Debug token information (safe logging)
      def debug_token(access_token)
        return "Token is blank" if access_token.blank?

        info = {
          length: access_token.length,
          preview: access_token[0, MAX_TOKEN_PREVIEW_LENGTH] + "...",
          dots_count: access_token.count("."),
          jwt_format: access_token.split(".").length == 3
        }

        Rails.logger.debug("Token info: length=#{info[:length]}, jwt_format=#{info[:jwt_format]}")
        info
      end

      private

      # Exchange authorization code for tokens
      def exchange_code_for_token(code:, redirect_uri:)
        Rails.logger.info("Microsoft OAuth: Exchanging code for token")

        body_params = {
          client_id: ENV["AZURE_APP_ID"],
          client_secret: ENV["AZURE_APP_SECRET"],
          code: code,
          redirect_uri: redirect_uri,
          grant_type: "authorization_code"
        }

        make_token_request(body_params)
      end

      # Refresh access token using refresh token
      def refresh_access_token(refresh_token:, redirect_uri:)
        Rails.logger.info("Microsoft OAuth: Refreshing access token")

        body_params = {
          client_id: ENV["AZURE_APP_ID"],
          client_secret: ENV["AZURE_APP_SECRET"],
          refresh_token: refresh_token,
          redirect_uri: redirect_uri,
          grant_type: "refresh_token"
        }

        make_token_request(body_params)
      end

      # Make token request to Microsoft OAuth endpoint
      def make_token_request(params)
        uri = URI(TOKEN_URL)

        http = Net::HTTP.new(uri.host, uri.port)
        http.use_ssl = true
        http.read_timeout = REQUEST_TIMEOUT
        http.open_timeout = REQUEST_TIMEOUT

        request = Net::HTTP::Post.new(uri)
        request["Content-Type"] = "application/x-www-form-urlencoded"
        request["User-Agent"] = "ATS-API/#{Rails.env}/1.0"
        request.body = URI.encode_www_form(params)

        response = http.request(request)

        if response.code.to_i >= 400
          error_body = JSON.parse(response.body) rescue {}
          error_code = error_body["error"] || "unknown"
          error_description = error_body["error_description"] || response.body

          error_msg = "Token request failed: #{response.code} - #{error_code}: #{error_description}"
          Rails.logger.error("Microsoft OAuth: #{error_msg}")
          raise AuthenticationError, error_msg
        end

        JSON.parse(response.body)
      rescue JSON::ParserError => e
        Rails.logger.error("Microsoft OAuth: Invalid JSON response - #{e.message}")
        raise AuthenticationError, "Invalid response format"
      rescue Timeout::Error, Net::OpenTimeout, Net::ReadTimeout => e
        Rails.logger.error("Microsoft OAuth: Request timeout - #{e.message}")
        raise AuthenticationError, "Request timeout"
      rescue StandardError => e
        # Don't mask AuthenticationError - let it propagate
        raise if e.is_a?(AuthenticationError)

        Rails.logger.error("Microsoft OAuth: Unexpected error - #{e.class}: #{e.message}")
        raise AuthenticationError, "Authentication service error: #{e.message}"
      end

      # Make request to Microsoft Graph API
      def make_graph_request(access_token, endpoint)
        uri = URI("#{GRAPH_BASE}#{endpoint}")

        http = Net::HTTP.new(uri.host, uri.port)
        http.use_ssl = true
        http.read_timeout = REQUEST_TIMEOUT
        http.open_timeout = REQUEST_TIMEOUT

        request = Net::HTTP::Get.new(uri)
        request["Authorization"] = "Bearer #{access_token}"
        request["Accept"] = "application/json"
        request["User-Agent"] = "ATS-API/#{Rails.env}/1.0"

        response = http.request(request)

        case response.code.to_i
        when 200..299
          {
            success: true,
            data: JSON.parse(response.body)
          }
        when 401
          {
            success: false,
            error: "Unauthorized - Token invalid or expired"
          }
        when 403
          {
            success: false,
            error: "Forbidden - Insufficient permissions"
          }
        when 429
          {
            success: false,
            error: "Rate limited - Too many requests"
          }
        else
          {
            success: false,
            error: "Graph API error: #{response.code}"
          }
        end
      rescue JSON::ParserError => e
        Rails.logger.error("Microsoft Graph API: Invalid JSON response - #{e.message}")
        { success: false, error: "Invalid response format" }
      rescue Timeout::Error, Net::OpenTimeout, Net::ReadTimeout => e
        Rails.logger.error("Microsoft Graph API: Request timeout - #{e.message}")
        { success: false, error: "Request timeout" }
      rescue => e
        Rails.logger.error("Microsoft Graph API: Unexpected error - #{e.class}: #{e.message}")
        { success: false, error: "Graph API unavailable" }
      end

      # Legacy HTTParty method - to be removed
      def make_login(body)
        HTTParty.post(
          TOKEN_URL,
          headers: { "Content-Type" => "application/x-www-form-urlencoded" },
          body: body
        )
      end

      # Legacy Faraday methods - to be removed in future versions
      def token_with_redirect(code:, redirect_uri:)
        exchange_code_for_token(code: code, redirect_uri: redirect_uri)
      end

      def refresh_with_redirect(refresh_token:, redirect_uri:)
        refresh_access_token(refresh_token: refresh_token, redirect_uri: redirect_uri)
      end

      def get_me_with_httparty(access_token)
        Rails.logger.warn("Using deprecated HTTParty method - please use get_me instead")
        get_me(access_token)
      end
    end
  end
end
