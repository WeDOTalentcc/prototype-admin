# frozen_string_literal: true

module Evaluations
  class ResponseRatesService
    def initialize(evaluation_ids: nil, job_ids: nil, min_rate: nil, max_rate: nil, include_pending: false)
      @evaluation_ids = evaluation_ids ? Array(evaluation_ids).compact.uniq.map(&:to_i) : nil
      @job_ids = job_ids ? Array(job_ids).compact.uniq.map(&:to_i) : nil
      @min_rate = min_rate&.to_f
      @max_rate = max_rate&.to_f
      @include_pending = include_pending
    end

    def call
      evaluations = load_evaluations
      return empty_result if evaluations.empty?

      stats = evaluations.map { |e| build_stats(e) }.compact
      filtered = apply_filters(stats)

      {
        success: true,
        data: filtered,
        meta: build_meta(stats, filtered)
      }
    rescue StandardError => e
      Rails.logger.error "[Evaluations::ResponseRatesService] #{e.message}"
      { success: false, error: e.message }
    end

    private

    attr_reader :evaluation_ids, :job_ids, :min_rate, :max_rate, :include_pending

    def load_evaluations
      scope = Evaluation.where(is_deleted: false)
      scope = scope.where(id: evaluation_ids) if evaluation_ids
      scope = scope.where(job_id: job_ids) if job_ids
      scope.includes(:evaluation_candidates, :job)
    end

    def build_stats(evaluation)
      candidates = evaluation.evaluation_candidates.to_a
      total_sent = candidates.size
      completed = candidates.select(&:completed)
      total_completed = completed.size
      total_pending = total_sent - total_completed
      response_rate = total_sent.positive? ? ((total_completed.to_f / total_sent) * 100).round(2) : 0.0

      scored = completed.select { |c| c.score.to_f > 0 }
      avg_score = scored.any? ? (scored.sum { |c| c.score.to_f } / scored.size).round(2) : nil

      result = {
        evaluation_id: evaluation.id,
        evaluation_name: evaluation.name,
        job_id: evaluation.job_id,
        job_title: evaluation.job&.title,
        is_active: evaluation.status,
        is_screening: evaluation.is_screening,
        total_sent: total_sent,
        total_completed: total_completed,
        total_pending: total_pending,
        response_rate: response_rate,
        completion_rate: total_sent.positive? ? ((total_completed.to_f / total_sent) * 100).round(2) : 0.0,
        avg_score: avg_score
      }

      result[:pending_candidates] = pending_candidates_list(candidates) if include_pending

      result
    end

    def pending_candidates_list(candidates)
      pending = candidates.select { |ec| !ec.completed }
      candidate_ids = pending.map(&:candidate_id).compact.uniq
      candidates_map = Candidate.where(id: candidate_ids).index_by(&:id)

      pending.map do |ec|
        candidate = candidates_map[ec.candidate_id]
        {
          evaluation_candidate_id: ec.id,
          candidate_id: ec.candidate_id,
          candidate_name: candidate&.name,
          candidate_email: candidate&.email,
          sent_at: ec.created_at&.iso8601,
          is_expired: ec.date_expiration.present? && ec.date_expiration < Time.current
        }
      end
    end

    def apply_filters(stats)
      result = stats
      result = result.select { |s| s[:response_rate] >= min_rate } if min_rate
      result = result.select { |s| s[:response_rate] <= max_rate } if max_rate
      result
    end

    def build_meta(all_stats, filtered_stats)
      total_sent_all = all_stats.sum { |s| s[:total_sent] }
      total_completed_all = all_stats.sum { |s| s[:total_completed] }
      overall_rate = total_sent_all.positive? ? ((total_completed_all.to_f / total_sent_all) * 100).round(2) : 0.0

      {
        total_evaluations: all_stats.size,
        filtered_count: filtered_stats.size,
        overall_response_rate: overall_rate,
        overall_total_sent: total_sent_all,
        overall_total_completed: total_completed_all,
        computed_at: Time.current.iso8601
      }
    end

    def empty_result
      { success: true, data: [], meta: { total_evaluations: 0, filtered_count: 0, computed_at: Time.current.iso8601 } }
    end
  end
end
