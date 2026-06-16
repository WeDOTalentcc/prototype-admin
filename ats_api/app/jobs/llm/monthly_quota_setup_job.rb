# frozen_string_literal: true

module Llm
  class MonthlyQuotaSetupJob
    include Sidekiq::Job

    sidekiq_options queue: :low, retry: 2

    def perform
      current_period = Date.current.strftime("%Y-%m")
      created_count = 0

      LlmQuota.where(enabled: true).find_each do |quota|
        LlmQuotaUsage.find_or_create_by!(
          account_id: quota.account_id,
          period: current_period
        ) do |usage|
          usage.total_cost_usd = 0
          usage.total_requests = 0
          usage.total_tokens = 0
          usage.cost_by_model = {}
          usage.cost_by_operation = {}
          created_count += 1
        end
      rescue => e
        Rails.logger.error "[Llm::MonthlyQuotaSetupJob] Error for account #{quota.account_id}: #{e.message}"
      end

      Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      Rails.logger.info "🔄 [Llm::MonthlyQuotaSetupJob] Monthly quota setup complete"
      Rails.logger.info "   Period: #{current_period}"
      Rails.logger.info "   New snapshots created: #{created_count}"
      Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    end
  end
end
