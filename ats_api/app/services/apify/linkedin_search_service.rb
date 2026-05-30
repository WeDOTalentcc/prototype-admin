module Apify
  class LinkedinSearchService
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

    # Versao pinada do actor Apify. Atualizar via ADR quando o autor publicar
    # breaking change confirmada. Floating latest = risco de schema drift silencioso.
    ACTOR_ID = "harvestapi~linkedin-profile-search".freeze

    class << self
      def search(**options)
        new.search(**options)
      end

      def builder
        QueryBuilder.new
      end
    end

    attr_reader :client, :logger

    def initialize(client: nil, logger: nil)
      @client = client || HttpClient.new
      @logger = logger || Rails.logger
    end

    def search(**options)
      query = Query.new(**options)

      return validation_error("No search criteria") unless query.valid?

      log_start(query)
      run_response = start_run(query)
      run = run_response[:data] || run_response
      completed = wait_for_completion(run[:id])

      return handle_failure(completed) unless completed[:status] == "SUCCEEDED"

      items = fetch_results(completed[:id])
      log_completion(completed, items.size)

      ResultSet.new(profiles: items, query: query, run_metadata: completed)
    end

    private

    def start_run(query)
      client.post("acts/#{ACTOR_ID}/runs", query.to_actor_input)
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

    def log_start(query)
      logger.info "[Apify::LinkedinSearch] Starting: #{query.log_summary}"
    end

    def log_poll(run, attempt)
      logger.debug "[Apify::LinkedinSearch] Polling: #{run[:status]} (#{attempt}/120)"
    end

    def log_completion(run, count)
      logger.info "[Apify::LinkedinSearch] Completed: #{count} profiles"
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
  end
end
