module Apify
  class LinkedinSearchService
    class HttpClient
      BASE_URL = "https://api.apify.com/v2"

      def initialize(api_key: nil, timeout: 300)
        @api_key = api_key || ENV.fetch("APIFY_KEY")
        @timeout = timeout
      end

      def post(path, body)
        json_body = body.to_json
        response = connection.post(path) do |req|
          req.headers["Content-Type"] = "application/json"
          req.body = json_body
        end

        parse_response(response)
      end

      def get(path, params: {})
        response = connection.get(path, params)
        parse_response(response)
      end

      private

      def connection
        @connection ||= Faraday.new(url: BASE_URL) do |f|
          f.request :url_encoded
          f.adapter Faraday.default_adapter
          f.options.timeout = @timeout
          f.params["token"] = @api_key
        end
      end

      def parse_response(response)
        return handle_error(response) unless response.success?

        JSON.parse(response.body, symbolize_names: true)
      rescue JSON::ParserError
        { data: [] }
      end

      def handle_error(response)
        error_body = JSON.parse(response.body) rescue {}
        message = error_body["message"] || error_body["error"] || "Request failed"

        raise ApiError, "#{response.status}: #{error_body.inspect}"
      end
    end
  end
end
