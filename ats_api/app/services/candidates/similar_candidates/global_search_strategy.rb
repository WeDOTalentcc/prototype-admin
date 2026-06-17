# frozen_string_literal: true

module Candidates
  module SimilarCandidates
    class GlobalSearchStrategy
      DEFAULT_PEARCH_TYPE = "pro"
      DEFAULT_LIMIT = 10

      def initialize(account:, user:)
        @account = account
        @user = user
      end

      def search(base_candidates:, exclude_docids: [], pearch_options: {})
        return empty_result("No base candidates provided") if base_candidates.blank?

        synthesis = synthesize_profile(base_candidates)
        pearch_params = build_pearch_params(synthesis, exclude_docids, pearch_options)

        estimated_cost = estimate_cost(pearch_params)
        validate_credits!(estimated_cost)

        pearch_response = call_pearch(pearch_params)

        {
          results: normalize_results(pearch_response),
          pearch_response: pearch_response,
          synthesis: synthesis,
          credits_used: pearch_response["credits_used"] || 0,
          credits_remaining: pearch_response["credits_remaining"] || @account.pearch_credits
        }
      rescue Pearch::CreditsService::InsufficientCreditsError => e
        Rails.logger.warn("[GlobalSearchStrategy] #{e.message}")
        empty_result("insufficient_credits", error: e.message)
      rescue StandardError => e
        Rails.logger.error("[GlobalSearchStrategy] Error: #{e.message}")
        Rails.logger.error(e.backtrace.first(10).join("\n"))
        empty_result("search_failed", error: e.message)
      end

      private

      def synthesize_profile(base_candidates)
        Rails.logger.info("🧠 [GlobalSearchStrategy] Synthesizing profile from #{base_candidates.size} candidate(s)")

        synthesizer = ProfileSynthesizer.new
        synthesis = synthesizer.call(base_candidates)

        Rails.logger.info("   Query: #{synthesis[:query]}")
        Rails.logger.info("   Filters: #{synthesis[:custom_filters].to_json}")
        Rails.logger.info("   Method: #{synthesis[:synthesis_method]}")

        synthesis
      end

      def build_pearch_params(synthesis, exclude_docids, options)
        {
          query: synthesis[:query],
          type: options[:type] || DEFAULT_PEARCH_TYPE,
          insights: true,
          profile_scoring: true,
          high_freshness: options.fetch(:high_freshness, false),
          strict_filters: false,
          custom_filters: synthesis[:custom_filters],
          limit: options[:limit] || DEFAULT_LIMIT,
          offset: options[:offset] || 0,
          docid_blacklist: build_blacklist(exclude_docids, options)
        }.tap do |params|
          params[:reveal_emails] = options[:show_emails] if options[:show_emails]
          params[:reveal_phones] = options[:show_phone_numbers] if options[:show_phone_numbers]
          params[:filter_out_no_emails] = options[:require_emails] if options[:require_emails]
          params[:filter_out_no_phones] = options[:require_phone_numbers] if options[:require_phone_numbers]
        end
      end

      def build_blacklist(exclude_docids, options)
        blacklist = Array(exclude_docids).compact.uniq
        blacklist += Array(options[:additional_exclusions]).compact if options[:additional_exclusions]
        blacklist.presence
      end

      def estimate_cost(params)
        per_profile_cost = case params[:type]
        when "fast" then 1
        when "pro" then 5
        else 5
        end

        per_profile_cost += 1 if params[:insights]
        per_profile_cost += 1 if params[:profile_scoring]
        per_profile_cost += 2 if params[:high_freshness]
        per_profile_cost += 2 if params[:reveal_emails]
        per_profile_cost += 14 if params[:reveal_phones]
        per_profile_cost += 1 if params[:filter_out_no_emails]
        per_profile_cost += 1 if params[:filter_out_no_phones]

        total = per_profile_cost * params[:limit]

        Rails.logger.info("💰 [GlobalSearchStrategy] Estimated cost: #{total} credits (#{per_profile_cost} per profile × #{params[:limit]})")

        total
      end

      def validate_credits!(estimated_cost)
        credits_service = Pearch::CreditsService.new(@account)
        current_balance = credits_service.current_balance

        unless credits_service.has_sufficient_credits?(estimated_cost)
          raise Pearch::CreditsService::InsufficientCreditsError,
                "insufficient_credits:#{estimated_cost}:#{current_balance}"
        end

        Rails.logger.info("✅ [GlobalSearchStrategy] Credits sufficient: #{current_balance} available, #{estimated_cost} required")
      end

      def call_pearch(params)
        Rails.logger.info("🔍 [GlobalSearchStrategy] Calling Pearch API")
        Rails.logger.info("   Type: #{params[:type]}")
        Rails.logger.info("   Limit: #{params[:limit]}")
        Rails.logger.info("   Query: #{params[:query]}")

        service = Pearch::SearchService.new(
          account: @account,
          user: @user
        )

        response = service.search(**params)

        results_count = response["search_results"]&.size || 0
        credits_used = response["credits_used"] || 0

        Rails.logger.info("✅ [GlobalSearchStrategy] Pearch returned #{results_count} results")
        Rails.logger.info("   Credits used: #{credits_used}")
        Rails.logger.info("   Duration: #{response['duration']}s")

        response
      end

      def normalize_results(pearch_response)
        search_results = pearch_response["search_results"] || pearch_response[:search_results]
        return [] unless search_results

        search_results.map do |result|
          profile = result["profile"] || result[:profile] || {}

          {
            docid: result["docid"] || profile["docid"],
            pearch_score: result["score"],
            name: build_full_name(profile),
            title: profile["title"],
            current_company: extract_current_company(profile),
            location: profile["location"],
            total_experience_years: profile["total_experience_years"],
            expertise: profile["expertise"] || [],
            insights: result["insights"] || {},
            profile_data: profile
          }
        end
      end

      def build_full_name(profile)
        [
          profile["first_name"],
          profile["middle_name"],
          profile["last_name"]
        ].compact.join(" ").presence || "Unknown"
      end

      def extract_current_company(profile)
        experiences = profile["experiences"] || []
        current_exp = experiences.find { |exp| exp["end_date"].nil? || exp["end_date"].blank? }
        current_exp&.dig("company")
      end

      def empty_result(reason, error: nil)
        {
          results: [],
          pearch_response: nil,
          synthesis: nil,
          credits_used: 0,
          credits_remaining: @account.pearch_credits,
          error: reason,
          error_message: error
        }
      end
    end
  end
end
