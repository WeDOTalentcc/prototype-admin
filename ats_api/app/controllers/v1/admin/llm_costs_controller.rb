# frozen_string_literal: true

module V1
  module Admin
    class LlmCostsController < ApplicationController
      before_action :ensure_admin

      def overview
        days = (params[:days] || 30).to_i
        start_date = days.days.ago
        scope = LlmUsage.where("created_at >= ?", start_date)

        total_cost = scope.sum(:cost_usd)

        costs_by_model = scope.group(:model).sum(:cost_usd)

        costs_by_operation = scope.group(:operation).sum(:cost_usd)

        costs_by_account = LlmUsage.joins(:account)
                                    .where("llm_usages.created_at >= ?", start_date)
                                    .group("accounts.name")
                                    .sum(:cost_usd)

        costs_by_user = LlmUsage.joins(:user)
                                .where("llm_usages.created_at >= ?", start_date)
                                .group("users.name")
                                .sum(:cost_usd)

        daily_costs = scope.group("DATE(created_at)").sum(:cost_usd)

        render json: {
          success: true,
          data: {
            period_days: days,
            total_cost: total_cost.to_f.round(6),
            costs_by_model: costs_by_model.transform_values { |v| v.to_f.round(6) },
            costs_by_operation: costs_by_operation.transform_values { |v| v.to_f.round(6) },
            costs_by_account: costs_by_account.transform_values { |v| v.to_f.round(6) },
            costs_by_user: costs_by_user.transform_values { |v| v.to_f.round(6) },
            daily_costs: daily_costs.transform_keys(&:to_s).transform_values { |v| v.to_f.round(6) },
            total_tokens: scope.sum(:total_tokens),
            record_count: scope.count
          }
        }
      end

      private

      def ensure_admin
        return if @current_user&.has_role?(:admin)

        render json: {
          success: false,
          error: {
            code: "UNAUTHORIZED",
            message: "Admin access required"
          }
        }, status: :forbidden
      end
    end
  end
end
