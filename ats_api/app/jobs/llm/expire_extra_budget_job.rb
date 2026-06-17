# frozen_string_literal: true

module Llm
  class ExpireExtraBudgetJob
    include Sidekiq::Job

    sidekiq_options queue: :low, retry: 2

    def perform
      expired_count = 0

      expired_scope = LlmQuota
        .where("extra_budget_usd > 0")
        .where("extra_budget_expires_at IS NOT NULL")
        .where("extra_budget_expires_at < ?", Time.current)

      expired_scope.find_each do |quota|
        quota.update!(
          extra_budget_usd: 0,
          extra_budget_expires_at: nil,
          metadata: quota.metadata.merge(
            "last_extra_expired_at" => Time.current.iso8601,
            "last_extra_amount_expired" => quota.extra_budget_usd.to_f
          )
        )
        expired_count += 1
      rescue => e
        Rails.logger.error "[Llm::ExpireExtraBudgetJob] Error expiring quota #{quota.id}: #{e.message}"
      end

      return if expired_count.zero?

      Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      Rails.logger.info "🔄 [Llm::ExpireExtraBudgetJob] Extra budgets expired"
      Rails.logger.info "   Expired count: #{expired_count}"
      Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    end
  end
end
