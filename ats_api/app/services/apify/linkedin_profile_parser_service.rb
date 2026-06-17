module Apify
  class LinkedinProfileParserService
    class HttpClient
      BASE_URL = "https://api.apify.com/v2"

      def initialize(api_key: nil, timeout: 300)
        @api_key = api_key || ENV.fetch("APIFY_KEY")
        @timeout = timeout
      end

      def post(path, body)
        response = connection.post(path) do |req|
          req.headers["Content-Type"] = "application/json"
          req.body = body.to_json
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

    class Error < StandardError; end
    class ValidationError < Error; end
    class RunFailedError < Error; end
    class TimeoutError < Error; end
    class AbortedError < Error; end
    class ApiError < Error; end

    class RateLimitError < Error
      attr_reader :retry_after

      def initialize(message, retry_after: nil)
        super(message)
        @retry_after = retry_after
      end

      def seconds_until_retry
        return nil unless retry_after

        [ (retry_after - Time.current).to_i, 0 ].max
      end

      def minutes_until_retry
        return nil unless retry_after

        (seconds_until_retry / 60.0).ceil
      end
    end

    class << self
      def parse(linkedin_profile_urls:, include_email: false, sourcing: nil, **options)
        new.parse(linkedin_profile_urls: linkedin_profile_urls, include_email: include_email, sourcing: sourcing, **options)
      end
    end

    attr_reader :client, :logger

    def initialize(client: nil, logger: nil)
      @client = client || HttpClient.new
      @logger = logger || Rails.logger
    end

    def parse(linkedin_profile_urls:, include_email: false, sourcing: nil, **options)
      urls = Array(linkedin_profile_urls)
      return validation_error("linkedin_profile_urls is required") if urls.empty?

      results = []
      total_urls = urls.size

      urls.each_with_index do |url, index|
        logger.info "[Apify::LinkedinProfileParserService] Processing URL #{index + 1}/#{total_urls}: #{url}"
        result = parse_single(url, include_email)
        results << result

        if sourcing
          percentage = ((index + 1).to_f / total_urls * 100).round(2)
          broadcast_progress(sourcing, percentage, index + 1, total_urls)
        end
      rescue => e
        logger.error "[Apify::LinkedinProfileParserService] Error processing #{url}: #{e.message}"
        results << { error: e.message, url: url }

        if sourcing
          percentage = ((index + 1).to_f / total_urls * 100).round(2)
          broadcast_progress(sourcing, percentage, index + 1, total_urls)
        end
      end

      results
    end

    private

    def parse_single(username, include_email)
      return validation_error("Username is required") if username.blank?

      log_start(username)
      run_response = start_run(username, include_email)
      run = run_response[:data] || run_response
      completed = wait_for_completion(run[:id])

      return handle_failure(completed) unless completed[:status] == "SUCCEEDED"

      items = fetch_results(completed[:id])
      log_completion(completed, items.size)

      profile = items.first || {}
      concatenate_profile_fields(profile)
    end

    def start_run(username, include_email)
      payload = {
        username: username,
        includeEmail: include_email
      }
      client.post("acts/apimaestro~linkedin-profile-detail/runs", payload)
    end

    def wait_for_completion(run_id)
      120.times do |attempt|
        run_response = client.get("actor-runs/#{run_id}")
        run = run_response[:data] || run_response
        log_poll(run, attempt + 1)

        return run if terminal_status?(run[:status])

        sleep 5
      end

      raise_timeout("Run #{run_id} timeout after 10 minutes")
    end

    def fetch_results(run_id)
      client.get("actor-runs/#{run_id}/dataset/items") || []
    end

    def terminal_status?(status)
      %w[SUCCEEDED FAILED TIMED-OUT ABORTED].include?(status)
    end

    def handle_failure(run)
      raise_rate_limit if run[:statusMessage] == "rate limited"
      raise_run_failed(run[:statusMessage]) if run[:status] == "FAILED"
      raise_timeout("Actor run timed out") if run[:status] == "TIMED-OUT"
      raise_aborted("Actor run aborted")
    end

    def log_start(username)
      logger.info "[Apify::LinkedinProfileParserService] Starting: username=#{username}"
    end

    def log_poll(run, attempt)
      logger.debug "[Apify::LinkedinProfileParserService] Polling: #{run[:status]} (#{attempt}/120)"
    end

    def log_completion(run, count)
      logger.info "[Apify::LinkedinProfileParserService] Completed: #{count} profile(s)"
    end

    def validation_error(msg)
      raise ArgumentError, msg
    end

    def raise_rate_limit
      raise RateLimitError.new("LinkedIn rate limit", retry_after: Time.current.beginning_of_hour + 1.hour)
    end

    def raise_run_failed(msg)
      raise RunFailedError, msg
    end

    def raise_timeout(msg)
      raise TimeoutError, msg
    end

    def raise_aborted(msg)
      raise AbortedError, msg
    end

    def concatenate_profile_fields(profile)
      return profile if profile.empty? || profile.key?(:error)

      basic_info = profile[:basic_info] || profile["basic_info"]
      return profile if basic_info.blank?

      fields = []

      headline = basic_info[:headline] || basic_info["headline"]
      fields << headline if headline.present?

      about = basic_info[:about] || basic_info["about"]
      fields << about if about.present?

      location = basic_info[:location] || basic_info["location"]
      location_full = location&.dig(:full) || location&.dig("full")
      fields << location_full if location_full.present?

      top_skills = basic_info[:top_skills] || basic_info["top_skills"]
      if top_skills.present? && top_skills.is_a?(Array)
        fields << top_skills.join(", ")
      end

      profile[:concatenated_text] = fields.join(" ") if fields.any?
      profile
    end

    def broadcast_progress(sourcing, percentage, current, total)
      return unless sourcing

      SourcingChannel.broadcast_to(
        "#{sourcing.user_id}_sourcing_#{sourcing.id}",
        {
          type: "sourcing_linkedin_progress",
          percentage: percentage,
          current_profile: current,
          total_profiles: total,
          sourcing_id: sourcing.id
        }
      )
    rescue => e
      logger.error "[Apify::LinkedinProfileParserService] Failed to broadcast progress: #{e.message}"
    end
  end
end
