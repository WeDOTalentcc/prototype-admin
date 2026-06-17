# frozen_string_literal: true

require "net/http"
require "uri"
require "json"

module Meta
  class Api
    DEFAULT_OPEN_TIMEOUT = 5
    DEFAULT_READ_TIMEOUT = 15

    Response = Struct.new(:code, :body, :raw, :success?)

    class << self
      def post(path, payload)
        url = build_url(path)
        http = Net::HTTP.new(url.host, url.port)
        http.use_ssl = true
        http.open_timeout = DEFAULT_OPEN_TIMEOUT
        http.read_timeout = DEFAULT_READ_TIMEOUT

        request = Net::HTTP::Post.new(url)
        apply_common_headers!(request)
        request["Content-Type"] = "application/json"
        request.body = payload.to_json

        raw_response = http.request(request)
        parsed = safe_parse(raw_response.body)
        success = raw_response.code.to_s.start_with?("2")
        report_error(raw_response.code, body: payload, parsed: parsed) unless success
        Response.new(raw_response.code.to_i, parsed, raw_response, success)
      rescue StandardError => e
        report_error("client_exception", body: payload, parsed: { error: e.message })
        Response.new(0, { "error" => e.message }, nil, false)
      end

      private

      def build_url(path)
        phone_number_id = ENV.fetch("META_WHATSAPP_PHONE_NUMBER_ID")
        version = ENV.fetch("META_WHATSAPP_GRAPH_VERSION", "v19.0")
        path = path.to_s.sub(%r{^/}, "")
        URI.parse("https://graph.facebook.com/#{version}/#{phone_number_id}/#{path}")
      end

      def apply_common_headers!(request)
        token = ENV.fetch("META_WHATSAPP_ACCESS_TOKEN")
        request["Authorization"] = "Bearer #{token}"
      end

      def safe_parse(body)
        return {} if body.nil? || body.empty?
        JSON.parse(body)
      rescue JSON::ParserError
        { "raw_body" => body }
      end

      def report_error(code, body:, parsed: {})
        if defined?(NotifyErrorService)
          NotifyErrorService.report_meta(code, { body: }, parsed)
        else
          Rails.logger.error("Meta::Api error code=#{code} parsed=#{parsed.inspect}")
        end
      rescue StandardError => e
        Rails.logger.error("Meta::Api secondary error while reporting: #{e.class} #{e.message}")
      end
    end
  end
end
