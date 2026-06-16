# frozen_string_literal: true

module AtsSync
  class CandidateJob
    include Sidekiq::Job

    sidekiq_options queue: :ats_sync, retry: 3

    def perform(candidate_id, account_id = nil)
      account = account_id ? Account.find(account_id) : find_account_from_candidate(candidate_id)
      return unless account&.tenant.present?

      Apartment::Tenant.switch(account.tenant) do
        candidate = Candidate.find(candidate_id)
        AtsSync::CandidateService.sync(candidate)
      end
    rescue ActiveRecord::RecordNotFound => e
      Rails.logger.warn "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      Rails.logger.warn "⚠️  [ATS_SYNC] Candidate not found"
      Rails.logger.warn "   ID: #{candidate_id}"
      Rails.logger.warn "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    rescue AtsSync::ApiClient::ApiError => e
      Rails.logger.error "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      Rails.logger.error "❌ [ATS_SYNC] API Error - Will retry"
      Rails.logger.error "   Candidate ID: #{candidate_id}"
      Rails.logger.error "   Error: #{e.message}"
      Rails.logger.error "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      raise
    end

    private

    def find_account_from_candidate(candidate_id)
      Account.joins(:candidates).where(candidates: { id: candidate_id }).first
    end
  end
end
