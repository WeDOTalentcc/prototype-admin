# frozen_string_literal: true

module AtsSync
  class ProcessApplyWithEnrichmentJob
    include Sidekiq::Job

    sidekiq_options queue: :ats_sync, retry: 3

    def perform(apply_id, account_id = nil)
      account = account_id ? Account.find(account_id) : find_account_from_apply(apply_id)
      return unless account&.tenant.present?

      Apartment::Tenant.switch(account.tenant) do
        apply = Apply.find_by(id: apply_id)
        return unless apply

        process_with_enrichment_and_sync(apply)
      end
    rescue ActiveRecord::RecordNotFound => e
      Rails.logger.warn "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      Rails.logger.warn "⚠️  [ProcessApplyWithEnrichmentJob] Apply not found: #{apply_id}"
      Rails.logger.warn "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    rescue AtsSync::ApiClient::ConnectionError => e
      Rails.logger.warn "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      Rails.logger.warn "⚠️  [ProcessApplyWithEnrichmentJob] ATS unreachable — skipping sync"
      Rails.logger.warn "   Apply ID: #{apply_id} | #{e.message}"
      Rails.logger.warn "   Local apply/candidate already saved. ATS sync will not be retried."
      Rails.logger.warn "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    rescue AtsSync::ApiClient::ApiError => e
      Rails.logger.error "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      Rails.logger.error "❌ [ProcessApplyWithEnrichmentJob] API Error - Will retry"
      Rails.logger.error "   Apply ID: #{apply_id}"
      Rails.logger.error "   Error: #{e.message}"
      Rails.logger.error "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      raise
    end

    private

    def process_with_enrichment_and_sync(apply)
      return unless validate_apply(apply)

      candidate = apply.candidate.reload

      ensure_candidate_ready(candidate)

      enrich_candidate_email(candidate)

      AtsSync::CandidateService.sync(candidate)

      apply.reload

      AtsSync::ApplyService.sync(apply)

      Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      Rails.logger.info "✅ [ProcessApplyWithEnrichmentJob] Process completed"
      Rails.logger.info "   Candidate: #{candidate.id} - #{candidate.name}"
      Rails.logger.info "   Email: #{candidate.email.present? ? '✅' : '❌'}"
      Rails.logger.info "   Apply: #{apply.id}"
      Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    end

    def validate_apply(apply)
      if apply.candidate.blank?
        Rails.logger.warn "⏭️  [ProcessApplyWithEnrichmentJob] Skipped - Apply##{apply.id} has no candidate"
        return false
      end
      if apply.job.blank?
        Rails.logger.warn "⏭️  [ProcessApplyWithEnrichmentJob] Skipped - Apply##{apply.id} has no job"
        return false
      end
      if apply.account.blank?
        Rails.logger.warn "⏭️  [ProcessApplyWithEnrichmentJob] Skipped - Apply##{apply.id} has no account"
        return false
      end
      if apply.account.ats_provider.blank?
        Rails.logger.warn "⏭️  [ProcessApplyWithEnrichmentJob] Skipped - Apply##{apply.id} account has no ats_provider"
        return false
      end

      true
    end

    def enrich_candidate_email(candidate)
      return if candidate.email.present?
      return if candidate.linkedin.blank?

      Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      Rails.logger.info "🔍 [ProcessApplyWithEnrichmentJob] ENRICHING EMAIL VIA APIFY"
      Rails.logger.info "   Candidate: #{candidate.id} - #{candidate.name}"
      Rails.logger.info "   LinkedIn: #{candidate.linkedin}"
      Rails.logger.info "   Current email: #{candidate.email.inspect}"
      Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

      service = Candidates::LinkedinEnrichmentService.new(candidate)
      result = service.call

      if result.success?
        candidate.reload
        Rails.logger.info "✅ [ProcessApplyWithEnrichmentJob] Email enrichment successful"
        Rails.logger.info "   New email: #{candidate.email.inspect}"
      else
        Rails.logger.warn "⚠️  [ProcessApplyWithEnrichmentJob] Email enrichment failed"
        Rails.logger.warn "   Error: #{result.error}"
      end
    rescue Apify::LinkedinProfileParserService::RateLimitError => e
      Rails.logger.warn "⚠️  [ProcessApplyWithEnrichmentJob] LinkedIn rate limit hit"
      Rails.logger.warn "   Will sync candidate without enrichment"
      Rails.logger.warn "   Retry in: #{e.minutes_until_retry} minutes"
    rescue => e
      Rails.logger.error "❌ [ProcessApplyWithEnrichmentJob] Email enrichment error"
      Rails.logger.error "   Error: #{e.message}"
      Rails.logger.error "   Will sync candidate without enrichment"
    end

    def find_account_from_apply(apply_id)
      Account.joins("JOIN applies ON applies.account_id = accounts.id")
             .where("applies.id = ?", apply_id)
             .first
    end

    def ensure_candidate_ready(candidate)
      return if candidate.name.present?

      candidate.update!(name: extract_name_from_curriculum(candidate))
    end

    def extract_name_from_curriculum(candidate)
      return "Candidato Sem Nome" if candidate.curriculum_text.blank?

      first_line = candidate.curriculum_text.lines.first&.strip
      return first_line if first_line.present? && first_line.length < 100

      "Candidato Sem Nome"
    end
  end
end
