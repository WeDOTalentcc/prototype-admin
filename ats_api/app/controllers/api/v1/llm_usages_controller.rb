# frozen_string_literal: true

module Api
  module V1
    class LlmUsagesController < ApplicationController
      before_action :authenticate_user!
      before_action :set_llm_usage, only: [ :show ]

      def index
        llm_usages = LlmUsage
          .where(account_id: current_account.id)
          .order(created_at: :desc)
          .page(params[:page] || 1)
          .per(params[:per_page] || 50)

        llm_usages = apply_filters(llm_usages)

        render json: {
          success: true,
          data: llm_usages.map { |usage| serialize_usage(usage) },
          meta: {
            current_page: llm_usages.current_page,
            total_pages: llm_usages.total_pages,
            total_count: llm_usages.total_count,
            per_page: llm_usages.limit_value
          }
        }, status: :ok
      end

      def show
        render json: {
          success: true,
          data: serialize_usage(@llm_usage)
        }, status: :ok
      end

      def stats
        stats = {
          today: today_stats,
          this_month: month_stats,
          last_30_days: last_30_days_stats,
          by_model: stats_by_model,
          by_operation: stats_by_operation,
          daily_trend: daily_trend
        }

        render json: {
          success: true,
          data: stats
        }, status: :ok
      end

      def create
        llm_usage = LlmUsage.new(llm_usage_params)
        llm_usage.account = current_account
        llm_usage.user = current_user

        if llm_usage.save
          render json: {
            success: true,
            data: serialize_usage(llm_usage),
            message: "LLM usage tracked successfully"
          }, status: :created
        else
          render json: {
            success: false,
            errors: llm_usage.errors.full_messages
          }, status: :unprocessable_entity
        end
      end

      private

      def set_llm_usage
        @llm_usage = LlmUsage.find_by(id: params[:id], account_id: current_account.id)

        unless @llm_usage
          render json: {
            success: false,
            error: "LLM usage not found"
          }, status: :not_found
        end
      end

      def apply_filters(relation)
        relation = relation.where(model: params[:model]) if params[:model].present?
        relation = relation.where(operation: params[:operation]) if params[:operation].present?
        relation = relation.where(success: params[:success]) if params[:success].present?
        relation = relation.where(user_id: params[:user_id]) if params[:user_id].present?

        if params[:start_date].present?
          relation = relation.where("created_at >= ?", params[:start_date])
        end

        if params[:end_date].present?
          relation = relation.where("created_at <= ?", params[:end_date])
        end

        relation
      end

      def serialize_usage(usage)
        {
          id: usage.id,
          model: usage.model,
          operation: usage.operation,
          input_tokens: usage.input_tokens,
          output_tokens: usage.output_tokens,
          total_tokens: usage.total_tokens,
          cost_usd: usage.cost_usd.to_f.round(8),
          latency_ms: usage.latency_ms.to_f.round(2),
          success: usage.success,
          error_message: usage.error_message,
          context: usage.context,
          user_id: usage.user_id,
          created_at: usage.created_at.iso8601
        }
      end

      def today_stats
        scope = LlmUsage.where(account_id: current_account.id).today

        {
          total_cost: scope.sum(:cost_usd).to_f.round(4),
          total_requests: scope.count,
          successful_requests: scope.successful.count,
          failed_requests: scope.failed.count,
          total_tokens: scope.sum(:total_tokens),
          avg_latency_ms: scope.successful.average(:latency_ms)&.to_f&.round(2) || 0
        }
      end

      def month_stats
        scope = LlmUsage.where(account_id: current_account.id).this_month

        {
          total_cost: scope.sum(:cost_usd).to_f.round(4),
          total_requests: scope.count,
          successful_requests: scope.successful.count,
          failed_requests: scope.failed.count,
          total_tokens: scope.sum(:total_tokens),
          avg_latency_ms: scope.successful.average(:latency_ms)&.to_f&.round(2) || 0
        }
      end

      def last_30_days_stats
        scope = LlmUsage
          .where(account_id: current_account.id)
          .where("created_at >= ?", 30.days.ago)

        {
          total_cost: scope.sum(:cost_usd).to_f.round(4),
          total_requests: scope.count,
          successful_requests: scope.successful.count,
          failed_requests: scope.failed.count,
          total_tokens: scope.sum(:total_tokens),
          avg_latency_ms: scope.successful.average(:latency_ms)&.to_f&.round(2) || 0
        }
      end

      def stats_by_model
        LlmUsage.usage_stats_by_model(current_account.id).map do |stat|
          {
            model: stat.model,
            request_count: stat.request_count,
            total_input_tokens: stat.total_input_tokens.to_i,
            total_output_tokens: stat.total_output_tokens.to_i,
            total_tokens: stat.total_tokens.to_i,
            total_cost: stat.total_cost.to_f.round(6),
            avg_latency_ms: stat.avg_latency_ms.to_f.round(2)
          }
        end
      end

      def stats_by_operation
        scope = LlmUsage
          .where(account_id: current_account.id)
          .successful
          .where("created_at >= ?", 30.days.ago)
          .group(:operation)
          .select(
            "operation",
            "COUNT(*) as count",
            "SUM(cost_usd) as total_cost",
            "AVG(latency_ms) as avg_latency"
          )

        scope.map do |stat|
          {
            operation: stat.operation,
            count: stat.count,
            total_cost: stat.total_cost.to_f.round(6),
            avg_latency_ms: stat.avg_latency.to_f.round(2)
          }
        end
      end

      def daily_trend
        LlmUsage.daily_costs(current_account.id, days: 7).map do |day|
          {
            date: day.date,
            total_cost: day.total_cost.to_f.round(4)
          }
        end
      end

      def llm_usage_params
        params.require(:llm_usage).permit(
          :model,
          :operation,
          :input_tokens,
          :output_tokens,
          :total_tokens,
          :cost_usd,
          :latency_ms,
          :success,
          :error_message,
          context: {}
        )
      end
    end
  end
end
