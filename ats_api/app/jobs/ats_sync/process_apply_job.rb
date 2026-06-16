# frozen_string_literal: true

module AtsSync
  class ProcessApplyJob
    include Sidekiq::Job

    sidekiq_options queue: :ats_sync, retry: 3

    def perform(apply_id, account_id = nil)
      account = account_id ? Account.find(account_id) : find_account_from_apply(apply_id)
      return unless account&.tenant.present?

      Apartment::Tenant.switch(account.tenant) do
        apply = Apply.find_by(id: apply_id)
        return unless apply

        process_and_sync(apply)
      end
    rescue ActiveRecord::RecordNotFound => e
      Rails.logger.warn "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      Rails.logger.warn "⚠️  [ATS_SYNC] Apply not found: #{apply_id}"
      Rails.logger.warn "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    rescue AtsSync::ApiClient::ApiError => e
      Rails.logger.error "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      Rails.logger.error "❌ [ATS_SYNC] API Error - Will retry"
      Rails.logger.error "   Apply ID: #{apply_id}"
      Rails.logger.error "   Error: #{e.message}"
      Rails.logger.error "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      raise
    end

    private

    def process_and_sync(apply)
      if apply.candidate.blank?
        Rails.logger.warn "⏭️  [ProcessApplyJob] Skipped - Apply##{apply.id} has no candidate"
        return
      end
      if apply.job.blank?
        Rails.logger.warn "⏭️  [ProcessApplyJob] Skipped - Apply##{apply.id} has no job"
        return
      end
      if apply.account.blank?
        Rails.logger.warn "⏭️  [ProcessApplyJob] Skipped - Apply##{apply.id} has no account"
        return
      end
      if apply.account.ats_provider.blank?
        Rails.logger.warn "⏭️  [ProcessApplyJob] Skipped - Apply##{apply.id} account has no ats_provider"
        return
      end

      candidate = apply.candidate.reload

      ensure_candidate_ready(candidate)

      AtsSync::CandidateService.sync(candidate)

      apply.reload

      AtsSync::ApplyService.sync(apply)

      Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      Rails.logger.info "✅ [ATS_SYNC] Process completed"
      Rails.logger.info "   Candidate: #{candidate.id} - #{candidate.name}"
      Rails.logger.info "   Apply: #{apply.id}"
      Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
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
