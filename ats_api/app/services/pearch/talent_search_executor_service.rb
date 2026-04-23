module Pearch
  class TalentSearchExecutorService
    attr_reader :user, :account, :query, :params

    def initialize(user:, query:, params:)
      @user = user
      @account = user.account
      @query = query
      @params = params
    end

    def call
      parsed_result = parse_query if should_parse_query?
      search_options = build_search_options
      merge_account_config!(search_options)
      query_to_use = extract_query(parsed_result)
      merge_custom_filters!(search_options, parsed_result)
      results = execute_search(query_to_use, search_options)
      sanitized_results = results.except(:credits_remaining)

      add_query_metadata!(sanitized_results, parsed_result) if parsed_result

      { success: true, data: sanitized_results }
    rescue Pearch::CreditsService::InsufficientCreditsError => e
      handle_insufficient_credits(e)
    rescue ArgumentError => e
      { success: false, error: e.message, status: :bad_request }
    rescue StandardError => e
      handle_standard_error(e)
    end

    private

    def should_parse_query?
      params[:parse_query] != "false"
    end

    def parse_query
      return nil if query.blank?
      Pearch::QueryParserService.call(query)
    rescue => e
      Rails.logger.error "❌ [TalentSearchExecutor] Parser failed: #{e.message}"
      nil
    end

    def build_search_options
      Pearch::SearchProfilesBuilder.build(params)
    end

    def extract_query(parsed_result)
      return query unless parsed_result&.dig(:query).present?
      parsed_result[:query]
    end

    def merge_custom_filters!(search_options, parsed_result)
      return unless parsed_result

      llm_filters = parsed_result[:custom_filters] || {}
      existing_filters = search_options[:custom_filters] || {}

      if llm_filters.any? || existing_filters.any?
        merged = existing_filters.deep_dup

        llm_filters.each do |key, value|
          if merged[key].is_a?(Array) && value.is_a?(Array)
            merged[key] = (merged[key] + value).uniq
          elsif value.present?
            merged[key] = value
          end
        end

        search_options[:custom_filters] = merged
      end
    end

    def merge_account_config!(search_options)
      config = account.pearch_config
      search_options[:type] ||= config["type"]
    end

    def execute_search(query_to_use, search_options)
      service = Pearch::SearchService.new(account: account, user: user)
      service.search(query: query_to_use, **search_options)
    end

    def add_query_metadata!(results, parsed_result)
      results[:query_metadata] = {
        original_query: parsed_result.dig(:metadata, :original_query),
        parsed_query: parsed_result[:query],
        custom_filters_applied: parsed_result[:custom_filters] || {},
        confidence: parsed_result.dig(:metadata, :confidence),
        notes: parsed_result.dig(:metadata, :notes)
      }
    end

    def handle_insufficient_credits(exception)
      Rails.logger.error("💳 Insufficient credits error: #{exception.message}")
      {
        success: false,
        error: exception.message,
        current_balance: account.pearch_credits,
        status: :payment_required
      }
    end

    def handle_standard_error(exception)
      Rails.logger.error("[TalentSearchExecutor] Search failed: #{exception.message}")
      Rails.logger.error(exception.backtrace.join("\n"))
      {
        success: false,
        error: "Search failed: #{exception.message}",
        status: :internal_server_error
      }
    end
  end
end
