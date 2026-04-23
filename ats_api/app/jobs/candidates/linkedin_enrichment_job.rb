# frozen_string_literal: true

module Candidates
  class LinkedinEnrichmentJob < ApplicationJob
    queue_as :linkedin_enrichment

    retry_on Apify::LinkedinProfileParserService::RateLimitError, wait: :exponentially_longer, attempts: 5
    discard_on Apify::LinkedinProfileParserService::ValidationError

    def perform(candidate_id, account_id)
      candidate = find_candidate(candidate_id, account_id)
      return unless candidate
      return unless should_enrich?(candidate)

      log_enrichment_start(candidate)

      result = enrich_candidate(candidate)

      return handle_failure(candidate, result) unless result.success?

      log_enrichment_success(candidate, result)
      broadcast_enrichment_completed(candidate)
    rescue => e
      handle_unexpected_error(candidate, e)
      raise
    end

    private

    def find_candidate(candidate_id, account_id)
      Apartment::Tenant.switch!(Account.find(account_id).tenant)
      Candidate.find_by(id: candidate_id, account_id: account_id)
    end

    def should_enrich?(candidate)
      return false if candidate.linkedin.blank?
      return false if recently_enriched?(candidate)
      true
    end

    def recently_enriched?(candidate)
      return false unless candidate.linkedin_enriched_at
      candidate.linkedin_enriched_at > 7.days.ago
    end

    def enrich_candidate(candidate)
      Candidates::LinkedinEnrichmentService.new(candidate).call
    end

    def handle_failure(candidate, result)
      log_enrichment_failure(candidate, result)
      broadcast_enrichment_failed(candidate, result.error)
    end

    def log_enrichment_start(candidate)
      Rails.logger.info "🔄 [LinkedinEnrichmentJob] Starting enrichment for candidate ##{candidate.id}"
      Rails.logger.info "   LinkedIn: #{candidate.linkedin}"
    end

    def log_enrichment_success(candidate, result)
      Rails.logger.info "✅ [LinkedinEnrichmentJob] Successfully enriched candidate ##{candidate.id}"
      Rails.logger.info "   Updated: #{result.stats.inspect}"
    end

    def log_enrichment_failure(candidate, result)
      Rails.logger.error "❌ [LinkedinEnrichmentJob] Failed to enrich candidate ##{candidate.id}"
      Rails.logger.error "   Error: #{result.error}"
    end

    def handle_unexpected_error(candidate, error)
      Rails.logger.error "❌ [LinkedinEnrichmentJob] Unexpected error for candidate ##{candidate&.id}"
      Rails.logger.error "   #{error.class}: #{error.message}"
      Rails.logger.error error.backtrace.first(5).join("\n")
    end

    def broadcast_enrichment_completed(candidate)
      Rails.logger.info "✅ Enrichment completed for candidate ##{candidate.id}"
    rescue => e
      Rails.logger.error "Failed to broadcast enrichment completion: #{e.message}"
    end

    def broadcast_enrichment_failed(candidate, error)
      Rails.logger.error "❌ Enrichment failed for candidate ##{candidate.id}: #{error}"
    rescue => e
      Rails.logger.error "Failed to broadcast enrichment failure: #{e.message}"
    end
  end
end
