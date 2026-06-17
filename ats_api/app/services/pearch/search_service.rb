module Pearch
  class SearchService
    API_URL = "https://api.pearch.ai/v2/search"

    def initialize(api_key: nil, account: nil, user: nil)
      @api_key = api_key || ENV["PEARCH_API_KEY"]
      @account = account
      @user = user

      raise ArgumentError, "PEARCH_API_KEY is required" if @api_key.blank?
      raise ArgumentError, "Account is required" if @account.blank?
      raise ArgumentError, "User is required" if @user.blank?
    end

    def search(query:, **options)
      validate_credits!(options)

      params = build_params(query, options)
      response = make_request(params)
      result = parse_response(response)

      log_search_and_consume_credits(result, params)

      result
    end

    private

    def validate_credits!(options)
      estimated_cost = estimate_cost(options)
      credits_service = Pearch::CreditsService.new(@account)

      unless credits_service.has_sufficient_credits?(estimated_cost)
        raise Pearch::CreditsService::InsufficientCreditsError,
              "Insufficient credits. Required: ~#{estimated_cost}, Available: #{credits_service.current_balance}"
      end
    end

    def estimate_cost(options)
      limit = options[:limit] || 10
      type_cost = options[:type] == "fast" ? 1 : 5
      base_cost = limit * type_cost

      base_cost += limit if options.fetch(:insights, true)
      base_cost += limit if options.fetch(:profile_scoring, true)
      base_cost += limit * 2 if options.fetch(:high_freshness, false)
      base_cost += limit * 2 if options.fetch(:reveal_emails, false) || options.fetch(:show_emails, false)
      base_cost += limit * 14 if options.fetch(:reveal_phones, false) || options.fetch(:show_phone_numbers, false)
      base_cost += limit if options.fetch(:filter_out_no_emails, false) || options.fetch(:require_emails, false)
      base_cost += limit if options.fetch(:filter_out_no_phones, false) || options.fetch(:require_phone_numbers, false)
      base_cost += limit if options.fetch(:filter_out_no_phones_or_emails, false) || options.fetch(:require_phones_or_emails, false)

      base_cost
    end

    def log_search_and_consume_credits(result, params)
      credits_used = result[:credits_used] || 0

      sourcing_id = params.delete(:sourcing_id)
      sourcing = sourcing_id ? Sourcing.find(sourcing_id) : nil

      ActiveRecord::Base.transaction do
        search_log = PearchSearchLog.create!(
          account: @account,
          user: @user,
          query: params[:query],
          thread_id: result[:thread_id],
          uuid: result[:uuid],
          search_parameters: params,
          results_count: result[:search_results]&.size || 0,
          total_estimate: result[:total_estimate],
          total_estimate_is_lower_bound: result[:total_estimate_is_lower_bound] || false,
          credits_used: credits_used,
          credits_remaining_after: result[:credits_remaining],
          duration_seconds: result[:duration],
          status: result[:status],
          response_metadata: result.except(:search_results, :parameters)
        )

        if credits_used > 0
          credits_service = Pearch::CreditsService.new(@account)
          credits_service.consume_credits!(
            credits_used,
            reason: "Pearch search: #{params[:query].truncate(100)}",
            reference_id: search_log.id.to_s,
            reference_type: "PearchSearchLog",
            metadata: {
              query: params[:query],
              type: params[:type],
              results_count: result[:search_results]&.size || 0
            }
          )
        else
          Rails.logger.info("ℹ️  [Pearch] Skipping credit consumption - credits_used is #{credits_used}")
        end

        if sourcing
          sourcing.update!(
            external_id: result[:uuid],
            thread_id: result[:thread_id],
            duration: result[:duration],
            total_estimate: result[:total_estimate],
            total_estimate_is_lower_bound: result[:total_estimate_is_lower_bound] || false,
            results_count: (result[:search_results] || []).size,
            credits_used: result[:credits_used],
            response_metadata: result.except(:search_results),
            status: "processing"
          )
        end
      end

      if sourcing
        ProcessSourcingJob.perform_async(
          @account.id,
          @user.id,
          params[:query],
          result.to_json,
          params.to_json,
          sourcing.id
        )

        broadcast_global_search_submitted(sourcing, result)
      end

      result[:sourcing_id] = sourcing.id if sourcing
      result
    rescue => e
      Rails.logger.error("[Pearch::SearchService] Failed to log search: #{e.message}")
      Rails.logger.error(e.backtrace.join("\n"))
      raise
    end

    def build_params(query, options)
      params = {
        query: query,
        type: options[:type] || "fast",
        insights: options.fetch(:insights, false),
        high_freshness: options.fetch(:high_freshness, false),
        profile_scoring: options.fetch(:profile_scoring, false),
        strict_filters: options.fetch(:strict_filters, false),
        filter_out_no_emails: options.fetch(:filter_out_no_emails, false),
        reveal_emails: options.fetch(:reveal_emails, false),
        filter_out_no_phones: options.fetch(:filter_out_no_phones, false),
        filter_out_no_phones_or_emails: options.fetch(:filter_out_no_phones_or_emails, false),
        reveal_phones: options.fetch(:reveal_phones, false),
        limit: options[:limit] || 1,
        offset: options[:offset] || 0
      }.tap do |p|
        p[:skip_sourcing_creation] = options[:skip_sourcing_creation] unless options[:skip_sourcing_creation].nil?
        p[:thread_id] = options[:thread_id] if options[:thread_id].present?
        p[:skip_sourcing_creation] = options[:skip_sourcing_creation] if options[:skip_sourcing_creation].present?
        p[:custom_filters] = build_custom_filters_with_default_location(options)
        p[:docid_blacklist] = options[:docid_blacklist] if options[:docid_blacklist].present?
        p[:docid_whitelist] = options[:docid_whitelist] if options[:docid_whitelist].present?
      end

      params
    end

    def build_custom_filters_with_default_location(options)
      custom_filters = options[:custom_filters] || {}

      has_location = has_location_parameter?(options, custom_filters)

      unless has_location
        custom_filters = custom_filters.deep_dup if custom_filters.is_a?(Hash)
        custom_filters ||= {}

        custom_filters[:locations] = [ "Brasil" ]
      end

      return nil unless custom_filters.is_a?(Hash)
      return nil if custom_filters.empty?
      custom_filters
    end

    def has_location_parameter?(options, custom_filters)
      return true if options[:city].present?
      return true if options[:state].present?
      return true if options[:country].present?

      return true if custom_filters.is_a?(Hash) && custom_filters[:locations].present?
      return true if custom_filters.is_a?(Hash) && custom_filters["locations"].present?

      return true if custom_filters.is_a?(Hash) && custom_filters[:country].present?
      return true if custom_filters.is_a?(Hash) && custom_filters["country"].present?

      false
    end

    def make_request(params)
      uri = URI(API_URL)
      http = Net::HTTP.new(uri.host, uri.port)
      http.use_ssl = true
      http.read_timeout = 180 # 3 minutes for pro search

      request = Net::HTTP::Post.new(uri.path)
      request["Content-Type"] = "application/json"
      request["Accept"] = "application/json"
      request["Authorization"] = "Bearer #{@api_key}"
      request.body = params.to_json

      response = http.request(request)

      unless response.is_a?(Net::HTTPSuccess)
        handle_error(response)
      end

      response
    end

    def parse_response(response)
      JSON.parse(response.body, symbolize_names: true)
    rescue JSON::ParserError => e
      Rails.logger.error("[Pearch::SearchService] Failed to parse response: #{e.message}")
      raise StandardError, "Invalid JSON response from Pearch API"
    end

    ERROR_HANDLERS = {
      400 => ->(msg) { raise ArgumentError, "Invalid parameters: #{msg}" },
      401 => ->(msg) { raise StandardError, "Invalid API key: #{msg}" },
      429 => ->(msg) { raise StandardError, "Rate limit exceeded: #{msg}" }
    }.freeze

    def handle_error(response)
      status_code = response.code.to_i
      raw_body = response.body

      begin
        error_body = JSON.parse(raw_body)
        error_message = error_body["error"] ||
                       error_body["message"] ||
                       error_body["status"] ||
                       error_body["detail"] ||
                       error_body["errors"]&.to_json ||
                       "Request failed"
      rescue JSON::ParserError
        error_message = raw_body.presence || "Request failed"
      end

      handler = ERROR_HANDLERS[status_code] || ->(msg) { raise StandardError, "Pearch API error (#{status_code}): #{msg}" }
      handler.call(error_message)
    end

    def broadcast_global_search_submitted(sourcing, result)
      SourcingChannel.broadcast_to(
        "#{@user.id}_sourcing_#{sourcing.id}",
        {
          type: "global_search_submitted",
          sourcing_id: sourcing.id,
          search_type: "global",
          external_id: result[:uuid],
          thread_id: result[:thread_id],
          total_estimate: result[:total_estimate],
          timestamp: Time.current.iso8601,
          message: "Busca global enviada ao Pearch..."
        }
      )
    rescue => e
      Rails.logger.error("[Pearch::SearchService] Failed to broadcast global_search_submitted: #{e.message}")
    end
  end
end
