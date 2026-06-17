module Pearch
  class ContactEnrichmentService
    def initialize(sourced_profile:, user:, enrich_emails: false, enrich_phones: false, require_phones_or_emails: true)
      @sourced_profile = sourced_profile
      @user = user
      @enrich_emails = enrich_emails
      @enrich_phones = enrich_phones
      @filter_out_no_phones_or_emails = require_phones_or_emails
      @account = sourced_profile.account

      Rails.logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
      Rails.logger.info("🔍 [ContactEnrichmentService] Initializing")
      Rails.logger.info("   Profile ID: #{sourced_profile.id}")
      Rails.logger.info("   User ID: #{user.id}")
      Rails.logger.info("   Enrich Emails: #{enrich_emails}")
      Rails.logger.info("   Enrich Phones: #{enrich_phones}")
      Rails.logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    end

    def enrich!
      return { success: false, error: "No enrichment requested" } unless enrichment_requested?

      validate_credits!
      search_options = build_search_options
      result = perform_search(search_options)

      process_enrichment_result(result)
    rescue Pearch::CreditsService::InsufficientCreditsError => e
      { success: false, error: e.message }
    rescue StandardError => e
      Rails.logger.error("[ContactEnrichmentService] Enrichment failed: #{e.message}")
      { success: false, error: e.message }
    end

    private

    def enrichment_requested?
      @enrich_emails || @enrich_phones
    end

    def validate_credits!
      estimated_cost = estimate_cost
      credits_service = Pearch::CreditsService.new(@account)

      return if credits_service.has_sufficient_credits?(estimated_cost)

      raise Pearch::CreditsService::InsufficientCreditsError,
            "Insufficient credits for contact enrichment. Required: ~#{estimated_cost}, Available: #{credits_service.current_balance}"
    end

    def estimate_cost
      cost = 1
      cost += 1 if @filter_out_no_phones_or_emails
      cost += 2 if @enrich_emails
      cost += 14 if @enrich_phones
      cost
    end

    def build_search_options
      {
        type: "fast",
        insights: false,
        profile_scoring: false,
        high_freshness: false,
        reveal_emails: @enrich_emails,
        reveal_phones: @enrich_phones,
        filter_out_no_phones_or_emails: @filter_out_no_phones_or_emails,
        limit: 1,
        docid_whitelist: [ @sourced_profile.external_id ],
        skip_sourcing_creation: true
      }
    end

    def perform_search(options)
      service = Pearch::SearchService.new(
        account: @account,
        user: @user
      )

      service.search(
        query: @sourced_profile.name || @sourced_profile.title,
        **options
      )
    end

    def process_enrichment_result(result)
      profile_data = result[:search_results]&.first&.dig(:profile)

      emails_found = false
      phones_found = false

      ActiveRecord::Base.transaction do
        if profile_data
          emails_data = profile_data[:personal_emails] || []
          emails_data = [ profile_data[:best_personal_email] ].compact if emails_data.empty? && profile_data[:best_personal_email].present?

          if @enrich_emails && emails_data.present?
            @sourced_profile.update!(
              emails: emails_data,
              emails_enriched_at: Time.current
            )
            emails_found = true
          end

          if @enrich_phones && profile_data[:phone_numbers].present?
            @sourced_profile.update!(
              phones: profile_data[:phone_numbers],
              phones_enriched_at: Time.current
            )
            phones_found = true
          end
        end
      end

      credits_used = result[:credits_used]

      if credits_used.nil? || credits_used.to_i.zero?
        credits_used = estimate_cost
      end

      {
        success: true,
        emails_found: emails_found,
        phones_found: phones_found,
        credits_used: credits_used
      }
    end
  end
end
