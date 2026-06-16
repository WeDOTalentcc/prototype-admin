# frozen_string_literal: true

module Evaluations
  class BulkDashboardStatsService
    def initialize(evaluation_ids: nil, min_response_rate: nil)
      @evaluation_ids = evaluation_ids ? Array(evaluation_ids).compact.uniq.map(&:to_i) : nil
      @min_response_rate = min_response_rate&.to_f
    end

    def call
      evaluations = load_evaluations
      return [] if evaluations.empty?

      stats_data = compute_bulk_stats(evaluations)
      filtered_data = apply_filters(stats_data)

      {
        success: true,
        data: filtered_data,
        meta: {
          total_evaluations: stats_data.size,
          filtered_count: filtered_data.size,
          computed_at: Time.current.iso8601
        }
      }
    rescue StandardError => e
      Rails.logger.error "[Evaluations::BulkDashboardStatsService] Error: #{e.message}"
      Rails.logger.error e.backtrace.first(5).join("\n")
      { success: false, error: e.message }
    end

    private

    def load_evaluations
      scope = @evaluation_ids ? Evaluation.where(id: @evaluation_ids) : Evaluation.where(is_deleted: false)
      scope.includes(:evaluation_candidates, :job)
    end

    def compute_bulk_stats(evaluations)
      evaluations.map do |evaluation|
        build_evaluation_stats(evaluation)
      rescue StandardError => e
        Rails.logger.error "[Evaluations::BulkDashboardStatsService] Failed for Evaluation##{evaluation.id}: #{e.message}"
        nil
      end.compact
    end

    def build_evaluation_stats(evaluation)
      candidates = evaluation.evaluation_candidates
      total_sent = candidates.size
      total_responded = candidates.count(&:completed)
      response_rate = total_sent.positive? ? ((total_responded.to_f / total_sent) * 100).round(2) : 0.0

      {
        evaluation_id: evaluation.id,
        name: evaluation.name,
        job_id: evaluation.job_id,
        job_title: evaluation.job&.title,
        is_active: evaluation.status,
        total_sent: total_sent,
        total_responded: total_responded,
        total_pending: total_sent - total_responded,
        response_rate: response_rate,
        avg_score: begin
          scored = candidates.select { |c| c.completed && c.score.to_f > 0 }
          scored.any? ? (scored.sum { |c| c.score.to_f } / scored.size).round(2) : nil
        end,
        is_screening: evaluation.is_screening,
        ai_enabled: evaluation.ai_enabled
      }
    end

    def apply_filters(stats_data)
      return stats_data unless @min_response_rate

      stats_data.select { |stat| stat[:response_rate] >= @min_response_rate }
    end
  end
end
