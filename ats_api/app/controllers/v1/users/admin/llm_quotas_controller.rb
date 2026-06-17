# frozen_string_literal: true

module V1
  module Users
    module Admin
      class LlmQuotasController < ApplicationController
        skip_before_action :load_resource
        skip_before_action :authorize_resource!
        skip_before_action :authorize_resource_class!
        skip_after_action :verify_policy_scoped
        before_action :set_quota, only: [ :show, :update, :grant_extra, :reset_usage ]

        def index
          authorize LlmQuota
          quotas = LlmQuota.includes(:account).order(:account_id)
          quotas = quotas.where(plan: params[:plan]) if params[:plan].present?
          quotas = quotas.where(enabled: params[:enabled]) if params[:enabled].present?

          render json: {
            success: true,
            data: quotas.map { |q| serialize_quota_with_usage(q) }
          }
        end

        def show
          authorize @llm_quota
          render json: {
            success: true,
            data: serialize_quota_with_usage(@llm_quota)
          }
        end

        def update
          authorize @llm_quota
          @llm_quota.update!(quota_params)

          render json: {
            success: true,
            data: serialize_quota_with_usage(@llm_quota),
            message: "Quota updated successfully"
          }
        end

        def grant_extra
          authorize @llm_quota, :update?
          amount = params.require(:extra_budget_usd).to_f
          expires_at = params[:expires_at].present? ? Time.zone.parse(params[:expires_at]) : nil
          reason = params[:reason]

          @llm_quota.grant_extra_budget!(amount: amount, expires_at: expires_at, reason: reason)

          render json: {
            success: true,
            data: serialize_quota_with_usage(@llm_quota.reload),
            message: "Extra budget of $#{amount} granted successfully"
          }
        end

        def reset_usage
          authorize @llm_quota, :update?
          usage = LlmQuotaUsage.current_for(@llm_quota.account_id)
          usage.update!(
            total_cost_usd: 0,
            total_requests: 0,
            total_tokens: 0,
            cost_by_model: {},
            cost_by_operation: {},
            last_synced_at: Time.current
          )

          render json: {
            success: true,
            message: "Usage reset for period #{usage.period}"
          }
        end

        private

        def set_quota
          @llm_quota = LlmQuota.find_by(id: params[:id])
          return if @llm_quota

          render json: { success: false, error: "Quota not found" }, status: :not_found
        end

        def quota_params
          params.require(:llm_quota).permit(
            :plan, :monthly_cost_limit_usd, :monthly_request_limit,
            :burst_rpm, :enabled, :notify_at_percentage, :hard_limit
          )
        end

        def serialize_quota_with_usage(quota)
          usage = LlmQuotaUsage.current_for(quota.account_id)
          {
            id: quota.id,
            account_id: quota.account_id,
            account_name: quota.account&.name,
            plan: quota.plan,
            monthly_cost_limit_usd: quota.monthly_cost_limit_usd.to_f,
            monthly_request_limit: quota.monthly_request_limit,
            burst_rpm: quota.burst_rpm,
            extra_budget_usd: quota.extra_budget_usd.to_f,
            extra_budget_expires_at: quota.extra_budget_expires_at&.iso8601,
            effective_monthly_limit: quota.effective_monthly_limit.to_f,
            enabled: quota.enabled,
            hard_limit: quota.hard_limit,
            notify_at_percentage: quota.notify_at_percentage,
            current_usage: {
              period: usage.period,
              total_cost_usd: usage.total_cost_usd.to_f.round(6),
              total_requests: usage.total_requests,
              total_tokens: usage.total_tokens,
              usage_percentage: quota.usage_percentage.to_f,
              cost_remaining: quota.cost_remaining.to_f.round(6)
            },
            metadata: quota.metadata,
            created_at: quota.created_at.iso8601,
            updated_at: quota.updated_at.iso8601
          }
        end
      end
    end
  end
end
