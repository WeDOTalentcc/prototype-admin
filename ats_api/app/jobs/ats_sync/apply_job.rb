# frozen_string_literal: true

module AtsSync
  class ApplyJob
    include Sidekiq::Job

    sidekiq_options queue: :ats_sync, retry: 3

    def perform(apply_id, account_id)
      account = Account.find_by(id: account_id)
      return unless account

      Apartment::Tenant.switch(account.tenant) do
        apply = Apply.find(apply_id)
        AtsSync::ApplyService.sync(apply)
      end
    rescue ActiveRecord::RecordNotFound => e
      Rails.logger.warn "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      Rails.logger.warn "⚠️  [ATS_SYNC] Apply not found"
      Rails.logger.warn "   ID: #{apply_id}"
      Rails.logger.warn "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    rescue AtsSync::ApiClient::ApiError => e
      Rails.logger.error "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      Rails.logger.error "❌ [ATS_SYNC] API Error - Will retry"
      Rails.logger.error "   Apply ID: #{apply_id}"
      Rails.logger.error "   Error: #{e.message}"
      Rails.logger.error "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      raise
    end
  end
end
