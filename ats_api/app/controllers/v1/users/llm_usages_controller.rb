# frozen_string_literal: true

module V1
  module Users
    class LlmUsagesController < ApplicationController
      def index
        perform_search(
          model: LlmUsage,
          serializer: LlmUsageSerializer
        )
      end

      def show
        usage = LlmUsage.find_by(id: params[:id], account_id: @current_user.account_id)
        return render_not_found("LlmUsage") unless usage

        render_success(usage, serializer: LlmUsageSerializer)
      end

      def create
        usage = LlmUsage.new(
          usage_params.merge(
            user_id: @current_user.id,
            account_id: @current_user.account_id
          )
        )

        return render_success(usage, serializer: LlmUsageSerializer, status: :created) if usage.save

        render_error(usage, status: :unprocessable_entity)
      end

      def stats
        scope = base_scope

        render json: {
          success: true,
          data: {
            today: period_stats(scope.today),
            this_week: period_stats(scope.where("created_at >= ?", Time.current.beginning_of_week)),
            this_month: period_stats(scope.this_month),
            last_30_days: period_stats(scope.where("created_at >= ?", 30.days.ago))
          }
        }
      end

      def by_model
        rows = base_scope
          .where("created_at >= ?", date_from)
          .group(:model)
          .select(
            "model",
            "COUNT(*) as request_count",
            "SUM(input_tokens) as total_input_tokens",
            "SUM(output_tokens) as total_output_tokens",
            "SUM(total_tokens) as total_tokens",
            "SUM(cost_usd) as total_cost",
            "AVG(latency_ms) as avg_latency_ms"
          )
          .order("total_cost DESC")

        render json: {
          success: true,
          data: rows.map { |r| serialize_model_row(r) }
        }
      end

      def by_operation
        rows = base_scope
          .where("created_at >= ?", date_from)
          .group(:operation)
          .select(
            "operation",
            "COUNT(*) as request_count",
            "SUM(total_tokens) as total_tokens",
            "SUM(cost_usd) as total_cost",
            "AVG(latency_ms) as avg_latency_ms"
          )
          .order("total_cost DESC")

        render json: {
          success: true,
          data: rows.map { |r| serialize_operation_row(r) }
        }
      end

      def by_service
        rows = base_scope
          .where("created_at >= ?", date_from)
          .where("context->>'service' IS NOT NULL")
          .group("context->>'service'")
          .select(
            "context->>'service' as service_name",
            "COUNT(*) as request_count",
            "SUM(total_tokens) as total_tokens",
            "SUM(cost_usd) as total_cost",
            "AVG(latency_ms) as avg_latency_ms"
          )
          .order("total_cost DESC")

        render json: {
          success: true,
          data: rows.map { |r| serialize_service_row(r) }
        }
      end

      def daily_trend
        days = (params[:days] || 30).to_i.clamp(1, 90)

        rows = base_scope
          .where("created_at >= ?", days.days.ago)
          .group("DATE(created_at)")
          .select(
            "DATE(created_at) as date",
            "COUNT(*) as request_count",
            "SUM(cost_usd) as total_cost",
            "SUM(total_tokens) as total_tokens",
            "COUNT(*) FILTER (WHERE success = false) as failed_count"
          )
          .order("date ASC")

        render json: {
          success: true,
          data: rows.map do |r|
            {
              date: r.date.to_s,
              request_count: r.request_count,
              total_cost: r.total_cost.to_f.round(6),
              total_tokens: r.total_tokens.to_i,
              failed_count: r.failed_count
            }
          end
        }
      end

      def failures
        scope = base_scope.failed.where("created_at >= ?", date_from).order(created_at: :desc).limit(100)

        render json: {
          success: true,
          data: scope.map { |u| serialize_failure(u) }
        }
      end

      def recent
        limit = (params[:limit] || 50).to_i.clamp(1, 200)
        scope = base_scope
          .where("created_at >= ?", date_from)
          .includes(:user)
          .order(created_at: :desc)
          .limit(limit)

        render json: {
          success: true,
          data: scope.map { |u| serialize_recent(u) }
        }
      end

      def top_consumers
        rows = base_scope
          .where("llm_usages.created_at >= ?", date_from)
          .joins(:user)
          .group("users.id", "users.name", "users.email")
          .select(
            "users.id as user_id",
            "users.name as user_name",
            "users.email as user_email",
            "COUNT(*) as request_count",
            "SUM(cost_usd) as total_cost",
            "SUM(total_tokens) as total_tokens"
          )
          .order("total_cost DESC")
          .limit(20)

        render json: {
          success: true,
          data: rows.map do |r|
            {
              user_id: r.user_id,
              user_name: r.user_name,
              user_email: r.user_email,
              request_count: r.request_count,
              total_cost: r.total_cost.to_f.round(6),
              total_tokens: r.total_tokens.to_i
            }
          end
        }
      end

      private

      def base_scope
        LlmUsage.where(account_id: @current_user.account_id)
      end

      def date_from
        return Time.zone.parse(params[:from]) if params[:from].present?

        30.days.ago
      end

      def period_stats(scope)
        {
          total_cost: scope.sum(:cost_usd).to_f.round(6),
          total_requests: scope.count,
          successful_requests: scope.successful.count,
          failed_requests: scope.failed.count,
          total_tokens: scope.sum(:total_tokens),
          total_input_tokens: scope.sum(:input_tokens),
          total_output_tokens: scope.sum(:output_tokens),
          avg_latency_ms: scope.successful.average(:latency_ms)&.to_f&.round(2) || 0
        }
      end

      def serialize_model_row(row)
        {
          model: row.model,
          request_count: row.request_count,
          total_input_tokens: row.total_input_tokens.to_i,
          total_output_tokens: row.total_output_tokens.to_i,
          total_tokens: row.total_tokens.to_i,
          total_cost: row.total_cost.to_f.round(6),
          avg_latency_ms: row.avg_latency_ms.to_f.round(2)
        }
      end

      def serialize_operation_row(row)
        {
          operation: row.operation,
          request_count: row.request_count,
          total_tokens: row.total_tokens.to_i,
          total_cost: row.total_cost.to_f.round(6),
          avg_latency_ms: row.avg_latency_ms.to_f.round(2)
        }
      end

      def serialize_service_row(row)
        {
          service: row.service_name,
          request_count: row.request_count,
          total_tokens: row.total_tokens.to_i,
          total_cost: row.total_cost.to_f.round(6),
          avg_latency_ms: row.avg_latency_ms.to_f.round(2)
        }
      end

      def serialize_failure(usage)
        {
          id: usage.id,
          model: usage.model,
          operation: usage.operation,
          error_message: usage.error_message,
          latency_ms: usage.latency_ms.to_f.round(2),
          context: usage.context,
          created_at: usage.created_at.iso8601
        }
      end

      def serialize_recent(usage)
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
          service: usage.context&.dig("service"),
          feature: usage.context&.dig("feature"),
          user_name: usage.user&.name,
          user_email: usage.user&.email,
          created_at: usage.created_at.iso8601
        }
      end

      def usage_params
        params.require(:llm_usage).permit(
          :model, :operation, :input_tokens, :output_tokens,
          :total_tokens, :cost_usd, :latency_ms, :success,
          :error_message, context: {}
        )
      end
    end
  end
end
