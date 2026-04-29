# frozen_string_literal: true

module Evaluations
  class ResetCandidateService
    Result = Struct.new(:success?, :data, :errors, keyword_init: true)

    def initialize(apply:)
      @apply = apply
    end

    def call
      return fail_result("Apply not found") unless @apply
      return fail_result("No evaluation candidates found") if evaluation_candidates.empty?

      ActiveRecord::Base.transaction do
        cleanup_issues
        cleanup_interview_sessions
        cleanup_answers
        destroy_evaluation_candidates
        reset_apply_status
      end

      success_result(deleted_count: @deleted_count)
    rescue StandardError => e
      Rails.logger.error "❌ [Evaluations::ResetCandidateService] #{e.message}"
      Rails.logger.error e.backtrace.first(5).join("\n")
      fail_result(e.message)
    end

    private

    attr_reader :apply

    def evaluation_candidates
      @evaluation_candidates ||= EvaluationCandidate.where(
        candidate_id: apply.candidate_id,
        job_id: apply.job_id,
        account_id: apply.account_id
      )
    end

    def ec_ids
      @ec_ids ||= evaluation_candidates.pluck(:id)
    end

    def cleanup_issues
      Issue.where(evaluation_candidate_id: ec_ids).delete_all
    end

    def cleanup_interview_sessions
      InterviewSession.where(evaluation_candidate_id: ec_ids)
                      .update_all(evaluation_candidate_id: nil, status: "cancelled")
    end

    def cleanup_answers
      evaluation_candidates.each do |ec|
        Answer.where(evaluation_id: ec.evaluation_id, candidate_id: ec.candidate_id).delete_all
      end
    end

    def destroy_evaluation_candidates
      @deleted_count = evaluation_candidates.delete_all
    end

    def reset_apply_status
      apply.update!(evaluation_candidate_status: :pending)
    end

    def success_result(data)
      Result.new(success?: true, data: data, errors: [])
    end

    def fail_result(errors)
      Result.new(success?: false, data: nil, errors: Array(errors))
    end
  end
end
