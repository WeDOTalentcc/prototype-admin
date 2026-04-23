# frozen_string_literal: true

module V1
  module Users
    class LlmQuotasController < V1::Users::ApplicationController
      def current
        quota = find_or_create_quota
        usage = LlmQuotaUsage.current_for(@current_user.account_id)

        render json: {
          success: true,
          data: {
            quota: serialize_quota(quota),
            usage: serialize_usage(usage),
            summary: build_summary(quota, usage)
          }
        }
      end

      def update_current
        quota = find_or_create_quota
        return render_forbidden unless @current_user.is_admin

        quota.update!(update_params)

        render json: {
          success: true,
          data: { quota: serialize_quota(quota) },
          message: "Quota updated successfully"
        }
      end

      private

      def find_or_create_quota
        LlmQuota.find_or_create_by!(account_id: @current_user.account_id) do |q|
          defaults = Llm::QuotaPlan.defaults_for(Llm::QuotaPlan::DEFAULT_PLAN)
          q.plan = Llm::QuotaPlan::DEFAULT_PLAN
          q.monthly_cost_limit_usd = defaults[:monthly_cost_limit_usd]
          q.monthly_request_limit = defaults[:monthly_request_limit]
          q.burst_rpm = defaults[:burst_rpm]
          q.extra_budget_usd = 0.0
          q.notify_at_percentage = 80
          q.enabled = true
          q.hard_limit = false
          q.metadata = {}
        end
      end

      def serialize_quota(quota)
        {
          id: quota.id,
          plan: quota.plan,
          monthly_cost_limit_usd: quota.monthly_cost_limit_usd.to_f,
          monthly_request_limit: quota.monthly_request_limit,
          burst_rpm: quota.burst_rpm,
          extra_budget_usd: quota.extra_budget_usd.to_f,
          extra_budget_expires_at: quota.extra_budget_expires_at&.iso8601,
          effective_monthly_limit: quota.effective_monthly_limit.to_f,
          enabled: quota.enabled,
          notify_at_percentage: quota.notify_at_percentage,
          hard_limit: quota.hard_limit
        }
      end

      def serialize_usage(usage)
        {
          period: usage.period,
          total_cost_usd: usage.total_cost_usd.to_f.round(6),
          total_requests: usage.total_requests,
          total_tokens: usage.total_tokens,
          cost_by_model: usage.cost_by_model,
          cost_by_operation: usage.cost_by_operation,
          last_synced_at: usage.last_synced_at&.iso8601
        }
      end

      def build_summary(quota, usage)
        {
          usage_percentage: quota.usage_percentage.to_f,
          cost_remaining_usd: quota.cost_remaining.to_f.round(6),
          requests_remaining: quota.requests_remaining,
          resets_at: Date.current.next_month.beginning_of_month.beginning_of_day.iso8601,
          over_limit: quota.hard_limit? && usage.total_cost_usd >= quota.effective_monthly_limit
        }
      end

      def update_params
        params.require(:llm_quota).permit(:notify_at_percentage, :hard_limit)
      end

      def render_forbidden
        render json: { success: false, error: "Admin access required" }, status: :forbidden
      end
    end
  end
end
