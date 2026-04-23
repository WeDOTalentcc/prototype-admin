# frozen_string_literal: true

module Llm
  class QuotaUsageSyncJob
    include Sidekiq::Job

    sidekiq_options queue: :low, retry: 2

    def perform
      current_period = Date.current.strftime("%Y-%m")
      start_of_month = Date.current.beginning_of_month
      end_of_month = Date.current.end_of_month.end_of_day

      LlmQuota.find_each do |quota|
        sync_account(quota.account_id, current_period, start_of_month, end_of_month)
      rescue => e
        Rails.logger.error "[Llm::QuotaUsageSyncJob] Error syncing account #{quota.account_id}: #{e.message}"
      end
    end

    private

    def sync_account(account_id, current_period, start_of_month, end_of_month)
      real_usage = LlmUsage
        .by_account(account_id)
        .where(created_at: start_of_month..end_of_month)
        .successful

      snapshot = LlmQuotaUsage.current_for(account_id)

      snapshot.update!(
        total_cost_usd: real_usage.sum(:cost_usd),
        total_requests: real_usage.count,
        total_tokens: real_usage.sum(:total_tokens),
        cost_by_model: real_usage.group(:model).sum(:cost_usd).transform_values { |v| v.to_f.round(8) },
        cost_by_operation: real_usage.group(:operation).sum(:cost_usd).transform_values { |v| v.to_f.round(8) },
        last_synced_at: Time.current
      )
    end
  end
end
